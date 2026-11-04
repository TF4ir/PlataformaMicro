"""Comparative evaluation framework for LLM question generation providers."""

from app.content_generation.evaluation.benchmark_datasets import (
    BenchmarkItem,
    get_benchmark_documents,
)
from app.content_generation.evaluation.evaluator import (
    BenchmarkAuthenticityAudit,
    ComparativeEvaluationReport,
    ComparativeEvaluator,
    audit_benchmark_runs,
    filter_authentic_runs,
)
from app.content_generation.evaluation.rubric import (
    DoubleBlindReviewScore,
    InterRaterAgreementReport,
    PedagogicalRubric,
    QuestionProvenanceScore,
    RubricEvaluationResult,
    TeacherRubricCriteria,
    compute_contingency_matrix,
    compute_rating_distribution,
    compute_weighted_cohen_kappa,
    evaluate_inter_rater_agreement,
)

__all__ = [
    "BenchmarkAuthenticityAudit",
    "BenchmarkItem",
    "ComparativeEvaluationReport",
    "ComparativeEvaluator",
    "DoubleBlindReviewScore",
    "InterRaterAgreementReport",
    "PedagogicalRubric",
    "QuestionProvenanceScore",
    "RubricEvaluationResult",
    "TeacherRubricCriteria",
    "audit_benchmark_runs",
    "compute_contingency_matrix",
    "compute_rating_distribution",
    "compute_weighted_cohen_kappa",
    "evaluate_inter_rater_agreement",
    "filter_authentic_runs",
    "get_benchmark_documents",
]
