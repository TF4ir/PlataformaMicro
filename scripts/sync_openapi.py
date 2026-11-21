#!/usr/bin/env python3
"""Canonical OpenAPI Specification Synchronization Script (PlataformaMicro Release R1.1 - C5)

Synchronizes `packages/contracts/openapi/openapi.json` directly from FastAPI's canonical
`app.openapi()`, preserving governance metadata (`info`, `servers`, `security`, `tags`,
and `components.securitySchemes`), while strictly updating paths and schemas.

Supports `--check` mode for CI pipelines to guarantee zero drift.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import sys
from pathlib import Path
from typing import Any

# Ensure services/ml-api virtualenv python is used if local python is missing dependencies
REPO_ROOT = Path(__file__).resolve().parent.parent
ML_API_DIR = REPO_ROOT / "services" / "ml-api"
VENV_PYTHON = ML_API_DIR / ".venv" / "bin" / "python"

if VENV_PYTHON.exists() and sys.executable != str(VENV_PYTHON):
    try:
        import fastapi  # noqa: F401
    except ImportError:
        # Re-exec under virtual environment python
        os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), __file__, *sys.argv[1:]])


def get_canonical_openapi() -> dict[str, Any]:
    """Generates canonical OpenAPI schema from FastAPI application instance."""
    sys.path.insert(0, str(ML_API_DIR))
    from app.main import app  # type: ignore

    return app.openapi()


def merge_governance_and_canonical(
    fastapi_schema: dict[str, Any], existing_spec: dict[str, Any]
) -> dict[str, Any]:
    """Preserves governance metadata while replacing paths and schemas with canonical FastAPI output."""
    canonical: dict[str, Any] = {
        "openapi": fastapi_schema.get("openapi", "3.1.0"),
        "info": existing_spec.get("info", fastapi_schema.get("info", {})),
        "servers": existing_spec.get("servers", fastapi_schema.get("servers", [])),
    }

    # Governance: Top-level security requirements
    if "security" in existing_spec:
        canonical["security"] = existing_spec["security"]
    elif "security" in fastapi_schema:
        canonical["security"] = fastapi_schema["security"]

    # Governance: Tags taxonomy
    if "tags" in existing_spec and existing_spec["tags"] is not None:
        canonical["tags"] = existing_spec["tags"]
    elif "tags" in fastapi_schema and fastapi_schema["tags"] is not None:
        canonical["tags"] = fastapi_schema["tags"]

    # Paths: sorted alphabetically for deterministic serialization
    raw_paths = fastapi_schema.get("paths", {})
    canonical["paths"] = {k: raw_paths[k] for k in sorted(raw_paths.keys())}

    # Components: schemas from FastAPI + securitySchemes from governance
    components: dict[str, Any] = {}
    raw_schemas = fastapi_schema.get("components", {}).get("schemas", {})
    if raw_schemas:
        components["schemas"] = {k: raw_schemas[k] for k in sorted(raw_schemas.keys())}

    governance_security_schemes = existing_spec.get("components", {}).get("securitySchemes")
    if governance_security_schemes:
        components["securitySchemes"] = governance_security_schemes
    elif "components" in fastapi_schema and "securitySchemes" in fastapi_schema["components"]:
        components["securitySchemes"] = fastapi_schema["components"]["securitySchemes"]

    canonical["components"] = components
    return canonical


def deterministic_serialize(data: dict[str, Any]) -> str:
    """Serializes JSON deterministically with 2-space indentation and trailing newline."""
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Synchronize packages/contracts/openapi/openapi.json from FastAPI app.openapi()."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check whether openapi.json is in sync with canonical FastAPI schema without writing changes.",
    )
    parser.add_argument(
        "--spec-path",
        type=Path,
        default=REPO_ROOT / "packages" / "contracts" / "openapi" / "openapi.json",
        help="Path to openapi.json contract file.",
    )
    args = parser.parse_args()

    spec_path: Path = args.spec_path.resolve()
    if not spec_path.exists():
        print(f"ERROR: Specification file not found at {spec_path}", file=sys.stderr)
        return 1

    try:
        with open(spec_path, encoding="utf-8") as f:
            existing_spec = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"ERROR: Could not parse existing specification: {e}", file=sys.stderr)
        return 1

    fastapi_schema = get_canonical_openapi()
    canonical_spec = merge_governance_and_canonical(fastapi_schema, existing_spec)
    canonical_json_str = deterministic_serialize(canonical_spec)

    with open(spec_path, encoding="utf-8") as f:
        current_content = f.read()

    def _display_path(p: Path) -> str:
        try:
            return str(p.relative_to(REPO_ROOT))
        except ValueError:
            return str(p)

    if args.check:
        if current_content == canonical_json_str:
            print("OK: OpenAPI contract is up to date with canonical FastAPI application.")
            return 0

        print(
            f"ERROR: OpenAPI contract at {_display_path(spec_path)} is OUT OF SYNC with FastAPI app.openapi()!",
            file=sys.stderr,
        )
        print("Diff (current vs canonical):", file=sys.stderr)
        diff = difflib.unified_diff(
            current_content.splitlines(keepends=True),
            canonical_json_str.splitlines(keepends=True),
            fromfile=_display_path(spec_path),
            tofile="canonical_app_openapi.json",
            n=3,
        )
        sys.stderr.writelines(diff)
        print(
            "\nPlease run 'python3 scripts/sync_openapi.py' to synchronize the contract before committing.",
            file=sys.stderr,
        )
        return 1

    # Write mode
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    with open(spec_path, "w", encoding="utf-8") as f:
        f.write(canonical_json_str)

    print(
        f"SUCCESS: Synchronized canonical OpenAPI schema ({len(canonical_spec['paths'])} paths, "
        f"{len(canonical_spec.get('components', {}).get('schemas', {}))} schemas) -> {_display_path(spec_path)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
