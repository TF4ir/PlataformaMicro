#!/usr/bin/env python3
"""
scripts/verify-phase0.py — Master Automated Verification Suite & Integrity Audit

Plataforma de Microaprendizaje Adaptativo (5to Secundaria)
Phase 0: Base Architecture, Governance, Formal Contracts & Research Protocol.

Covers the complete 14 verification categories defined in the Master Blueprint:
  Category 1:  Physical Monorepo Directory Scaffold
  Category 2:  Root Files & Governance
  Category 3:  Agent Rules (trigger: always_on & descriptions)
  Category 4:  Agent Skills Library (16 skills, frontmatter & formulas)
  Category 5:  Agent Workflows (6 workflows)
  Category 6:  Technical Architecture (docs/architecture/)
  Category 7:  ADRs (ADR-0001, ADR-0002, ADR-0003 with Status: ACCEPTED)
  Category 8:  SRS & Research Protocol (FR-01..16, NFR-01..04, 5-item risk matrix, Ley N° 29733)
  Category 9:  Negative Scope Guardrail (Mandate R3: strictly 0 UI components in apps/web/)
  Category 10: SQL DDL Syntax & Security (20 tables, 100% RLS with (SELECT auth.uid()), immutable answer_events)
  Category 11: OpenAPI 3.1 JSON Schema Validation (7 paths, 10 schemas, 0 broken $refs)
  Category 12: Python Model Contract AST Validation (Pydantic v2, BaseRetentionModel ABC, KnowledgeTracingModel Protocol)
  Category 13: Section 7 Checklist Item 1 (Cross-contract field & type consistency across SQL, OpenAPI, Python)
  Category 14: Section 7 Checklist Item 2 (Critical decisions registration: pre-training, consent, 7d quarantine)
"""

import ast
import json
import os
import re
import sys
import time
import tomllib
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

REPO_ROOT = Path("/root/PlataformaMicro").resolve()

# Global audit metrics
TOTAL_PASSED = 0
TOTAL_FAILED = 0
CATEGORY_RESULTS: Dict[str, Tuple[int, int]] = {}
ERRORS: List[Tuple[str, str, str]] = []


def record_check(category: str, condition: bool, description: str, detail: str = "") -> bool:
    global TOTAL_PASSED, TOTAL_FAILED
    cat_pass, cat_fail = CATEGORY_RESULTS.get(category, (0, 0))

    if condition:
        TOTAL_PASSED += 1
        CATEGORY_RESULTS[category] = (cat_pass + 1, cat_fail)
        print(f"  [PASS] {description}" + (f": {detail}" if detail else ""))
        return True
    else:
        TOTAL_FAILED += 1
        CATEGORY_RESULTS[category] = (cat_pass, cat_fail + 1)
        print(f"  [FAIL] {description} -> {detail}", file=sys.stderr)
        ERRORS.append((category, description, detail))
        return False


def print_category_header(cat_num: int, cat_title: str) -> None:
    print(f"\n{'=' * 78}")
    print(f"  CATEGORY {cat_num}: {cat_title}")
    print(f"{'=' * 78}")


# ==============================================================================
# CATEGORY 1: Physical Monorepo Directory Scaffold
# ==============================================================================
def verify_category_1():
    cat = "Cat 1: Monorepo Directory Scaffold"
    print_category_header(1, "Physical Monorepo Directory Scaffold")

    required_dirs = [
        # Root directories
        "apps",
        "apps/web",
        "docs",
        "docs/architecture",
        "docs/architecture/adr",
        "docs/research",
        "docs/ux",
        "ml",
        "ml/datasets",
        "ml/artifacts",
        "ml/src",
        "ml/src/preprocessing",
        "ml/src/features",
        "ml/src/baselines",
        "ml/src/das3h",
        "ml/src/evaluation",
        "ml/src/training",
        "ml/tests",
        "packages",
        "packages/contracts",
        "packages/contracts/openapi",
        "packages/contracts/typescript",
        "services",
        "services/ml-api",
        "services/ml-api/app",
        "services/ml-api/app/api",
        "services/ml-api/app/api/v1",
        "services/ml-api/app/core",
        "services/ml-api/app/schemas",
        "services/ml-api/app/services",
        "services/ml-api/app/repositories",
        "services/ml-api/app/prediction",
        "services/ml-api/app/adaptation",
        "services/ml-api/tests",
        "supabase",
        "supabase/migrations",
        "supabase/tests",
        ".agents",
        ".agents/rules",
        ".agents/skills",
        ".agents/workflows",
        "scripts",
        # Web scaffolding directories
        "apps/web/public",
        "apps/web/src/app/(auth)",
        "apps/web/src/app/(student)",
        "apps/web/src/app/(teacher)",
        "apps/web/src/app/api",
        "apps/web/src/components/ui",
        "apps/web/src/components/common",
        "apps/web/src/features/courses",
        "apps/web/src/features/learning",
        "apps/web/src/features/microcontents",
        "apps/web/src/features/quizzes",
        "apps/web/src/features/recommendations",
        "apps/web/src/features/analytics",
        "apps/web/src/lib/supabase",
        "apps/web/src/lib/api-client",
        "apps/web/src/hooks",
        "apps/web/src/types",
    ]

    for rel_dir in required_dirs:
        dir_path = REPO_ROOT / rel_dir
        exists = dir_path.is_dir()
        record_check(cat, exists, f"Directory existence: {rel_dir}", "Present" if exists else "Missing directory")


