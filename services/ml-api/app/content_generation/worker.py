"""Durable background worker for consuming and processing queued content generation jobs.

Features:
- Atomic lease acquisition via SELECT FOR UPDATE SKIP LOCKED.
- Continuous heartbeat lease extension during long document extractions.
- Automatic reclamation of abandoned jobs from crashed workers.
- Max attempt limits and fence-token protection.
- Can run standalone as a background daemon or invoked programmatically.
"""

import asyncio
import logging
import os
import signal
import uuid

import asyncpg

from app.content_generation.exceptions import ContentGenerationError
from app.content_generation.infrastructure.database import (
    close_db_pool,
    get_db_pool,
)
from app.content_generation.infrastructure.postgres_draft_repository import (
    PostgresDraftRepository,
)
from app.content_generation.infrastructure.postgres_job_repository import (
    PostgresJobRepository,
)
from app.content_generation.infrastructure.unit_of_work import (
    PostgresUnitOfWork,
)
from app.content_generation.repositories.job_repository import (
    ContentGenerationJobRecord,
    JobRepositoryProtocol,
)
from app.content_generation.repositories.storage_client import (
    StorageClientProtocol,
    SupabaseStorageClient,
)
from app.content_generation.services.draft_validation_service import (
    DraftValidationService,
)
from app.content_generation.services.extraction_service import (
    DocumentExtractionService,
)
from app.content_generation.services.generation_orchestrator import (
    GenerationOrchestrator,
)
from app.content_generation.services.question_generation_service import (
    QuestionGenerationService,
)

logger = logging.getLogger(__name__)


class GenerationWorker:
    """Durable worker polling PostgreSQL for queued/abandoned jobs using atomic leases."""

    def __init__(
        self,
        job_repository: JobRepositoryProtocol,
        orchestrator: GenerationOrchestrator,
        worker_id: str | None = None,
        lease_duration_seconds: int = 300,
        heartbeat_interval_seconds: int = 30,
        poll_interval_seconds: float = 1.0,
    ) -> None:
        self._job_repo = job_repository
        self._orchestrator = orchestrator
        self._worker_id = worker_id or str(uuid.uuid4())
        self._lease_duration = lease_duration_seconds
        self._heartbeat_interval = heartbeat_interval_seconds
        self._poll_interval = poll_interval_seconds
        self._running = False

    async def _heartbeat_loop(self, job_id: str, tenant_id: str, lease_token: str) -> None:
        """Periodically renew lease and update heartbeat while generation is in progress."""
        try:
            while True:
                await asyncio.sleep(self._heartbeat_interval)
                success = await self._job_repo.heartbeat(
                    job_id=job_id,
                    tenant_id=tenant_id,
                    lease_token=lease_token,
                )
                if success:
                    await self._job_repo.renew_lease(
                        job_id=job_id,
                        tenant_id=tenant_id,
                        lease_token=lease_token,
                        extension_seconds=self._lease_duration,
                    )
                    logger.debug(
                        "Worker %s renewed lease for job %s with token %s",
                        self._worker_id,
                        job_id,
                        lease_token,
                    )
                else:
                    logger.warning(
                        "Heartbeat failed for job %s; lease may have expired or been reclaimed",
                        job_id,
                    )
                    break
        except asyncio.CancelledError:
            pass

    async def process_job(self, job: ContentGenerationJobRecord) -> bool:
        """Process a single claimed job with active heartbeat monitoring."""
        lease_token = job.processing_lease_token or str(uuid.uuid4())
        logger.info(
            "Worker %s executing job %s (tenant: %s, attempt: %d/%d)",
            self._worker_id,
            job.id,
            job.tenant_id,
            job.attempt_count,
            job.max_attempts,
        )

        heartbeat_task = asyncio.create_task(
            self._heartbeat_loop(job.id, job.tenant_id, lease_token)
        )

        try:
            await self._orchestrator.execute_job(
                job_id=job.id,
                tenant_id=job.tenant_id,
                requesting_user_id=job.created_by,
                lease_token=lease_token,
            )
            logger.info("Successfully completed processing for job %s", job.id)
            return True
        except ContentGenerationError as e:
            logger.warning(
                "Controlled generation error for job %s: [%s] %s",
                job.id,
                e.code,
                e.message_safe,
            )
            return False
        except Exception:
            logger.exception("Unexpected error executing job %s", job.id)
            return False
        finally:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass

    async def process_one(
        self,
        tenant_id: str | None = None,
        job_id: str | None = None,
    ) -> bool:
        """Attempt to claim and process a single eligible job. Returns True if a job was processed."""
        worker_token = str(uuid.uuid4())
        claimed_job = await self._job_repo.claim_pending_job(
            tenant_id=tenant_id,
            lease_duration_seconds=self._lease_duration,
            worker_token=worker_token,
            job_id=job_id,
        )
        if not claimed_job:
            return False

        return await self.process_job(claimed_job)

    async def run_loop(self) -> None:
        """Run continuous worker polling loop."""
        self._running = True
        logger.info("Generation worker %s started.", self._worker_id)
        while self._running:
            try:
                processed = await self.process_one()
                if not processed:
                    await asyncio.sleep(self._poll_interval)
            except asyncio.CancelledError:
                break
            except (asyncpg.PostgresError, OSError) as e:
                logger.error("Error in worker polling loop: %s", e)
                await asyncio.sleep(self._poll_interval)
        logger.info("Generation worker %s stopped.", self._worker_id)

    def stop(self) -> None:
        """Signal worker to stop gracefully."""
        self._running = False


async def create_production_worker(
    storage_client: StorageClientProtocol | None = None,
    lease_duration_seconds: int = 300,
    poll_interval_seconds: float = 1.0,
) -> GenerationWorker:
    """Factory creating a production GenerationWorker configured with PostgreSQL pool."""
    pool = await get_db_pool()
    job_repo = PostgresJobRepository(pool)
    draft_repo = PostgresDraftRepository(pool)
    uow = PostgresUnitOfWork(pool, draft_repository=draft_repo)

    if storage_client is None:
        supabase_url = os.getenv("SUPABASE_URL", "http://localhost:54321")
        service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "dummy_service_role_key")
        storage_client = SupabaseStorageClient(
            supabase_url=supabase_url,
            service_role_key=service_role_key,
        )

    extraction_service = DocumentExtractionService(
        job_repository=job_repo,
        storage_client=storage_client,
    )
    validation_service = DraftValidationService()
    generation_service = QuestionGenerationService(validation_service=validation_service)
    orchestrator = GenerationOrchestrator(
        job_repository=job_repo,
        extraction_service=extraction_service,
        generation_service=generation_service,
        draft_repository=draft_repo,
        unit_of_work=uow,
    )

    return GenerationWorker(
        job_repository=job_repo,
        orchestrator=orchestrator,
        lease_duration_seconds=lease_duration_seconds,
        poll_interval_seconds=poll_interval_seconds,
    )


async def main() -> None:
    """CLI entrypoint for standalone worker process."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    logger.info("Starting standalone Content Generation Worker process...")

    worker = await create_production_worker()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, worker.stop)
        except NotImplementedError:
            pass

    try:
        await worker.run_loop()
    finally:
        await close_db_pool()
        logger.info("Worker process exited cleanly.")


if __name__ == "__main__":
    asyncio.run(main())
