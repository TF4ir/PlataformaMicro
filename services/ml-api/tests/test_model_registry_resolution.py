"""Unit tests for RetentionModelRegistry and dynamic artifact resolution across environments.

Verifies resolution under:
- Local monorepo structure
- Container structure (/app/app/prediction/...)
- Explicit MODEL_ARTIFACTS_DIR env variable
- Explicit constructor parameter
- Non-existent artifacts directory (safe fallback, no IndexError)
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from app.core.config import settings
from app.prediction.model_registry import (
    RetentionModelRegistry,
    resolve_artifacts_dir,
)
from app.schemas.prediction import ModelAvailabilityStatus


class TestModelRegistryResolution:
    """Tests for artifact path resolution robustness and safety."""

    def test_resolution_in_local_repo(self) -> None:
        """Should find ml/artifacts by searching ascending directory tree from local file."""
        resolved = resolve_artifacts_dir()
        assert resolved.name == "artifacts"
        assert resolved.parent.name == "ml"
        assert resolved.is_dir()

    def test_resolution_explicit_param_path(self, tmp_path: Path) -> None:
        """Should respect explicit Path passed to resolver or constructor."""
        custom_dir = tmp_path / "custom_artifacts"
        custom_dir.mkdir()
        resolved = resolve_artifacts_dir(custom_dir)
        assert resolved == custom_dir.resolve()

        registry = RetentionModelRegistry(artifacts_dir=custom_dir)
        assert registry.artifacts_dir == custom_dir.resolve()

    def test_resolution_explicit_param_str(self, tmp_path: Path) -> None:
        """Should accept string path and convert to resolved Path."""
        custom_dir = tmp_path / "custom_str_dir"
        custom_dir.mkdir()
        resolved = resolve_artifacts_dir(str(custom_dir))
        assert resolved == custom_dir.resolve()

    def test_resolution_via_env_var(self, tmp_path: Path) -> None:
        """Should respect MODEL_ARTIFACTS_DIR environment variable."""
        custom_env_dir = tmp_path / "env_artifacts"
        custom_env_dir.mkdir()
        with patch.dict(os.environ, {"MODEL_ARTIFACTS_DIR": str(custom_env_dir)}):
            resolved = resolve_artifacts_dir()
            assert resolved == custom_env_dir.resolve()

            registry = RetentionModelRegistry()
            assert registry.artifacts_dir == custom_env_dir.resolve()

    def test_simulated_container_path_no_index_error(self, tmp_path: Path) -> None:
        """Simulate container structure /app/app/prediction/model_registry.py where parents has 4 elements.

        Verifies that resolve_artifacts_dir() executes directly and successfully resolves
        to the container ml/artifacts directory without raising IndexError.
        """
        import app.prediction.model_registry as mr

        container_root = tmp_path / "container_app"
        fake_ml_artifacts = container_root / "ml" / "artifacts"
        fake_ml_artifacts.mkdir(parents=True)

        fake_file_dir = container_root / "app" / "prediction"
        fake_file_dir.mkdir(parents=True)
        fake_file = fake_file_dir / "model_registry.py"
        fake_file.touch()

        # Patch __file__ on the module to simulate running inside container
        with patch.object(mr, "__file__", str(fake_file)):
            # 1. resolve_artifacts_dir must locate the fake container ml/artifacts
            resolved = mr.resolve_artifacts_dir()
            assert resolved == fake_ml_artifacts.resolve()

            # 2. RetentionModelRegistry initialization must succeed without IndexError
            registry = mr.RetentionModelRegistry()
            assert registry.artifacts_dir == fake_ml_artifacts.resolve()

    def test_whitespace_and_empty_inputs(self, tmp_path: Path) -> None:
        """Whitespace-only paths in explicit_path or MODEL_ARTIFACTS_DIR should fall back safely."""
        with patch.dict(os.environ, {"MODEL_ARTIFACTS_DIR": "   "}):
            resolved = resolve_artifacts_dir("   ")
            assert resolved.name == "artifacts"
            assert resolved.parent.name == "ml"
            assert resolved.is_dir()

    def test_nonexistent_artifacts_dir_does_not_crash(self, tmp_path: Path) -> None:
        """Non-existent directory should be handled gracefully without IndexError."""
        fake_dir = tmp_path / "does_not_exist"
        registry = RetentionModelRegistry(artifacts_dir=fake_dir)
        assert registry.artifacts_dir == fake_dir.resolve()

        # In dev, should fall back to synthetic model
        model, _meta, status = registry.get_active_model(allow_synthetic_in_dev=True)
        assert model is not None
        assert status == ModelAvailabilityStatus.SYNTHETIC_TEST_MODE

    def test_production_guardrail_with_missing_artifacts(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """In production, missing artifacts safely return INSUFFICIENT_EMPIRICAL_DATA with clear logging."""
        import logging

        fake_dir = tmp_path / "does_not_exist"
        registry = RetentionModelRegistry(artifacts_dir=fake_dir)

        orig_env = settings.ENVIRONMENT
        try:
            settings.ENVIRONMENT = "production"
            with caplog.at_level(logging.WARNING):
                model, _meta, status = registry.get_active_model()
            assert model is None
            assert status == ModelAvailabilityStatus.INSUFFICIENT_EMPIRICAL_DATA
            # Must log actionable diagnosis
            assert any("INSUFFICIENT_EMPIRICAL_DATA" in r.message for r in caplog.records)
        finally:
            settings.ENVIRONMENT = orig_env
