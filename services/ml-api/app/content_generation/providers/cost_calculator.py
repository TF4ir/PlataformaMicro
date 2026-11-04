"""Cost calculation and telemetry estimation for LLM assisted question generation.

Maintains traceable, dated commercial pricing structures (Google Gemini & OpenAI)
and computes per-execution, per-generated-question, and per-valid-question costs.
"""

from dataclasses import dataclass
from typing import Any

PRICING_EFFECTIVE_DATE = "2026-01-01"
PRICING_VERIFIED_DATE = "2026-11-03"


@dataclass(frozen=True)
class ModelPricing:
    """Official published pricing definition for an LLM model and tier."""

    provider: str
    model_id: str
    input_price_per_million: float
    output_price_per_million: float
    cached_input_price: float | None = None
    pricing_tier: str = "standard"  # "standard" | "batch" | "flex" | "free" | "priority"
    currency: str = "USD"
    effective_from: str = PRICING_EFFECTIVE_DATE
    effective_until: str | None = None
    verified_at: str = PRICING_VERIFIED_DATE
    source_url: str = ""


# Master list of all official pricing definitions including temporal validity ranges
MODEL_PRICING_REGISTRY: list[ModelPricing] = [
    # --- Google Gemini 3.5 Flash-Lite (Active from 2026-01-01) ---
    ModelPricing(
        provider="gemini",
        model_id="gemini-3.5-flash-lite",
        input_price_per_million=0.300,
        output_price_per_million=2.500,
        cached_input_price=0.030,
        pricing_tier="standard",
        currency="USD",
        effective_from="2026-01-01",
        effective_until=None,
        verified_at=PRICING_VERIFIED_DATE,
        source_url="https://ai.google.dev/pricing",
    ),
    ModelPricing(
        provider="gemini",
        model_id="gemini-3.5-flash-lite",
        input_price_per_million=0.150,
        output_price_per_million=1.250,
        cached_input_price=0.015,
        pricing_tier="batch",
        currency="USD",
        effective_from="2026-01-01",
        effective_until=None,
        verified_at=PRICING_VERIFIED_DATE,
        source_url="https://ai.google.dev/pricing",
    ),
    ModelPricing(
        provider="gemini",
        model_id="gemini-3.5-flash-lite",
        input_price_per_million=0.150,
        output_price_per_million=1.250,
        cached_input_price=0.020,
        pricing_tier="flex",
        currency="USD",
        effective_from="2026-01-01",
        effective_until=None,
        verified_at=PRICING_VERIFIED_DATE,
        source_url="https://ai.google.dev/pricing",
    ),
    ModelPricing(
        provider="gemini",
        model_id="gemini-3.5-flash-lite",
        input_price_per_million=0.0,
        output_price_per_million=0.0,
        cached_input_price=None,
        pricing_tier="free",
        currency="USD",
        effective_from="2026-01-01",
        effective_until=None,
        verified_at=PRICING_VERIFIED_DATE,
        source_url="https://ai.google.dev/pricing",
    ),
    # --- Google Gemini 3.8 Flash (Promotional rates through 2026-12-31) ---
    ModelPricing(
        provider="gemini",
        model_id="gemini-3.8-flash",
        input_price_per_million=0.750,
        output_price_per_million=3.750,
        cached_input_price=0.075,
        pricing_tier="standard",
        currency="USD",
        effective_from="2026-01-01",
        effective_until="2026-12-31",
        verified_at=PRICING_VERIFIED_DATE,
        source_url="https://ai.google.dev/pricing",
    ),
    ModelPricing(
        provider="gemini",
        model_id="gemini-3.8-flash",
        input_price_per_million=0.375,
        output_price_per_million=1.875,
        cached_input_price=0.0375,
        pricing_tier="batch",
        currency="USD",
        effective_from="2026-01-01",
        effective_until="2026-12-31",
        verified_at=PRICING_VERIFIED_DATE,
        source_url="https://ai.google.dev/pricing",
    ),
    ModelPricing(
        provider="gemini",
        model_id="gemini-3.8-flash",
        input_price_per_million=0.375,
        output_price_per_million=1.875,
        cached_input_price=0.0375,
        pricing_tier="flex",
        currency="USD",
        effective_from="2026-01-01",
        effective_until="2026-12-31",
        verified_at=PRICING_VERIFIED_DATE,
        source_url="https://ai.google.dev/pricing",
    ),
    ModelPricing(
        provider="gemini",
        model_id="gemini-3.8-flash",
        input_price_per_million=0.0,
        output_price_per_million=0.0,
        cached_input_price=None,
        pricing_tier="free",
        currency="USD",
        effective_from="2026-01-01",
        effective_until="2026-12-31",
        verified_at=PRICING_VERIFIED_DATE,
        source_url="https://ai.google.dev/pricing",
    ),
    # --- Google Gemini 3.8 Flash (Post-promotional standard rates from 2027-01-01) ---
    ModelPricing(
        provider="gemini",
        model_id="gemini-3.8-flash",
        input_price_per_million=1.500,
        output_price_per_million=7.500,
        cached_input_price=0.150,
        pricing_tier="standard",
        currency="USD",
        effective_from="2027-01-01",
        effective_until=None,
        verified_at=PRICING_VERIFIED_DATE,
        source_url="https://ai.google.dev/pricing",
    ),
    ModelPricing(
        provider="gemini",
        model_id="gemini-3.8-flash",
        input_price_per_million=0.750,
        output_price_per_million=3.750,
        cached_input_price=0.075,
        pricing_tier="batch",
        currency="USD",
        effective_from="2027-01-01",
        effective_until=None,
        verified_at=PRICING_VERIFIED_DATE,
        source_url="https://ai.google.dev/pricing",
    ),
    ModelPricing(
        provider="gemini",
        model_id="gemini-3.8-flash",
        input_price_per_million=0.750,
        output_price_per_million=3.750,
        cached_input_price=0.075,
        pricing_tier="flex",
        currency="USD",
        effective_from="2027-01-01",
        effective_until=None,
        verified_at=PRICING_VERIFIED_DATE,
        source_url="https://ai.google.dev/pricing",
    ),
    ModelPricing(
        provider="gemini",
        model_id="gemini-3.8-flash",
        input_price_per_million=0.0,
        output_price_per_million=0.0,
        cached_input_price=None,
        pricing_tier="free",
        currency="USD",
        effective_from="2027-01-01",
        effective_until=None,
        verified_at=PRICING_VERIFIED_DATE,
        source_url="https://ai.google.dev/pricing",
    ),
    # --- OpenAI GPT-6 Luna (Active from 2026-01-01) ---
    ModelPricing(
        provider="openai",
        model_id="gpt-6-luna",
        input_price_per_million=0.100,
        output_price_per_million=0.500,
        cached_input_price=0.010,
        pricing_tier="standard",
        currency="USD",
        effective_from="2026-01-01",
        effective_until=None,
        verified_at=PRICING_VERIFIED_DATE,
        source_url="https://openai.com/api/pricing/",
    ),
    ModelPricing(
        provider="openai",
        model_id="gpt-6-luna",
        input_price_per_million=0.050,
        output_price_per_million=0.250,
        cached_input_price=0.005,
        pricing_tier="batch",
        currency="USD",
        effective_from="2026-01-01",
        effective_until=None,
        verified_at=PRICING_VERIFIED_DATE,
        source_url="https://openai.com/api/pricing/",
    ),
    ModelPricing(
        provider="openai",
        model_id="gpt-6-luna",
        input_price_per_million=0.200,
        output_price_per_million=1.000,
        cached_input_price=0.020,
        pricing_tier="priority",
        currency="USD",
        effective_from="2026-01-01",
        effective_until=None,
        verified_at=PRICING_VERIFIED_DATE,
        source_url="https://openai.com/api/pricing/",
    ),
]

