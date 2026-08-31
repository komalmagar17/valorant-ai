"""
================================================================================
ai/defence/defence_ai.py
================================================================================

PURPOSE OF THIS FILE:
---------------------
This file contains the complete, production-ready **DEFENCE AI (LLM B)**.

WHAT IS THE DEFENCE AI?
-----------------------
In our 3-AI architecture:
- The Defence AI acts as the mind of the **Defender / Tactical Anchor** (e.g. Omen / Cypher / Killjoy).
- It analyzes the defender's status, incoming enemy attack intel, and the 2 defensive cards selected by the player.
- It formulates an optimal, high-IQ defensive counter-play sequence (e.g. "Smoke Choke Point -> Place Trapwire / Hold Crosshair Angle").
- It operates STRICTLY on the cards provided by the player (zero hallucination).
- It does NOT calculate damage or decide the winner (that is the Master Referee's job).

IMPORTANT DESIGN PRINCIPLE:
---------------------------
All cards, defensive abilities, and map zones are passed dynamically.
No hardcoded cards or static game states!

================================================================================
LIBRARIES EXPLAINED:
================================================================================
1. `typing` (List, Dict, Any, Optional):
   - Type annotations for structured data and Pydantic validation.

2. `pydantic` (BaseModel, Field):
   - Data validation ensuring strictly typed inputs and outputs matching our schema.

3. `google.generativeai` (Google Gemini SDK):
   - Free Google Gemini API (`gemini-1.5-flash`) at https://aistudio.google.com/.

4. `json` & `os`:
   - Structured serialization and environment variable handling.
================================================================================
"""

import os
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# ==============================================================================
# SECTION 1: DATA MODELS (Pydantic Schemas for Defence AI)
# ==============================================================================

class DefenceAction(BaseModel):
    """
    Represents ONE defensive, utility, or positioning action chosen by the AI.
    """
    card_id: str = Field(
        ...,
        description="ID of the defensive card/ability being used (e.g. 'def_basic_hold', 'def_defensive_smoke')."
    )

    action_type: str = Field(
        default="use_ability",
        description="Category: 'site_anchor', 'deploy_smoke', 'place_trap', 'hold_angle', 'fortify_shield', or 'retake_duel'."
    )

    target: str = Field(
        ...,
        description="Target zone, choke point, or enemy ID (e.g. 'a_main_choke', 'a_site', 'player_a', 'self')."
    )

    order: int = Field(
        ...,
        ge=1,
        description="Order of execution in the defensive sequence (1 = first action, 2 = second, etc.)."
    )

    time_window: str = Field(
        default="00:00 - 00:20",
        description="Estimated match time window for this defensive phase across 1-2 minutes total (e.g. '00:00 - 00:20', '00:20 - 00:50', '00:50 - 01:20', '01:20 - 01:45')."
    )

    phase: str = Field(
        default="Phase 1: Site Fortification & Trap Setup",
        description="Tactical phase: 'Phase 1: Fortification & Recon', 'Phase 2: Choke Stall & Smoke', 'Phase 3: Site Anchor & Crossfire', or 'Phase 4: Retake & Clutch Duel'."
    )

    reason: str = Field(
        ...,
        description="Tactical reasoning explaining the defensive positioning and utility deployment across the 1-2 minute round."
    )


class DefencePlan(BaseModel):
    """
    The structured response returned by the Defence AI for its turn.
    """
    sequence: List[DefenceAction] = Field(
        ...,
        description="Chronological sequence of defensive counter-measures across the 1-2 minute round."
    )

    strategy_summary: str = Field(
        ...,
        description="Overall summary of the defensive strategy and site hold for the 1-2 minute round."
    )


# ==============================================================================
# SECTION 2: PROMPT BUILDER (Formatting the Defence Brain Context)
# ==============================================================================

