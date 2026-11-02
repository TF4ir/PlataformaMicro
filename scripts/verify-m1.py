#!/usr/bin/env python3
"""
Verification Script for Milestone 1: Monorepo Structure & Agent Governance.
Verifies:
1. Presence of all required files and directories across monorepo subsystems.
2. Syntax validity of JSON and TOML configuration files.
3. Python AST validation / compilation of all Python files.
4. Strict absence of visual UI components / wireframes in apps/web/.
5. Frontmatter triggers on all 6 rule files (trigger: always_on).
6. Layout compliance in .agents/teamwork/ (metadata only).
"""

import ast
import json
import os
import sys
import tomllib
from pathlib import Path

ROOT = Path("/root/PlataformaMicro")
ERRORS = []
PASSED_CHECKS = 0

def check(condition: bool, description: str, fail_msg: str):
    global PASSED_CHECKS
    if condition:
        print(f"[PASS] {description}")
        PASSED_CHECKS += 1
    else:
        print(f"[FAIL] {description} -> {fail_msg}")
        ERRORS.append(f"{description}: {fail_msg}")

print("=" * 70)
print("PLATAFORMAMICRO MILESTONE 1 VERIFICATION AUDIT")
print("=" * 70)

# 1. ROOT FILES
print("\n--- 1. Root Files & Configurations ---")
required_root_files = [
    "AGENTS.md",
    "README.md",
    "CONTRIBUTING.md",
    "docker-compose.yml",
    ".env.example",
    ".gitignore",
    "PROJECT.md",
]
for rf in required_root_files:
    p = ROOT / rf
    check(p.is_file(), f"Root file: {rf}", "File does not exist")

# 2. GOVERNANCE: RULES
print("\n--- 2. Agent Governance Rules (.agents/rules/) ---")
required_rules = [
    "architecture.md",
    "frontend.md",
    "backend.md",
    "database.md",
    "machine-learning.md",
    "research-integrity.md",
]
for rule in required_rules:
    p = ROOT / ".agents" / "rules" / rule
    check(p.is_file(), f"Rule file: {rule}", "File does not exist")
    if p.is_file():
        content = p.read_text(encoding="utf-8")
        check("trigger: always_on" in content, f"Rule {rule} trigger: always_on", "Missing trigger: always_on in frontmatter")

# 3. GOVERNANCE: SKILLS
print("\n--- 3. Agent Skills Library (.agents/skills/) ---")
expected_skills = [
    "fastapi-templates",
    "supabase",
    "supabase-postgres-best-practices",
    "improve-animations",
    "eda-pipeline",
    "feature-engineering",
    "model-training",
    "model-evaluation",
    "architecture-design",
    "frontend-development",
    "supabase-database",
    "fastapi-development",
    "predictive-modeling",
    "adaptive-learning",
    "ux-usability",
    "testing-security",
]
for skill in expected_skills:
    p = ROOT / ".agents" / "skills" / skill / "SKILL.md"
    check(p.is_file(), f"Skill SKILL.md: {skill}", "SKILL.md does not exist")

# 4. GOVERNANCE: WORKFLOWS
print("\n--- 4. Agent Workflows (.agents/workflows/) ---")
expected_workflows = [
    "plan-feature.md",
    "implement-feature.md",
    "review-code.md",
    "database-migration.md",
    "integrate-model.md",
    "release-mvp.md",
]
for wf in expected_workflows:
    p = ROOT / ".agents" / "workflows" / wf
    check(p.is_file(), f"Workflow file: {wf}", "Workflow file does not exist")

# 5. SUBSYSTEM: APPS/WEB
print("\n--- 5. Subsystem Scaffolding: apps/web/ ---")
web_files = [
    "apps/web/AGENTS.md",
    "apps/web/package.json",
    "apps/web/tsconfig.json",
    "apps/web/tailwind.config.ts",
]
for wf in web_files:
    p = ROOT / wf
    check(p.is_file(), f"Web config: {wf}", "File does not exist")

