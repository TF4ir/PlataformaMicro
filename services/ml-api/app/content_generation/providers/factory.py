"""Factory for instantiating QuestionGenerationProvider based on dynamic configuration.

Adheres strictly to ADR-0004: reads LLM_PROVIDER and LLM_MODEL_ID from environment,
without hardcoding commercial vendors or model IDs in business logic.
"""

import os
from typing import Any

from app.content_generation.exceptions import UnsupportedProviderError
from app.content_generation.providers.base import QuestionGenerationProvider
from app.content_generation.providers.mock_provider import (
    MockBehaviorMode,
    MockQuestionGenerationProvider,
)


def get_llm_provider(
    provider_name: str | None = None,
    model_id: str | None = None,
    **kwargs: Any,
) -> QuestionGenerationProvider:
    """Instantiate and return a configured QuestionGenerationProvider.

    Args:
        provider_name: Explicit provider name. If None, resolved from env `LLM_PROVIDER` (default: 'mock').
        model_id: Explicit model identifier. If None, resolved from env `LLM_MODEL_ID` (default: 'mock-v1').
        **kwargs: Implementation-specific options (e.g. behavior_mode for mock).

    Returns:
        Instance conforming to QuestionGenerationProvider protocol.

    Raises:
        UnsupportedProviderError: If the requested provider is unknown or not supported in this milestone.
    """
    env_provider = os.getenv("LLM_PROVIDER") or "mock"
    env_model = os.getenv("LLM_MODEL_ID") or "mock-v1"
    resolved_provider = (provider_name or env_provider).strip().lower()
    resolved_model_id = (model_id or env_model).strip()

    if resolved_provider == "mock":
        behavior_mode_val = kwargs.get("behavior_mode", MockBehaviorMode.VALID)
        if isinstance(behavior_mode_val, str):
            behavior_mode = MockBehaviorMode(behavior_mode_val)
        else:
            behavior_mode = behavior_mode_val

        custom_questions = kwargs.get("custom_questions", None)

        return MockQuestionGenerationProvider(
            model_id=resolved_model_id,
            behavior_mode=behavior_mode,
            custom_questions=custom_questions,
        )

    # In Milestone M2.2, external LLM providers (e.g. vertex, openai, anthropic) are not implemented
    raise UnsupportedProviderError(
        f"El proveedor LLM '{resolved_provider}' no está implementado o no está configurado en este entorno.",
        details={"provider": resolved_provider, "model_id": resolved_model_id},
    )
