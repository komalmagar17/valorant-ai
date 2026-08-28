"""
ai/defence/test_defence_ai.py
=============================
Unit tests for the Defence AI module.
Validates:
1. Pydantic schema validation for defensive actions and plans.
2. Prompt construction with dynamic inputs.
3. Cooldown and illegal card interception.
4. End-to-end plan generation.
"""

import unittest
from pydantic import ValidationError
from ai.defence.defence_ai import (
    DefenceAction,
    DefencePlan,
    build_defence_prompt,
    validate_defence_plan,
    generate_defence_plan,
)


class TestDefenceAI(unittest.TestCase):

    def setUp(self):
        self.sample_defender = {
            "player_id": "player_b",
            "name": "Cypher",
            "role": "defender",
            "hp": 100,
            "shield": 50,
            "current_zone": "a_site",
            "cooldowns": {
                "dark_cover_smoke": 0,
                "cypher_trapwire": 0
            }
        }

        self.sample_attacker_intel = {
            "threat_level": "high",
            "spotted_in": "a_main",
            "expected_weapon": "vandal_rifle"
        }

        self.sample_defensive_cards = [
            {
                "id": "dark_cover_smoke",
                "name": "Dark Cover Smoke",
                "type": "smoke",
                "cooldown_turns": 2
            },
            {
                "id": "cypher_trapwire",
                "name": "Cypher Trapwire",
                "type": "trap",
                "cooldown_turns": 3
            }
        ]

        self.sample_map = {
            "map_name": "Ascent",
            "site": "a_site"
        }

    def test_defence_action_pydantic_validation(self):
        """Verify DefenceAction validates field requirements."""
        action = DefenceAction(
            card_id="dark_cover_smoke",
            action_type="deploy_smoke",
            target="a_main_choke",
            order=1,
            reason="Block vision"
        )
        self.assertEqual(action.card_id, "dark_cover_smoke")
        self.assertEqual(action.order, 1)

        with self.assertRaises(ValidationError):
            DefenceAction(
                card_id="dark_cover_smoke",
                target="a_main",
                order=0,  # Invalid order < 1
                reason="Invalid"
            )

    def test_build_defence_prompt(self):
        """Verify prompt contains dynamic inputs."""
        prompt = build_defence_prompt(
            defender=self.sample_defender,
            attacker_intel=self.sample_attacker_intel,
            available_cards=self.sample_defensive_cards,
            map_context=self.sample_map
        )
        self.assertIn("dark_cover_smoke", prompt)
        self.assertIn("cypher_trapwire", prompt)
        self.assertIn("Ascent", prompt)

    def test_validate_illegal_card_rejection(self):
        """Verify hallucinated cards are caught and rejected."""
        bad_plan = DefencePlan(
            sequence=[
                DefenceAction(
                    card_id="force_field_god_mode_999",  # Illegal!
                    action_type="use_ability",
                    target="a_site",
                    order=1,
                    reason="Cheating with fake shield."
                )
            ],
            strategy_summary="Illegal defence"
        )

        with self.assertRaises(ValueError) as ctx:
            validate_defence_plan(
                plan=bad_plan,
                defender=self.sample_defender,
                available_cards=self.sample_defensive_cards
            )
        self.assertIn("illegal/unknown card", str(ctx.exception))

    def test_validate_cooldown_rejection(self):
        """Verify cards on cooldown are rejected."""
        self.sample_defender["cooldowns"]["dark_cover_smoke"] = 2
        bad_plan = DefencePlan(
            sequence=[
                DefenceAction(
                    card_id="dark_cover_smoke",
                    action_type="deploy_smoke",
                    target="a_main",
                    order=1,
                    reason="Smoke on cooldown"
                )
            ],
            strategy_summary="Cooldown error"
        )

        with self.assertRaises(ValueError) as ctx:
            validate_defence_plan(
                plan=bad_plan,
                defender=self.sample_defender,
                available_cards=self.sample_defensive_cards
            )
        self.assertIn("card on cooldown", str(ctx.exception))

    def test_end_to_end_defence_generation(self):
        """Verify generate_defence_plan works end-to-end."""
        plan = generate_defence_plan(
            defender=self.sample_defender,
            attacker_intel=self.sample_attacker_intel,
            available_cards=self.sample_defensive_cards,
            map_context=self.sample_map
        )
        self.assertIsInstance(plan, DefencePlan)
        self.assertTrue(len(plan.sequence) >= 1)
        self.assertTrue(len(plan.strategy_summary) > 0)


if __name__ == "__main__":
    unittest.main()
