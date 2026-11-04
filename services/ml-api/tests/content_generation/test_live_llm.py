"""Opt-in live integration tests for external LLM providers (Google Gemini & OpenAI).

These tests make REAL external API calls and require valid credentials and internet access.
They are strictly disabled in normal CI and unit test runs.

To execute:
    export RUN_LIVE_LLM_TESTS=1
    export GEMINI_API_KEY=your_key
    export OPENAI_API_KEY=your_key
    pytest tests/content_generation/test_live_llm.py -v
"""

import os
import uuid

import pytest

from app.content_generation.evaluation.benchmark_datasets import (
    get_thermodynamics_pdf_benchmark,
)
from app.content_generation.providers.gemini_provider import (
    GoogleGeminiQuestionGenerationProvider,
)
from app.content_generation.providers.openai_provider import (
    OpenAIQuestionGenerationProvider,
)
from app.content_generation.schemas.generated_questions import (
    GenerationContext,
    LLMGenerationOutput,
)
from app.content_generation.services.draft_validation_service import (
    DraftValidationService,
)

RUN_LIVE = os.getenv("RUN_LIVE_LLM_TESTS", "").lower() in ("1", "true", "yes")
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "").strip()
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "").strip()


@pytest.mark.skipif(
    not RUN_LIVE or not GEMINI_KEY,
    reason="Live Gemini test requires RUN_LIVE_LLM_TESTS=1 and GEMINI_API_KEY",
)
@pytest.mark.asyncio
async def test_live_google_gemini_generation() -> None:
    """Execute real live generation call against Google Gemini API."""
    benchmark = get_thermodynamics_pdf_benchmark()
    provider = GoogleGeminiQuestionGenerationProvider(
        api_key=GEMINI_KEY,
        model_id=os.getenv("LLM_MODEL_ID", "gemini-3.5-flash-lite"),
        timeout_seconds=45.0,
    )
    context = GenerationContext(
        job_id=str(uuid.uuid4()),
        tenant_id=str(uuid.uuid4()),
        language="es",
        target_num_questions=2,
        document_units=benchmark.document.units,
        document_type="pdf",
    )
    output = await provider.generate_drafts(
        extracted_text="Text representation",
        schema=None,
        context=context,
    )

    assert isinstance(output, LLMGenerationOutput)
    assert len(output.questions) >= 1
    assert output.token_usage is not None
    assert output.token_usage["prompt_tokens"] > 0
    assert output.token_usage["completion_tokens"] > 0

    # Validate provenance
    val_service = DraftValidationService()
    unit_map = {u.index: u for u in benchmark.document.units}
    for q in output.questions:
        val_service.validate_draft(q, benchmark.document, unit_map)


@pytest.mark.skipif(
    not RUN_LIVE or not OPENAI_KEY,
    reason="Live OpenAI test requires RUN_LIVE_LLM_TESTS=1 and OPENAI_API_KEY",
)
@pytest.mark.asyncio
async def test_live_openai_generation() -> None:
    """Execute real live generation call against OpenAI API."""
    benchmark = get_thermodynamics_pdf_benchmark()
    provider = OpenAIQuestionGenerationProvider(
        api_key=OPENAI_KEY,
        model_id=os.getenv("LLM_MODEL_ID", "gpt-6-luna"),
        timeout_seconds=45.0,
    )
    context = GenerationContext(
        job_id=str(uuid.uuid4()),
        tenant_id=str(uuid.uuid4()),
        language="es",
        target_num_questions=2,
        document_units=benchmark.document.units,
        document_type="pdf",
    )
    output = await provider.generate_drafts(
        extracted_text="Text representation",
        schema=None,
        context=context,
    )

    assert isinstance(output, LLMGenerationOutput)
    assert len(output.questions) >= 1
    assert output.token_usage is not None
    assert output.token_usage["prompt_tokens"] > 0
    assert output.token_usage["completion_tokens"] > 0

    # Validate provenance
    val_service = DraftValidationService()
    unit_map = {u.index: u for u in benchmark.document.units}
    for q in output.questions:
        val_service.validate_draft(q, benchmark.document, unit_map)
