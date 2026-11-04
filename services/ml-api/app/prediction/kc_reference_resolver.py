"""Knowledge Component difficulty reference resolver.

Addresses Section 4.3 of TASK M5.3:
Ensures retention probability predictions are comparable across Knowledge Components
by grounding them on a standardized reference frame rather than arbitrary individual questions.
"""

from __future__ import annotations

import math


class KCReferenceResolver:
    """Resolves standardized, comparable difficulty references for Knowledge Components."""

    @staticmethod
    def resolve_reference_difficulty_logit(difficulty_prior: float) -> float:
        """Convert [0, 1] difficulty prior into a standardized logit difficulty offset beta_k.

        Formula:
            beta_k = ln((difficulty_prior + eps) / (1 - difficulty_prior + eps))

        If difficulty_prior = 0.50 (neutral/medium), beta_k = 0.0.
        If difficulty_prior = 0.70 (hard), beta_k > 0 (reduces P_recall).
        If difficulty_prior = 0.30 (easy), beta_k < 0 (increases P_recall).

        This establishes a standardized baseline reference for the entire KC rather than
        varying randomly based on whichever specific question happened to be drawn.
        """
        # Clamp prior to [0.05, 0.95]
        p = max(0.05, min(0.95, difficulty_prior))
        return math.log(p / (1.0 - p))
