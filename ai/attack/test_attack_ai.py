"""
ai/attack/test_attack_ai.py
===========================
Unit tests for the Attack AI module.
Validates:
1. Pydantic schema validation.
2. Prompt construction.
3. Cooldown and illegal card interception.
4. End-to-end plan generation.
"""

import unittest
from pydantic import ValidationError
from ai.attack.attack_ai import (
    AttackAction,
    AttackPlan,
    build_attack_prompt,
    validate_attack_plan,
    generate_attack_plan,
)


class TestAttackAI(unittest.TestCase):

    def setUp(self):
        self.sample_attacker = {
            "player_id": "player_a",
            "name": "Jett",
            "role": "attacker",
            "hp": 100,
            "shield": 50,
            "energy": 100,
            "current_zone": "a_main",
            "equipped_weapon": "vandal_rifle",
            "cooldowns": {
                "tailwind_dash": 0,
                "curveball_flash": 0
            }
        }

        self.sample_defender_intel = {
            "visible": True,
            "enemy_id": "player_b",
            "enemy_known_zone": "a_site",
            "intel_summary": "Enemy Omen spotted holding angle on A Site!"
        }

        self.sample_cards = [
            {
                "id": "vandal_rifle",
                "name": "Vandal Rifle",
                "type": "damage",
                "base_damage": 40,
                "energy_cost": 0,
                "cooldown_turns": 0,
                "description": "High damage assault rifle."
            },
            {
                "id": "curveball_flash",
                "name": "Curveball Flash",
                "type": "flash",
                "base_damage": 0,
                "energy_cost": 25,
                "cooldown_turns": 2,
                "description": "Blinds opponents in target zone."
            }
        ]

        self.sample_rules = {
            "round_turn_limit": 8,
            "fog_of_war_enabled": True
        }

    def test_attack_action_pydantic_validation(self):
        """Verify that Pydantic enforces required fields and types."""
        action = AttackAction(
            card_id="vandal_rifle",
            action_type="attack",
            target="player_b",
            order=1,
            reason="Firing rifle at enemy."
        )
        self.assertEqual(action.card_id, "vandal_rifle")
        self.assertEqual(action.order, 1)

        # Invalid order (< 1) should raise ValidationError
        with self.assertRaises(ValidationError):
            AttackAction(
                card_id="vandal_rifle",
                target="player_b",
                order=0,  # Invalid: ge=1 constraint
                reason="Invalid order"
            )

    def test_build_attack_prompt(self):
        """Verify prompt builder includes all dynamic inputs."""
        prompt = build_attack_prompt(
            attacker=self.sample_attacker,
            defender_intel=self.sample_defender_intel,
            available_cards=self.sample_cards,
            game_rules=self.sample_rules
        )
        self.assertIn("vandal_rifle", prompt)
        self.assertIn("curveball_flash", prompt)
        self.assertIn("a_main", prompt)
        self.assertIn("schema", prompt.lower())

    def test_validate_illegal_card_rejection(self):
        """Verify that hallucinated cards are caught and rejected."""
        fake_plan = AttackPlan(
            sequence=[
                AttackAction(
                    card_id="orbital_nuke_9999",  # Does NOT exist!
                    action_type="attack",
                    target="player_b",
                    order=1,
                    reason="Cheating with fake card."
                )
            ],
            strategy_summary="Illegal attack"
        )

        with self.assertRaises(ValueError) as ctx:
            validate_attack_plan(
                plan=fake_plan,
                attacker=self.sample_attacker,
                available_cards=self.sample_cards
            )
        self.assertIn("illegal/unknown card", str(ctx.exception))

    def test_validate_cooldown_rejection(self):
        """Verify that cards currently on cooldown cannot be used."""
        # Set flash on cooldown (2 turns left)
        self.sample_attacker["cooldowns"]["curveball_flash"] = 2

        cooldown_plan = AttackPlan(
            sequence=[
                AttackAction(
                    card_id="curveball_flash",
                    action_type="use_ability",
                    target="a_site",
                    order=1,
                    reason="Trying to flash while on cooldown."
                )
            ],
            strategy_summary="Cooldown breach"
        )

        with self.assertRaises(ValueError) as ctx:
            validate_attack_plan(
                plan=cooldown_plan,
                attacker=self.sample_attacker,
                available_cards=self.sample_cards
            )
        self.assertIn("card on cooldown", str(ctx.exception))

    def test_end_to_end_generation(self):
        """Verify generate_attack_plan works end-to-end with validation."""
        plan = generate_attack_plan(
            attacker=self.sample_attacker,
            defender_intel=self.sample_defender_intel,
            available_cards=self.sample_cards,
            game_rules=self.sample_rules
        )
        self.assertIsInstance(plan, AttackPlan)
        self.assertTrue(len(plan.sequence) >= 1)
        self.assertTrue(len(plan.strategy_summary) > 0)


if __name__ == "__main__":
    unittest.main()
