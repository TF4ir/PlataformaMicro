---
name: adaptive-learning
description: Pedagogical adaptation policies, forgetting curve decay thresholds, review scheduling, anti-fatigue frequency capping, and deterministic rule-based fallback.
---
# Adaptive Learning Skill

## 1. Overview & Role
Governs the pedagogical adaptation engine implemented in `services/ml-api/app/adaptation/`. Translates raw probabilistic retention estimates into actionable pedagogical decisions.

## 2. Decision Logic & Policies
- **Decoupling**: Probability calculation ($P(R=1)$) is strictly decoupled from pedagogical adaptation decisions.
- **Recall Threshold Policy**: Trigger review recommendation when predicted recall probability drops below threshold $\tau$ (default $\tau = 0.65$):
  $$P(R=1 \mid \Delta t) \le \tau \implies \text{Trigger Review}$$
- **Anti-Spam Frequency Capping**: Prevent student fatigue by limiting maximum review recommendations per KC to once per 24 hours.
- **Rule-Based Contingency Fallback**: If inference fails or student has insufficient historical attempts ($< 3$), fall back to standard spaced intervals ($1\text{d}, 3\text{d}, 7\text{d}$) with deterministic audit reason.
- **Audit Trail Persistence**: Every generated recommendation must persist `selection_method`, `recall_probability`, and `decision_reason`.

## 3. Cross-References
- `services/ml-api/app/adaptation/`
- ADR-0003: Probabilistic Adaptation Boundary
- `packages/contracts/openapi/openapi.json`