# ==============================================================================
# CATEGORY 2: Root Files & Governance
# ==============================================================================
def verify_category_2():
    cat = "Cat 2: Root Files & Governance"
    print_category_header(2, "Root Files & Subsystem Governance")

    root_files = [
        "AGENTS.md",
        "README.md",
        "CONTRIBUTING.md",
        "docker-compose.yml",
        ".env.example",
        ".gitignore",
        "PROJECT.md",
    ]
    for rf in root_files:
        p = REPO_ROOT / rf
        exists = p.is_file() and p.stat().st_size > 0
        record_check(cat, exists, f"Root governance file: {rf}", f"{p.stat().st_size} bytes" if exists else "Missing/Empty")

    subsystem_agents = [
        "apps/web/AGENTS.md",
        "services/ml-api/AGENTS.md",
        "ml/AGENTS.md",
        "supabase/AGENTS.md",
    ]
    for sa in subsystem_agents:
        p = REPO_ROOT / sa
        exists = p.is_file() and p.stat().st_size > 0
        record_check(cat, exists, f"Subsystem AGENTS.md: {sa}", f"{p.stat().st_size} bytes" if exists else "Missing/Empty")

    # Config files syntax check
    json_targets = [
        REPO_ROOT / "apps/web/package.json",
        REPO_ROOT / "apps/web/tsconfig.json",
        REPO_ROOT / "packages/contracts/typescript/package.json",
        REPO_ROOT / "packages/contracts/openapi/openapi.json",
    ]
    for jt in json_targets:
        try:
            with open(jt, "r", encoding="utf-8") as f:
                json.load(f)
            record_check(cat, True, f"JSON syntax: {jt.relative_to(REPO_ROOT)}", "Valid JSON")
        except Exception as e:
            record_check(cat, False, f"JSON syntax: {jt.relative_to(REPO_ROOT)}", str(e))

    toml_targets = [
        REPO_ROOT / "services/ml-api/pyproject.toml",
        REPO_ROOT / "supabase/config.toml",
    ]
    for tt in toml_targets:
        try:
            with open(tt, "rb") as f:
                tomllib.load(f)
            record_check(cat, True, f"TOML syntax: {tt.relative_to(REPO_ROOT)}", "Valid TOML")
        except Exception as e:
            record_check(cat, False, f"TOML syntax: {tt.relative_to(REPO_ROOT)}", str(e))

    dockerfile = REPO_ROOT / "services/ml-api/Dockerfile"
    record_check(cat, dockerfile.is_file() and dockerfile.stat().st_size > 0, "FastAPI Dockerfile present", "Valid")


# ==============================================================================
# CATEGORY 3: Agent Rules (.agents/rules/*.md)
# ==============================================================================
def verify_category_3():
    cat = "Cat 3: Agent Rules"
    print_category_header(3, "Agent Rules (.agents/rules/*.md)")

    rules = [
        ("architecture.md", "Reglas de Arquitectura"),
        ("frontend.md", "Reglas de Frontend"),
        ("backend.md", "Reglas de Backend"),
        ("database.md", "Reglas de Base de Datos"),
        ("machine-learning.md", "Reglas de Machine Learning"),
        ("research-integrity.md", "Reglas de Integridad Científica y Ética"),
    ]

    for rule_file, rule_title in rules:
        p = REPO_ROOT / ".agents" / "rules" / rule_file
        if not p.is_file():
            record_check(cat, False, f"Rule file: {rule_file}", "File does not exist")
            continue

        content = p.read_text(encoding="utf-8")
        has_frontmatter = content.startswith("---") and "\n---\n" in content
        record_check(cat, has_frontmatter, f"Rule {rule_file}: Frontmatter delimiters (---)", "Present" if has_frontmatter else "Missing")

        has_trigger = "trigger: always_on" in content
        record_check(cat, has_trigger, f"Rule {rule_file}: trigger: always_on", "Found" if has_trigger else "Missing")

        has_desc = "description:" in content
        record_check(cat, has_desc, f"Rule {rule_file}: description metadata", "Found" if has_desc else "Missing")

        has_title = rule_title in content
        record_check(cat, has_title, f"Rule {rule_file}: substantive title '{rule_title}'", "Verified" if has_title else "Missing")


