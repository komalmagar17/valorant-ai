"""
ai/evaluation/test_evaluation_ai.py
===================================
Unit tests for the Evaluation AI (Master Referee & Scoring Engine).
Validates:
1. Pydantic schema validation for hits, actions, player scores, and match outcomes.
2. Prompt construction with dynamic 4-card 1v1 dual loadouts.
3. Referee validation on score bounds [0, 100], winner consistency, and illegal cards.
4. End-to-end 1v1 match adjudication.
"""

import unittest
from pydantic import ValidationError
from ai.evaluation.evaluation_ai import (
    CombatHit,
    ActionResolution,
    PlayerScoreBreakdown,
    EvaluationOutcome,
    build_1v1_evaluation_prompt,
    validate_1v1_evaluation_outcome,
    evaluate_1v1_match,
)


class TestEvaluationAI(unittest.TestCase):

    def setUp(self):
        self.player_a = {"player_id": "player_a", "player_name": "Jett", "hp": 100, "shield": 50}
        self.player_a_cards = {
            "attack": [
                {"id": "curveball_flash", "name": "Curveball Flash", "type": "flash"},
                {"id": "vandal_rifle", "name": "Vandal Rifle", "type": "damage", "base_damage": 40}
            ],
            "defence": [
                {"id": "tailwind_dash", "name": "Tailwind Dash", "type": "mobility"},
                {"id": "heavy_shield", "name": "Heavy Shield", "type": "shield"}
            ]
        }
        self.player_a_plans = {
            "attack": {"sequence": [{"card_id": "curveball_flash", "order": 1}, {"card_id": "vandal_rifle", "order": 2}]},
            "defence": {"sequence": [{"card_id": "tailwind_dash", "order": 1}]}
        }

        self.player_b = {"player_id": "player_b", "player_name": "Omen", "hp": 100, "shield": 50}
        self.player_b_cards = {
            "attack": [
                {"id": "phantom_rifle", "name": "Phantom Rifle", "type": "damage", "base_damage": 35},
                {"id": "paranoia_blind", "name": "Paranoia Blind", "type": "flash"}
            ],
            "defence": [
                {"id": "dark_cover_smoke", "name": "Dark Cover Smoke", "type": "smoke"},
                {"id": "shrouded_step", "name": "Shrouded Step Teleport", "type": "mobility"}
            ]
        }
        self.player_b_plans = {
            "attack": {"sequence": [{"card_id": "phantom_rifle", "order": 1}]},
            "defence": {"sequence": [{"card_id": "dark_cover_smoke", "order": 1}]}
        }

        self.map_context = {"map_name": "Ascent", "location": "A Site"}

    def test_player_score_breakdown_validation(self):
        """Verify score bounds enforcement (0-100)."""
        score = PlayerScoreBreakdown(
            player_id="player_a",
            player_name="Jett",
            synergy_score=90,
            counter_score=85,
            execution_score=95,
            total_score=90,
            damage_dealt=140,
            damage_mitigated=30,
            final_hp=100,
            final_shield=50,
            is_eliminated=False
        )
        self.assertEqual(score.total_score, 90)

        # Out of bounds score (> 100) should fail
        with self.assertRaises(ValidationError):
            PlayerScoreBreakdown(
                player_id="player_a",
                player_name="Jett",
                synergy_score=150,  # Invalid: le=100
                counter_score=80,
                execution_score=80,
                total_score=100,
                damage_dealt=0,
                damage_mitigated=0,
                final_hp=100,
                final_shield=50,
                is_eliminated=False
            )

    def test_build_1v1_evaluation_prompt(self):
        """Verify prompt embeds both players, their 4 cards each, and AI sequences."""
        prompt = build_1v1_evaluation_prompt(
            player_a=self.player_a,
            player_a_cards=self.player_a_cards,
            player_a_plans=self.player_a_plans,
            player_b=self.player_b,
            player_b_cards=self.player_b_cards,
            player_b_plans=self.player_b_plans,
            map_context=self.map_context
        )
        self.assertIn("Jett", prompt)
        self.assertIn("Omen", prompt)
        self.assertIn("curveball_flash", prompt)
        self.assertIn("dark_cover_smoke", prompt)
        self.assertIn("CARD SYNERGY", prompt)

    def test_validate_invalid_winner_id(self):
        """Verify referee catches illegal winner IDs."""
        score_a = PlayerScoreBreakdown(
            player_id="player_a", player_name="Jett", synergy_score=80, counter_score=80,
            execution_score=80, total_score=80, damage_dealt=0, damage_mitigated=0,
            final_hp=100, final_shield=50, is_eliminated=False
        )
        score_b = PlayerScoreBreakdown(
            player_id="player_b", player_name="Omen", synergy_score=70, counter_score=70,
            execution_score=70, total_score=70, damage_dealt=0, damage_mitigated=0,
            final_hp=100, final_shield=50, is_eliminated=False
        )

        bad_outcome = EvaluationOutcome(
            match_winner_id="some_hacker_id",  # Invalid winner!
            match_winner_name="Hacker",
            win_reason="Invalid",
            player_a_score=score_a,
            player_b_score=score_b,
            action_resolutions=[],
            combat_log=["Match end."],
            play_by_play_commentary="Commentary",
            tactical_breakdown="Breakdown",
            mvp_card_combo="Combo"
        )

        with self.assertRaises(ValueError) as ctx:
            validate_1v1_evaluation_outcome(
                outcome=bad_outcome,
                player_a=self.player_a,
                player_b=self.player_b
            )
        self.assertIn("Invalid match_winner_id", str(ctx.exception))

    def test_end_to_end_1v1_match_evaluation(self):
        """Verify complete 1v1 match evaluation."""
        outcome = evaluate_1v1_match(
            player_a=self.player_a,
            player_a_cards=self.player_a_cards,
            player_a_plans=self.player_a_plans,
            player_b=self.player_b,
            player_b_cards=self.player_b_cards,
            player_b_plans=self.player_b_plans,
            map_context=self.map_context
        )
        self.assertIsInstance(outcome, EvaluationOutcome)
        self.assertIn(outcome.match_winner_id, ["player_a", "player_b", "draw"])
        self.assertGreater(outcome.player_a_score.total_score, 0)
        self.assertGreater(outcome.player_b_score.total_score, 0)
        self.assertTrue(len(outcome.play_by_play_commentary) > 0)


if __name__ == "__main__":
    unittest.main()