# Primary catalogue indexed by (provider, model_id, tier) for currently active pricing
MODEL_PRICING_CATALOG: dict[tuple[str, str, str], ModelPricing] = {
    # Active Gemini 3.5 Flash-Lite
    ("gemini", "gemini-3.5-flash-lite", "standard"): MODEL_PRICING_REGISTRY[0],
    ("gemini", "gemini-3.5-flash-lite", "batch"): MODEL_PRICING_REGISTRY[1],
    ("gemini", "gemini-3.5-flash-lite", "flex"): MODEL_PRICING_REGISTRY[2],
    ("gemini", "gemini-3.5-flash-lite", "free"): MODEL_PRICING_REGISTRY[3],
    # Active Gemini 3.8 Flash (promotional period through 2026-12-31)
    ("gemini", "gemini-3.8-flash", "standard"): MODEL_PRICING_REGISTRY[4],
    ("gemini", "gemini-3.8-flash", "batch"): MODEL_PRICING_REGISTRY[5],
    ("gemini", "gemini-3.8-flash", "flex"): MODEL_PRICING_REGISTRY[6],
    ("gemini", "gemini-3.8-flash", "free"): MODEL_PRICING_REGISTRY[7],
    # Active GPT-6 Luna
    ("openai", "gpt-6-luna", "standard"): MODEL_PRICING_REGISTRY[12],
    ("openai", "gpt-6-luna", "batch"): MODEL_PRICING_REGISTRY[13],
    ("openai", "gpt-6-luna", "priority"): MODEL_PRICING_REGISTRY[14],
    # Legacy / Baseline models maintained for reproducibility and backward compatibility
    ("gemini", "gemini-2.5-flash", "standard"): ModelPricing(
        provider="gemini",
        model_id="gemini-2.5-flash",
        input_price_per_million=0.075,
        output_price_per_million=0.300,
        cached_input_price=0.01875,
        pricing_tier="standard",
        currency="USD",
        effective_from="2024-11-01",
        verified_at="2024-11-01",
        source_url="https://ai.google.dev/pricing",
    ),
    ("gemini", "gemini-2.0-flash", "standard"): ModelPricing(
        provider="gemini",
        model_id="gemini-2.0-flash",
        input_price_per_million=0.075,
        output_price_per_million=0.300,
        cached_input_price=0.01875,
        pricing_tier="standard",
        currency="USD",
        effective_from="2024-11-01",
        verified_at="2024-11-01",
        source_url="https://ai.google.dev/pricing",
    ),
    ("gemini", "gemini-1.5-flash", "standard"): ModelPricing(
        provider="gemini",
        model_id="gemini-1.5-flash",
        input_price_per_million=0.075,
        output_price_per_million=0.300,
        cached_input_price=0.01875,
        pricing_tier="standard",
        currency="USD",
        effective_from="2024-05-14",
        verified_at="2024-11-01",
        source_url="https://ai.google.dev/pricing",
    ),
    ("gemini", "gemini-1.5-pro", "standard"): ModelPricing(
        provider="gemini",
        model_id="gemini-1.5-pro",
        input_price_per_million=1.250,
        output_price_per_million=5.000,
        cached_input_price=0.3125,
        pricing_tier="standard",
        currency="USD",
        effective_from="2024-05-14",
        verified_at="2024-11-01",
        source_url="https://ai.google.dev/pricing",
    ),
    ("openai", "gpt-4o-mini", "standard"): ModelPricing(
        provider="openai",
        model_id="gpt-4o-mini",
        input_price_per_million=0.150,
        output_price_per_million=0.600,
        cached_input_price=0.075,
        pricing_tier="standard",
        currency="USD",
        effective_from="2024-07-18",
        verified_at="2024-11-01",
        source_url="https://openai.com/api/pricing/",
    ),
    ("openai", "gpt-4o", "standard"): ModelPricing(
        provider="openai",
        model_id="gpt-4o",
        input_price_per_million=2.500,
        output_price_per_million=10.000,
        cached_input_price=1.250,
        pricing_tier="standard",
        currency="USD",
        effective_from="2024-05-13",
        verified_at="2024-11-01",
        source_url="https://openai.com/api/pricing/",
    ),
    ("openai", "gpt-4.5-preview", "standard"): ModelPricing(
        provider="openai",
        model_id="gpt-4.5-preview",
        input_price_per_million=75.000,
        output_price_per_million=150.000,
        cached_input_price=37.500,
        pricing_tier="standard",
        currency="USD",
        effective_from="2025-02-27",
        verified_at="2025-02-27",
        source_url="https://openai.com/api/pricing/",
    ),
    ("mock", "mock-v1", "standard"): ModelPricing(
        provider="mock",
        model_id="mock-v1",
        input_price_per_million=0.0,
        output_price_per_million=0.0,
        cached_input_price=0.0,
        pricing_tier="standard",
        currency="USD",
        effective_from="2026-01-01",
        verified_at=PRICING_VERIFIED_DATE,
        source_url="mock://internal",
    ),
}

