"""Prediction and retention inference package."""

import sys
from pathlib import Path

# Ensure monorepo root is on sys.path for ml.* package discovery
_curr = Path(__file__).resolve().parent
_repo_root = next((p for p in [_curr, *_curr.parents] if (p / "ml").is_dir()), None)
if _repo_root is not None and str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from app.prediction.history_builder import (
    StudentKCHistorySummary,
    UnifiedHistoryBuilder,
    UnifiedInteractionRecord,
)
from app.prediction.inference_service import RetentionInferenceService
from app.prediction.kc_reference_resolver import KCReferenceResolver
from app.prediction.model_registry import (
    ModelArtifactMetadata,
    RetentionModelRegistry,
)

__all__ = [
    "KCReferenceResolver",
    "ModelArtifactMetadata",
    "RetentionInferenceService",
    "RetentionModelRegistry",
    "StudentKCHistorySummary",
    "UnifiedHistoryBuilder",
    "UnifiedInteractionRecord",
]