web_dirs = [
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
for wd in web_dirs:
    p = ROOT / wd
    check(p.is_dir(), f"Web dir: {wd}", "Directory does not exist")
    gitkeep = p / ".gitkeep"
    check(gitkeep.is_file(), f"Web dir placeholder: {wd}/.gitkeep", ".gitkeep missing")

# 6. NEGATIVE GUARDRAIL: ZERO UI COMPONENTS IN APPS/WEB
print("\n--- 6. Negative Guardrail: Zero UI Components / Wireframes ---")
prohibited_ext = {".tsx", ".jsx", ".vue", ".svelte", ".html"}
violations = []
web_src = ROOT / "apps/web" / "src"
for f in web_src.rglob("*"):
    if f.is_file() and f.name != ".gitkeep":
        if f.suffix.lower() in prohibited_ext:
            violations.append(str(f.relative_to(ROOT)))
        if "wireframe" in f.name.lower() or "button" in f.name.lower() or "page" in f.name.lower():
            violations.append(str(f.relative_to(ROOT)))

check(len(violations) == 0, "Zero UI components/wireframes in apps/web/src", f"Found prohibited files: {violations}")

# 7. SUBSYSTEM: ML/
print("\n--- 7. Subsystem Scaffolding: ml/ ---")
ml_files = [
    "ml/AGENTS.md",
    "ml/datasets/README.md",
    "ml/artifacts/README.md",
    "ml/src/__init__.py",
    "ml/src/preprocessing/__init__.py",
    "ml/src/features/__init__.py",
    "ml/src/baselines/__init__.py",
    "ml/src/das3h/__init__.py",
    "ml/src/evaluation/__init__.py",
    "ml/src/training/__init__.py",
    "ml/tests/__init__.py",
]
for mf in ml_files:
    p = ROOT / mf
    check(p.is_file(), f"ML file: {mf}", "File does not exist")

# 8. SUBSYSTEM: PACKAGES/CONTRACTS/
print("\n--- 8. Subsystem Scaffolding: packages/contracts/ ---")
contracts_files = [
    "packages/contracts/typescript/package.json",
    "packages/contracts/openapi/openapi.json",
]
for cf in contracts_files:
    p = ROOT / cf
    check(p.is_file(), f"Contract file: {cf}", "File does not exist")

# 9. SUBSYSTEM: SERVICES/ML-API/
print("\n--- 9. Subsystem Scaffolding: services/ml-api/ ---")
api_files = [
    "services/ml-api/AGENTS.md",
    "services/ml-api/Dockerfile",
    "services/ml-api/pyproject.toml",
    "services/ml-api/README.md",
    "services/ml-api/app/__init__.py",
    "services/ml-api/app/main.py",
    "services/ml-api/app/core/__init__.py",
    "services/ml-api/app/api/__init__.py",
    "services/ml-api/app/api/v1/__init__.py",
    "services/ml-api/app/schemas/__init__.py",
    "services/ml-api/app/services/__init__.py",
    "services/ml-api/app/repositories/__init__.py",
    "services/ml-api/app/prediction/__init__.py",
    "services/ml-api/app/adaptation/__init__.py",
    "services/ml-api/tests/__init__.py",
    "services/ml-api/tests/test_health.py",
]
for af in api_files:
    p = ROOT / af
    check(p.is_file(), f"API file: {af}", "File does not exist")

# 10. SUBSYSTEM: SUPABASE/ & DOCS/
print("\n--- 10. Subsystem Scaffolding: supabase/ & docs/ ---")
supabase_files = [
    "supabase/AGENTS.md",
    "supabase/config.toml",
    "supabase/seed.sql",
    "supabase/migrations/.gitkeep",
    "supabase/tests/.gitkeep",
]
for sf in supabase_files:
    p = ROOT / sf
    check(p.is_file(), f"Supabase file: {sf}", "File does not exist")

docs_dirs = [
    "docs/architecture/adr",
    "docs/research",
    "docs/ux",
]
for dd in docs_dirs:
    p = ROOT / dd
    check(p.is_dir(), f"Docs dir: {dd}", "Directory does not exist")
    check((p / ".gitkeep").is_file(), f"Docs dir .gitkeep: {dd}", ".gitkeep missing")

# 11. SYNTAX PARSING: JSON & TOML
print("\n--- 11. Syntax Parsing Validation (JSON & TOML) ---")
json_targets = [
    ROOT / "apps/web/package.json",
    ROOT / "packages/contracts/typescript/package.json",
    ROOT / "packages/contracts/openapi/openapi.json",
]
for jt in json_targets:
    try:
        with open(jt, "rb") as f:
            data = json.load(f)
        check(True, f"JSON Syntax: {jt.relative_to(ROOT)}", "")
    except Exception as e:
        check(False, f"JSON Syntax: {jt.relative_to(ROOT)}", str(e))

toml_targets = [
    ROOT / "services/ml-api/pyproject.toml",
    ROOT / "supabase/config.toml",
]
for tt in toml_targets:
    try:
        with open(tt, "rb") as f:
            data = tomllib.load(f)
        check(True, f"TOML Syntax: {tt.relative_to(ROOT)}", "")
    except Exception as e:
        check(False, f"TOML Syntax: {tt.relative_to(ROOT)}", str(e))

# 12. PYTHON AST SYNTAX VALIDATION
print("\n--- 12. Python AST Syntax Validation ---")
py_targets = list(ROOT.glob("services/ml-api/**/*.py")) + list(ROOT.glob("ml/**/*.py"))
for py_file in py_targets:
    try:
        source = py_file.read_text(encoding="utf-8")
        ast.parse(source, filename=str(py_file))
        check(True, f"Python AST: {py_file.relative_to(ROOT)}", "")
    except Exception as e:
        check(False, f"Python AST: {py_file.relative_to(ROOT)}", str(e))

# 13. LAYOUT COMPLIANCE (.agents/teamwork/)
print("\n--- 13. Layout Compliance Guardrail (.agents/teamwork/) ---")
teamwork_dir = ROOT / ".agents" / "teamwork"
disallowed_teamwork_ext = {".py", ".ts", ".tsx", ".js", ".jsx", ".sql", ".toml", ".lock", ".tar", ".gz"}
teamwork_violations = []
for f in teamwork_dir.rglob("*"):
    # Allow scripts in verification or markdown
    if f.is_file() and f.suffix.lower() in disallowed_teamwork_ext:
        teamwork_violations.append(str(f.relative_to(ROOT)))

check(len(teamwork_violations) == 0, ".agents/teamwork/ layout compliance", f"Disallowed files found: {teamwork_violations}")

print("\n" + "=" * 70)
print(f"AUDIT SUMMARY: {PASSED_CHECKS} CHECKS PASSED, {len(ERRORS)} ERRORS")
print("=" * 70)

if ERRORS:
    print("\nFAILED CHECKS:")
    for err in ERRORS:
        print(f"  - {err}")
    sys.exit(1)
else:
    print("\nALL CHECKS PASSED PERFECTLY (EXIT 0).")
    sys.exit(0)
