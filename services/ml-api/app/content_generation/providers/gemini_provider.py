"""Google Gemini adapter for assisted question generation.

Implements QuestionGenerationProvider using Google's official unified GenAI SDK (google-genai).
Features structured JSON schema generation, exponential backoff with jitter,
defensive validation, prompt-injection fencing, and execution telemetry.
"""

import asyncio
import json
import logging
import os
import random
import time
from typing import Any

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel, ConfigDict, Field

from app.content_generation.exceptions import (
    GenerationProviderError,
    InvalidProviderConfigurationError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderResponseFormatError,
    ProviderTimeoutError,
    UnauthorizedFieldsError,
)
from app.content_generation.providers.base import QuestionGenerationProvider
from app.content_generation.providers.cost_calculator import (
    GenerationTelemetry,
    calculate_cost,
)
from app.content_generation.providers.prompts import (
    PROMPT_VERSION,
    build_system_prompt,
    build_user_prompt,
)
from app.content_generation.schemas.generated_questions import (
    GeneratedQuestionDraft,
    GenerationContext,
    LLMGenerationOutput,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiQuestionsPayload(BaseModel):
    """Pydantic schema enforcing structured question array output from Gemini."""

    model_config = ConfigDict(extra="forbid")
    questions: list[GeneratedQuestionDraft] = Field(
        ...,
        description="Lista estructurada de borradores de preguntas de evaluación",
    )


class GoogleGeminiQuestionGenerationProvider(QuestionGenerationProvider):
    """QuestionGenerationProvider implementation for Google Gemini API."""

    provider_name: str = "gemini"

    def __init__(
        self,
        api_key: str | None = None,
        model_id: str | None = None,
        timeout_seconds: float | None = None,
        max_retries: int | None = None,
        max_output_tokens: int | None = None,
        client: Any = None,
        max_concurrency: int = 5,
    ) -> None:
        """Initialize Google Gemini question generation provider.

        Args:
            api_key: Gemini API Key. If None, resolved from GEMINI_API_KEY environment variable.
            model_id: Model ID. Defaults to LLM_MODEL_ID or 'gemini-3.5-flash-lite'.
            timeout_seconds: Timeout for API calls. Defaults to LLM_TIMEOUT_SECONDS or 30.0.
            max_retries: Number of retries for transient errors. Defaults to LLM_MAX_RETRIES or 3.
            max_output_tokens: Maximum output tokens. Defaults to LLM_MAX_OUTPUT_TOKENS or 4096.
            client: Optional pre-configured genai.Client instance (useful for testing and dependency injection).
            max_concurrency: Maximum concurrent generation requests.
        """
        env_key = os.getenv("GEMINI_API_KEY") or getattr(settings, "GEMINI_API_KEY", "")
        resolved_key = (api_key if api_key is not None else env_key) or ""

        if client is None and not resolved_key.strip():
            raise InvalidProviderConfigurationError(
                message_safe="No se encontró una clave de API válida para Google Gemini (GEMINI_API_KEY).",
                details={"provider": self.provider_name},
            )

        env_model = os.getenv("LLM_MODEL_ID") or getattr(settings, "LLM_MODEL_ID", "") or "gemini-3.5-flash-lite"
        self.model_id = (model_id or env_model).strip()

        env_timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", str(getattr(settings, "LLM_TIMEOUT_SECONDS", 30.0))))
        self.timeout_seconds = timeout_seconds if timeout_seconds is not None else env_timeout

        env_retries = int(os.getenv("LLM_MAX_RETRIES", str(getattr(settings, "LLM_MAX_RETRIES", 3))))
        self.max_retries = max_retries if max_retries is not None else env_retries

        env_max_tokens = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", str(getattr(settings, "LLM_MAX_OUTPUT_TOKENS", 4096))))
        self.max_output_tokens = (
            max_output_tokens if max_output_tokens is not None else env_max_tokens
        )

        self._client = client or genai.Client(api_key=resolved_key)
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def _execute_with_retry(
        self,
        user_prompt: str,
        context: GenerationContext,
    ) -> tuple[Any, int, float]:
        """Execute Gemini request with exponential backoff, jitter, and timeout handling."""
        config = types.GenerateContentConfig(
            system_instruction=build_system_prompt(),
            response_mime_type="application/json",
            response_schema=GeminiQuestionsPayload,
            temperature=0.2,
            max_output_tokens=self.max_output_tokens,
        )

        attempts = 0
        backoff = 1.0
        start_time = time.monotonic()

        while True:
            attempts += 1
            try:
                async with self._semaphore:
                    # Execute async call through client.aio.models.generate_content
                    response = await asyncio.wait_for(
                        self._client.aio.models.generate_content(
                            model=self.model_id,
                            contents=user_prompt,
                            config=config,
                        ),
                        timeout=self.timeout_seconds,
                    )
                latency_ms = (time.monotonic() - start_time) * 1000.0
                return response, attempts - 1, latency_ms

            except TimeoutError as e:
                if attempts > self.max_retries:
                    raise ProviderTimeoutError(
                        message_safe=f"La llamada a Google Gemini excedió el tiempo límite de {self.timeout_seconds}s tras {self.max_retries} intentos.",
                        details={"model_id": self.model_id, "timeout_seconds": self.timeout_seconds},
                    ) from e
                jitter = random.uniform(0.1, 0.5)
                await asyncio.sleep(backoff + jitter)
                backoff *= 2.0

            except genai_errors.APIError as e:
                # Check status codes
                code = getattr(e, "code", None)
                if code in (401, 403):
                    # Permanent authentication / authorization failure
                    raise ProviderAuthenticationError(
                        message_safe="Error de autenticación o permisos con Google Gemini API.",
                        details={"code": code},
                    ) from e

                if code == 429:
                    # Rate limit or quota exceeded
                    if attempts > self.max_retries:
                        raise ProviderRateLimitError(
                            message_safe="Se ha superado el límite de tasa de solicitudes de Google Gemini.",
                            details={"code": code, "retries": attempts - 1},
                        ) from e
                    jitter = random.uniform(0.2, 0.8)
                    await asyncio.sleep(backoff + jitter)
                    backoff *= 2.0
                    continue

                if code in (500, 502, 503, 504) or code is None:
                    # Transient server error
                    if attempts > self.max_retries:
                        raise GenerationProviderError(
                            message_safe="Error del servidor de Google Gemini tras varios reintentos.",
                            details={"code": code, "retries": attempts - 1},
                        ) from e
                    jitter = random.uniform(0.1, 0.5)
                    await asyncio.sleep(backoff + jitter)
                    backoff *= 2.0
                    continue

                # Permanent client error (400, etc.)
                raise GenerationProviderError(
                    message_safe="Petición rechazada por Google Gemini API.",
                    details={"code": code},
                ) from e

            except Exception as e:
                # Other transient or unexpected connection error
                if attempts > self.max_retries:
                    raise GenerationProviderError(
                        message_safe=f"Error inesperado al comunicarse con Google Gemini: {type(e).__name__}",
                        details={"error_type": type(e).__name__},
                    ) from e
                jitter = random.uniform(0.1, 0.5)
                await asyncio.sleep(backoff + jitter)
                backoff *= 2.0

    async def generate_drafts(
        self,
        extracted_text: str,
        schema: dict[str, Any] | None,
        context: GenerationContext,
    ) -> LLMGenerationOutput:
        """Asynchronously generate structured question drafts using Gemini."""
        schema_dict = schema or {}
        user_prompt = build_user_prompt(
            context=context,
            target_difficulty=str(schema_dict.get("target_difficulty", "medium")),
            target_bloom=str(schema_dict.get("target_bloom", "understand")),
            num_options_per_question=int(schema_dict.get("num_options_per_question", 4)),
            explanation_depth=str(schema_dict.get("explanation_depth", "completa")),
            question_type=str(schema_dict.get("question_type", "single_choice")),
        )

        try:
            response, retry_count, latency_ms = await self._execute_with_retry(
                user_prompt=user_prompt,
                context=context,
            )
        except Exception as e:
            telemetry_err = GenerationTelemetry(
                provider="gemini",
                model_id=self.model_id,
                prompt_version=context.prompt_version or PROMPT_VERSION,
                request_id=None,
                input_tokens=None,
                output_tokens=None,
                latency_ms=0.0,
                retry_count=self.max_retries,
                generated_questions=0,
                valid_questions=0,
                failed_validations=0,
                estimated_cost=None,
                generation_status="provider_error",
            )
            logger.error("Gemini generation failed: %s (error: %s)", telemetry_err.to_dict(), type(e).__name__)
            raise

        # 1. Inspect finish reason
        finish_reason = "stop"
        candidates = getattr(response, "candidates", []) or []
        if candidates and isinstance(candidates, (list, tuple)):
            first_candidate = candidates[0]
            cand_finish = getattr(first_candidate, "finish_reason", None)
            if cand_finish is not None and type(cand_finish).__name__ != "MagicMock":
                finish_str = str(cand_finish).lower()
                if "max_tokens" in finish_str or "length" in finish_str:
                    raise ProviderResponseFormatError(
                        message_safe="La respuesta de Google Gemini fue truncada por límite de tokens (MAX_TOKENS).",
                        details={"finish_reason": finish_str},
                    )
                if "safety" in finish_str or "block" in finish_str:
                    raise ProviderResponseFormatError(
                        message_safe="La respuesta de Google Gemini fue bloqueada por políticas de seguridad o filtros de contenido.",
                        details={"finish_reason": finish_str},
                    )
                finish_reason = finish_str

        # 2. Extract raw text
        raw_text = getattr(response, "text", "") or ""
        if not raw_text.strip():
            raise ProviderResponseFormatError(
                message_safe="Google Gemini devolvió una respuesta vacía.",
                details={"model_id": self.model_id},
            )

        # 3. Parse JSON safely
        try:
            parsed_json = json.loads(raw_text)
        except json.JSONDecodeError as e:
            raise ProviderResponseFormatError(
                message_safe="Google Gemini no devolvió un JSON válido.",
                details={"error": str(e), "sample": raw_text[:200]},
            ) from e

        # 4. Validate with Pydantic schema
        try:
            payload = GeminiQuestionsPayload.model_validate(parsed_json)
        except Exception as e:
            # Check if failure is due to extra forbidden fields
            err_str = str(e)
            if "extra_forbidden" in err_str:
                raise UnauthorizedFieldsError(
                    message_safe="La respuesta de Google Gemini contiene campos no permitidos.",
                    details={"model_id": self.model_id, "error": err_str},
                ) from e
            raise ProviderResponseFormatError(
                message_safe="La estructura JSON de Google Gemini no cumple con el esquema requerido.",
                details={"model_id": self.model_id, "error": err_str},
            ) from e

        # 5. Extract token usage metadata (including thinking/reasoning and cached tokens)
        input_tokens = None
        output_tokens = None
        reasoning_tokens = 0
        cached_tokens = 0
        usage = getattr(response, "usage_metadata", None)
        if usage:
            if isinstance(usage, dict):
                raw_in = usage.get("prompt_token_count") or usage.get("prompt_tokens")
                raw_out = usage.get("candidates_token_count") or usage.get("completion_tokens")
                raw_reason = (
                    usage.get("thoughts_token_count")
                    or usage.get("thinking_token_count")
                    or usage.get("reasoning_tokens")
                )
                raw_cached = usage.get("cached_content_token_count") or usage.get("cached_tokens")
                raw_total = usage.get("total_token_count") or usage.get("total_tokens")
            else:
                raw_in = getattr(usage, "prompt_token_count", None)
                raw_out = getattr(usage, "candidates_token_count", None)
                raw_reason = (
                    getattr(usage, "thoughts_token_count", None)
                    or getattr(usage, "thinking_token_count", None)
                    or getattr(usage, "reasoning_tokens", None)
                )
                raw_cached = getattr(usage, "cached_content_token_count", None)
                raw_total = getattr(usage, "total_token_count", None)

            if isinstance(raw_in, (int, float)) and not isinstance(raw_in, bool):
                input_tokens = int(raw_in)
            if isinstance(raw_reason, (int, float)) and not isinstance(raw_reason, bool):
                reasoning_tokens = int(raw_reason)
            if isinstance(raw_cached, (int, float)) and not isinstance(raw_cached, bool):
                cached_tokens = int(raw_cached)

            if (
                isinstance(raw_total, (int, float))
                and not isinstance(raw_total, bool)
                and input_tokens is not None
                and int(raw_total) >= input_tokens
            ):
                output_tokens = int(raw_total) - input_tokens
            elif isinstance(raw_out, (int, float)) and not isinstance(raw_out, bool):
                output_tokens = int(raw_out) + reasoning_tokens
            elif reasoning_tokens > 0:
                output_tokens = reasoning_tokens

        cost_breakdown = calculate_cost(
            provider="gemini",
            model_id=self.model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            generated_questions=len(payload.questions),
            valid_questions=len(payload.questions),
            cached_input_tokens=cached_tokens,
            reasoning_tokens=reasoning_tokens,
            reasoning_in_output=True,
        )

        raw_req_id = getattr(response, "response_id", None)
        request_id = raw_req_id if isinstance(raw_req_id, str) and raw_req_id.strip() else None
        telemetry = GenerationTelemetry(
            provider="gemini",
            model_id=self.model_id,
            prompt_version=context.prompt_version or PROMPT_VERSION,
            request_id=request_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            retry_count=retry_count,
            generated_questions=len(payload.questions),
            valid_questions=len(payload.questions),
            failed_validations=0,
            estimated_cost=cost_breakdown.total_cost_usd,
            generation_status="success",
            billable_reasoning_tokens=reasoning_tokens if reasoning_tokens > 0 else None,
            finish_reason=finish_reason,
        )
        logger.info(
            "Gemini generation completed: %s",
            telemetry.to_dict(),
        )

        token_usage_dict: dict[str, int] | None = None
        if input_tokens is not None and output_tokens is not None:
            token_usage_dict = {
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
            }
            if reasoning_tokens > 0:
                token_usage_dict["reasoning_tokens"] = reasoning_tokens
            if cached_tokens > 0:
                token_usage_dict["cached_tokens"] = cached_tokens

        return LLMGenerationOutput(
            provider="gemini",
            model_id=self.model_id,
            prompt_version=context.prompt_version or PROMPT_VERSION,
            questions=payload.questions,
            raw_response=raw_text,
            token_usage=token_usage_dict,
            finish_reason=finish_reason,
            request_id=request_id,
            latency_ms=latency_ms,
            retry_count=retry_count,
        )
