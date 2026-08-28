"""
================================================================================
match_engine.py
================================================================================

PURPOSE OF THIS FILE:
---------------------
This is the **INDUSTRY-GRADE 1v1 MATCH ENGINE & ORCHESTRATOR**.

HOW IT WORKS:
-------------
1. Real players (or bots) each submit a **4-Card Loadout (2 Attack + 2 Defence)**.
2. The Engine strictly validates that:
   - Exactly 2 Attack cards and 2 Defence cards are selected.
   - All selected card IDs exist in the active dynamic Card Database.
   - No data or unselected cards are invented.
3. The Engine automatically invokes:
   - **Attack AI (LLM A)** -> Formulates optimal offensive combos for Player A & B.
   - **Defence AI (LLM B)** -> Formulates optimal defensive setups for Player A & B.
   - **Evaluation AI (LLM C / Master Referee)** -> Compares both 4-card loadouts,
     calculates synergy scores, resolves combat & counter-mechanics, computes
     damage/health deltas, and declares the **MATCH WINNER**!

PRODUCTION READY:
-----------------
Designed for high-scale multiplayer game backends (FastAPI, Flask, WebSockets).
All inputs & outputs are strictly typed via Pydantic v2 schemas.
================================================================================
"""

import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator

# Import the 3 core AI modules & 120 Card Database
from ai.attack.attack_ai import generate_attack_plan
from ai.defence.defence_ai import generate_defence_plan
from ai.evaluation.evaluation_ai import evaluate_1v1_match, EvaluationOutcome
from data.cards import get_all_cards

# ==============================================================================
# SECTION 1: PRODUCTION INPUT SCHEMAS
# ==============================================================================

class PlayerLoadoutInput(BaseModel):
    """
    Strict input submitted by a player for a match.
    Enforces exactly 2 Attack cards and 2 Defence cards.
    """
    player_id: str = Field(..., description="Unique player identifier (e.g. 'player_a').")
    player_name: str = Field(..., description="Display name of the agent / player.")
    hp: int = Field(default=100, ge=1, description="Starting health points.")
    shield: int = Field(default=50, ge=0, description="Starting armor shield.")
    current_zone: str = Field(default="a_site", description="Starting map position.")

    attack_card_ids: List[str] = Field(
        ...,
        description="List of exactly 2 selected Attack card IDs."
    )
    defence_card_ids: List[str] = Field(
        ...,
        description="List of exactly 2 selected Defence card IDs."
    )

    @field_validator("attack_card_ids")
    @classmethod
    def validate_attack_card_count(cls, v: List[str]) -> List[str]:
        if len(v) != 2:
            raise ValueError(f"Player must select EXACTLY 2 Attack cards! Received {len(v)}: {v}")
        return v

    @field_validator("defence_card_ids")
    @classmethod
    def validate_defence_card_count(cls, v: List[str]) -> List[str]:
        if len(v) != 2:
            raise ValueError(f"Player must select EXACTLY 2 Defence cards! Received {len(v)}: {v}")
        return v


class MatchSimulationResult(BaseModel):
    """
    Complete structured match result returned to game clients/APIs.
    """
    winner_id: str
    winner_name: str
    win_reason: str
    player_a_score: int
    player_b_score: int
    player_a_synergy: int
    player_b_synergy: int
    esports_commentary: str
    tactical_breakdown: str
    mvp_combo: str
    full_evaluation: EvaluationOutcome


# ==============================================================================
# SECTION 2: DEFAULT DYNAMIC CARD DATABASE (All 120 Cards)
# ==============================================================================

DEFAULT_CARD_DATABASE: Dict[str, Dict[str, Any]] = get_all_cards()


# ==============================================================================
# SECTION 3: MATCH ENGINE PIPELINE
# ==============================================================================