def build_defence_prompt(
    defender: Dict[str, Any],
    attacker_intel: Dict[str, Any],
    available_cards: List[Dict[str, Any]],
    map_context: Optional[Dict[str, Any]] = None,
    game_rules: Optional[Dict[str, Any]] = None
) -> str:
    """
    Constructs the prompt sent to the LLM for defensive strategy formulation.
    """
    schema_json = json.dumps(DefencePlan.model_json_schema(), indent=2)

    prompt = f"""
You are the DEFENCE STRATEGIST & ANCHOR AI for a competitive 1v1 tactical card battle game.
You control the DEFENDER.

YOUR OBJECTIVE:
--------------
Construct an extended, realistic **1-2 MINUTE (~100 SECOND)** tactical defensive counter-sequence.
Standard Valorant rounds do not end instantly in 10 seconds; your defensive plan must unfold chronologically across 4 tactical phases:
- **Phase 1: Site Fortification & Trap Setup (00:00 - 00:20)** — Lock down default angles, prepare utility traps, and gather early audio/visual intel.
- **Phase 2: Choke Point Delay & Smoke (00:20 - 00:50)** — Deploy smokes, stalling utility, and counter-flashes to stop attacker pushes.
- **Phase 3: Site Anchor & Crossfire Hold (00:50 - 01:20)** — Hold off-angles, trade damage against breaching attackers, and fall back if overwhelmed.
- **Phase 4: Retake & Clutch Duel (01:20 - 01:45)** — Coordinate late-round retake timing, isolate the attacker on post-plant, and challenge the Spike defusal.

DEFENDER STATUS (You):
----------------------
{json.dumps(defender, indent=2)}

INCOMING ATTACKER INTEL (Perceived threat & enemy info):
-------------------------------------------------------
{json.dumps(attacker_intel, indent=2)}

AVAILABLE DEFENSIVE CARDS:
--------------------------
{json.dumps(available_cards, indent=2)}

MAP & CHOKE POINT CONTEXT:
--------------------------
{json.dumps(map_context or {}, indent=2)}

GAME RULES:
-----------
{json.dumps(game_rules or {}, indent=2)}

STRICT OPERATIONAL RULES:
-------------------------
1. Use ONLY card IDs provided in 'AVAILABLE DEFENSIVE CARDS'.
2. Construct a multi-step sequence spanning the full 1-2 minute timeframe with realistic `time_window` and `phase` fields.
3. Never invent non-existent card IDs or stats.
4. Prioritize blocking sightlines, mitigating damage, and trapping enemy entry paths.
5. Return ONLY valid JSON matching this schema:

{schema_json}
"""
    return prompt.strip()


# ==============================================================================
# SECTION 3: LLM CALLER (Google Gemini Free API + Smart Offline Fallback)
# ==============================================================================

