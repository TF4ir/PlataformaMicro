#!/usr/bin/env python3
"""
Verification Script for Milestone 2: Technical Architecture & Formal Contracts
Plataforma de Microaprendizaje Adaptativo (5to Secundaria)

Validates:
1. Presence of all 5 docs/architecture/ files and packages/contracts/openapi/openapi.json.
2. JSON parsing and schema structure of packages/contracts/openapi/openapi.json.
3. Python AST parsing of all python code blocks in docs/architecture/model-contract.md.
4. Cross-contract consistency: 100% field presence and alignment for answer_events and predictions
   across database-schema.md, api-contracts.md, openapi.json, and model-contract.md.
5. Database schema specifications: RLS on 100% tables, REVOKE UPDATE/DELETE on answer_events,
   optimized scalar subqueries (SELECT auth.uid()), and temporal index idx_answer_events_student_kc.
6. Security and ethics specifications: Ley N° 29733, student_id_pseudo, delayed_assessment quarantine.
"""

import ast
import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path("/root/PlataformaMicro")

REQUIRED_FILES = [
    "docs/architecture/overview.md",
    "docs/architecture/database-schema.md",
    "docs/architecture/api-contracts.md",
    "packages/contracts/openapi/openapi.json",
    "docs/architecture/model-contract.md",
    "docs/architecture/security.md",
]

ANSWER_EVENTS_REQUIRED_FIELDS = [
    "attempt_id",
    "question_id",
    "selected_option_id",
    "response_time_seconds",
    "idempotency_key",
]

PREDICTIONS_REQUIRED_FIELDS = [
    "student_id",
    "knowledge_component_id",
    "estimated_risk",
    "risk_level",
    "prediction_status",
]

passed_tests = 0
failed_tests = 0


def report_assert(condition: bool, test_name: str, detail: str = ""):
    global passed_tests, failed_tests
    if condition:
        passed_tests += 1
        print(f"  [PASS] {test_name}" + (f": {detail}" if detail else ""))
    else:
        failed_tests += 1
        print(f"  [FAIL] {test_name}: {detail}", file=sys.stderr)


def test_file_presence():
    print("\n--- Test 1: Presence of Milestone 2 Deliverables ---")
    for rel_path in REQUIRED_FILES:
        full_path = REPO_ROOT / rel_path
        exists = full_path.is_file()
        size = full_path.stat().st_size if exists else 0
        report_assert(exists and size > 0, f"File existence: {rel_path}", f"size={size} bytes")


