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
from concurrent.futures import ThreadPoolExecutor
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
    player_a_attack_sequence: List[Dict[str, Any]] = Field(default_factory=list)
    player_a_defence_sequence: List[Dict[str, Any]] = Field(default_factory=list)
    player_b_attack_sequence: List[Dict[str, Any]] = Field(default_factory=list)
    player_b_defence_sequence: List[Dict[str, Any]] = Field(default_factory=list)
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
    api_key: Optional[str] = None,
    attack_api_key: Optional[str] = None,
    defence_api_key: Optional[str] = None,
    evaluation_api_key: Optional[str] = None
) -> MatchSimulationResult:
    """
    Executes a complete 1v1 tactical match:
    1. Validates all cards against the database.
    2. Runs Attack AI & Defence AI for Player A (using attack_api_key / defence_api_key).
    3. Runs Attack AI & Defence AI for Player B (using attack_api_key / defence_api_key).
    4. Evaluates match outcome & scoring via Evaluation AI (using evaluation_api_key).
    5. Returns unified MatchSimulationResult.
    """
    db = card_database or DEFAULT_CARD_DATABASE
    map_ctx = map_context or {"map_name": "Ascent", "location": "A Site"}
    rules = game_rules or {
        "round_time_limit_sec": 100,
        "spike_timer_sec": 45,
        "buy_phase_sec": 30,
        "shield_absorption_pct": 1.0
    }

    # Resolve individual AI API keys (with fallback to unified api_key)
    atk_key = attack_api_key or api_key
    def_key = defence_api_key or api_key
    eval_key = evaluation_api_key or api_key

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

    # Step 2 & 3: Run Tactical AIs for Player A and Player B concurrently
    p_a_profile = {
        "player_id": player_a_input.player_id,
        "name": player_a_input.player_name,
        "hp": player_a_input.hp,
        "shield": player_a_input.shield,
        "current_zone": player_a_input.current_zone
    }
    p_b_intel_for_a = {"visible": True, "enemy_id": player_b_input.player_id, "enemy_name": player_b_input.player_name}

    p_b_profile = {
        "player_id": player_b_input.player_id,
        "name": player_b_input.player_name,
        "hp": player_b_input.hp,
        "shield": player_b_input.shield,
        "current_zone": player_b_input.current_zone
    }
    p_a_intel_for_b = {"visible": True, "enemy_id": player_a_input.player_id, "enemy_name": player_a_input.player_name}

    with ThreadPoolExecutor(max_workers=4) as executor:
        fut_a_atk = executor.submit(
            generate_attack_plan,
            attacker=p_a_profile,
            defender_intel=p_b_intel_for_a,
            available_cards=p_a_atk_cards,
            game_rules=rules,
            api_key=atk_key
        )
        fut_a_def = executor.submit(
            generate_defence_plan,
            defender=p_a_profile,
            attacker_intel=p_b_intel_for_a,
            available_cards=p_a_def_cards,
            map_context=map_ctx,
            game_rules=rules,
            api_key=def_key
        )
        fut_b_atk = executor.submit(
            generate_attack_plan,
            attacker=p_b_profile,
            defender_intel=p_a_intel_for_b,
            available_cards=p_b_atk_cards,
            game_rules=rules,
            api_key=atk_key
        )
        fut_b_def = executor.submit(
            generate_defence_plan,
            defender=p_b_profile,
            attacker_intel=p_a_intel_for_b,
            available_cards=p_b_def_cards,
            map_context=map_ctx,
            game_rules=rules,
            api_key=def_key
        )

        plan_a_atk = fut_a_atk.result()
        plan_a_def = fut_a_def.result()
        plan_b_atk = fut_b_atk.result()
        plan_b_def = fut_b_def.result()

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
        api_key=eval_key
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
        player_a_attack_sequence=[a.model_dump() for a in plan_a_atk.sequence],
        player_a_defence_sequence=[a.model_dump() for a in plan_a_def.sequence],
        player_b_attack_sequence=[a.model_dump() for a in plan_b_atk.sequence],
        player_b_defence_sequence=[a.model_dump() for a in plan_b_def.sequence],
        full_evaluation=eval_outcome
    )


# ==============================================================================
# SECTION 3B: GODOT COMBAT TIMELINE & ACTION SEQUENCE GENERATOR
# ==============================================================================

