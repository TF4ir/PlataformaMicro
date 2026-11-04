"""Model Registry and Artifact Loader for Retention Inference.

Addresses Section 4.4 and 4.5 of TASK M5.3:
Enforces decoupled loading of versioned model artifacts and strict production guards
against using uncalibrated synthetic models on real students.
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Ensure monorepo root is on sys.path for ml.* package discovery
_curr = Path(__file__).resolve().parent
_repo_root = next((p for p in [_curr, *_curr.parents] if (p / "ml").is_dir()), None)
if _repo_root is not None and str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from ml.src.baselines.hlr_model import HalfLifeRegressionModel
from ml.src.das3h.model import ExtendedDAS3HModel
from ml.src.models.base import TemporalRetentionModel

from app.core.config import settings
from app.schemas.prediction import ModelAvailabilityStatus

logger = logging.getLogger(__name__)


@dataclass
class ModelArtifactMetadata:
    """Lineage and provenance metadata accompanying frozen retention models."""

    model_name: str
    model_version: str
    data_origin: str  # "empirical" or "synthetic"
    training_timestamp: str
    feature_schema_version: str
    is_empirically_validated: bool
    evaluation_metrics: dict[str, Any]


class RetentionModelRegistry:
    """Manages frozen model artifacts and enforces environment safety boundaries."""

    def __init__(self, artifacts_dir: Path | None = None) -> None:
        if artifacts_dir is None:
            # ml/artifacts directory at repository root
            self.artifacts_dir = Path(__file__).resolve().parents[4] / "ml" / "artifacts"
        else:
            self.artifacts_dir = artifacts_dir

        self._cached_model: TemporalRetentionModel | None = None
        self._cached_metadata: ModelArtifactMetadata | None = None

    def get_active_model(
        self,
        allow_synthetic_in_dev: bool = True,
    ) -> tuple[TemporalRetentionModel | None, ModelArtifactMetadata | None, ModelAvailabilityStatus]:
        """Load and return the active retention model, validating environment constraints.

        STRICT SAFETY ENFORCEMENT (Section 4.4):
        In production (settings.ENVIRONMENT == "production"):
        - Models with data_origin == "synthetic" are strictly rejected.
        - If no empirically validated model exists, returns INSUFFICIENT_EMPIRICAL_DATA.

        In development / test:
        - If allow_synthetic_in_dev is True, returns a calibrated synthetic-mode model
          flagged with SYNTHETIC_TEST_MODE.
        """
        # Return cached model if already initialized
        if self._cached_model is not None and self._cached_metadata is not None:
            if settings.ENVIRONMENT == "production" and self._cached_metadata.data_origin == "synthetic":
                return None, None, ModelAvailabilityStatus.INSUFFICIENT_EMPIRICAL_DATA
            status = (
                ModelAvailabilityStatus.SYNTHETIC_TEST_MODE
                if self._cached_metadata.data_origin == "synthetic"
                else ModelAvailabilityStatus.EMPIRICAL_MODEL_READY
            )
            return self._cached_model, self._cached_metadata, status

        # Search for frozen models on disk
        metadata_file = self.artifacts_dir / "active_model" / "metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, encoding="utf-8") as f:
                    meta_dict = json.load(f)

                meta = ModelArtifactMetadata(
                    model_name=meta_dict.get("model_name", "DAS3H-Extended"),
                    model_version=meta_dict.get("model_version", "1.0.0"),
                    data_origin=meta_dict.get("data_origin", "synthetic"),
                    training_timestamp=meta_dict.get("training_timestamp", ""),
                    feature_schema_version=meta_dict.get("feature_schema_version", "1.0.0"),
                    is_empirically_validated=meta_dict.get("is_empirically_validated", False),
                    evaluation_metrics=meta_dict.get("evaluation_metrics", {}),
                )

                if settings.ENVIRONMENT == "production" and meta.data_origin != "empirical":
                    # Production requires real empirical data
                    return None, None, ModelAvailabilityStatus.INSUFFICIENT_EMPIRICAL_DATA

                model = ExtendedDAS3HModel(version=meta.model_version)
                self._cached_model = model
                self._cached_metadata = meta

                status = (
                    ModelAvailabilityStatus.EMPIRICAL_MODEL_READY
                    if meta.data_origin == "empirical"
                    else ModelAvailabilityStatus.SYNTHETIC_TEST_MODE
                )
                return model, meta, status
            except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
                logger.warning("Failed to load model artifact from disk: %s", exc)
                return None, None, ModelAvailabilityStatus.MODEL_UNAVAILABLE

        # No frozen model found on disk
        if settings.ENVIRONMENT == "production":
            # In production, without empirical artifact, system must declare insufficient data
            return None, None, ModelAvailabilityStatus.INSUFFICIENT_EMPIRICAL_DATA

        # In dev/test: instantiate default test model if permitted
        if allow_synthetic_in_dev:
            # Default to HLR / Extended-DAS3H for dev testing
            meta = ModelArtifactMetadata(
                model_name="Half-Life-Regression",
                model_version="1.0.0-dev",
                data_origin="synthetic",
                training_timestamp="2026-11-03T00:00:00Z",
                feature_schema_version="1.0.0",
                is_empirically_validated=False,
                evaluation_metrics={"note": "Default dev test mode"},
            )
            model = HalfLifeRegressionModel(version=meta.model_version)
            self._cached_model = model
            self._cached_metadata = meta
            return model, meta, ModelAvailabilityStatus.SYNTHETIC_TEST_MODE

        return None, None, ModelAvailabilityStatus.MODEL_UNAVAILABLE
