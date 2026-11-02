#!/usr/bin/env python3
"""
Verification Script for Milestone 3: ADRs, SRS & Research Evaluation Protocol
Plataforma de Microaprendizaje Adaptativo (5to Secundaria)

Validates:
1. Presence and structural completeness of all 3 ADR files in docs/architecture/adr/:
   - 0001-stack-selection.md
   - 0002-service-separation-and-inference-hosting.md
   - 0003-probabilistic-adaptation-boundary.md
2. Presence and completeness of docs/SRS.md:
   - Structured per IEEE 830 / ISO/IEC/IEEE 29148.
   - User roles: student, teacher, researcher, system_worker.
   - All 16 Functional Requirements (FR-01 through FR-16).
   - All 4 Non-Functional Requirements (NFR-01 through NFR-04).
3. Presence and completeness of docs/research/evaluation-protocol.md:
   - Quasi-experimental design (control vs experimental) on 7-day post-test (h = 168 hours).
   - Metrics: Discrimination (AUC-ROC, F1, Recall, Precision), Calibration (Brier Score, ECE).
   - Student-stratified Group-K-Fold (K=5) and temporal cutoff filtering (event_timestamp < t).
   - Baseline models: PFA/Temporal Logistic, BKT, CatBoost, DAS3H.
   - The 5 Critical Issues & Risk Matrix from Section 5 of the Master Plan.
   - Peruvian Law N° 29733, parental informed consent, empathetic feedback standards.
4. Presence of supplemental research documents:
   - docs/research/model-selection.md
   - docs/research/data-dictionary.md
5. Zero regressions in M1 and M2 (scripts/verify-m1.py and scripts/verify-m2.py exit 0).
"""

import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path("/root/PlataformaMicro")

passed_tests = 0
failed_tests = 0


def report_assert(condition: bool, test_name: str, detail: str = ""):
    global passed_tests, failed_tests
    if condition:
        passed_tests += 1
        print(f"  [PASS] {test_name}" + (f": {detail}" if detail else ""))
    else:
        failed_tests += 1
        print(f"  [FAIL] {test_name}" + (f": {detail}" if detail else ""))


def check_file_contains(filepath: Path, regex_pattern: str, description: str):
    if not filepath.exists():
        report_assert(False, description, f"File {filepath} does not exist")
        return False
    content = filepath.read_text(encoding="utf-8")
    match = re.search(regex_pattern, content, re.IGNORECASE | re.MULTILINE)
    report_assert(bool(match), description, f"Pattern '{regex_pattern}' found in {filepath.name}")
    return bool(match)