def test_openapi_json():
    print("\n--- Test 2: OpenAPI 3.1.0 JSON Parsing & Specification Integrity ---")
    openapi_path = REPO_ROOT / "packages/contracts/openapi/openapi.json"
    try:
        with open(openapi_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        report_assert(True, "JSON parse of openapi.json")
    except Exception as e:
        report_assert(False, "JSON parse of openapi.json", str(e))
        return

    # Check OpenAPI version
    version = data.get("openapi", "")
    report_assert(version.startswith("3.1"), "OpenAPI version 3.1.x", f"found '{version}'")

    # Check Required Paths
    expected_paths = [
        "/api/v1/diagnostic/answers",
        "/api/v1/learning/attempts/{attempt_id}/answers",
        "/api/v1/ml/predict-risk",
        "/api/v1/predictions/retention",
        "/api/v1/recommendations/{student_id}",
        "/api/v1/recommendations/generate",
        "/api/v1/health/warmup",
    ]
    paths = data.get("paths", {})
    for path in expected_paths:
        report_assert(path in paths, f"Path defined in OpenAPI: {path}")

    # Check Required Schemas
    expected_schemas = [
        "AnswerEventSubmitRequest",
        "AnswerEventSubmitResponse",
        "PredictRiskRequest",
        "PredictRiskResponse",
        "PredictionItem",
        "GetRecommendationsResponse",
        "RecommendationItem",
        "MicrocontentSummary",
        "WarmupResponse",
        "ProblemDetails",
    ]
    schemas = data.get("components", {}).get("schemas", {})
    for schema_name in expected_schemas:
        report_assert(schema_name in schemas, f"Schema component: {schema_name}")

    # Check AnswerEventSubmitRequest properties in OpenAPI
    answer_req_props = schemas.get("AnswerEventSubmitRequest", {}).get("properties", {})
    for field in ANSWER_EVENTS_REQUIRED_FIELDS:
        report_assert(
            field in answer_req_props,
            f"OpenAPI AnswerEventSubmitRequest property: {field}",
        )


def test_python_ast():
    print("\n--- Test 3: Python AST Parsing of model-contract.md ---")
    model_contract_path = REPO_ROOT / "docs/architecture/model-contract.md"
    with open(model_contract_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract all ```python blocks
    code_blocks = re.findall(r"```python\s*(.*?)\s*```", content, re.DOTALL)
    report_assert(len(code_blocks) > 0, "Python code block found in model-contract.md", f"{len(code_blocks)} block(s)")

    combined_code = "\n\n".join(code_blocks)
    try:
        tree = ast.parse(combined_code)
        report_assert(True, "AST parse of model-contract.md code blocks")
    except SyntaxError as e:
        report_assert(False, "AST parse of model-contract.md code blocks", f"SyntaxError at line {e.lineno}: {e.msg}")
        return

    # Check presence of required classes and protocols
    class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    expected_classes = [
        "StudentInteractionEvent",
        "TemporalWindowFeatures",
        "TemporalSequenceFeatures",
        "PredictionOutput",
        "ShapExplanation",
        "ModelInferenceResult",
        "BKTParameters",
        "KnowledgeTracingModel",
        "BaseRetentionModel",
        "ModelEvaluationMetrics",
        "ModelArtifactMetadata",
        "RiskLevel",
        "PredictionStatus",
    ]
    for cname in expected_classes:
        report_assert(cname in class_names, f"Class/Protocol definition: {cname}")


def test_cross_contract_consistency():
    print("\n--- Test 4: Cross-Contract Consistency (answer_events & predictions) ---")

    # Load file contents
    db_ddl = (REPO_ROOT / "docs/architecture/database-schema.md").read_text(encoding="utf-8")
    api_md = (REPO_ROOT / "docs/architecture/api-contracts.md").read_text(encoding="utf-8")
    with open(REPO_ROOT / "packages/contracts/openapi/openapi.json", "r", encoding="utf-8") as f:
        openapi_data = json.load(f)
    model_md = (REPO_ROOT / "docs/architecture/model-contract.md").read_text(encoding="utf-8")

    # Extract answer_events table block from DDL
    answer_events_table_match = re.search(
        r"CREATE TABLE answer_events\s*\((.*?)\);", db_ddl, re.DOTALL | re.IGNORECASE
    )
    report_assert(
        answer_events_table_match is not None,
        "Found CREATE TABLE answer_events in database-schema.md",
    )
    answer_events_ddl = answer_events_table_match.group(1) if answer_events_table_match else ""

    # 4.1 answer_events fields consistency across all 4 contracts
    openapi_answer_props = openapi_data.get("components", {}).get("schemas", {}).get(
        "AnswerEventSubmitRequest", {}
    ).get("properties", {})

    for field in ANSWER_EVENTS_REQUIRED_FIELDS:
        # Check in PostgreSQL DDL
        in_ddl = bool(re.search(rf"\b{field}\b", answer_events_ddl))
        report_assert(in_ddl, f"answer_events.{field} in database-schema.md DDL")

        # Check in api-contracts.md
        in_api_md = f'"{field}"' in api_md
        report_assert(in_api_md, f"answer_events.{field} in api-contracts.md JSON Schema")

        # Check in openapi.json
        in_openapi = field in openapi_answer_props
        report_assert(in_openapi, f"answer_events.{field} in openapi.json schema properties")

        # Check in model-contract.md
        in_model = bool(re.search(rf"\b{field}\b", model_md))
        report_assert(in_model, f"answer_events.{field} in model-contract.md StudentInteractionEvent")

    # 4.2 predictions fields consistency across all 4 contracts
    predictions_table_match = re.search(
        r"CREATE TABLE predictions\s*\((.*?)\);", db_ddl, re.DOTALL | re.IGNORECASE
    )
    report_assert(
        predictions_table_match is not None,
        "Found CREATE TABLE predictions in database-schema.md",
    )
    predictions_ddl = predictions_table_match.group(1) if predictions_table_match else ""

    openapi_pred_props = openapi_data.get("components", {}).get("schemas", {}).get(
        "PredictRiskResponse", {}
    ).get("properties", {})
    openapi_pred_item = openapi_data.get("components", {}).get("schemas", {}).get(
        "PredictionItem", {}
    ).get("properties", {})

    for field in PREDICTIONS_REQUIRED_FIELDS:
        # Check in PostgreSQL DDL
        in_ddl = bool(re.search(rf"\b{field}\b", predictions_ddl))
        report_assert(in_ddl, f"predictions.{field} in database-schema.md DDL")

        # Check in api-contracts.md
        in_api_md = f'"{field}"' in api_md
        report_assert(in_api_md, f"predictions.{field} in api-contracts.md JSON Schema")

        # Check in openapi.json
        in_openapi = (field in openapi_pred_props) or (field in openapi_pred_item)
        report_assert(in_openapi, f"predictions.{field} in openapi.json schema")

        # Check in model-contract.md
        in_model = bool(re.search(rf"\b{field}\b", model_md))
        report_assert(in_model, f"predictions.{field} in model-contract.md")

    # Horizon hours consistency: horizon_hours / prediction_horizon_hours
    report_assert("prediction_horizon_hours" in predictions_ddl, "prediction_horizon_hours in predictions DDL")
    report_assert("horizon_hours" in openapi_pred_item, "horizon_hours in openapi PredictionItem")
    report_assert("horizon_hours" in model_md, "horizon_hours in model-contract.md PredictionOutput")

    # Recall probability consistency: predicted_recall_probability / recall_probability
    report_assert("predicted_recall_probability" in predictions_ddl, "predicted_recall_probability in predictions DDL")
    report_assert("recall_probability" in openapi_pred_item, "recall_probability in openapi PredictionItem")
    report_assert("recall_probability" in model_md, "recall_probability in model-contract.md PredictionOutput")


def test_database_schema_rules():
    print("\n--- Test 5: Database Schema Rules (RLS, Inmutability & Indexing) ---")
    db_ddl = (REPO_ROOT / "docs/architecture/database-schema.md").read_text(encoding="utf-8")

    # Check table count (must be >= 17 tables)
    created_tables = re.findall(r"CREATE TABLE (\w+)", db_ddl, re.IGNORECASE)
    report_assert(len(created_tables) >= 17, f"At least 17 tables created (found {len(created_tables)} tables)", str(created_tables))

    # Check RLS enabled on all created tables
    rls_tables = re.findall(r"ALTER TABLE (\w+) ENABLE ROW LEVEL SECURITY;", db_ddl, re.IGNORECASE)
    missing_rls = [t for t in created_tables if t not in rls_tables]
    report_assert(len(missing_rls) == 0, "RLS enabled on 100% of tables", f"missing: {missing_rls}" if missing_rls else "100% covered")

    # Check scalar subquery optimization (SELECT auth.uid())
    has_scalar_auth = "(SELECT auth.uid())" in db_ddl
    report_assert(has_scalar_auth, "RLS policies use scalar subquery '(SELECT auth.uid())'")

    # Check strict immutability: REVOKE UPDATE, DELETE ON answer_events
    revoke_match = bool(re.search(r"REVOKE UPDATE,\s*DELETE ON answer_events FROM anon,\s*authenticated;", db_ddl, re.IGNORECASE))
    report_assert(revoke_match, "Strict immutability: REVOKE UPDATE, DELETE ON answer_events FROM anon, authenticated")

    # Check temporal window index
    has_temporal_idx = "idx_answer_events_student_kc" in db_ddl
    report_assert(has_temporal_idx, "Temporal window index idx_answer_events_student_kc defined on answer_events")


def test_security_and_governance():
    print("\n--- Test 6: Security, Governance & Minor Privacy (Ley N° 29733) ---")
    sec_md = (REPO_ROOT / "docs/architecture/security.md").read_text(encoding="utf-8")
    db_ddl = (REPO_ROOT / "docs/architecture/database-schema.md").read_text(encoding="utf-8")
    overview_md = (REPO_ROOT / "docs/architecture/overview.md").read_text(encoding="utf-8")

    # Check Peruvian Law 29733
    report_assert("29733" in sec_md, "Peruvian Personal Data Protection Law N° 29733 in security.md")

    # Check student_id_pseudo in database and security
    report_assert("student_id_pseudo" in db_ddl, "student_id_pseudo in database-schema.md enrollments")
    report_assert("student_id_pseudo" in sec_md, "student_id_pseudo in security.md anonymization")

    # Check delayed assessment quarantine
    report_assert("delayed_assessment" in sec_md, "delayed_assessment quarantine in security.md")
    report_assert("delayed_assessment" in db_ddl, "delayed_assessment in activity_type_enum in database-schema.md")
    report_assert("delayed_assessment" in overview_md, "delayed_assessment quarantine mentioned in overview.md")

    # Check blitz.cloud cold start mitigation in overview and openapi
    report_assert("warmup" in overview_md.lower(), "Warmup ping mitigation in overview.md")
    report_assert("/api/v1/health/warmup" in sec_md or "/api/v1/health/warmup" in overview_md, "Warmup endpoint in architecture docs")


def main():
    print("=" * 70)
    print("STARTING VERIFICATION SCRIPT: scripts/verify-m2.py")
    print("Milestone 2: Technical Architecture & Formal Contracts")
    print("=" * 70)

    test_file_presence()
    test_openapi_json()
    test_python_ast()
    test_cross_contract_consistency()
    test_database_schema_rules()
    test_security_and_governance()

    print("\n" + "=" * 70)
    print(f"VERIFICATION RESULTS: {passed_tests} PASSED, {failed_tests} FAILED")
    print("=" * 70)

    if failed_tests > 0:
        print("\n❌ Milestone 2 Verification FAILED! Please resolve the errors above.", file=sys.stderr)
        sys.exit(1)
    else:
        print("\n✅ Milestone 2 Verification PASSED! All architectural contracts and criteria verified.")
        sys.exit(0)


if __name__ == "__main__":
    main()
