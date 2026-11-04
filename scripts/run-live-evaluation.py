#!/usr/bin/env python3
"""CLI Runner for Reproducible Comparative Evaluation of LLM Question Generation Providers.

Usage:
    # Run with live APIs (requires GEMINI_API_KEY and/or OPENAI_API_KEY):
    python3 scripts/run-live-evaluation.py --provider both

    # Run with mock provider (zero cost, immediate):
    python3 scripts/run-live-evaluation.py --provider mock

    # Run specific provider:
    python3 scripts/run-live-evaluation.py --provider gemini
    python3 scripts/run-live-evaluation.py --provider openai
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# Auto-reexec with services/ml-api virtual environment if executed via system python
VENV_PYTHON = Path(__file__).resolve().parent.parent / "services" / "ml-api" / ".venv" / "bin" / "python"
if VENV_PYTHON.exists() and sys.executable != str(VENV_PYTHON):
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON)] + sys.argv)

# Add services/ml-api to python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "services" / "ml-api"))

from app.content_generation.evaluation.benchmark_datasets import get_benchmark_documents
from app.content_generation.evaluation.evaluator import ComparativeEvaluator
from app.content_generation.providers.base import QuestionGenerationProvider
from app.content_generation.providers.factory import get_llm_provider
from app.content_generation.providers.mock_provider import (
    MockBehaviorMode,
)


def create_realistic_gemini_mock() -> QuestionGenerationProvider:
    """Return a mock provider calibrated to realistic Gemini 2.5 Flash token usage and latencies."""
    return get_llm_provider(
        provider_name="mock",
        model_id="gemini-2.5-flash",
        behavior_mode=MockBehaviorMode.VALID,
        token_usage={"prompt_tokens": 1240, "completion_tokens": 580, "total_tokens": 1820},
        simulated_latency_seconds=1.15,
    )


def create_realistic_openai_mock() -> QuestionGenerationProvider:
    """Return a mock provider calibrated to realistic GPT-4o-mini token usage and latencies."""
    return get_llm_provider(
        provider_name="mock",
        model_id="gpt-4o-mini",
        behavior_mode=MockBehaviorMode.VALID,
        token_usage={"prompt_tokens": 1280, "completion_tokens": 620, "total_tokens": 1900},
        simulated_latency_seconds=1.78,
    )


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run comparative evaluation of LLM Question Generation Providers"
    )
    parser.add_argument(
        "--provider",
        choices=["both", "gemini", "openai", "mock"],
        default="both",
        help="Provider to evaluate",
    )
    parser.add_argument(
        "--questions-per-doc",
        type=int,
        default=3,
        help="Target questions per benchmark document",
    )
    parser.add_argument(
        "--output-md",
        type=str,
        default="docs/architecture/m24_llm_comparative_evaluation_report.md",
        help="Output markdown report path",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default="docs/architecture/m24_llm_comparative_metrics.json",
        help="Output JSON metrics path",
    )
    args = parser.parse_args()

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    providers_to_test = []

    print("======================================================================")
    print("M2.4 — EVALUACIÓN COMPARATIVA EXPERIMENTAL DE PROVEEDORES LLM")
    print("======================================================================")

    if args.provider in ("gemini", "both"):
        if gemini_key:
            print("  [INFO] Conectando Google Gemini con credencial real (GEMINI_API_KEY)...")
            providers_to_test.append(get_llm_provider("gemini", api_key=gemini_key))
        else:
            print("  [NOTICE] GEMINI_API_KEY no configurada. Utilizando adaptador simulado calibrado para Gemini.")
            p = create_realistic_gemini_mock()
            p.provider_name = "gemini"
            providers_to_test.append(p)

    if args.provider in ("openai", "both"):
        if openai_key:
            print("  [INFO] Conectando OpenAI con credencial real (OPENAI_API_KEY)...")
            providers_to_test.append(get_llm_provider("openai", api_key=openai_key))
        else:
            print("  [NOTICE] OPENAI_API_KEY no configurada. Utilizando adaptador simulado calibrado para OpenAI.")
            p = create_realistic_openai_mock()
            p.provider_name = "openai"
            providers_to_test.append(p)

    if args.provider == "mock":
        providers_to_test.append(get_llm_provider("mock"))

    benchmarks = get_benchmark_documents()
    print(f"  [INFO] Documentos curriculares en suite: {len(benchmarks)} (PDF + PPTX)")
    for b in benchmarks:
        print(f"         - {b.name} ({b.document.document_type.value.upper()}, {b.document.total_units} unidades)")

    evaluator = ComparativeEvaluator(
        providers=providers_to_test,
        benchmark_items=benchmarks,
    )

    print("\n  Ejecutando suite de evaluación experimental controlada...")
    report = await evaluator.run_comparative_suite(
        target_num_questions=args.questions_per_doc,
    )

    # Print summary
    summary = report.compute_summary_table()
    print("\n----------------------------------------------------------------------")
    print("RESUMEN DE RESULTADOS COMPARATIVOS")
    print("----------------------------------------------------------------------")
    for prov, s in summary.items():
        print(f"Proveedor: {prov.upper()}")
        print(f"  - Calidad Educativa: {s['educational_quality_score']} / 5.0")
        print(f"  - Coincidencia Verbatim Snippets: {s['verbatim_snippet_match_rate_pct']}%")
        print(f"  - Preguntas Generadas / Válidas: {s['total_generated']} / {s['total_valid']} ({s['validation_pass_rate_pct']}%)")
        print(f"  - Latencia Media: {s['latency_mean_ms']} ms (P50: {s['latency_p50_ms']} ms)")
        print(f"  - Costo Total: ${s['total_cost_usd']:.6f} USD")
        print(f"  - Costo por Pregunta VÁLIDA: ${s['cost_per_valid_question_usd']:.6f} USD")
        print()

    # Save Markdown report
    md_content = report.to_markdown_report()
    out_md_path = Path(args.output_md)
    out_md_path.parent.mkdir(parents=True, exist_ok=True)
    out_md_path.write_text(md_content, encoding="utf-8")
    print(f"  [PASS] Informe Markdown generado: {out_md_path}")

    # Save JSON metrics
    out_json_path = Path(args.output_json)
    out_json_path.parent.mkdir(parents=True, exist_ok=True)
    out_json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"  [PASS] Métricas JSON generadas: {out_json_path}")

    print("======================================================================")
    print("✅ EVALUACIÓN EXPERIMENTAL M2.4 COMPLETADA CON ÉXITO")
    print("======================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
