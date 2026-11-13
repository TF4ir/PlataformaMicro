"""Model Registry and Artifact Loader for Retention Inference.

Addresses Section 4.4 and 4.5 of TASK M5.3:
Enforces decoupled loading of versioned model artifacts and strict production guards
against using uncalibrated synthetic models on real students.
"""

from __future__ import annotations

import json
import logging
import os
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


def resolve_artifacts_dir(explicit_path: Path | str | None = None) -> Path:
    """Resolve the directory containing model artifacts safely across environments.

    Precedence order:
    1. Explicit path parameter (if provided).
    2. MODEL_ARTIFACTS_DIR environment variable or application setting.
    3. Ascending directory search from current file for an 'ml/artifacts' directory.
    4. Ascending directory search from current working directory (CWD) for 'ml/artifacts'.
    5. Fallback candidate within container environments (/app/ml/artifacts).
    6. Default fallback adjacent to current file with a clear log warning.

    Validates existence, usability, and logs actionable diagnostics if artifacts are not found.
    Never uses hardcoded Path.parents indices, preventing IndexError inside containers.
    """
    if explicit_path is not None and str(explicit_path).strip():
        p = Path(str(explicit_path).strip()).resolve()
        if not p.is_dir():
            logger.warning(
                "Explicitly configured artifacts directory does not exist or is not a directory: %s",
                p,
            )
        return p

    raw_env_dir = os.environ.get("MODEL_ARTIFACTS_DIR") or getattr(settings, "MODEL_ARTIFACTS_DIR", None)
    if raw_env_dir and str(raw_env_dir).strip():
        p = Path(str(raw_env_dir).strip()).resolve()
        if not p.is_dir():
            logger.warning(
                "MODEL_ARTIFACTS_DIR setting (%s) does not exist or is not a directory.",
                p,
            )
        return p

    curr = Path(__file__).resolve().parent
    for ancestor in [curr, *curr.parents]:
        candidate = ancestor / "ml" / "artifacts"
        if candidate.is_dir():
            return candidate

    cwd = Path.cwd().resolve()
    for ancestor in [cwd, *cwd.parents]:
        candidate = ancestor / "ml" / "artifacts"
        if candidate.is_dir():
            return candidate

    container_fallback = Path("/app/ml/artifacts")
    if container_fallback.is_dir():
        return container_fallback

    # Final fallback if directory structure cannot be resolved
    fallback = curr / "artifacts"
    logger.warning(
        "Could not automatically locate 'ml/artifacts' directory in any parent of %s or %s. "
        "Defaulting to %s",
        curr,
        cwd,
        fallback,
    )
    return fallback


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

    def __init__(self, artifacts_dir: Path | str | None = None) -> None:
        self.artifacts_dir = resolve_artifacts_dir(artifacts_dir)
        self._cached_model: TemporalRetentionModel | None = None
        self._cached_metadata: ModelArtifactMetadata | None = None

        # Validate that the selected artifacts path exists and is usable
        if not self.artifacts_dir.exists():
            logger.warning(
                "Model artifacts directory does not exist: %s. Models will not be loaded from disk.",
                self.artifacts_dir,
            )
        elif not self.artifacts_dir.is_dir():
            logger.warning(
                "Model artifacts path exists but is not a directory: %s",
                self.artifacts_dir,
            )
        elif not os.access(self.artifacts_dir, os.R_OK):
            logger.warning(
                "Model artifacts directory is not readable (check file permissions): %s",
                self.artifacts_dir,
            )
        else:
            logger.info("Model registry initialized with artifacts directory: %s", self.artifacts_dir)

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
                    logger.warning(
                        "Active model metadata at %s has data_origin='%s' but production requires 'empirical'. "
                        "Declaring INSUFFICIENT_EMPIRICAL_DATA.",
                        metadata_file,
                        meta.data_origin,
                    )
                    return None, None, ModelAvailabilityStatus.INSUFFICIENT_EMPIRICAL_DATA

                loaded_model: TemporalRetentionModel = ExtendedDAS3HModel(version=meta.model_version)
                self._cached_model = loaded_model
                self._cached_metadata = meta

                status = (
                    ModelAvailabilityStatus.EMPIRICAL_MODEL_READY
                    if meta.data_origin == "empirical"
                    else ModelAvailabilityStatus.SYNTHETIC_TEST_MODE
                )
                logger.info(
                    "Loaded active model artifact: %s v%s (origin=%s, status=%s)",
                    meta.model_name,
                    meta.model_version,
                    meta.data_origin,
                    status.value,
                )
                return loaded_model, meta, status
            except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
                logger.warning("Failed to load model artifact from disk: %s", exc)
                return None, None, ModelAvailabilityStatus.MODEL_UNAVAILABLE

        # No frozen model found on disk - inform clearly via structured logging
        if settings.ENVIRONMENT == "production":
            logger.warning(
                "Active model artifact not found at %s. Production environment requires empirical model; "
                "declaring INSUFFICIENT_EMPIRICAL_DATA.",
                metadata_file,
            )
            return None, None, ModelAvailabilityStatus.INSUFFICIENT_EMPIRICAL_DATA

        # In dev/test: instantiate default test model if permitted
        if allow_synthetic_in_dev:
            logger.info(
                "Active model artifact not found at %s. Falling back to synthetic model for dev/test execution.",
                metadata_file,
            )
            meta = ModelArtifactMetadata(
                model_name="Half-Life-Regression",
                model_version="1.0.0-dev",
                data_origin="synthetic",
                training_timestamp="2026-11-03T00:00:00Z",
                feature_schema_version="1.0.0",
                is_empirically_validated=False,
                evaluation_metrics={"note": "Default dev test mode"},
            )
            fallback_model: TemporalRetentionModel = HalfLifeRegressionModel(version=meta.model_version)
            self._cached_model = fallback_model
            self._cached_metadata = meta
            return fallback_model, meta, ModelAvailabilityStatus.SYNTHETIC_TEST_MODE

        logger.warning(
            "Active model artifact not found at %s and synthetic mode disabled; declaring MODEL_UNAVAILABLE.",
            metadata_file,
        )
        return None, None, ModelAvailabilityStatus.MODEL_UNAVAILABLE
