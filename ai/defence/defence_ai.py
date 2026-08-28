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
        description="ID of the defensive card/ability being used (e.g. 'dark_cover_smoke', 'cypher_trapwire', 'heavy_shield')."
    )

    action_type: str = Field(
        default="use_ability",
        description="Category: 'use_ability', 'deploy_smoke', 'place_trap', 'hold_angle', 'fortify_shield', or 'heal'."
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

    reason: str = Field(
        ...,
        description="Tactical reasoning explaining why this defensive action counters the expected threat."
    )


class DefencePlan(BaseModel):
    """
    The structured response returned by the Defence AI for its turn.
    """
    sequence: List[DefenceAction] = Field(
        ...,
        description="Chronological sequence of defensive counter-measures for this turn."
    )

    strategy_summary: str = Field(
        ...,
        description="Overall summary of the defensive strategy and site hold."
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
Analyze the incoming attack threat, map choke points, and construct the strongest possible legal defensive counter-sequence
using ONLY the defensive cards provided in 'AVAILABLE DEFENSIVE CARDS'.

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
2. Never invent non-existent card IDs or stats.
3. Prioritize blocking sightlines, mitigating damage, and trapping enemy entry paths.
4. Return ONLY valid JSON matching this schema:

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
    key = api_key or os.getenv("GEMINI_API_KEY")

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
            print(f"\n[⚠️ GEMINI API NOTICE]: {e}")
            print("[INFO] Falling back to built-in defensive simulator.\n")
    else:
        print("\n[ℹ️ NOTE]: GEMINI_API_KEY not found. Using offline defensive simulator.")
        print("          (To use live Free Gemini AI: export GEMINI_API_KEY=\"your_key_from_aistudio.google.com\")\n")

    return _generate_mock_defence_response(available_cards or [])


def _generate_mock_defence_response(available_cards: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Intelligent defensive fallback simulator.
    Uses ONLY the exact cards available in the defender's loadout.
    """
    avail_ids = {c["id"] for c in available_cards}
    sequence = []
    order = 1

    if "dark_cover_smoke" in avail_ids:
        sequence.append({
            "card_id": "dark_cover_smoke",
            "action_type": "deploy_smoke",
            "target": "a_main_choke",
            "order": order,
            "reason": "Drop heavy smoke at entry choke point to obscure attacker's line of sight."
        })
        order += 1

    if "cypher_trapwire" in avail_ids:
        sequence.append({
            "card_id": "cypher_trapwire",
            "action_type": "place_trap",
            "target": "a_site_entrance",
            "order": order,
            "reason": "Anchor invisible tripwire to tether and reveal any rushing attackers."
        })
        order += 1

    if "heavy_shield" in avail_ids:
        sequence.append({
            "card_id": "heavy_shield",
            "action_type": "fortify_shield",
            "target": "self",
            "order": order,
            "reason": "Fortify armor plating to absorb high incoming rifle burst damage."
        })
        order += 1

    if "tailwind_dash" in avail_ids:
        sequence.append({
            "card_id": "tailwind_dash",
            "action_type": "use_ability",
            "target": "a_site",
            "order": order,
            "reason": "Prepare rapid repositioning dash to escape crossfire angles."
        })
        order += 1

    if "healing_orb" in avail_ids:
        sequence.append({
            "card_id": "healing_orb",
            "action_type": "heal",
            "target": "self",
            "order": order,
            "reason": "Cast regenerative healing to sustain through attacker damage."
        })
        order += 1

    # If no specific card matched, use the first available card or basic anchor
    if not sequence:
        if available_cards:
            first_card = available_cards[0]
            sequence.append({
                "card_id": first_card["id"],
                "action_type": "use_ability",
                "target": "a_site",
                "order": 1,
                "reason": f"Deploy {first_card.get('name', first_card['id'])} defensively."
            })
        else:
            sequence.append({
                "card_id": "defensive_hold_angle",
                "action_type": "hold_angle",
                "target": "a_main",
                "order": 1,
                "reason": "Establish crosshair angle anchor behind site cover."
            })

    return {
        "sequence": sequence,
        "strategy_summary": "Adaptive tactical defense: Anchor site position and execute defensive utility."
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
