"""Provider abstractions and implementations for assisted question generation."""

from app.content_generation.providers.base import QuestionGenerationProvider
from app.content_generation.providers.cost_calculator import (
    MODEL_PRICING_CATALOG,
    CostBreakdown,
    GenerationTelemetry,
    ModelPricing,
    calculate_cost,
    resolve_model_pricing,
    resolve_rates,
)
from app.content_generation.providers.factory import get_llm_provider
from app.content_generation.providers.gemini_provider import (
    GoogleGeminiQuestionGenerationProvider,
)
from app.content_generation.providers.mock_provider import (
    MockBehaviorMode,
    MockQuestionGenerationProvider,
)
from app.content_generation.providers.openai_provider import (
    OpenAIQuestionGenerationProvider,
)
from app.content_generation.providers.prompts import (
    PROMPT_VERSION,
    build_system_prompt,
    build_user_prompt,
    segment_document_units,
)

__all__ = [
    "MODEL_PRICING_CATALOG",
    "PROMPT_VERSION",
    "CostBreakdown",
    "GenerationTelemetry",
    "GoogleGeminiQuestionGenerationProvider",
    "MockBehaviorMode",
    "MockQuestionGenerationProvider",
    "ModelPricing",
    "OpenAIQuestionGenerationProvider",
    "QuestionGenerationProvider",
    "build_system_prompt",
    "build_user_prompt",
    "calculate_cost",
    "get_llm_provider",
    "resolve_model_pricing",
    "resolve_rates",
    "segment_document_units",
]
