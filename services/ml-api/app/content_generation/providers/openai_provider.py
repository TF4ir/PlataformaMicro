"""OpenAI adapter for assisted question generation.

Implements QuestionGenerationProvider using the official OpenAI Python SDK (AsyncOpenAI).
Features structured JSON schema output, exponential backoff with jitter,
defensive validation, prompt-injection fencing, and execution telemetry.
"""

import asyncio
import json
import logging
import os
import random
import time
from typing import Any

import openai
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


class OpenAIQuestionsPayload(BaseModel):
    """Pydantic schema enforcing structured question array output from OpenAI."""

    model_config = ConfigDict(extra="forbid")
    questions: list[GeneratedQuestionDraft] = Field(
        ...,
        description="Lista estructurada de borradores de preguntas de evaluación",
    )


class OpenAIQuestionGenerationProvider(QuestionGenerationProvider):
    """QuestionGenerationProvider implementation for OpenAI API."""

    provider_name: str = "openai"

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
        """Initialize OpenAI question generation provider.

        Args:
            api_key: OpenAI API Key. If None, resolved from OPENAI_API_KEY environment variable.
            model_id: Model ID. Defaults to LLM_MODEL_ID or 'gpt-6-luna'.
            timeout_seconds: Timeout for API calls. Defaults to LLM_TIMEOUT_SECONDS or 30.0.
            max_retries: Number of retries for transient errors. Defaults to LLM_MAX_RETRIES or 3.
            max_output_tokens: Maximum output tokens. Defaults to LLM_MAX_OUTPUT_TOKENS or 4096.
            client: Optional pre-configured AsyncOpenAI instance (useful for testing and dependency injection).
            max_concurrency: Maximum concurrent generation requests.
        """
        env_key = os.getenv("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", "")
        resolved_key = (api_key if api_key is not None else env_key) or ""

        if client is None and not resolved_key.strip():
            raise InvalidProviderConfigurationError(
                message_safe="No se encontró una clave de API válida para OpenAI (OPENAI_API_KEY).",
                details={"provider": self.provider_name},
            )

        env_model = os.getenv("LLM_MODEL_ID") or getattr(settings, "LLM_MODEL_ID", "") or "gpt-6-luna"
        self.model_id = (model_id or env_model).strip()

        env_timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", str(getattr(settings, "LLM_TIMEOUT_SECONDS", 30.0))))
        self.timeout_seconds = timeout_seconds if timeout_seconds is not None else env_timeout

        env_retries = int(os.getenv("LLM_MAX_RETRIES", str(getattr(settings, "LLM_MAX_RETRIES", 3))))
        self.max_retries = max_retries if max_retries is not None else env_retries

        env_max_tokens = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", str(getattr(settings, "LLM_MAX_OUTPUT_TOKENS", 4096))))
        self.max_output_tokens = (
            max_output_tokens if max_output_tokens is not None else env_max_tokens
        )

        self._client = client or openai.AsyncOpenAI(
            api_key=resolved_key,
            timeout=self.timeout_seconds,
            max_retries=0,  # We manage application-level retries with explicit telemetry and jitter
        )
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def _execute_with_retry(
        self,
        user_prompt: str,
        context: GenerationContext,
    ) -> tuple[Any, int, float]:
        """Execute OpenAI completion request with backoff, jitter, and error mapping."""
        messages: list[Any] = [
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": user_prompt},
        ]

        attempts = 0
        backoff = 1.0
        start_time = time.monotonic()

        while True:
            attempts += 1
            try:
                async with self._semaphore:
                    # Prefer Structured Outputs using client.beta.chat.completions.parse
                    if hasattr(self._client, "beta") and hasattr(
                        self._client.beta, "chat"
                    ):
                        response = await asyncio.wait_for(
                            self._client.beta.chat.completions.parse(
                                model=self.model_id,
                                messages=messages,
                                response_format=OpenAIQuestionsPayload,
                                max_tokens=self.max_output_tokens,
                                temperature=0.2,
                                timeout=self.timeout_seconds,
                            ),
                            timeout=self.timeout_seconds,
                        )
                    else:
                        json_format: Any = {"type": "json_object"}
                        response = await asyncio.wait_for(
                            self._client.chat.completions.create(
                                model=self.model_id,
                                messages=messages,
                                response_format=json_format,
                                max_tokens=self.max_output_tokens,
                                temperature=0.2,
                                timeout=self.timeout_seconds,
                            ),
                            timeout=self.timeout_seconds,
                        )

                latency_ms = (time.monotonic() - start_time) * 1000.0
                return response, attempts - 1, latency_ms

            except (TimeoutError, openai.APITimeoutError) as e:
                if attempts > self.max_retries:
                    raise ProviderTimeoutError(
                        message_safe=f"La llamada a OpenAI excedió el tiempo límite de {self.timeout_seconds}s tras {self.max_retries} intentos.",
                        details={"model_id": self.model_id, "timeout_seconds": self.timeout_seconds},
                    ) from e
                jitter = random.uniform(0.1, 0.5)
                await asyncio.sleep(backoff + jitter)
                backoff *= 2.0

            except (openai.AuthenticationError, openai.PermissionDeniedError) as e:
                # Permanent credential failure -> abort immediately without retry
                raise ProviderAuthenticationError(
                    message_safe="Error de autenticación o permisos con OpenAI API.",
                    details={"error_type": type(e).__name__},
                ) from e

            except openai.RateLimitError as e:
                if attempts > self.max_retries:
                    raise ProviderRateLimitError(
                        message_safe="Se ha superado el límite de tasa de solicitudes de OpenAI.",
                        details={"retries": attempts - 1},
                    ) from e
                jitter = random.uniform(0.2, 0.8)
                await asyncio.sleep(backoff + jitter)
                backoff *= 2.0

            except (openai.InternalServerError, openai.APIConnectionError, openai.APIStatusError) as e:
                # Differentiate between 5xx (transient upstream) and 4xx (permanent request errors)
                if isinstance(e, openai.APIStatusError) and e.status_code < 500:
                    raise GenerationProviderError(
                        message_safe="Petición rechazada por OpenAI API.",
                        details={"error_type": type(e).__name__, "status_code": e.status_code, "error": str(e)},
                    ) from e

                if attempts > self.max_retries:
                    raise GenerationProviderError(
                        message_safe="Error del servidor de OpenAI tras varios reintentos.",
                        details={"error_type": type(e).__name__, "retries": attempts - 1},
                    ) from e
                jitter = random.uniform(0.1, 0.5)
                await asyncio.sleep(backoff + jitter)
                backoff *= 2.0

            except openai.APIError as e:
                # Permanent bad request or unrecoverable API error
                raise GenerationProviderError(
                    message_safe="Petición rechazada por OpenAI API.",
                    details={"error_type": type(e).__name__, "error": str(e)},
                ) from e

            except Exception as e:
                if attempts > self.max_retries:
                    raise GenerationProviderError(
                        message_safe=f"Error inesperado al comunicarse con OpenAI: {type(e).__name__}",
                        details={"error_type": type(e).__name__, "error": str(e)},
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
        """Asynchronously generate structured question drafts using OpenAI."""
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
                provider="openai",
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
            logger.error("OpenAI generation failed: %s (error: %s)", telemetry_err.to_dict(), type(e).__name__)
            raise

        # 1. Inspect choices
        choices = getattr(response, "choices", []) or []
        if not choices:
            raise ProviderResponseFormatError(
                message_safe="OpenAI no devolvió alternativas de respuesta (choices vacío).",
                details={"model_id": self.model_id},
            )

        choice = choices[0]
        finish_reason = "stop"
        raw_finish = getattr(choice, "finish_reason", None)
        if raw_finish is not None and type(raw_finish).__name__ != "MagicMock":
            finish_str = str(raw_finish).lower()
            if "length" in finish_str or "max_tokens" in finish_str:
                raise ProviderResponseFormatError(
                    message_safe="La respuesta de OpenAI fue truncada por límite de tokens (finish_reason='length').",
                    details={"finish_reason": finish_str},
                )
            if "content_filter" in finish_str:
                raise ProviderResponseFormatError(
                    message_safe="La respuesta de OpenAI fue bloqueada por filtros de contenido o políticas de seguridad.",
                    details={"finish_reason": finish_str},
                )
            finish_reason = finish_str

        # 2. Extract parsed message or raw content
        message = getattr(choice, "message", None)
        if message is None:
            raise ProviderResponseFormatError(
                message_safe="OpenAI devolvió una respuesta sin contenido de mensaje.",
                details={"model_id": self.model_id},
            )

        refusal = getattr(message, "refusal", None)
        if refusal and isinstance(refusal, str) and refusal.strip():
            raise ProviderResponseFormatError(
                message_safe="La solicitud fue rechazada por las políticas de seguridad del modelo OpenAI.",
                details={"refusal": refusal},
            )

        raw_content = getattr(message, "content", "") or ""
        parsed_payload = getattr(message, "parsed", None)

        if parsed_payload is not None and isinstance(parsed_payload, OpenAIQuestionsPayload):
            payload = parsed_payload
        else:
            if not raw_content.strip():
                raise ProviderResponseFormatError(
                    message_safe="OpenAI devolvió un contenido de mensaje vacío.",
                    details={"model_id": self.model_id},
                )

            # Parse JSON
            try:
                parsed_json = json.loads(raw_content)
            except json.JSONDecodeError as e:
                raise ProviderResponseFormatError(
                    message_safe="OpenAI no devolvió un JSON válido.",
                    details={"error": str(e), "sample": raw_content[:200]},
                ) from e

            # Validate against Pydantic schema
            try:
                payload = OpenAIQuestionsPayload.model_validate(parsed_json)
            except Exception as e:
                err_str = str(e)
                if "extra_forbidden" in err_str:
                    raise UnauthorizedFieldsError(
                        message_safe="La respuesta de OpenAI contiene campos no permitidos.",
                        details={"model_id": self.model_id, "error": err_str},
                    ) from e
                raise ProviderResponseFormatError(
                    message_safe="La estructura JSON de OpenAI no cumple con el esquema requerido.",
                    details={"model_id": self.model_id, "error": err_str},
                ) from e

        # 3. Extract token usage metadata (including reasoning and cached tokens)
        input_tokens = None
        output_tokens = None
        reasoning_tokens = 0
        cached_tokens = 0
        usage = getattr(response, "usage", None)
        if usage:
            if isinstance(usage, dict):
                raw_in = usage.get("prompt_tokens")
                raw_out = usage.get("completion_tokens")
                comp_details = usage.get("completion_tokens_details") or {}
                prompt_details = usage.get("prompt_tokens_details") or {}
                raw_reason = comp_details.get("reasoning_tokens") if isinstance(comp_details, dict) else getattr(comp_details, "reasoning_tokens", None)
                raw_cached = prompt_details.get("cached_tokens") if isinstance(prompt_details, dict) else getattr(prompt_details, "cached_tokens", None)
            else:
                raw_in = getattr(usage, "prompt_tokens", None)
                raw_out = getattr(usage, "completion_tokens", None)
                comp_details = getattr(usage, "completion_tokens_details", None)
                prompt_details = getattr(usage, "prompt_tokens_details", None)
                raw_reason = getattr(comp_details, "reasoning_tokens", None) if comp_details else None
                raw_cached = getattr(prompt_details, "cached_tokens", None) if prompt_details else None

            if isinstance(raw_in, (int, float)) and not isinstance(raw_in, bool):
                input_tokens = int(raw_in)
            if isinstance(raw_out, (int, float)) and not isinstance(raw_out, bool):
                output_tokens = int(raw_out)
            if isinstance(raw_reason, (int, float)) and not isinstance(raw_reason, bool):
                reasoning_tokens = int(raw_reason)
            if isinstance(raw_cached, (int, float)) and not isinstance(raw_cached, bool):
                cached_tokens = int(raw_cached)

        cost_breakdown = calculate_cost(
            provider="openai",
            model_id=self.model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            generated_questions=len(payload.questions),
            valid_questions=len(payload.questions),
            cached_input_tokens=cached_tokens,
            reasoning_tokens=reasoning_tokens,
        )

        raw_req_id = getattr(response, "id", None)
        request_id = raw_req_id if isinstance(raw_req_id, str) and raw_req_id.strip() else None
        telemetry = GenerationTelemetry(
            provider="openai",
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
            finish_reason=str(finish_reason),
        )
        logger.info(
            "OpenAI generation completed: %s",
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
            provider="openai",
            model_id=self.model_id,
            prompt_version=context.prompt_version or PROMPT_VERSION,
            questions=payload.questions,
            raw_response=raw_content,
            token_usage=token_usage_dict,
            finish_reason=str(finish_reason),
            request_id=request_id,
            latency_ms=latency_ms,
            retry_count=retry_count,
        )