def main():
    global passed_tests, failed_tests
    print("=" * 70)
    print("PLATAFORMAMICRO MILESTONE 3 VERIFICATION AUDIT")
    print("=" * 70)

    # ---------------------------------------------------------
    # 1. Architecture Decision Records (docs/architecture/adr/)
    # ---------------------------------------------------------
    print("\n--- 1. Architecture Decision Records (docs/architecture/adr/) ---")
    adr1 = REPO_ROOT / "docs/architecture/adr/0001-stack-selection.md"
    adr2 = REPO_ROOT / "docs/architecture/adr/0002-service-separation-and-inference-hosting.md"
    adr3 = REPO_ROOT / "docs/architecture/adr/0003-probabilistic-adaptation-boundary.md"

    report_assert(adr1.exists(), "ADR-0001 file exists", str(adr1))
    report_assert(adr2.exists(), "ADR-0002 file exists", str(adr2))
    report_assert(adr3.exists(), "ADR-0003 file exists", str(adr3))

    if adr1.exists():
        check_file_contains(adr1, r"ADR-0001", "ADR-0001 Title present")
        check_file_contains(adr1, r"Status:?\*{0,2}\s*ACCEPTED", "ADR-0001 Status ACCEPTED")
        check_file_contains(adr1, r"Next\.js", "ADR-0001 Next.js technology")
        check_file_contains(adr1, r"Supabase", "ADR-0001 Supabase persistence")
        check_file_contains(adr1, r"FastAPI", "ADR-0001 FastAPI microservice")
        check_file_contains(adr1, r"packages/contracts", "ADR-0001 Shared contracts boundary")
        check_file_contains(adr1, r"Context", "ADR-0001 Context section")
        check_file_contains(adr1, r"Decision", "ADR-0001 Decision section")
        check_file_contains(adr1, r"Consequences", "ADR-0001 Consequences section")

    if adr2.exists():
        check_file_contains(adr2, r"ADR-0002", "ADR-0002 Title present")
        check_file_contains(adr2, r"Status:?\*{0,2}\s*ACCEPTED", "ADR-0002 Status ACCEPTED")
        check_file_contains(adr2, r"blitz\.cloud", "ADR-0002 blitz.cloud hosting context")
        check_file_contains(adr2, r"cold-start|cold\s*start", "ADR-0002 Cold-start mitigation")
        check_file_contains(adr2, r"/health/warmup", "ADR-0002 Warmup ping endpoint")
        check_file_contains(adr2, r"rule_based_fallback", "ADR-0002 Deterministic rule-based fallback")
        check_file_contains(adr2, r"DAS3H", "ADR-0002 DAS3H candidate model")
        check_file_contains(adr2, r"BKT", "ADR-0002 BKT baseline model")
        check_file_contains(adr2, r"PFA|Logistic", "ADR-0002 PFA/Logistic baseline model")
        check_file_contains(adr2, r"metadata\.json", "ADR-0002 Model artifact metadata.json versioning")

    if adr3.exists():
        check_file_contains(adr3, r"ADR-0003", "ADR-0003 Title present")
        check_file_contains(adr3, r"Status:?\*{0,2}\s*ACCEPTED", "ADR-0003 Status ACCEPTED")
        check_file_contains(adr3, r"Row\s*Level\s*Security|RLS", "ADR-0003 Native RLS multi-tenancy")
        check_file_contains(adr3, r"answer_events", "ADR-0003 Immutable answer_events store")
        check_file_contains(adr3, r"PredictionEngine|Prediction\s*Engine", "ADR-0003 PredictionEngine specification")
        check_file_contains(adr3, r"AdaptationPolicy|Adaptation\s*Policy", "ADR-0003 AdaptationPolicy pedagogical decoupling")
        check_file_contains(adr3, r"student_id_pseudo", "ADR-0003 Persistent student_id_pseudo")
        check_file_contains(adr3, r"29733", "ADR-0003 Peruvian Law N° 29733")
        check_file_contains(adr3, r"quarantine|delayed_assessment", "ADR-0003 Delayed assessment item quarantine")

    # ---------------------------------------------------------
    # 2. System Requirements Specification (docs/SRS.md)
    # ---------------------------------------------------------
    print("\n--- 2. System Requirements Specification (docs/SRS.md) ---")
    srs = REPO_ROOT / "docs/SRS.md"
    report_assert(srs.exists(), "docs/SRS.md file exists", str(srs))

    if srs.exists():
        # IEEE Standard check
        check_file_contains(srs, r"IEEE\s*830|ISO/IEC/IEEE\s*29148", "SRS IEEE 830 / ISO 29148 structure")
        check_file_contains(srs, r"1\.\s*Introduction", "SRS Section 1: Introduction")
        check_file_contains(srs, r"2\.\s*Overall Description", "SRS Section 2: Overall Description")
        check_file_contains(srs, r"3\.\s*Specific Requirements", "SRS Section 3: Specific Requirements")

        # User roles check
        check_file_contains(srs, r"`student`", "SRS User Role: student")
        check_file_contains(srs, r"`teacher`", "SRS User Role: teacher")
        check_file_contains(srs, r"`researcher`", "SRS User Role: researcher")
        check_file_contains(srs, r"`system_worker`", "SRS User Role: system_worker")

        # Functional Requirements FR-01 through FR-16
        fr_list = [
            ("FR-01", r"FR-01.*Authentication", "FR-01: Authentication & Profile Management"),
            ("FR-02", r"FR-02.*Course.*Section", "FR-02: Course & Section Hierarchical Structure"),
            ("FR-03", r"FR-03.*Enrollment.*Pseudonymization", "FR-03: Student Enrollment & Pseudonymization"),
            ("FR-04", r"FR-04.*Microcontent", "FR-04: Microcontent Management"),
            ("FR-05", r"FR-05.*Question Bank.*Calibration", "FR-05: Question Bank & Calibration"),
            ("FR-06", r"FR-06.*Activity Lifecycle.*Typology", "FR-06: Activity Lifecycle & Typology"),
            ("FR-07", r"FR-07.*Quiz Attempt", "FR-07: Quiz Attempt Execution"),
            ("FR-08", r"FR-08.*Immutable Answer Event", "FR-08: Immutable Answer Event Logging"),
            ("FR-09", r"FR-09.*Feature Extraction.*Temporal", "FR-09: Feature Extraction & Temporal Windowing"),
            ("FR-10", r"FR-10.*Retention Probability", "FR-10: Retention Probability Inference"),
            ("FR-11", r"FR-11.*Adaptive Recommendation", "FR-11: Adaptive Recommendation Generation"),
            ("FR-12", r"FR-12.*Review Assignment", "FR-12: Review Assignment Scheduling"),
            ("FR-13", r"FR-13.*Degraded Fallback", "FR-13: Degraded Fallback & Cold-Start Resilience"),
            ("FR-14", r"FR-14.*Teacher Analytics", "FR-14: Teacher Analytics & Section Monitoring"),
            ("FR-15", r"FR-15.*Quasi-Experimental.*Assessment Isolation|Quarantine", "FR-15: 7-Day Assessment Quarantine"),
            ("FR-16", r"FR-16.*Audit Trail.*Research Export", "FR-16: Audit Trail & Research Export"),
        ]
        for fr_id, pattern, desc in fr_list:
            check_file_contains(srs, pattern, desc)

        # Non-Functional Requirements NFR-01 through NFR-04
        nfr_list = [
            ("NFR-01", r"NFR-01.*Latency", "NFR-01: Latency & Performance (<=300ms, <=1500ms, >=5000ms)"),
            ("NFR-02", r"NFR-02.*Availability", "NFR-02: Availability & Reliability (99.9%, cold-start tolerance)"),
            ("NFR-03", r"NFR-03.*Security", "NFR-03: Security & Regulatory Compliance (RLS, RS256, Ley N° 29733)"),
            ("NFR-04", r"NFR-04.*Scalability|Concurrency", "NFR-04: Scalability & Classroom Concurrency (30 concurrent students)"),
        ]
        for nfr_id, pattern, desc in nfr_list:
            check_file_contains(srs, pattern, desc)

    # ---------------------------------------------------------
    # 3. Research Evaluation Protocol (docs/research/evaluation-protocol.md)
    # ---------------------------------------------------------
    print("\n--- 3. Research Evaluation Protocol (docs/research/evaluation-protocol.md) ---")
    eval_doc = REPO_ROOT / "docs/research/evaluation-protocol.md"
    report_assert(eval_doc.exists(), "docs/research/evaluation-protocol.md file exists", str(eval_doc))

    if eval_doc.exists():
        check_file_contains(eval_doc, r"Quasi-Experimental", "Study Design: Quasi-Experimental Design")
        check_file_contains(eval_doc, r"Control.*Group", "Control Group definition")
        check_file_contains(eval_doc, r"Experimental.*Group", "Experimental Group definition")
        check_file_contains(eval_doc, r"168\s*hours|7\s*days", "Primary Endpoint: 7-day delayed post-test (168h)")

        # Metrics check
        check_file_contains(eval_doc, r"AUC-ROC", "Discrimination Metric: AUC-ROC")
        check_file_contains(eval_doc, r"Brier\s*Score", "Calibration Metric: Brier Score")
        check_file_contains(eval_doc, r"Expected Calibration Error|ECE", "Calibration Metric: ECE")
        check_file_contains(eval_doc, r"Reliability Diagrams", "Calibration Tool: Reliability Diagrams")

        # Cross-validation check
        check_file_contains(eval_doc, r"Group-K-Fold|GroupKFold", "Cross-Validation: Student Group-K-Fold (K=5)")
        check_file_contains(eval_doc, r"event_timestamp\s*<\s*t|temporal.*cutoff", "Temporal Cutoff: No lookahead data leakage")

        # Baseline Models check
        check_file_contains(eval_doc, r"DAS3H", "Target Candidate: DAS3H")
        check_file_contains(eval_doc, r"PFA|Temporal Logistic", "Baseline 1: PFA / Temporal Logistic Regression")
        check_file_contains(eval_doc, r"BKT|Bayesian Knowledge Tracing", "Baseline 2: Modified BKT")
        check_file_contains(eval_doc, r"CatBoost", "Baseline 3: CatBoost GBDT")

        # The 5 Critical Issues & Risk Matrix (Master Plan Section 5)
        check_file_contains(eval_doc, r"Sample Size vs\.? ML Complexity|N\s*≈\s*66", "Risk Matrix Item 1: Sample Size vs ML Complexity")
        check_file_contains(eval_doc, r"Contradiction:?\s*Adaptation.*Protocol|Quarantine", "Risk Matrix Item 2: Adaptation vs Experimental Protocol Contradiction")
        check_file_contains(eval_doc, r"Cold Start.*blitz\.cloud|Classroom Concurrency", "Risk Matrix Item 3: Cold Start vs Classroom Concurrency")
        check_file_contains(eval_doc, r"Review Trigger Thresholds|tau|0\.65", "Risk Matrix Item 4: Review Trigger Threshold tau Calibration")
        check_file_contains(eval_doc, r"Data Privacy.*Ley N°\s*29733|student_id_pseudo", "Risk Matrix Item 5: Minor Data Privacy under Ley N° 29733")

        # Ethical AI & Consent
        check_file_contains(eval_doc, r"informed consent|consentimiento informado", "Parental Informed Consent Protocol")
        check_file_contains(eval_doc, r"Empathetic Feedback|Momento ideal para repasar", "Empathetic Feedback Standards")

    # ---------------------------------------------------------
    # 4. Supplemental Research Documents
    # ---------------------------------------------------------
    print("\n--- 4. Supplemental Research Documents (docs/research/) ---")
    model_sel = REPO_ROOT / "docs/research/model-selection.md"
    data_dict = REPO_ROOT / "docs/research/data-dictionary.md"

    report_assert(model_sel.exists(), "docs/research/model-selection.md file exists", str(model_sel))
    report_assert(data_dict.exists(), "docs/research/data-dictionary.md file exists", str(data_dict))

    if model_sel.exists():
        check_file_contains(model_sel, r"DAS3H", "model-selection.md: DAS3H mathematical model")
        check_file_contains(model_sel, r"logit", "model-selection.md: Mathematical logit formulation")
        check_file_contains(model_sel, r"trade-off|comparative", "model-selection.md: Comparative trade-off matrix")

    if data_dict.exists():
        check_file_contains(data_dict, r"answer_events", "data-dictionary.md: answer_events entity")
        check_file_contains(data_dict, r"student_id_pseudo", "data-dictionary.md: student_id_pseudo pseudonymization")
        check_file_contains(data_dict, r"view_research_interaction_logs", "data-dictionary.md: Anonymized research view")

    # ---------------------------------------------------------
    # 5. Regression Suite: Milestone 1 & Milestone 2 Verification
    # ---------------------------------------------------------
    print("\n--- 5. Regression Check: Milestone 1 & Milestone 2 Suites ---")
    m1_proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts/verify-m1.py")],
        capture_output=True,
        text=True,
    )
    report_assert(m1_proc.returncode == 0, "Regression Check verify-m1.py exits 0", f"Exit code {m1_proc.returncode}")

    m2_proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts/verify-m2.py")],
        capture_output=True,
        text=True,
    )
    report_assert(m2_proc.returncode == 0, "Regression Check verify-m2.py exits 0", f"Exit code {m2_proc.returncode}")

    # ---------------------------------------------------------
    # Final Summary
    # ---------------------------------------------------------
    print("\n" + "=" * 70)
    print(f"VERIFICATION RESULTS: {passed_tests} PASSED, {failed_tests} FAILED")
    print("=" * 70)

    if failed_tests == 0:
        print("\n✅ Milestone 3 Verification PASSED! All ADRs, SRS and Research specifications verified.")
        sys.exit(0)
    else:
        print(f"\n❌ Milestone 3 Verification FAILED with {failed_tests} errors.")
        sys.exit(1)


if __name__ == "__main__":
    main()