# Standard rate lookup table for quick reference and backwards compatibility
PRICING_TABLE: dict[str, dict[str, dict[str, float]]] = {
    "gemini": {
        "gemini-3.5-flash-lite": {"input_per_million": 0.300, "output_per_million": 2.500},
        "gemini-3.8-flash": {"input_per_million": 0.750, "output_per_million": 3.750},
        "gemini-2.5-flash": {"input_per_million": 0.075, "output_per_million": 0.300},
        "gemini-2.0-flash": {"input_per_million": 0.075, "output_per_million": 0.300},
        "gemini-1.5-flash": {"input_per_million": 0.075, "output_per_million": 0.300},
        "gemini-1.5-pro": {"input_per_million": 1.250, "output_per_million": 5.000},
        "default": {"input_per_million": 0.300, "output_per_million": 2.500},
    },
    "openai": {
        "gpt-6-luna": {"input_per_million": 0.100, "output_per_million": 0.500},
        "gpt-4o-mini": {"input_per_million": 0.150, "output_per_million": 0.600},
        "gpt-4o": {"input_per_million": 2.500, "output_per_million": 10.000},
        "gpt-4.5-preview": {"input_per_million": 75.000, "output_per_million": 150.000},
        "default": {"input_per_million": 0.100, "output_per_million": 0.500},
    },
    "mock": {
        "mock-v1": {"input_per_million": 0.0, "output_per_million": 0.0},
        "default": {"input_per_million": 0.0, "output_per_million": 0.0},
    },
}