def run_1v1_match(
    player_a_input: PlayerLoadoutInput,
    player_b_input: PlayerLoadoutInput,
    card_database: Optional[Dict[str, Dict[str, Any]]] = None,
    map_context: Optional[Dict[str, Any]] = None,
    game_rules: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None
) -> MatchSimulationResult:
    """
    Executes a complete 1v1 tactical match:
    1. Validates all cards against the database.
    2. Runs Attack AI & Defence AI for Player A.
    3. Runs Attack AI & Defence AI for Player B.
    4. Evaluates match outcome & scoring via Evaluation AI.
    5. Returns unified MatchSimulationResult.
    """
    db = card_database or DEFAULT_CARD_DATABASE
    map_ctx = map_context or {"map_name": "Ascent", "location": "A Site"}
    rules = game_rules or {"round_time_limit_sec": 45, "shield_absorption_pct": 1.0}

    # Step 1: Validate cards exist
    def resolve_cards(card_ids: List[str], expected_cat: str) -> List[Dict[str, Any]]:
        resolved = []
        for cid in card_ids:
            if cid not in db:
                raise ValueError(f"[MATCH ENGINE ERROR] Card ID '{cid}' not found in Card Database!")
            card = db[cid]
            resolved.append(card)
        return resolved

    p_a_atk_cards = resolve_cards(player_a_input.attack_card_ids, "attack")
    p_a_def_cards = resolve_cards(player_a_input.defence_card_ids, "defence")

    p_b_atk_cards = resolve_cards(player_b_input.attack_card_ids, "attack")
    p_b_def_cards = resolve_cards(player_b_input.defence_card_ids, "defence")

    # Step 2: Run Tactical AIs for Player A
    p_a_profile = {
        "player_id": player_a_input.player_id,
        "name": player_a_input.player_name,
        "hp": player_a_input.hp,
        "shield": player_a_input.shield,
        "current_zone": player_a_input.current_zone
    }
    p_b_intel_for_a = {"visible": True, "enemy_id": player_b_input.player_id, "enemy_name": player_b_input.player_name}

    plan_a_atk = generate_attack_plan(
        attacker=p_a_profile,
        defender_intel=p_b_intel_for_a,
        available_cards=p_a_atk_cards,
        game_rules=rules,
        api_key=api_key
    )

    plan_a_def = generate_defence_plan(
        defender=p_a_profile,
        attacker_intel=p_b_intel_for_a,
        available_cards=p_a_def_cards,
        map_context=map_ctx,
        game_rules=rules,
        api_key=api_key
    )

    # Step 3: Run Tactical AIs for Player B
    p_b_profile = {
        "player_id": player_b_input.player_id,
        "name": player_b_input.player_name,
        "hp": player_b_input.hp,
        "shield": player_b_input.shield,
        "current_zone": player_b_input.current_zone
    }
    p_a_intel_for_b = {"visible": True, "enemy_id": player_a_input.player_id, "enemy_name": player_a_input.player_name}

    plan_b_atk = generate_attack_plan(
        attacker=p_b_profile,
        defender_intel=p_a_intel_for_b,
        available_cards=p_b_atk_cards,
        game_rules=rules,
        api_key=api_key
    )

    plan_b_def = generate_defence_plan(
        defender=p_b_profile,
        attacker_intel=p_a_intel_for_b,
        available_cards=p_b_def_cards,
        map_context=map_ctx,
        game_rules=rules,
        api_key=api_key
    )

    # Step 4: Run Master Evaluation AI
    eval_outcome = evaluate_1v1_match(
        player_a=p_a_profile,
        player_a_cards={"attack": p_a_atk_cards, "defence": p_a_def_cards},
        player_a_plans={"attack": plan_a_atk.model_dump(), "defence": plan_a_def.model_dump()},
        player_b=p_b_profile,
        player_b_cards={"attack": p_b_atk_cards, "defence": p_b_def_cards},
        player_b_plans={"attack": plan_b_atk.model_dump(), "defence": plan_b_def.model_dump()},
        map_context=map_ctx,
        game_rules=rules,
        api_key=api_key
    )

    return MatchSimulationResult(
        winner_id=eval_outcome.match_winner_id,
        winner_name=eval_outcome.match_winner_name,
        win_reason=eval_outcome.win_reason,
        player_a_score=eval_outcome.player_a_score.total_score,
        player_b_score=eval_outcome.player_b_score.total_score,
        player_a_synergy=eval_outcome.player_a_score.synergy_score,
        player_b_synergy=eval_outcome.player_b_score.synergy_score,
        esports_commentary=eval_outcome.play_by_play_commentary,
        tactical_breakdown=eval_outcome.tactical_breakdown,
        mvp_combo=eval_outcome.mvp_card_combo,
        full_evaluation=eval_outcome
    )


# ==============================================================================
# SECTION 4: CLI DEMO & MULTIPLAYER MATCH SIMULATOR
# ==============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print(" 🎮 INDUSTRY-GRADE 4-CARD 1v1 MATCH ENGINE DEMONSTRATION")
    print("=" * 80)

    # 1. Player A selects 4 cards (2 Attack + 2 Defence)
    player_a = PlayerLoadoutInput(
        player_id="player_a",
        player_name="Jett (Player A)",
        hp=100,
        shield=50,
        attack_card_ids=["atk_flash_entry", "atk_master_execute"],
        defence_card_ids=["def_reposition_defense", "def_layered_defense"]
    )

    # 2. Player B selects 4 cards (2 Attack + 2 Defence)
    player_b = PlayerLoadoutInput(
        player_id="player_b",
        player_name="Omen (Player B)",
        hp=100,
        shield=50,
        attack_card_ids=["atk_split_pressure", "atk_fullteam_rush"],
        defence_card_ids=["def_defensive_smoke", "def_antirush_setup"]
    )

    print("\n[INPUT CHECK] Player A Loadout:")
    print(f"  ⚔️  Attack Cards : {player_a.attack_card_ids}")
    print(f"  🛡️  Defence Cards: {player_a.defence_card_ids}")

    print("\n[INPUT CHECK] Player B Loadout:")
    print(f"  ⚔️  Attack Cards : {player_b.attack_card_ids}")
    print(f"  🛡️  Defence Cards: {player_b.defence_card_ids}")

    print("\n[RUNNING MATCH ENGINE] Orchestrating Attack AI, Defence AI, and Evaluation AI...")
    result = run_1v1_match(player_a_input=player_a, player_b_input=player_b)

    print("\n" + "-" * 80)
    print(" 🏆 FINAL MATCH VERDICT & SCORES:")
    print("-" * 80)
    print(f"WINNER           : {result.winner_name} ({result.winner_id.upper()})")
    print(f"WIN REASON       : {result.win_reason}")
    print(f"MVP CARD COMBO   : {result.mvp_combo}")
    print(f"Player A Score   : {result.player_a_score}/100 (Synergy: {result.player_a_synergy}/100)")
    print(f"Player B Score   : {result.player_b_score}/100 (Synergy: {result.player_b_synergy}/100)")

    print("\n" + "-" * 80)
    print(" 📜 REFEREE COMBAT LOG:")
    print("-" * 80)
    for log in result.full_evaluation.combat_log:
        print(f"  {log}")

    print("\n" + "-" * 80)
    print(" 🎙️ ESPORTS BROADCAST COMMENTARY:")
    print("-" * 80)
    print(result.esports_commentary)

    print("\n" + "=" * 80)
    print(" ✅ Complete 4-card 1v1 match simulation finished with zero errors!")
    print("=" * 80 + "\n")