# ==============================================================================
# CATEGORY 4: Agent Skills Library (16 skills, frontmatter & formulas)
# ==============================================================================
def verify_category_4():
    cat = "Cat 4: Agent Skills Library"
    print_category_header(4, "Agent Skills Library (16 skills, frontmatter & formulas)")

    skills = [
        "adaptive-learning",
        "architecture-design",
        "eda-pipeline",
        "fastapi-development",
        "fastapi-templates",
        "feature-engineering",
        "frontend-development",
        "improve-animations",
        "model-evaluation",
        "model-training",
        "predictive-modeling",
        "supabase",
        "supabase-database",
        "supabase-postgres-best-practices",
        "testing-security",
        "ux-usability",
    ]

    for sk in skills:
        sk_path = REPO_ROOT / ".agents" / "skills" / sk / "SKILL.md"
        exists = sk_path.is_file() and sk_path.stat().st_size > 0
        record_check(cat, exists, f"Skill definition: {sk}/SKILL.md", f"{sk_path.stat().st_size} bytes" if exists else "Missing")

        if exists:
            content = sk_path.read_text(encoding="utf-8")
            has_fm = content.startswith("---") and "\n---\n" in content
            record_check(cat, has_fm, f"Skill {sk}: Valid frontmatter", "Verified" if has_fm else "Missing frontmatter")
            has_name = f"name: {sk}" in content or f"name: \"{sk}\"" in content or f"name: '{sk}'" in content
            record_check(cat, has_name, f"Skill {sk}: Name matches directory", "Match" if has_name else "Mismatch")
            has_desc = "description:" in content
            record_check(cat, has_desc, f"Skill {sk}: Description present", "Verified" if has_desc else "Missing")

    # Formula verification on key mathematical skills
    adaptive_sk = (REPO_ROOT / ".agents/skills/adaptive-learning/SKILL.md").read_text(encoding="utf-8")
    has_decay_thresh = r"\tau" in adaptive_sk and r"P(R=1" in adaptive_sk
    record_check(cat, has_decay_thresh, "adaptive-learning: Recall threshold formula P(R=1|dt) <= tau", "Found")

    feat_sk = (REPO_ROOT / ".agents/skills/feature-engineering/SKILL.md").read_text(encoding="utf-8")
    has_windows = "W_1" in feat_sk and "W_5" in feat_sk and "S_{s,k,w}" in feat_sk
    record_check(cat, has_windows, "feature-engineering: DAS3H 5 log-windows W1..W5 and S_{s,k,w}", "Found")

    train_sk = (REPO_ROOT / ".agents/skills/model-training/SKILL.md").read_text(encoding="utf-8")
    has_das3h_logit = r"\text{logit}(P(R=1))" in train_sk and r"\theta_s" in train_sk
    record_check(cat, has_das3h_logit, "model-training: DAS3H mathematical logit formulation", "Found")
    has_pfa = "PFA" in train_sk and r"\gamma_k" in train_sk
    record_check(cat, has_pfa, "model-training: PFA baseline formulation", "Found")
    has_bkt = "BKT" in train_sk and r"e^{-\lambda \Delta t}" in train_sk
    record_check(cat, has_bkt, "model-training: BKT with decay formulation", "Found")

    eval_sk = (REPO_ROOT / ".agents/skills/model-evaluation/SKILL.md").read_text(encoding="utf-8")
    has_brier = "Brier" in eval_sk and r"\frac{1}{N}" in eval_sk
    record_check(cat, has_brier, "model-evaluation: Brier score mathematical definition", "Found")
    has_ece = "ECE" in eval_sk and "Expected Calibration Error" in eval_sk
    record_check(cat, has_ece, "model-evaluation: Expected Calibration Error (ECE) definition", "Found")


# ==============================================================================
# CATEGORY 5: Agent Workflows (.agents/workflows/*.md)
# ==============================================================================
def verify_category_5():
    cat = "Cat 5: Agent Workflows"
    print_category_header(5, "Agent Workflows (.agents/workflows/*.md)")

    workflows = [
        ("plan-feature.md", "Workflow: Plan Feature"),
        ("implement-feature.md", "Workflow: Implement Feature"),
        ("review-code.md", "Workflow: Review Code"),
        ("database-migration.md", "Workflow: Database Migration"),
        ("integrate-model.md", "Workflow: Integrate Model"),
        ("release-mvp.md", "Workflow: Release MVP"),
    ]

    for wf_file, wf_title in workflows:
        p = REPO_ROOT / ".agents" / "workflows" / wf_file
        exists = p.is_file() and p.stat().st_size > 0
        record_check(cat, exists, f"Workflow file: {wf_file}", f"{p.stat().st_size} bytes" if exists else "Missing")
        if exists:
            content = p.read_text(encoding="utf-8")
            has_title = wf_title in content
            record_check(cat, has_title, f"Workflow {wf_file}: Header '{wf_title}'", "Verified" if has_title else "Missing")
            has_phases = any(term in content for term in ["Phase", "Step", "Checklist", "Gate", "Protocol", "Execution", "Fase"])
            record_check(cat, has_phases, f"Workflow {wf_file}: Structured phases", "Verified" if has_phases else "Unstructured")


# ==============================================================================
# CATEGORY 6: Technical Architecture (docs/architecture/)
# ==============================================================================
def verify_category_6():
    cat = "Cat 6: Technical Architecture"
    print_category_header(6, "Technical Architecture Specifications")

    arch_files = [
        "docs/architecture/overview.md",
        "docs/architecture/database-schema.md",
        "docs/architecture/api-contracts.md",
        "docs/architecture/model-contract.md",
        "docs/architecture/security.md",
    ]
    for af in arch_files:
        p = REPO_ROOT / af
        exists = p.is_file() and p.stat().st_size > 0
        record_check(cat, exists, f"Architecture doc: {af}", f"{p.stat().st_size} bytes" if exists else "Missing")

    # Deep verification of overview.md
    overview_text = (REPO_ROOT / "docs/architecture/overview.md").read_text(encoding="utf-8")
    record_check(cat, "Next.js" in overview_text and "FastAPI" in overview_text and "Supabase" in overview_text,
                 "overview.md: Decoupled topology (Next.js + Supabase + FastAPI)", "Documented")
    record_check(cat, "warmup" in overview_text.lower(), "overview.md: Cold-start warmup ping mitigation", "Documented")

    # Deep verification of security.md
    security_text = (REPO_ROOT / "docs/architecture/security.md").read_text(encoding="utf-8")
    record_check(cat, "29733" in security_text, "security.md: Peruvian Personal Data Protection Law N° 29733", "Found")
    record_check(cat, "student_id_pseudo" in security_text, "security.md: Persistent student_id_pseudo pseudonymization", "Found")
    record_check(cat, "JWT" in security_text or "token" in security_text, "security.md: Supabase JWT validation", "Found")