@dataclass
class CostBreakdown:
    """Detailed estimated monetary cost breakdown in USD."""

    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    input_cost_usd: float | None
    output_cost_usd: float | None
    total_cost_usd: float | None
    cost_per_generated_question: float | None
    cost_per_valid_question: float | None
    pricing_effective_date: str = PRICING_EFFECTIVE_DATE
    pricing_effective_until: str | None = None
    pricing_tier: str = "standard"
    pricing_verified_at: str = PRICING_VERIFIED_DATE
    source_url: str = ""
    cached_input_tokens: int = 0
    billable_reasoning_tokens: int = 0


def resolve_model_pricing(
    provider: str,
    model_id: str,
    tier: str = "standard",
    as_of_date: str | None = None,
) -> ModelPricing | None:
    """Find matching ModelPricing entry from the catalogue based on provider, model_id, tier, and date."""
    prov_key = provider.lower().strip()
    if prov_key in ("google", "google_gemini"):
        prov_key = "gemini"

    model_key = model_id.lower().strip()
    tier_key = tier.lower().strip()
    target_date = as_of_date or PRICING_VERIFIED_DATE

    # 1. Exact match in full registry with temporal validity checking
    for pricing in MODEL_PRICING_REGISTRY:
        if (
            pricing.provider == prov_key
            and pricing.pricing_tier == tier_key
            and pricing.model_id == model_key
            and pricing.effective_from <= target_date
            and (pricing.effective_until is None or target_date <= pricing.effective_until)
        ):
            return pricing

    # 2. Prefix match in full registry with temporal validity checking
    for pricing in MODEL_PRICING_REGISTRY:
        if (
            pricing.provider == prov_key
            and pricing.pricing_tier == tier_key
            and model_key.startswith(pricing.model_id)
            and pricing.effective_from <= target_date
            and (pricing.effective_until is None or target_date <= pricing.effective_until)
        ):
            return pricing

    # 3. Direct lookup in static active catalog dictionary
    direct = MODEL_PRICING_CATALOG.get((prov_key, model_key, tier_key))
    if direct is not None:
        return direct

    # 4. Prefix match in active catalog dictionary
    for (cat_prov, cat_model, cat_tier), pricing in MODEL_PRICING_CATALOG.items():
        if cat_prov == prov_key and cat_tier == tier_key and model_key.startswith(cat_model):
            return pricing

    # 5. Default fallback for provider at standard tier
    if prov_key == "gemini":
        return resolve_model_pricing("gemini", "gemini-3.5-flash-lite", "standard", as_of_date=target_date)
    if prov_key == "openai":
        return resolve_model_pricing("openai", "gpt-6-luna", "standard", as_of_date=target_date)
    if prov_key == "mock":
        return resolve_model_pricing("mock", "mock-v1", "standard", as_of_date=target_date)

    return None


