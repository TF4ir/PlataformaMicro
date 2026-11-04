"""Retention inference orchestration service.

Addresses Section 4 of TASK M5.3:
Combines causal history reconstruction, standardized KC difficulty referencing,
model registry lookups, multi-horizon retention projection, and persistence into
the canonical predictions table.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import asyncpg

from app.prediction.history_builder import (
    UnifiedHistoryBuilder,
)
from app.prediction.kc_reference_resolver import KCReferenceResolver
from app.prediction.model_registry import RetentionModelRegistry
from app.schemas.prediction import (
    HorizonPrediction,
    KCRetentionPrediction,
    ModelAvailabilityStatus,
    RiskLevelEnum,
    StudentRetentionSummaryResponse,
)

logger = logging.getLogger(__name__)


def _categorize_risk(recall_prob: float) -> RiskLevelEnum:
    """Categorize forgetting risk level based on recall probability."""
    if recall_prob >= 0.80:
        return RiskLevelEnum.LOW
    elif recall_prob >= 0.65:
        return RiskLevelEnum.MEDIUM
    elif recall_prob >= 0.45:
        return RiskLevelEnum.HIGH
    return RiskLevelEnum.CRITICAL


class RetentionInferenceService:
    """Orchestrates temporal retention inference for students."""

    def __init__(
        self,
        history_builder: UnifiedHistoryBuilder | None = None,
        model_registry: RetentionModelRegistry | None = None,
    ) -> None:
        self.history_builder = history_builder or UnifiedHistoryBuilder()
        self.model_registry = model_registry or RetentionModelRegistry()

    async def get_student_retention_profile(
        self,
        pool: asyncpg.Pool,
        student_id: uuid.UUID,
        tenant_id: uuid.UUID,
        knowledge_component_id: uuid.UUID | None = None,
        tau: float = 0.650,
        horizons_hours: list[int] | None = None,
        persist_predictions: bool = True,
    ) -> StudentRetentionSummaryResponse:
        """Evaluate retention for all accessible KCs for the student."""
        if horizons_hours is None:
            # Default evaluation horizons: 24h (1d), 72h (3d), 168h (7d / primary research horizon)
            horizons_hours = [24, 72, 168]

        cutoff_time = datetime.now(UTC)

        # 1. Fetch causal histories
        histories = await self.history_builder.fetch_student_kc_history(
            pool=pool,
            student_id=student_id,
            tenant_id=tenant_id,
            knowledge_component_id=knowledge_component_id,
            reference_time=cutoff_time,
        )

        # 2. Get active model and environment status
        model, metadata, global_status = self.model_registry.get_active_model()

        kc_predictions: list[KCRetentionPrediction] = []
        prediction_inserts: list[dict[str, Any]] = []

        for kc_id, summary in histories.items():
            total_interactions = summary.total_exposures + summary.total_retrieval_attempts

            # Check cold-start condition per KC
            if total_interactions < 3:
                kc_status = ModelAvailabilityStatus.COLD_START
            else:
                kc_status = global_status

            # Handle states where ML model cannot run
            if (
                model is None
                or kc_status
                in (
                    ModelAvailabilityStatus.COLD_START,
                    ModelAvailabilityStatus.INSUFFICIENT_EMPIRICAL_DATA,
                    ModelAvailabilityStatus.MODEL_UNAVAILABLE,
                )
            ):
                # Standard prior heuristic without fabricating individual model estimates
                p_current = max(0.20, min(0.80, 1.0 - summary.kc_difficulty_prior))
                risk_current = round(1.0 - p_current, 4)

                kc_predictions.append(
                    KCRetentionPrediction(
                        knowledge_component_id=kc_id,
                        knowledge_component_name=summary.knowledge_component_name,
                        current_recall_probability=round(p_current, 4),
                        current_forgetting_risk=risk_current,
                        predicted_forgetting_time_seconds=None,
                        predicted_forgetting_time_days=None,
                        recommended_review_time=None,
                        tau_threshold=tau,
                        model_name=metadata.model_name if metadata else "rule_based_fallback",
                        model_version=metadata.model_version if metadata else "1.0.0",
                        availability_status=kc_status,
                        horizons=[],
                        input_event_cutoff=cutoff_time,
                        total_exposures=summary.total_exposures,
                        total_retrieval_attempts=summary.total_retrieval_attempts,
                        last_interaction_at=summary.last_interaction_at,
                    )
                )
                continue

            # Standardized KC difficulty logit reference
            KCReferenceResolver.resolve_reference_difficulty_logit(summary.kc_difficulty_prior)

            # Fit model on student KC history if needed
            model.fit(summary.interaction_events)

            # Predict current retention (delta = 0)
            p_now = model.predict_retention(
                student_id=str(student_id),
                kc_id=str(kc_id),
                delta_seconds=0.0,
                history=summary.interaction_events,
                reference_time=cutoff_time,
            )
            p_now = float(max(0.01, min(0.99, p_now)))
            risk_now = round(1.0 - p_now, 4)

            # Projections across horizons
            horizon_items: list[HorizonPrediction] = []
            for h in sorted(horizons_hours):
                p_h = model.predict_retention(
                    student_id=str(student_id),
                    kc_id=str(kc_id),
                    delta_seconds=h * 3600.0,
                    history=summary.interaction_events,
                    reference_time=cutoff_time,
                )
                p_h = float(max(0.01, min(0.99, p_h)))
                risk_h = round(1.0 - p_h, 4)
                horizon_items.append(
                    HorizonPrediction(
                        horizon_hours=h,
                        predicted_recall_probability=round(p_h, 4),
                        estimated_risk=risk_h,
                        risk_level=_categorize_risk(p_h),
                    )
                )

            # Critical forgetting time (delta where P <= tau)
            t_crit_sec = model.predict_forgetting_time(
                student_id=str(student_id),
                kc_id=str(kc_id),
                tau=tau,
                history=summary.interaction_events,
                reference_time=cutoff_time,
            )

            t_crit_days: float | None = None
            review_time: datetime | None = None

            if t_crit_sec is not None:
                t_crit_days = round(t_crit_sec / 86400.0, 2)
                if t_crit_sec <= 0.0:
                    # Threshold already crossed -> recommend immediate review
                    review_time = cutoff_time
                else:
                    # Preventive review scheduled at 85% of critical forgetting time
                    review_window_sec = t_crit_sec * 0.85
                    review_time = cutoff_time + timedelta(seconds=review_window_sec)

            pred_item = KCRetentionPrediction(
                knowledge_component_id=kc_id,
                knowledge_component_name=summary.knowledge_component_name,
                current_recall_probability=round(p_now, 4),
                current_forgetting_risk=risk_now,
                predicted_forgetting_time_seconds=t_crit_sec,
                predicted_forgetting_time_days=t_crit_days,
                recommended_review_time=review_time,
                tau_threshold=tau,
                model_name=metadata.model_name if metadata else model.name,
                model_version=metadata.model_version if metadata else model.version,
                availability_status=kc_status,
                horizons=horizon_items,
                input_event_cutoff=cutoff_time,
                total_exposures=summary.total_exposures,
                total_retrieval_attempts=summary.total_retrieval_attempts,
                last_interaction_at=summary.last_interaction_at,
            )
            kc_predictions.append(pred_item)

            # Primary 7-day (168h) record for persistence
            primary_horizon = 168
            p_primary = p_now
            for h_item in horizon_items:
                if h_item.horizon_hours == 168:
                    p_primary = h_item.predicted_recall_probability
                    break

            prediction_inserts.append(
                {
                    "id": uuid.uuid4(),
                    "tenant_id": tenant_id,
                    "student_id": student_id,
                    "knowledge_component_id": kc_id,
                    "prediction_horizon_hours": primary_horizon,
                    "predicted_recall_probability": p_primary,
                    "estimated_risk": round(1.0 - p_primary, 4),
                    "risk_level": _categorize_risk(p_primary).value,
                    "input_event_cutoff": cutoff_time,
                    "prediction_status": "valid" if kc_status == ModelAvailabilityStatus.EMPIRICAL_MODEL_READY else "degraded_fallback",
                    "predicted_forgetting_time_seconds": t_crit_sec,
                    "tau_threshold": tau,
                }
            )

        # 3. Persist predictions asynchronously
        if persist_predictions and prediction_inserts:
            await self._persist_predictions_batch(pool, prediction_inserts)

        audit_msg = (
            f"Evaluated {len(kc_predictions)} KCs at {cutoff_time.isoformat()} with {global_status.value}."
        )

        return StudentRetentionSummaryResponse(
            student_id=student_id,
            as_of=cutoff_time,
            status=global_status,
            kcs=kc_predictions,
            audit_note=audit_msg,
        )

    async def _persist_predictions_batch(
        self,
        pool: asyncpg.Pool,
        records: list[dict[str, Any]],
    ) -> None:
        """Insert prediction records into PostgreSQL predictions table."""
        async with pool.acquire() as conn:
            for r in records:
                try:
                    await conn.execute(
                        """
                        INSERT INTO predictions (
                            id, tenant_id, student_id, knowledge_component_id,
                            prediction_horizon_hours, predicted_recall_probability,
                            estimated_risk, risk_level, input_event_cutoff,
                            prediction_status, predicted_forgetting_time_seconds, tau_threshold
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8::risk_level_enum, $9, $10::prediction_status_enum, $11, $12)
                        """,
                        r["id"],
                        r["tenant_id"],
                        r["student_id"],
                        r["knowledge_component_id"],
                        r["prediction_horizon_hours"],
                        r["predicted_recall_probability"],
                        r["estimated_risk"],
                        r["risk_level"],
                        r["input_event_cutoff"],
                        r["prediction_status"],
                        r["predicted_forgetting_time_seconds"],
                        r["tau_threshold"],
                    )
                except (asyncpg.PostgresError, OSError) as exc:
                    logger.warning("Non-blocking prediction telemetry persistence error: %s", exc)