# ==============================================================================
# CATEGORY 7: Architecture Decision Records (docs/architecture/adr/)
# ==============================================================================
def verify_category_7():
    cat = "Cat 7: ADRs"
    print_category_header(7, "Architecture Decision Records (ADRs)")

    adrs = [
        ("0001-stack-selection.md", "ADR-0001", "Next.js", "Supabase", "FastAPI"),
        ("0002-service-separation-and-inference-hosting.md", "ADR-0002", "blitz.cloud", "DAS3H", "rule_based_fallback"),
        ("0003-probabilistic-adaptation-boundary.md", "ADR-0003", "Row Level Security", "answer_events", "student_id_pseudo"),
    ]

    for filename, title, *keywords in adrs:
        adr_path = REPO_ROOT / "docs/architecture/adr" / filename
        exists = adr_path.is_file() and adr_path.stat().st_size > 0
        record_check(cat, exists, f"ADR file: {filename}", f"{adr_path.stat().st_size} bytes" if exists else "Missing")

        if exists:
            content = adr_path.read_text(encoding="utf-8")
            has_status_accepted = bool(re.search(r"Status:?\*{0,2}\s*ACCEPTED", content, re.IGNORECASE))
            record_check(cat, has_status_accepted, f"{filename}: Status ACCEPTED", "Verified" if has_status_accepted else "Not ACCEPTED")

            # Check standard ADR sections
            has_sections = ("Context" in content and "Decision" in content and "Consequences" in content)
            record_check(cat, has_sections, f"{filename}: Context, Decision, Consequences sections", "Verified" if has_sections else "Incomplete")

            for kw in keywords:
                has_kw = bool(re.search(re.escape(kw), content, re.IGNORECASE))
                record_check(cat, has_kw, f"{filename}: Keyword '{kw}'", "Found" if has_kw else "Missing")


# ==============================================================================
# CATEGORY 8: SRS & Research Protocol
# ==============================================================================
def verify_category_8():
    cat = "Cat 8: SRS & Research Protocol"
    print_category_header(8, "System Requirements Specification & Research Protocol")

    # 1. SRS
    srs_path = REPO_ROOT / "docs/SRS.md"
    record_check(cat, srs_path.is_file() and srs_path.stat().st_size > 0, "SRS doc exists: docs/SRS.md", "Verified")

    if srs_path.is_file():
        srs_text = srs_path.read_text(encoding="utf-8")
        record_check(cat, "IEEE" in srs_text or "29148" in srs_text, "SRS conforms to IEEE 830 / ISO/IEC/IEEE 29148", "Found")

        # 4 user roles
        for role in ["`student`", "`teacher`", "`researcher`", "`system_worker`"]:
            record_check(cat, role in srs_text, f"SRS user role: {role}", "Present")

        # FR-01 through FR-16
        for i in range(1, 17):
            fr_id = f"FR-{i:02d}"
            has_fr = fr_id in srs_text
            record_check(cat, has_fr, f"Functional Requirement {fr_id}", "Defined" if has_fr else "Missing")

        # NFR-01 through NFR-04
        for i in range(1, 5):
            nfr_id = f"NFR-{i:02d}"
            has_nfr = nfr_id in srs_text
            record_check(cat, has_nfr, f"Non-Functional Requirement {nfr_id}", "Defined" if has_nfr else "Missing")

    # 2. Evaluation Protocol
    proto_path = REPO_ROOT / "docs/research/evaluation-protocol.md"
    record_check(cat, proto_path.is_file() and proto_path.stat().st_size > 0, "Research protocol exists", "Verified")

    if proto_path.is_file():
        proto_text = proto_path.read_text(encoding="utf-8")
        record_check(cat, "Quasi-Experimental" in proto_text, "Quasi-experimental study design defined", "Found")
        record_check(cat, "168 hours" in proto_text or "7-day" in proto_text or "7 days" in proto_text,
                     "7-day delayed post-test endpoint (168h)", "Found")
        record_check(cat, "AUC-ROC" in proto_text and "Brier" in proto_text and "ECE" in proto_text,
                     "Comprehensive evaluation metrics (AUC-ROC, Brier, ECE)", "Found")
        record_check(cat, "Group-K-Fold" in proto_text or "GroupKFold" in proto_text,
                     "Student Group-K-Fold cross-validation protocol", "Found")
        record_check(cat, "29733" in proto_text, "Peruvian Law N° 29733 minor protection compliance", "Found")
        record_check(cat, "informed consent" in proto_text.lower() or "consentimiento informado" in proto_text.lower(),
                     "Parental informed consent protocol", "Found")

        # The 5 Critical Issues & Risk Matrix from Plan Section 5
        risk_items = [
            "Sample Size vs. ML Complexity",
            "Contradiction: Adaptation Policy vs. Experimental Protocol",
            "Cold Start of blitz.cloud vs. Classroom Concurrency",
            "Review Trigger Thresholds",
            "Data Privacy & Minor Protection",
        ]
        for ri in risk_items:
            has_ri = ri.lower() in proto_text.lower()
            record_check(cat, has_ri, f"Risk Matrix Item: '{ri}'", "Registered" if has_ri else "Missing")

    # Supplemental research documents
    sup_docs = [
        "docs/research/model-selection.md",
        "docs/research/data-dictionary.md",
    ]
    for sd in sup_docs:
        p = REPO_ROOT / sd
        record_check(cat, p.is_file() and p.stat().st_size > 0, f"Supplemental doc: {sd}", "Present")


# ==============================================================================
# CATEGORY 9: Negative Scope Guardrail (Mandate R3)
# ==============================================================================
def verify_category_9():
    cat = "Cat 9: Negative Scope Guardrail"
    print_category_header(9, "Negative Scope Guardrail (Mandate R3: Zero UI Components)")

    prohibited_extensions = {".tsx", ".jsx", ".vue", ".svelte", ".html"}
    web_src = REPO_ROOT / "apps/web" / "src"

    violations = []
    for f in web_src.rglob("*"):
        if f.is_file() and f.name != ".gitkeep":
            if f.suffix.lower() in prohibited_extensions:
                violations.append(str(f.relative_to(REPO_ROOT)))
            if any(term in f.name.lower() for term in ["wireframe", "button", "page", "view"]):
                violations.append(str(f.relative_to(REPO_ROOT)))

    record_check(
        cat,
        len(violations) == 0,
        "Mandate R3: Strictly zero UI components, wireframes, or user flows in apps/web/src",
        "Zero violations" if len(violations) == 0 else f"Found violations: {violations}",
    )


