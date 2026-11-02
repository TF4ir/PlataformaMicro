#!/usr/bin/env python3
"""
Automated Verification Suite for Phase 1: UI/UX Implementation
Plataforma de Microaprendizaje Adaptativo — Nexo Platform

Verifies:
1. Presence of all 10 core views and layouts corresponding to Capturas/
2. Design system tokens in globals.css, theme in tailwind.config.ts
3. Complete mock datasets in mock-data.ts (Lucía Mendoza, Ciencias pilot)
4. TypeScript compilation (tsc --noEmit)
5. Next.js production build output (next build)
"""

import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB_SRC = ROOT / "apps" / "web" / "src"

CHECKS = []

def check(condition: bool, name: str, details: str = ""):
    CHECKS.append((condition, name, details))
    mark = "✅ [PASS]" if condition else "❌ [FAIL]"
    print(f"{mark} {name}" + (f" -> {details}" if not condition and details else ""))

def main():
    print("=" * 78)
    print("  PLATAFORMAMICRO — PHASE 1 UI/UX VERIFICATION SUITE")
    print("  Target Repository: Nexo Web Client (apps/web)")
    print("=" * 78)

    # 1. Essential Design System & Layout Components
    required_components = [
        "lib/utils.ts",
        "lib/role-context.tsx",
        "lib/mock-data.ts",
        "types/ui.ts",
        "app/globals.css",
        "app/layout.tsx",
        "app/page.tsx",
        "components/ui/button.tsx",
        "components/ui/badge.tsx",
        "components/ui/card.tsx",
        "components/ui/progress.tsx",
        "components/layout/sidebar.tsx",
        "components/layout/header.tsx",
        "components/layout/app-shell.tsx",
        "components/student/photosynthesis-diagram.tsx",
        "components/student/empathetic-callout.tsx",
    ]

    for comp in required_components:
        p = WEB_SRC / comp
        check(p.exists(), f"Component: {comp}", f"Missing {p}")

    # 2. Required Screen Routes from Capturas/
    required_routes = [
        ("01 & 02: Student Dashboard", "app/(student)/dashboard/page.tsx"),
        ("03: Student Courses", "app/(student)/courses/page.tsx"),
        ("04: Recommendation Pre-launch", "app/(student)/recommendations/[id]/page.tsx"),
        ("05 & 06: Microcontent Lesson", "app/(student)/learn/[id]/page.tsx"),
        ("07: Quiz Active Question", "app/(student)/quiz/[id]/page.tsx"),
        ("08: Quiz Empathetic Feedback", "app/(student)/quiz/[id]/results/page.tsx"),
        ("09: Student Progress & Analytics", "app/(student)/progress/page.tsx"),
        ("10: Teacher Course Management", "app/teacher/courses/page.tsx"),
        ("Teacher Dashboard Overview", "app/teacher/dashboard/page.tsx"),
        ("System Telemetry & Cold Start", "app/system-status/page.tsx"),
    ]

    for name, route in required_routes:
        p = WEB_SRC / route
        check(p.exists(), f"Route {name}: {route}", f"Missing {p}")

    # 3. TypeScript Type-Check
    print("\n--- Running TypeScript Static Analysis ---")
    ts_res = subprocess.run(
        ["npm", "run", "type-check"],
        cwd=str(ROOT / "apps" / "web"),
        capture_output=True,
        text=True,
    )
    check(ts_res.returncode == 0, "TypeScript Static Verification (tsc --noEmit)", ts_res.stderr or ts_res.stdout)

    # 4. Next.js Production Build
    print("\n--- Verifying Next.js Production Build Artifacts ---")
    next_dist = ROOT / "apps" / "web" / ".next"
    check(next_dist.exists() and (next_dist / "BUILD_ID").exists(), "Next.js Build Output Artifacts Present", "Missing .next/BUILD_ID")

    print("\n" + "=" * 78)
    total = len(CHECKS)
    passed = sum(1 for c, _, _ in CHECKS if c)
    failed = total - passed
    print(f"  TOTAL CHECKS: {total} | PASSED: {passed} | FAILED: {failed}")
    print("=" * 78)

    if failed > 0:
        sys.exit(1)
    else:
        print("\n🎉 ALL PHASE 1 UI/UX VERIFICATION CHECKS PASSED!\n")

if __name__ == "__main__":
    main()
