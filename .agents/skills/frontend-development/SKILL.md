---
name: frontend-development
description: Next.js App Router, React Server Components, Tailwind CSS, shadcn/ui, Zod validation, and typed API consumption for adaptive microlearning.
---
# Frontend Development Skill

## 1. Overview & Role
Guides development within `apps/web/` using Next.js App Router, TypeScript strict mode, and Tailwind CSS.

## 2. Guardrails & Best Practices
- **Phase 0 Strict Guardrail**: During Phase 0, UI wireframes, page views, and interactive components in `src/components/ui/` are prohibited. Scaffolding is limited to configuration, types, and directories.
- **Server Components by Default**: Reserve `'use client'` strictly for components requiring event listeners, state hooks, or browser APIs.
- **Form Management**: All forms must leverage `react-hook-form` integrated with `zod` schemas.
- **Zero In-Browser ML**: No machine learning calculations or model loading in client code.
- **Empathetic Feedback**: Avoid punitive or anxiety-inducing feedback terms (e.g. use "Refuerzo sugerido" instead of "Riesgo de reprobar").

## 3. Cross-References
- `apps/web/AGENTS.md`
- `.agents/rules/frontend.md`
- `.agents/skills/improve-animations/`