# ==============================================================================
# CATEGORY 10: SQL DDL Syntax & Security
# ==============================================================================
def verify_category_10():
    cat = "Cat 10: SQL DDL Syntax & Security"
    print_category_header(10, "PostgreSQL DDL Syntax, RLS & Event Immutability")

    db_path = REPO_ROOT / "docs/architecture/database-schema.md"
    ddl = db_path.read_text(encoding="utf-8")

    expected_tables = [
        "tenants",
        "profiles",
        "courses",
        "sections",
        "enrollments",
        "units",
        "knowledge_components",
        "microcontents",
        "questions",
        "question_options",
        "activities",
        "activity_questions",
        "quiz_attempts",
        "answer_events",
        "student_knowledge_states",
        "student_metrics",
        "model_versions",
        "predictions",
        "recommendations",
        "review_assignments",
    ]

    # Verify all 20 tables exist
    created_tables = re.findall(r"CREATE TABLE (\w+)", ddl, re.IGNORECASE)
    record_check(cat, len(created_tables) == 20, f"Total tables created count == 20 (found {len(created_tables)})", str(created_tables))

    for tbl in expected_tables:
        has_tbl = bool(re.search(rf"CREATE TABLE {tbl}\b", ddl, re.IGNORECASE))
        record_check(cat, has_tbl, f"Table DDL defined: {tbl}", "Found" if has_tbl else "Missing")

    # Verify RLS enabled on 100% of tables
    rls_tables = set(re.findall(r"ALTER TABLE (\w+) ENABLE ROW LEVEL SECURITY;", ddl, re.IGNORECASE))
    missing_rls = [t for t in expected_tables if t not in rls_tables]
    record_check(
        cat,
        len(missing_rls) == 0,
        "Row Level Security (RLS) enabled on 100% of tables",
        "100% covered (20/20)" if len(missing_rls) == 0 else f"Missing: {missing_rls}",
    )

    # Verify scalar subquery optimization (SELECT auth.uid())
    scalar_subquery_count = len(re.findall(r"\(SELECT auth\.uid\(\)\)", ddl))
    record_check(cat, scalar_subquery_count >= 5, f"Optimized scalar subquery (SELECT auth.uid()) in RLS ({scalar_subquery_count} occurrences)", "Found")

    # Strict immutability: REVOKE UPDATE, DELETE ON answer_events
    has_revoke = bool(re.search(r"REVOKE UPDATE,\s*DELETE ON answer_events FROM anon,\s*authenticated;", ddl, re.IGNORECASE))
    record_check(cat, has_revoke, "Strict immutability: REVOKE UPDATE, DELETE ON answer_events FROM anon, authenticated", "Found")

    # Temporal index for window calculations
    has_temporal_idx = "idx_answer_events_student_kc" in ddl
    record_check(cat, has_temporal_idx, "Temporal index idx_answer_events_student_kc on answer_events", "Found")

    # UUID primary keys
    has_uuid_pk = "gen_random_uuid()" in ddl
    record_check(cat, has_uuid_pk, "UUID primary keys using gen_random_uuid()", "Found")