def resolve_rates(
    provider: str,
    model_id: str,
    tier: str = "standard",
    as_of_date: str | None = None,
) -> tuple[float, float]:
    """Retrieve per-million token rates for (input, output) based on provider, model, tier, and date.

    Returns:
        tuple (input_rate_per_million, output_rate_per_million)
    """
    pricing = resolve_model_pricing(provider, model_id, tier, as_of_date=as_of_date)
    if pricing is not None:
        return pricing.input_price_per_million, pricing.output_price_per_million

    # Fallback to PRICING_TABLE
    prov_key = provider.lower().strip()
    if prov_key in ("google", "google_gemini"):
        prov_key = "gemini"

    models_map = PRICING_TABLE.get(prov_key, PRICING_TABLE["mock"])
    model_key = model_id.lower().strip()

    rates = models_map.get(model_key)
    if rates is None:
        for known_model, known_rates in models_map.items():
            if known_model != "default" and model_key.startswith(known_model):
                rates = known_rates
                break

    if rates is None:
        rates = models_map.get("default", {"input_per_million": 0.0, "output_per_million": 0.0})

    return rates["input_per_million"], rates["output_per_million"]


def calculate_cost(
    provider: str,
    model_id: str,
    input_tokens: int | None,
    output_tokens: int | None,
    generated_questions: int = 0,
    valid_questions: int = 0,
    cached_input_tokens: int = 0,
    reasoning_tokens: int = 0,
    pricing_tier: str = "standard",
    reasoning_in_output: bool | None = None,
    as_of_date: str | None = None,
) -> CostBreakdown:
    """Calculate realistic cost based on token usage reported by provider.

    Adheres strictly to the requirement: does NOT invent tokens or prices if
    the provider does not report token counts. Includes cached tokens and billable
    reasoning tokens when relevant.
    """
    if input_tokens is None or output_tokens is None:
        return CostBreakdown(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=None,
            input_cost_usd=None,
            output_cost_usd=None,
            total_cost_usd=None,
            cost_per_generated_question=None,
            cost_per_valid_question=None,
            pricing_tier=pricing_tier,
        )

    pricing = resolve_model_pricing(provider, model_id, pricing_tier, as_of_date=as_of_date)
    if pricing is not None:
        in_rate = pricing.input_price_per_million
        out_rate = pricing.output_price_per_million
        cached_rate = pricing.cached_input_price if pricing.cached_input_price is not None else in_rate
        source_url = pricing.source_url
        effective_date = pricing.effective_from
        effective_until = pricing.effective_until
        verified_at = pricing.verified_at
    else:
        in_rate, out_rate = resolve_rates(provider, model_id, pricing_tier, as_of_date=as_of_date)
        cached_rate = in_rate
        source_url = ""
        effective_date = PRICING_EFFECTIVE_DATE
        effective_until = None
        verified_at = PRICING_VERIFIED_DATE

    # Effective cached vs uncached input
    c_tokens = max(0, min(cached_input_tokens, input_tokens))
    u_tokens = max(0, input_tokens - c_tokens)

    input_cost = ((u_tokens / 1_000_000.0) * in_rate) + ((c_tokens / 1_000_000.0) * cached_rate)

    # For output tokens: include reasoning tokens when applicable
    # If reasoning_in_output is True: output_tokens already includes reasoning tokens (e.g. OpenAI completion_tokens).
    # If reasoning_in_output is False: reasoning_tokens are separate from output_tokens and must be summed.
    # If None (default): auto-detect — if output_tokens < reasoning_tokens, they are separate and must be summed;
    # otherwise output_tokens represents total completion tokens.
    if reasoning_in_output is False:
        billable_output = output_tokens + max(0, reasoning_tokens)
    elif reasoning_in_output is True:
        billable_output = max(output_tokens, reasoning_tokens)
    else:
        if reasoning_tokens > 0 and output_tokens < reasoning_tokens:
            billable_output = output_tokens + reasoning_tokens
        else:
            billable_output = max(output_tokens, reasoning_tokens)

    output_cost = (billable_output / 1_000_000.0) * out_rate
    total_cost = input_cost + output_cost

    cost_per_generated = (
        round(total_cost / generated_questions, 8)
        if generated_questions > 0
        else None
    )
    cost_per_valid = (
        round(total_cost / valid_questions, 8)
        if valid_questions > 0
        else None
    )

    return CostBreakdown(
        input_tokens=input_tokens,
        output_tokens=billable_output,
        total_tokens=input_tokens + billable_output,
        input_cost_usd=round(input_cost, 8),
        output_cost_usd=round(output_cost, 8),
        total_cost_usd=round(total_cost, 8),
        cost_per_generated_question=cost_per_generated,
        cost_per_valid_question=cost_per_valid,
        pricing_effective_date=effective_date,
        pricing_effective_until=effective_until,
        pricing_tier=pricing_tier,
        pricing_verified_at=verified_at,
        source_url=source_url,
        cached_input_tokens=c_tokens,
        billable_reasoning_tokens=max(0, reasoning_tokens),
    )


@dataclass
class GenerationTelemetry:
    """Complete execution metrics record for a generation request."""

    provider: str
    model_id: str
    prompt_version: str
    request_id: str | None
    input_tokens: int | None
    output_tokens: int | None
    latency_ms: float
    retry_count: int
    generated_questions: int
    valid_questions: int
    failed_validations: int
    estimated_cost: float | None
    generation_status: str  # "success" | "validation_failed" | "provider_error"
    billable_reasoning_tokens: int | None = None
    finish_reason: str = "stop"
    error_category: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert telemetry to safe serializable dictionary for logging and audit."""
        return {
            "provider": self.provider,
            "model_id": self.model_id,
            "prompt_version": self.prompt_version,
            "request_id": self.request_id,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "billable_reasoning_tokens": self.billable_reasoning_tokens,
            "latency_ms": round(self.latency_ms, 2),
            "retry_count": self.retry_count,
            "finish_reason": self.finish_reason,
            "error_category": self.error_category,
            "generated_questions": self.generated_questions,
            "valid_questions": self.valid_questions,
            "failed_validations": self.failed_validations,
            "estimated_cost_usd": self.estimated_cost,
            "generation_status": self.generation_status,
        }
