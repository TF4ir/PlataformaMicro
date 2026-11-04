"""Pedagogical adaptation engine for spaced review recommendations.

Addresses Section 5 of TASK M5.3:
Translates retention predictions into actionable microlearning reviews while enforcing:
1. Configurable retention threshold tau (default 0.650).
2. Projected review timing with preventive safety margin (0.85 * Delta_crit).
3. Published microcontent catalog selection for authorized tenant and KC.
4. Strict 24-hour anti-fatigue frequency capping and deduplication of pending recommendations.
5. Deterministic rule-based fallback for cold-start and insufficient history states.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import asyncpg

from app.schemas.adaptation import (
    AdaptationEvaluationResponse,
    EvaluationResultItem,
    MicrocontentSummary,
    RecommendationItemResponse,
    RecommendationMethodEnum,
    RecommendationStatusEnum,
)
from app.schemas.prediction import KCRetentionPrediction, ModelAvailabilityStatus


class AdaptationEngine:
    """Orchestrates pedagogical adaptation and spaced review scheduling."""

    def __init__(
        self,
        policy_name: str = "preventive_spaced_repetition",
        policy_version: str = "1.0.0",
        anti_fatigue_hours: int = 24,
    ) -> None:
        self.policy_name = policy_name
        self.policy_version = policy_version
        self.anti_fatigue_hours = anti_fatigue_hours

    async def evaluate_and_generate_recommendations(
        self,
        pool: asyncpg.Pool,
        student_id: uuid.UUID,
        tenant_id: uuid.UUID,
        retention_predictions: list[KCRetentionPrediction],
        tau: float = 0.650,
    ) -> AdaptationEvaluationResponse:
        """Evaluate retention states and issue non-duplicate, cooldown-compliant recommendations."""
        now = datetime.now(UTC)
        cooldown_window = now - timedelta(hours=self.anti_fatigue_hours)

        decisions: list[EvaluationResultItem] = []
        created_count = 0

        async with pool.acquire() as conn:
            for pred in retention_predictions:
                kc_id = pred.knowledge_component_id
                kc_name = pred.knowledge_component_name

                # --- STEP 1: Determine Pedagogical Review Need ---
                needs_review = False
                decision_reason = ""
                selection_method = RecommendationMethodEnum.PREDICTIVE_MODEL

                if pred.availability_status == ModelAvailabilityStatus.COLD_START:
                    # Cold-start fallback rule: if practiced/exposed but cold-start, recommend initial consolidation
                    if pred.total_exposures > 0 or pred.total_retrieval_attempts > 0:
                        needs_review = True
                        selection_method = RecommendationMethodEnum.RULE_BASED_FALLBACK
                        decision_reason = "Consolidación inicial sugerida por regla pedagógica de respaldo (cold-start)."
                    else:
                        decisions.append(
                            EvaluationResultItem(
                                knowledge_component_id=kc_id,
                                knowledge_component_name=kc_name,
                                decision="retention_sufficient",
                                reason="Concepto sin actividad previa de estudio.",
                            )
                        )
                        continue

                elif pred.availability_status == ModelAvailabilityStatus.INSUFFICIENT_EMPIRICAL_DATA:
                    # In production without empirical model: fallback
                    needs_review = True
                    selection_method = RecommendationMethodEnum.RULE_BASED_FALLBACK
                    decision_reason = "Repaso preventivo programado según calendario canónico de refuerzo."

                else:
                    # Model prediction available: check threshold crossing
                    if pred.current_recall_probability <= tau:
                        needs_review = True
                        decision_reason = f"Probabilidad actual ({pred.current_recall_probability:.2f}) se encuentra en o por debajo del umbral de consolidación ({tau:.2f})."
                    elif pred.predicted_forgetting_time_days is not None and pred.predicted_forgetting_time_days <= 3.0:
                        needs_review = True
                        decision_reason = f"Se proyecta que la probabilidad descenderá al umbral en {pred.predicted_forgetting_time_days:.1f} días. Momento ideal para repaso preventivo."
                    else:
                        decisions.append(
                            EvaluationResultItem(
                                knowledge_component_id=kc_id,
                                knowledge_component_name=kc_name,
                                decision="retention_sufficient",
                                reason=f"Retención estimada ({pred.current_recall_probability:.2f}) confortable por encima del umbral.",
                            )
                        )
                        continue

                if not needs_review:
                    continue

                # --- STEP 2: Anti-Fatigue 24h & Pending Duplication Check ---
                existing_rec = await conn.fetchrow(
                    """
                    SELECT id, status, created_at, cooldown_until
                    FROM recommendations
                    WHERE student_id = $1 AND knowledge_component_id = $2
                      AND (
                          status = 'pending'
                          OR created_at >= $3
                          OR (cooldown_until IS NOT NULL AND cooldown_until > $4)
                      )
                    ORDER BY created_at DESC
                    LIMIT 1;
                    """,
                    student_id,
                    kc_id,
                    cooldown_window,
                    now,
                )

                if existing_rec:
                    if existing_rec["status"] == "pending":
                        decisions.append(
                            EvaluationResultItem(
                                knowledge_component_id=kc_id,
                                knowledge_component_name=kc_name,
                                decision="cooldown_active",
                                recommendation_id=existing_rec["id"],
                                reason="Existe una recomendación previa pendiente de completar para este concepto.",
                            )
                        )
                    else:
                        decisions.append(
                            EvaluationResultItem(
                                knowledge_component_id=kc_id,
                                knowledge_component_name=kc_name,
                                decision="cooldown_active",
                                recommendation_id=existing_rec["id"],
                                reason=f"Límite anti-fatiga activo: se emitió una recomendación hace menos de {self.anti_fatigue_hours} horas.",
                            )
                        )
                    continue

                # --- STEP 3: Catalog Microcontent Selection ---
                microcontent = await conn.fetchrow(
                    """
                    SELECT id, title, content_type, estimated_duration_seconds
                    FROM microcontents
                    WHERE knowledge_component_id = $1 
                      AND tenant_id = $2 
                      AND is_published = true
                    ORDER BY created_at ASC
                    LIMIT 1;
                    """,
                    kc_id,
                    tenant_id,
                )

                if not microcontent:
                    decisions.append(
                        EvaluationResultItem(
                            knowledge_component_id=kc_id,
                            knowledge_component_name=kc_name,
                            decision="no_content_available",
                            reason="No existe microcontenido publicado en catálogo para este componente.",
                        )
                    )
                    continue

                # --- STEP 4: Schedule and Persist Recommendation ---
                rec_id = uuid.uuid4()
                idempotency_key = uuid.uuid4()
                scheduled_for = pred.recommended_review_time or now
                cooldown_until = now + timedelta(hours=self.anti_fatigue_hours)
                expires_at = now + timedelta(days=7)

                await conn.execute(
                    """
                    INSERT INTO recommendations (
                        id, tenant_id, student_id, knowledge_component_id,
                        microcontent_id, selection_method, decision_reason,
                        status, policy_name, policy_version, scheduled_for,
                        cooldown_until, expires_at, idempotency_key, created_at
                    ) VALUES (
                        $1, $2, $3, $4,
                        $5, $6::recommendation_method_enum, $7,
                        'pending'::recommendation_status_enum, $8, $9, $10,
                        $11, $12, $13, $14
                    )
                    """,
                    rec_id,
                    tenant_id,
                    student_id,
                    kc_id,
                    microcontent["id"],
                    selection_method.value,
                    decision_reason,
                    self.policy_name,
                    self.policy_version,
                    scheduled_for,
                    cooldown_until,
                    expires_at,
                    idempotency_key,
                    now,
                )

                created_count += 1
                decisions.append(
                    EvaluationResultItem(
                        knowledge_component_id=kc_id,
                        knowledge_component_name=kc_name,
                        decision="recommended",
                        recommendation_id=rec_id,
                        reason=decision_reason,
                    )
                )

        return AdaptationEvaluationResponse(
            student_id=student_id,
            evaluated_at=now,
            decisions=decisions,
            recommendations_created=created_count,
        )

    async def get_active_recommendations(
        self,
        pool: asyncpg.Pool,
        student_id: uuid.UUID,
        tenant_id: uuid.UUID,
        include_completed: bool = False,
    ) -> list[RecommendationItemResponse]:
        """Fetch recommendations for the student, resolving KC and microcontent details."""
        async with pool.acquire() as conn:
            query = """
                SELECT 
                    r.id,
                    r.knowledge_component_id,
                    kc.name AS kc_name,
                    r.selection_method::text AS selection_method,
                    r.decision_reason,
                    r.status::text AS status,
                    r.created_at,
                    r.scheduled_for,
                    r.cooldown_until,
                    r.expires_at,
                    r.completed_at,
                    m.id AS microcontent_id,
                    m.title AS microcontent_title,
                    m.content_type::text AS content_type,
                    m.estimated_duration_seconds
                FROM recommendations r
                JOIN knowledge_components kc ON r.knowledge_component_id = kc.id
                JOIN microcontents m ON r.microcontent_id = m.id
                WHERE r.student_id = $1 AND r.tenant_id = $2
            """
            if not include_completed:
                query += " AND r.status = 'pending'"
            query += " ORDER BY r.created_at DESC"

            rows = await conn.fetch(query, student_id, tenant_id)

            results: list[RecommendationItemResponse] = []
            for r in rows:
                results.append(
                    RecommendationItemResponse(
                        id=r["id"],
                        knowledge_component_id=r["knowledge_component_id"],
                        knowledge_component_name=r["kc_name"],
                        microcontent=MicrocontentSummary(
                            id=r["microcontent_id"],
                            title=r["microcontent_title"],
                            content_type=r["content_type"],
                            estimated_duration_seconds=r["estimated_duration_seconds"],
                        ),
                        selection_method=RecommendationMethodEnum(r["selection_method"]),
                        decision_reason=r["decision_reason"],
                        status=RecommendationStatusEnum(r["status"]),
                        created_at=r["created_at"],
                        scheduled_for=r["scheduled_for"],
                        cooldown_until=r["cooldown_until"],
                        expires_at=r["expires_at"],
                        completed_at=r["completed_at"],
                        is_pending=r["status"] == "pending",
                    )
                )

            return results

    async def mark_recommendation_completed(
        self,
        pool: asyncpg.Pool,
        recommendation_id: uuid.UUID,
        student_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> bool:
        """Mark a recommendation as completed, verifying ownership and tenant isolation."""
        now = datetime.now(UTC)
        async with pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE recommendations
                SET status = 'completed'::recommendation_status_enum,
                    completed_at = $1
                WHERE id = $2 AND student_id = $3 AND tenant_id = $4 AND status = 'pending'
                """,
                now,
                recommendation_id,
                student_id,
                tenant_id,
            )
            # Result string is "UPDATE 1" if row was modified
            return bool(result == "UPDATE 1")