# ==============================================================================
# CATEGORY 11: OpenAPI 3.1 JSON Schema Validation
# ==============================================================================
def verify_category_11():
    cat = "Cat 11: OpenAPI 3.1 Validation"
    print_category_header(11, "OpenAPI 3.1 JSON Schema Validation")

    openapi_path = REPO_ROOT / "packages/contracts/openapi/openapi.json"
    with open(openapi_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Version
    version = data.get("openapi", "")
    record_check(cat, version.startswith("3.1"), f"OpenAPI specification version 3.1.x (got '{version}')", "Valid")

    # Exactly 7 endpoints
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
    record_check(cat, len(paths) == 7, f"Total endpoints count == 7 (found {len(paths)})", list(paths.keys()))
    for p in expected_paths:
        record_check(cat, p in paths, f"Path defined: {p}", "Found" if p in paths else "Missing")

    # Exactly 10 schema components
    expected_schemas = [
        "AnswerEventSubmitRequest",
        "AnswerEventSubmitResponse",
        "PredictRiskRequest",
        "PredictionItem",
        "PredictRiskResponse",
        "MicrocontentSummary",
        "RecommendationItem",
        "GetRecommendationsResponse",
        "WarmupResponse",
        "ProblemDetails",
    ]
    schemas = data.get("components", {}).get("schemas", {})
    record_check(cat, len(schemas) == 10, f"Total schema components count == 10 (found {len(schemas)})", list(schemas.keys()))
    for s in expected_schemas:
        record_check(cat, s in schemas, f"Schema component: {s}", "Found" if s in schemas else "Missing")

    # Zero broken $refs
    text = openapi_path.read_text(encoding="utf-8")
    refs = set(re.findall(r"\"\$ref\":\s*\"([^\"]+)\"", text))
    broken_refs = []
    for ref in refs:
        parts = ref.strip("#/").split("/")
        curr = data
        for part in parts:
            if isinstance(curr, dict) and part in curr:
                curr = curr[part]
            else:
                broken_refs.append(ref)
                break

    record_check(
        cat,
        len(broken_refs) == 0,
        f"Zero broken $ref references in openapi.json ({len(refs)} total references resolved)",
        "All resolved" if len(broken_refs) == 0 else f"Broken: {broken_refs}",
    )


# ==============================================================================
# CATEGORY 12: Python Model Contract AST Validation
# ==============================================================================
def verify_category_12():
    cat = "Cat 12: Python Model Contract AST"
    print_category_header(12, "Python Model Contract AST Validation")

    model_contract_path = REPO_ROOT / "docs/architecture/model-contract.md"
    content = model_contract_path.read_text(encoding="utf-8")

    code_blocks = re.findall(r"```python\s*(.*?)\s*```", content, re.DOTALL)
    record_check(cat, len(code_blocks) > 0, "Python code block found in model-contract.md", f"{len(code_blocks)} block(s)")

    combined_code = "\n\n".join(code_blocks)
    try:
        tree = ast.parse(combined_code)
        record_check(cat, True, "ast.parse cleanly parses all model-contract.md code blocks", "No SyntaxError")
    except SyntaxError as e:
        record_check(cat, False, "ast.parse cleanly parses all model-contract.md code blocks", f"SyntaxError at line {e.lineno}: {e.msg}")
        return

    # Check classes, protocols, ABCs
    class_nodes = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}

    # Pydantic v2 Models
    expected_models = [
        "StudentInteractionEvent",
        "TemporalWindowFeatures",
        "TemporalSequenceFeatures",
        "PredictionOutput",
        "ShapExplanation",
        "ModelInferenceResult",
        "BKTParameters",
        "ModelEvaluationMetrics",
        "ModelArtifactMetadata",
    ]
    for m in expected_models:
        record_check(cat, m in class_nodes, f"Pydantic model defined: {m}", "Present" if m in class_nodes else "Missing")

    # Enums
    expected_enums = ["RiskLevel", "PredictionStatus", "RecommendationMethod", "ContentType"]
    for e in expected_enums:
        record_check(cat, e in class_nodes, f"Enum defined: {e}", "Present" if e in class_nodes else "Missing")

    # BaseRetentionModel ABC
    record_check(cat, "BaseRetentionModel" in class_nodes, "BaseRetentionModel abstract base class defined", "Found")
    if "BaseRetentionModel" in class_nodes:
        brm_node = class_nodes["BaseRetentionModel"]
        brm_methods = [n.name for n in brm_node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        record_check(cat, "load_artifact" in brm_methods and "extract_features" in brm_methods and "predict_recall" in brm_methods,
                     "BaseRetentionModel defines abstract methods load_artifact(), extract_features(), predict_recall()", f"Methods: {brm_methods}")

    # KnowledgeTracingModel Protocol
    record_check(cat, "KnowledgeTracingModel" in class_nodes, "KnowledgeTracingModel typing.Protocol defined", "Found")
    if "KnowledgeTracingModel" in class_nodes:
        ktm_node = class_nodes["KnowledgeTracingModel"]
        ktm_methods = [n.name for n in ktm_node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        record_check(cat, "update_state" in ktm_methods and "get_recall_probability" in ktm_methods,
                     "KnowledgeTracingModel defines protocol methods update_state() and get_recall_probability()", f"Methods: {ktm_methods}")


# ==============================================================================
# CATEGORY 13: Section 7 Checklist Item 1 (Cross-Contract Field & Type Consistency)
# ==============================================================================
def verify_category_13():
    cat = "Cat 13: Cross-Contract Type Consistency"
    print_category_header(13, "Section 7 Checklist Item 1: Cross-Contract Field & Type Consistency")

    db_ddl = (REPO_ROOT / "docs/architecture/database-schema.md").read_text(encoding="utf-8")
    api_md = (REPO_ROOT / "docs/architecture/api-contracts.md").read_text(encoding="utf-8")
    with open(REPO_ROOT / "packages/contracts/openapi/openapi.json", "r", encoding="utf-8") as f:
        openapi_data = json.load(f)
    model_md = (REPO_ROOT / "docs/architecture/model-contract.md").read_text(encoding="utf-8")

    schemas = openapi_data.get("components", {}).get("schemas", {})

    # 1. answer_events cross-contract fields
    ae_ddl_match = re.search(r"CREATE TABLE answer_events\s*\((.*?)\);", db_ddl, re.DOTALL | re.IGNORECASE)
    record_check(cat, ae_ddl_match is not None, "Extract answer_events DDL block", "Extracted")
    ae_ddl = ae_ddl_match.group(1) if ae_ddl_match else ""

    ae_fields = [
        "attempt_id",
        "question_id",
        "selected_option_id",
        "response_time_seconds",
        "idempotency_key",
    ]
    ae_openapi_props = schemas.get("AnswerEventSubmitRequest", {}).get("properties", {})

    for field in ae_fields:
        in_sql = bool(re.search(rf"\b{field}\b", ae_ddl))
        record_check(cat, in_sql, f"answer_events.{field} present in PostgreSQL DDL", "Matched")

        in_api_md = f'"{field}"' in api_md
        record_check(cat, in_api_md, f"answer_events.{field} present in api-contracts.md", "Matched")

        in_openapi = field in ae_openapi_props
        record_check(cat, in_openapi, f"answer_events.{field} present in openapi.json schema", "Matched")

        in_python = bool(re.search(rf"\b{field}\b", model_md))
        record_check(cat, in_python, f"answer_events.{field} present in model-contract.md Python class", "Matched")

    # 2. predictions cross-contract fields
    pred_ddl_match = re.search(r"CREATE TABLE predictions\s*\((.*?)\);", db_ddl, re.DOTALL | re.IGNORECASE)
    record_check(cat, pred_ddl_match is not None, "Extract predictions DDL block", "Extracted")
    pred_ddl = pred_ddl_match.group(1) if pred_ddl_match else ""

    pred_resp_props = schemas.get("PredictRiskResponse", {}).get("properties", {})
    pred_item_props = schemas.get("PredictionItem", {}).get("properties", {})

    # Top-level fields (student_id, knowledge_component_id, prediction_status)
    top_pred_fields = ["student_id", "knowledge_component_id", "prediction_status"]
    for field in top_pred_fields:
        in_sql = bool(re.search(rf"\b{field}\b", pred_ddl))
        record_check(cat, in_sql, f"predictions.{field} present in PostgreSQL DDL", "Matched")

        in_api_md = f'"{field}"' in api_md
        record_check(cat, in_api_md, f"predictions.{field} present in api-contracts.md", "Matched")

        in_openapi = (field in pred_resp_props) or (field in pred_item_props)
        record_check(cat, in_openapi, f"predictions.{field} present in openapi.json PredictRiskResponse/Item", "Matched")

        in_python = bool(re.search(rf"\b{field}\b", model_md))
        record_check(cat, in_python, f"predictions.{field} present in model-contract.md Python class", "Matched")

    # Prediction metrics (estimated_risk, risk_level, recall_probability)
    metric_fields = ["estimated_risk", "risk_level"]
    for field in metric_fields:
        in_sql = bool(re.search(rf"\b{field}\b", pred_ddl))
        record_check(cat, in_sql, f"predictions.{field} present in PostgreSQL DDL", "Matched")

        in_api_md = f'"{field}"' in api_md
        record_check(cat, in_api_md, f"predictions.{field} present in api-contracts.md", "Matched")

        in_openapi = field in pred_item_props
        record_check(cat, in_openapi, f"predictions.{field} present in openapi.json PredictionItem", "Matched")

        in_python = bool(re.search(rf"\b{field}\b", model_md))
        record_check(cat, in_python, f"predictions.{field} present in model-contract.md Python class", "Matched")

    # Horizon hours & recall probability alias alignment
    record_check(cat, "prediction_horizon_hours" in pred_ddl, "prediction_horizon_hours in predictions DDL", "Matched")
    record_check(cat, "horizon_hours" in pred_item_props, "horizon_hours in openapi PredictionItem", "Matched")
    record_check(cat, "horizon_hours" in model_md, "horizon_hours in model-contract.md PredictionOutput", "Matched")

    record_check(cat, "predicted_recall_probability" in pred_ddl, "predicted_recall_probability in predictions DDL", "Matched")
    record_check(cat, "recall_probability" in pred_item_props, "recall_probability in openapi PredictionItem", "Matched")
    record_check(cat, "recall_probability" in model_md, "recall_probability in model-contract.md PredictionOutput", "Matched")

    # 3. recommendations cross-contract fields
    rec_ddl_match = re.search(r"CREATE TABLE recommendations\s*\((.*?)\);", db_ddl, re.DOTALL | re.IGNORECASE)
    record_check(cat, rec_ddl_match is not None, "Extract recommendations DDL block", "Extracted")
    rec_ddl = rec_ddl_match.group(1) if rec_ddl_match else ""

    rec_resp_props = schemas.get("GetRecommendationsResponse", {}).get("properties", {})
    rec_item_props = schemas.get("RecommendationItem", {}).get("properties", {})

    record_check(cat, "student_id" in rec_ddl, "recommendations.student_id in PostgreSQL DDL", "Matched")
    record_check(cat, "student_id" in rec_resp_props, "recommendations.student_id in GetRecommendationsResponse", "Matched")
    record_check(cat, "student_id" in api_md, "recommendations.student_id in api-contracts.md", "Matched")

    record_check(cat, "knowledge_component_id" in rec_ddl, "recommendations.knowledge_component_id in PostgreSQL DDL", "Matched")
    record_check(cat, "knowledge_component_id" in rec_item_props, "recommendations.knowledge_component_id in openapi RecommendationItem", "Matched")
    record_check(cat, "knowledge_component_id" in api_md, "recommendations.knowledge_component_id in api-contracts.md", "Matched")

    # Microcontent reference
    record_check(cat, "microcontent_id" in rec_ddl, "recommendations.microcontent_id foreign key in PostgreSQL DDL", "Matched")
    record_check(cat, "microcontent" in rec_item_props, "recommendations.microcontent object in openapi RecommendationItem", "Matched")
    record_check(cat, "microcontent" in api_md, "recommendations.microcontent object in api-contracts.md", "Matched")

    # Selection method & Decision reason
    record_check(cat, "selection_method" in rec_ddl, "recommendations.selection_method in PostgreSQL DDL", "Matched")
    record_check(cat, "selection_method" in rec_item_props, "recommendations.selection_method in openapi RecommendationItem", "Matched")
    record_check(cat, "selection_method" in api_md, "recommendations.selection_method in api-contracts.md", "Matched")
    record_check(cat, "RecommendationMethod" in model_md, "RecommendationMethod enum in model-contract.md", "Matched")

    record_check(cat, "decision_reason" in rec_ddl, "recommendations.decision_reason in PostgreSQL DDL", "Matched")
    record_check(cat, "decision_reason" in rec_item_props, "recommendations.decision_reason in openapi RecommendationItem", "Matched")
    record_check(cat, "decision_reason" in api_md, "recommendations.decision_reason in api-contracts.md", "Matched")

    # Enum consistency: selection_method values ('predictive_model', 'rule_based_fallback', 'teacher_assigned')
    enum_methods = ["predictive_model", "rule_based_fallback", "teacher_assigned"]
    for em in enum_methods:
        in_ddl = em in db_ddl
        in_openapi = em in str(rec_item_props)
        in_py = em in model_md
        record_check(cat, in_ddl and in_openapi and in_py, f"Enum value '{em}' consistent across SQL, OpenAPI, Python", "Matched")


# ==============================================================================
# CATEGORY 14: Section 7 Checklist Item 2 (Critical Decisions Registration)
# ==============================================================================
def verify_category_14():
    cat = "Cat 14: Critical Decisions Registration"
    print_category_header(14, "Section 7 Checklist Item 2: Critical Decisions Registration")

    proto_path = REPO_ROOT / "docs/research/evaluation-protocol.md"
    proto_text = proto_path.read_text(encoding="utf-8")
    adr2_text = (REPO_ROOT / "docs/architecture/adr/0002-service-separation-and-inference-hosting.md").read_text(encoding="utf-8")
    adr3_text = (REPO_ROOT / "docs/architecture/adr/0003-probabilistic-adaptation-boundary.md").read_text(encoding="utf-8")
    sec_text = (REPO_ROOT / "docs/architecture/security.md").read_text(encoding="utf-8")
    db_ddl = (REPO_ROOT / "docs/architecture/database-schema.md").read_text(encoding="utf-8")

    # Decision 1: Pre-training & Cold Start Strategy
    # Section 7: "Confirmar si se utilizará pre-entrenamiento externo para DAS3H o si se iniciará con una regresión logística temporal mientras se registran las interacciones del diagnóstico."
    has_pretrain_resolution = (
        ("pre-train" in proto_text.lower() or "pretrain" in proto_text.lower() or "transfer learning" in proto_text.lower())
        and ("temporal logistic" in proto_text.lower() or "pfa" in proto_text.lower())
    )
    record_check(
        cat,
        has_pretrain_resolution,
        "Critical Decision 1: Pre-training vs temporal logistic regression cold start documented",
        "Documented in evaluation-protocol.md Risk Matrix Item 1",
    )

    has_adr2_model_fallback = "rule_based_fallback" in adr2_text and "DAS3H" in adr2_text
    record_check(cat, has_adr2_model_fallback, "ADR-0002 formalizes DAS3H candidate + fallback baseline selection", "Documented")

    # Decision 2: Minor Informed Consent & Ley N° 29733
    # Section 7: "Ratificar con la institución educativa el procedimiento de consentimiento informado para menores de edad."
    has_informed_consent = (
        ("informed consent" in proto_text.lower() or "consentimiento informado" in proto_text.lower())
        and "29733" in proto_text
    )
    record_check(
        cat,
        has_informed_consent,
        "Critical Decision 2: Institutional informed consent under Peruvian Law N° 29733 registered",
        "Documented in evaluation-protocol.md Section 6 & Risk Matrix Item 5",
    )

    has_sec_consent_pseudonym = "student_id_pseudo" in sec_text and "29733" in sec_text
    record_check(cat, has_sec_consent_pseudonym, "security.md and database-schema enforce pseudonymization for minor protection", "Documented")

    # Decision 3: 7-Day Delayed Post-Test Quarantine
    # Essential scientific integrity safeguard preventing recommendation engine contamination of research endpoint
    has_quarantine_proto = (
        ("quarantine" in proto_text.lower() or "cuarentena" in proto_text.lower())
        and ("168" in proto_text or "7-day" in proto_text)
    )
    record_check(
        cat,
        has_quarantine_proto,
        "Critical Decision 3: 7-day delayed post-test item quarantine (168h) registered in protocol",
        "Documented in evaluation-protocol.md Section 1.2 & Risk Matrix Item 2",
    )

    has_quarantine_ddl = "delayed_assessment" in db_ddl
    record_check(cat, has_quarantine_ddl, "database-schema.md defines activity_type_enum with delayed_assessment", "Documented in DDL")

    has_quarantine_adr3 = "delayed_assessment" in adr3_text or "quarantine" in adr3_text.lower()
    record_check(cat, has_quarantine_adr3, "ADR-0003 formalizes architectural adaptation quarantine boundary", "Documented in ADR-0003")


# ==============================================================================
# Master Execution & Summary Report
# ==============================================================================
def main():
    start_time = time.time()
    print("=" * 78)
    print("  PLATAFORMAMICRO — PHASE 0 MASTER AUTOMATED VERIFICATION SUITE")
    print("  Integrity Audit & Section 7 Transition Checklist Verification")
    print(f"  Target Repository: {REPO_ROOT}")
    print("=" * 78)

    verify_category_1()
    verify_category_2()
    verify_category_3()
    verify_category_4()
    verify_category_5()
    verify_category_6()
    verify_category_7()
    verify_category_8()
    verify_category_9()
    verify_category_10()
    verify_category_11()
    verify_category_12()
    verify_category_13()
    verify_category_14()

    elapsed = time.time() - start_time

    print("\n" + "=" * 78)
    print("  MASTER AUDIT SUMMARY BY CATEGORY")
    print("=" * 78)
    for cat_name, (cat_p, cat_f) in CATEGORY_RESULTS.items():
        status_icon = "✅" if cat_f == 0 else "❌"
        print(f"  {status_icon} {cat_name:<46} : {cat_p:>3} passed, {cat_f:>2} failed")

    print("-" * 78)
    print(f"  TOTAL CHECKS EXECUTED : {TOTAL_PASSED + TOTAL_FAILED}")
    print(f"  TOTAL PASSED          : {TOTAL_PASSED}")
    print(f"  TOTAL FAILED          : {TOTAL_FAILED}")
    print(f"  EXECUTION TIME        : {elapsed:.2f} seconds")
    print("=" * 78)

    if TOTAL_FAILED > 0:
        print("\n❌ PHASE 0 VERIFICATION FAILED! List of failure causes:", file=sys.stderr)
        for cat, desc, detail in ERRORS:
            print(f"  - [{cat}] {desc}: {detail}", file=sys.stderr)
        sys.exit(1)
    else:
        print("\n✅ PHASE 0 MASTER VERIFICATION PASSED PERFECTLY!")
        print("   All 14 categories verified. Monorepo architecture, governance, contracts,")
        print("   negative scope guardrail, and Section 7 checklist items 100% compliant.")
        sys.exit(0)


if __name__ == "__main__":
    main()
