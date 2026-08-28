"""
ai/evaluation/__init__.py
=========================
Exports Evaluation AI data models, prompt builder, validator, and evaluator functions.
"""

from ai.evaluation.evaluation_ai import (
    CombatHit,
    ActionResolution,
    PlayerScoreBreakdown,
    PlayerStateImpact,
    SpikeObjectiveUpdate,
    EvaluationOutcome,
    build_1v1_evaluation_prompt,
    validate_1v1_evaluation_outcome,
    evaluate_1v1_match,
)

__all__ = [
    "CombatHit",
    "ActionResolution",
    "PlayerScoreBreakdown",
    "PlayerStateImpact",
    "SpikeObjectiveUpdate",
    "EvaluationOutcome",
    "build_1v1_evaluation_prompt",
    "validate_1v1_evaluation_outcome",
    "evaluate_1v1_match",
]