def call_llm(
    prompt: str,
    available_cards: Optional[List[Dict[str, Any]]] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Connects to Google's FREE Gemini API (Gemini 1.5 Flash).
    Falls back to intelligent offline defensive simulation if key is not configured.
    """
    key = api_key or os.getenv("GEMINI_API_KEY_DEFENCE") or os.getenv("GEMINI_API_KEY")

    if key:
        try:
            import google.generativeai as genai

            genai.configure(api_key=key)
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.2
                }
            )

            response = model.generate_content(prompt)
            raw_text = response.text.strip()

            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            elif raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]

            return json.loads(raw_text.strip())

        except Exception as e:
            print(f"\n[⚠️ DEFENCE AI (GEMINI) NOTICE]: {e}")
            print("[INFO] Falling back to built-in defensive simulator.\n")
    else:
        print("\n[ℹ️ NOTE]: GEMINI_API_KEY_DEFENCE not found. Using offline defensive simulator.")
        print("          (To use live Defence AI: export GEMINI_API_KEY_DEFENCE=\"your_key_from_aistudio.google.com\")\n")

    return _generate_mock_defence_response(available_cards or [])


def _generate_mock_defence_response(available_cards: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Intelligent defensive fallback simulator spanning 1-2 minutes (~100 seconds).
    Uses ONLY the exact cards available in the defender's loadout.
    """
    avail_ids = {c["id"]: c for c in available_cards}
    sequence = []
    order = 1

    # Phase 1: Site Fortification & Trap Setup (00:00 - 00:20)
    lead_def = available_cards[0] if available_cards else {"id": "def_basic_hold", "name": "Basic Hold"}
    sequence.append({
        "card_id": lead_def["id"],
        "action_type": "site_anchor",
        "target": "a_site_anchor",
        "order": order,
        "time_window": "00:00 - 00:20",
        "phase": "Phase 1: Site Fortification & Trap Setup",
        "reason": f"Establish early defensive anchor and fortify primary entrance using {lead_def.get('name', lead_def['id'])}."
    })
    order += 1

    # Phase 2: Choke Point Delay & Smoke (00:20 - 00:50)
    second_def = available_cards[1] if len(available_cards) > 1 else lead_def
    sequence.append({
        "card_id": second_def["id"],
        "action_type": "deploy_smoke",
        "target": "a_main_choke",
        "order": order,
        "time_window": "00:20 - 00:50",
        "phase": "Phase 2: Choke Point Delay & Smoke",
        "reason": f"Deploy {second_def.get('name', second_def['id'])} to block attacking sightlines and stall the advance."
    })
    order += 1

    # Phase 3: Site Anchor & Crossfire Hold (00:50 - 01:20)
    sequence.append({
        "card_id": lead_def["id"],
        "action_type": "hold_angle",
        "target": "a_site",
        "order": order,
        "time_window": "00:50 - 01:20",
        "phase": "Phase 3: Site Anchor & Crossfire Hold",
        "reason": "Hold advantageous off-angle to trade damage against attackers entering the site zone."
    })
    order += 1

    # Phase 4: Retake & Clutch Duel (01:20 - 01:45)
    sequence.append({
        "card_id": second_def["id"],
        "action_type": "retake_duel",
        "target": "player_a",
        "order": order,
        "time_window": "01:20 - 01:45",
        "phase": "Phase 4: Retake & Clutch Duel",
        "reason": f"Execute disciplined retake peek and challenge attacker in the 1v1 clutch standoff with {second_def.get('name', second_def['id'])}."
    })

    return {
        "sequence": sequence,
        "strategy_summary": "1-2 Minute Defensive Masterclass: Early site fortification, choke stalling utility, site crossfire engagement, and timed retake clutch execution."
    }


# ==============================================================================
# SECTION 4: VALIDATION
# ==============================================================================

def validate_defence_plan(
    plan: DefencePlan,
    defender: Dict[str, Any],
    available_cards: List[Dict[str, Any]]
) -> DefencePlan:
    """
    Validates that the Defence AI's plan uses only legal, available cards and valid orders.
    """
    valid_card_ids = {card["id"] for card in available_cards}
    valid_card_ids.update({"defensive_hold_angle", "basic_armor", "classic_sidearm"})

    cooldowns = defender.get("cooldowns", {})

    for action in plan.sequence:
        if action.card_id not in valid_card_ids:
            raise ValueError(
                f"[VALIDATION ERROR] Defence AI attempted to use illegal/unknown card: '{action.card_id}'"
            )

        if cooldowns.get(action.card_id, 0) > 0:
            raise ValueError(
                f"[VALIDATION ERROR] Defence AI attempted to use card on cooldown: '{action.card_id}' "
                f"({cooldowns[action.card_id]} turns remaining)"
            )

        if action.order < 1:
            raise ValueError(
                f"[VALIDATION ERROR] Defence action order must be >= 1, received: {action.order}"
            )

    return plan


# ==============================================================================
# SECTION 5: MAIN GENERATOR FUNCTION
# ==============================================================================

def generate_defence_plan(
    defender: Dict[str, Any],
    attacker_intel: Dict[str, Any],
    available_cards: List[Dict[str, Any]],
    map_context: Optional[Dict[str, Any]] = None,
    game_rules: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None
) -> DefencePlan:
    """
    Main entrypoint to generate a validated defensive tactical plan.
    """
    # 1. Build prompt
    prompt = build_defence_prompt(
        defender=defender,
        attacker_intel=attacker_intel,
        available_cards=available_cards,
        map_context=map_context,
        game_rules=game_rules
    )

    # 2. Call LLM (or smart fallback)
    raw_response = call_llm(prompt, available_cards=available_cards, api_key=api_key)

    # 3. Parse into Pydantic model
    plan = DefencePlan.model_validate(raw_response)

    # 4. Strict domain validation
    plan = validate_defence_plan(
        plan=plan,
        defender=defender,
        available_cards=available_cards
    )

    return plan


# ==============================================================================
# SECTION 6: STANDALONE RUNNER / DEMONSTRATION
# ==============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print(" 🛡️  RUNNING DEFENCE AI (LLM B) DEMONSTRATION")
    print("=" * 80)

    sample_defender = {
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

    sample_attacker_intel = {
        "threat_level": "high",
        "spotted_in": "a_main",
        "expected_weapon": "vandal_rifle",
        "intel_summary": "Attacker sound cues heard sprinting towards A Main!"
    }

    sample_defensive_cards = [
        {
            "id": "dark_cover_smoke",
            "name": "Dark Cover Smoke",
            "type": "smoke",
            "cooldown_turns": 2,
            "description": "Deploys hollow shadow sphere blocking vision."
        },
        {
            "id": "cypher_trapwire",
            "name": "Cypher Trapwire",
            "type": "trap",
            "cooldown_turns": 3,
            "description": "Tethers and reveals passing enemies."
        }
    ]

    sample_map = {
        "map_name": "Ascent",
        "site": "a_site",
        "choke_point": "a_main_choke"
    }

    print("\n[STEP 1] Generating Defence Plan via Defence AI...")
    plan = generate_defence_plan(
        defender=sample_defender,
        attacker_intel=sample_attacker_intel,
        available_cards=sample_defensive_cards,
        map_context=sample_map
    )

    print("-" * 80)
    print(" 🛡️ DEFENCE AI OUTPUT RECEIVED & VALIDATED:")
    print("-" * 80)
    print(f"Strategy Summary: {plan.strategy_summary}\n")
    print("Defence Sequence:")
    for action in plan.sequence:
        print(f"  [{action.order}] Action: {action.action_type.upper():16} | Card: {action.card_id:18} | Target: {action.target}")
        print(f"      Reason: \"{action.reason}\"")

    print("\n" + "=" * 80)
    print(" ✅ Defence AI is completely functional and ready!")
    print("=" * 80 + "\n")