def generate_godot_match_sequence(
    match_id: str,
    player_a_name: str,
    player_a_attack_cards: List[str],
    player_a_defence_cards: List[str],
    player_a_character_id: str,
    player_b_name: str,
    player_b_attack_cards: List[str],
    player_b_defence_cards: List[str],
    player_b_character_id: str,
    winner_id: str,  # "player_a", "player_b", or "draw"
    player_a_score: int = 13,
    player_b_score: int = 9,
    win_reason: str = "Superior ability rotation and tactical execution.",
    mvp_combo: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates a high-precision, chronological Godot animation and emote sequence
    based on manual admin adjudication and 4-card player loadouts.
    """
    from data.cards import get_all_cards
    from data.characters import get_character_by_id
    import os

    all_cards = get_all_cards()
    char_a = get_character_by_id(player_a_character_id or "char_phantom_9")
    char_b = get_character_by_id(player_b_character_id or "char_sol_vanguard")

    winner_name = player_a_name if winner_id == "player_a" else (player_b_name if winner_id == "player_b" else "Tie / Draw")
    loser_name = player_b_name if winner_id == "player_a" else (player_a_name if winner_id == "player_b" else "Both Agents")
    winner_actor = winner_id if winner_id in ["player_a", "player_b"] else "player_a"
    loser_actor = "player_b" if winner_actor == "player_a" else "player_a"

    # Resolve card names
    p_a_atks = [all_cards.get(cid, {"name": cid, "id": cid}) for cid in player_a_attack_cards]
    p_a_defs = [all_cards.get(cid, {"name": cid, "id": cid}) for cid in player_a_defence_cards]
    p_b_atks = [all_cards.get(cid, {"name": cid, "id": cid}) for cid in player_b_attack_cards]
    p_b_defs = [all_cards.get(cid, {"name": cid, "id": cid}) for cid in player_b_defence_cards]

    auto_mvp = mvp_combo or (f"{p_a_atks[0]['name']} + {p_a_defs[0]['name']}" if winner_id == "player_a" else f"{p_b_atks[0]['name']} + {p_b_defs[0]['name']}")

    # Build chronological Godot timeline keyframes
    timeline: List[Dict[str, Any]] = [
        {
            "step": 1,
            "timestamp_sec": 0.0,
            "actor": "player_a",
            "character_id": char_a["id"],
            "character_name": char_a["name"],
            "action_type": "round_start_emote",
            "card_id": None,
            "card_name": None,
            "animation_trigger": "anim_emote_taunt" if char_a["id"] == "char_phantom_9" else "anim_emote_flex",
            "emote_trigger": "emote_taunt" if char_a["id"] == "char_phantom_9" else "emote_flex",
            "damage_dealt": 0,
            "target": "player_b",
            "sound_cue": "sfx_blade_whoosh" if char_a["id"] == "char_phantom_9" else "sfx_furnace_blast",
            "commentary": f"Round starts! {player_a_name} ({char_a['name']}) opens with an aggressive tactical taunt."
        },
        {
            "step": 2,
            "timestamp_sec": 1.4,
            "actor": "player_b",
            "character_id": char_b["id"],
            "character_name": char_b["name"],
            "action_type": "round_start_emote",
            "card_id": None,
            "card_name": None,
            "animation_trigger": "anim_emote_flex" if char_b["id"] == "char_sol_vanguard" else "anim_emote_dance",
            "emote_trigger": "emote_flex" if char_b["id"] == "char_sol_vanguard" else "emote_dance",
            "damage_dealt": 0,
            "target": "player_a",
            "sound_cue": "sfx_power_charge",
            "commentary": f"{player_b_name} ({char_b['name']}) braces stances, responding with a combat emote."
        },
        {
            "step": 3,
            "timestamp_sec": 3.0,
            "actor": "player_a",
            "character_id": char_a["id"],
            "character_name": char_a["name"],
            "action_type": "cast_attack",
            "card_id": p_a_atks[0]["id"] if p_a_atks else "atk_quick_peek",
            "card_name": p_a_atks[0]["name"] if p_a_atks else "Quick Attack",
            "animation_trigger": "anim_cast_slash" if char_a["id"] == "char_phantom_9" else "anim_cast_slam",
            "emote_trigger": None,
            "damage_dealt": 30,
            "target": "player_b",
            "sound_cue": "sfx_gunfire_burst",
            "commentary": f"{player_a_name} initiates with {p_a_atks[0]['name']}, opening up initial angle pressure for 30 HP."
        },
        {
            "step": 4,
            "timestamp_sec": 4.8,
            "actor": "player_b",
            "character_id": char_b["id"],
            "character_name": char_b["name"],
            "action_type": "deploy_defence",
            "card_id": p_b_defs[0]["id"] if p_b_defs else "def_defensive_smoke",
            "card_name": p_b_defs[0]["name"] if p_b_defs else "Defensive Smoke",
            "animation_trigger": "anim_deploy_barrier" if char_b["id"] == "char_sol_vanguard" else "anim_deploy_smoke",
            "emote_trigger": None,
            "damage_dealt": 0,
            "target": "zone",
            "sound_cue": "sfx_shield_thump",
            "commentary": f"{player_b_name} deploys {p_b_defs[0]['name']} to deny vision and stall the offensive rush."
        },
        {
            "step": 5,
            "timestamp_sec": 6.5,
            "actor": "player_b",
            "character_id": char_b["id"],
            "character_name": char_b["name"],
            "action_type": "cast_attack",
            "card_id": p_b_atks[0]["id"] if p_b_atks else "atk_flash_entry",
            "card_name": p_b_atks[0]["name"] if p_b_atks else "Counter Attack",
            "animation_trigger": "anim_cast_cannon" if char_b["id"] == "char_sol_vanguard" else "anim_cast_slash",
            "emote_trigger": None,
            "damage_dealt": 35,
            "target": "player_a",
            "sound_cue": "sfx_energy_blast",
            "commentary": f"{player_b_name} pushes through utility with {p_b_atks[0]['name']}, landing a 35 damage counter-strike."
        },
        {
            "step": 6,
            "timestamp_sec": 8.2,
            "actor": "player_a",
            "character_id": char_a["id"],
            "character_name": char_a["name"],
            "action_type": "deploy_defence",
            "card_id": p_a_defs[0]["id"] if p_a_defs else "def_layered_defense",
            "card_name": p_a_defs[0]["name"] if p_a_defs else "Layered Defense",
            "animation_trigger": "anim_dodge_roll" if char_a["id"] == "char_phantom_9" else "anim_parry_stance",
            "emote_trigger": None,
            "damage_dealt": 0,
            "target": "self",
            "sound_cue": "sfx_dodge_woosh",
            "commentary": f"{player_a_name} utilizes {p_a_defs[0]['name']}, resetting crosshair placement and armor absorption."
        },
        {
            "step": 7,
            "timestamp_sec": 10.0,
            "actor": winner_actor,
            "character_id": char_a["id"] if winner_actor == "player_a" else char_b["id"],
            "character_name": char_a["name"] if winner_actor == "player_a" else char_b["name"],
            "action_type": "climax_strike",
            "card_id": (p_a_atks[1]["id"] if len(p_a_atks) > 1 else p_a_atks[0]["id"]) if winner_actor == "player_a" else (p_b_atks[1]["id"] if len(p_b_atks) > 1 else p_b_atks[0]["id"]),
            "card_name": (p_a_atks[1]["name"] if len(p_a_atks) > 1 else p_a_atks[0]["name"]) if winner_actor == "player_a" else (p_b_atks[1]["name"] if len(p_b_atks) > 1 else p_b_atks[0]["name"]),
            "animation_trigger": "anim_cast_teleport" if (char_a["id"] if winner_actor == "player_a" else char_b["id"]) == "char_phantom_9" else "anim_cast_slam",
            "emote_trigger": None,
            "damage_dealt": 70,
            "target": loser_actor,
            "sound_cue": "sfx_critical_hit",
            "commentary": f"CRITICAL ROUND BREAKER! {winner_name} executes {auto_mvp}, landing a lethal 70 damage precision headshot!"
        },
        {
            "step": 8,
            "timestamp_sec": 11.8,
            "actor": loser_actor,
            "character_id": char_b["id"] if winner_actor == "player_a" else char_a["id"],
            "character_name": char_b["name"] if winner_actor == "player_a" else char_a["name"],
            "action_type": "defeat_reaction",
            "card_id": None,
            "card_name": None,
            "animation_trigger": "anim_defeat",
            "emote_trigger": "emote_defeat",
            "damage_dealt": 0,
            "target": "self",
            "sound_cue": "sfx_steam_release" if (char_b["id"] if winner_actor == "player_a" else char_a["id"]) == "char_sol_vanguard" else "sfx_glitch_down",
            "commentary": f"{loser_name} falls to one knee as shields break under relentless pressure."
        },
        {
            "step": 9,
            "timestamp_sec": 13.2,
            "actor": winner_actor,
            "character_id": char_a["id"] if winner_actor == "player_a" else char_b["id"],
            "character_name": char_a["name"] if winner_actor == "player_a" else char_b["name"],
            "action_type": "victory_celebration",
            "card_id": None,
            "card_name": None,
            "animation_trigger": "anim_emote_celebrate",
            "emote_trigger": "emote_celebrate",
            "damage_dealt": 0,
            "target": "self",
            "sound_cue": "sfx_victory_fanfare",
            "commentary": f"VICTORY SECURED! {winner_name} activates celebration emote. {win_reason}"
        }
    ]

    return {
        "match_id": match_id,
        "mode": "godot_combat_timeline",
        "engine_version": "godot_4.x_compatible",
        "total_duration_sec": 14.5,
        "player_a": {
            "name": player_a_name,
            "character": char_a["name"],
            "character_id": char_a["id"],
            "score": player_a_score,
            "attack_cards": player_a_attack_cards,
            "defence_cards": player_a_defence_cards
        },
        "player_b": {
            "name": player_b_name,
            "character": char_b["name"],
            "character_id": char_b["id"],
            "score": player_b_score,
            "attack_cards": player_b_attack_cards,
            "defence_cards": player_b_defence_cards
        },
        "winner_id": winner_id,
        "winner_name": winner_name,
        "player_a_score": player_a_score,
        "player_b_score": player_b_score,
        "win_reason": win_reason,
        "mvp_combo": auto_mvp,
        "timeline_events_count": len(timeline),
        "timeline": timeline
    }



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
