"""
================================================================================
ai/attack/attack_ai.py
================================================================================

PURPOSE OF THIS FILE:
---------------------
This file contains the complete, production-ready **ATTACK AI (LLM A)**.

WHAT IS THE ATTACK AI?
----------------------
In our 3-AI architecture:
- The Attack AI acts as the mind of the **Attacker** (e.g. Jett / Phoenix).
- It analyzes the attacker's status, available cards/abilities, and enemy intel.
- It proposes a legal, high-IQ tactical sequence for its turn (e.g. "Curveball Flash -> Push Site -> Vandal Rifle").
- It does NOT directly change HP (that is the Game Engine's job).
- It does NOT decide who wins (that is the Master Referee's job).

IMPORTANT DESIGN PRINCIPLE:
---------------------------
All cards, abilities, player stats, and game rules are supplied dynamically as inputs.
This means you can add 10, 100, or 1000 cards in the future without modifying this AI!

================================================================================
LIBRARIES EXPLAINED:
================================================================================
1. `typing` (List, Dict, Any, Optional):
   - Built into Python.
   - Provides type hints (e.g. `List[AttackAction]`) so you know what data types
     are expected, and allows Pydantic to validate them at runtime.

2. `pydantic` (BaseModel, Field):
   - What is it? Python's #1 data validation and serialization library.
   - `BaseModel`: Guarantees that any data created matches our strict schema.
   - `Field(...)`: Lets us define field descriptions, default values, and constraints (e.g. `ge=1`).
     These descriptions are automatically turned into JSON Schemas sent to the LLM.

3. `google.generativeai` (Google Gemini SDK):
   - Connects to Google's **FREE Gemini API** (`gemini-1.5-flash`).
   - Free tier available at https://aistudio.google.com/ with no credit card required.

4. `json` & `os`:
   - `json`: Formats prompt inputs and parses model outputs.
   - `os`: Reads the `GEMINI_API_KEY` from your environment.
================================================================================
"""

import os
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# ==============================================================================
# SECTION 1: DATA MODELS (Pydantic Schemas for AI Inputs & Outputs)
# ==============================================================================

class AttackAction(BaseModel):
    """
    Represents ONE single attack or ability action chosen by the AI.
    
    Why use Pydantic here?
    - If the AI returns a string for 'order' (like "first"), Pydantic will catch the bug!
    - Enforces that card_id, target, order, and reason are always provided.
    """

    card_id: str = Field(
        ...,
        description="ID of the card/weapon/ability being used (e.g. 'vandal_rifle', 'curveball_flash')."
    )

    action_type: str = Field(
        default="attack",
        description="Action category: 'attack', 'use_ability', 'move', or 'plant_spike'."
    )

    target: str = Field(
        ...,
        description="Target of this action: enemy player ID ('player_b') or map zone ('a_site')."
    )

    order: int = Field(
        ...,
        ge=1,
        description="Order of execution in the sequence (1 = first action, 2 = second, etc.)."
    )

    reason: str = Field(
        ...,
        description="Short tactical reasoning explaining why this action was selected."
    )


class AttackPlan(BaseModel):
    """
    The complete structured response returned by the Attack AI for its turn.
    
    Contains:
    - sequence: Ordered list of AttackActions.
    - strategy_summary: Overall high-level tactical objective.
    """

    sequence: List[AttackAction] = Field(
        ...,
        description="Chronological sequence of tactical actions proposed for this turn."
    )

    strategy_summary: str = Field(
        ...,
        description="Summary of the overall attack strategy for this turn."
    )


# ==============================================================================
# SECTION 2: PROMPT BUILDER (Formatting the AI's Brain Context)
# ==============================================================================

def build_attack_prompt(
    attacker: Dict[str, Any],
    defender_intel: Dict[str, Any],
    available_cards: List[Dict[str, Any]],
    game_rules: Optional[Dict[str, Any]] = None
) -> str:
    """
    Constructs the prompt sent to the LLM.

    WHY WE DO NOT HARD-CODE CARDS:
    ------------------------------
    We pass the complete card database and player states into the prompt dynamically.
    Later, you can load cards from a database or JSON file without changing this code.
    """

    # Generate the exact JSON schema so the LLM knows how to format its output
    schema_json = json.dumps(AttackPlan.model_json_schema(), indent=2)

    prompt = f"""
You are the ATTACK STRATEGIST & DUELIST AI for a competitive 1v1 tactical card battle game.
You control the ATTACKER.

YOUR OBJECTIVE:
--------------
Analyze the current match situation and construct the strongest possible legal attack sequence.

ATTACKER STATUS (You):
----------------------
{json.dumps(attacker, indent=2)}

DEFENDER INTEL (Opponent information perceived through Fog of War):
-------------------------------------------------------------------
{json.dumps(defender_intel, indent=2)}

AVAILABLE CARDS / WEAPONS / ABILITIES:
--------------------------------------
{json.dumps(available_cards, indent=2)}

GAME RULES:
-----------
{json.dumps(game_rules or {}, indent=2)}

STRICT OPERATIONAL RULES:
-------------------------
1. Use ONLY card IDs provided in 'AVAILABLE CARDS'.
2. Never invent non-existent card IDs or abilities.
3. Never invent damage numbers (damage is calculated by the game engine).
4. Do NOT modify HP directly.
5. Do NOT decide the winner.
6. A player can only use cards where cooldown is 0 and energy is sufficient.
7. Sequence actions smartly (e.g. Flash utility first -> then Weapon Attack).
8. Return ONLY valid JSON matching this schema:

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

    HOW TO GET YOUR FREE API KEY:
    -----------------------------
    1. Visit https://aistudio.google.com/
    2. Click "Get API Key" (100% free tier, generous rate limits, no credit card).
    3. In your terminal run: export GEMINI_API_KEY="your_api_key_here"

    OFFLINE FALLBACK:
    -----------------
    If GEMINI_API_KEY is not set, this function prints a helpful notice and uses
    an intelligent offline tactical simulator so you can test immediately!
    """

    key = api_key or os.getenv("GEMINI_API_KEY")

    if key:
        try:
            import google.generativeai as genai
            
            # Configure the official Google Generative AI SDK
            genai.configure(api_key=key)
            
            # Use 'gemini-1.5-flash' (fastest, high intelligence, completely free tier)
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.2
                }
            )

            response = model.generate_content(prompt)
            raw_text = response.text.strip()

            # Clean markdown code fences if model returned ```json ... ```
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            elif raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]

            return json.loads(raw_text.strip())

        except Exception as e:
            print(f"\n[⚠️ GEMINI API NOTICE]: {e}")
            print("[INFO] Falling back to built-in tactical simulator.\n")
    else:
        print("\n[ℹ️ NOTE]: GEMINI_API_KEY not found. Using offline tactical simulator.")
        print("          (To use live Free Gemini AI: export GEMINI_API_KEY=\"your_key_from_aistudio.google.com\")\n")

    return _generate_mock_attack_response(available_cards or [])


def _generate_mock_attack_response(available_cards: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Intelligent tactical fallback simulator.
    Uses ONLY the exact cards available in the attacker's hand.
    """
    avail_ids = {c["id"]: c for c in available_cards}
    sequence = []
    order = 1

    # 1. Use Utility/Flash/Shock ability first if present
    for cid in ["curveball_flash", "shock_dart", "paranoia_blind"]:
        if cid in avail_ids:
            card = avail_ids[cid]
            sequence.append({
                "card_id": cid,
                "action_type": "use_ability",
                "target": "a_site",
                "order": order,
                "reason": f"Deploy {card.get('name', cid)} to disrupt enemy positions on site."
            })
            order += 1
            break

    # 2. Use Primary Weapon Attack
    weapon_found = False
    for cid in ["vandal_rifle", "phantom_rifle", "blade_storm"]:
        if cid in avail_ids:
            card = avail_ids[cid]
            sequence.append({
                "card_id": cid,
                "action_type": "attack",
                "target": "player_b",
                "order": order,
                "reason": f"Engage target using {card.get('name', cid)} with optimal crosshair placement."
            })
            order += 1
            weapon_found = True
            break

    # If no recognized combo, sequence remaining available cards
    if not sequence:
        for card in available_cards:
            sequence.append({
                "card_id": card["id"],
                "action_type": "attack" if card.get("type") == "damage" else "use_ability",
                "target": "player_b",
                "order": order,
                "reason": f"Execute action with {card.get('name', card['id'])}."
            })
            order += 1

    if not sequence:
        sequence.append({
            "card_id": "classic_sidearm",
            "action_type": "attack",
            "target": "player_b",
            "order": 1,
            "reason": "Engage target with standard sidearm."
        })

    return {
        "sequence": sequence,
        "strategy_summary": "High-IQ tactical entry: Lead with tactical utility before executing lethal weapon duel."
    }


# ==============================================================================
# SECTION 4: VALIDATION (Never Trust the Model Blindly)
# ==============================================================================

def validate_attack_plan(
    plan: AttackPlan,
    attacker: Dict[str, Any],
    available_cards: List[Dict[str, Any]]
) -> AttackPlan:
    """
    Validates that the AI's proposal is strictly legal under game rules:
    1. Did the AI try to use a non-existent/invented card?
    2. Is the card currently on cooldown?
    3. Are execution orders positive integers?

    If validation fails, an error is raised to prevent game corruption.
    """

    # Build set of all legal card IDs
    valid_card_ids = {card["id"] for card in available_cards}
    valid_card_ids.add("classic_sidearm")
    valid_card_ids.add("spike_bomb")

    # Attacker's active cooldowns
    cooldowns = attacker.get("cooldowns", {})

    for action in plan.sequence:
        # Rule 1: Check card exists
        if action.card_id not in valid_card_ids:
            raise ValueError(
                f"[VALIDATION ERROR] AI attempted to use illegal/unknown card: '{action.card_id}'"
            )

        # Rule 2: Check card cooldown
        if cooldowns.get(action.card_id, 0) > 0:
            raise ValueError(
                f"[VALIDATION ERROR] AI attempted to use card on cooldown: '{action.card_id}' "
                f"({cooldowns[action.card_id]} turns remaining)"
            )

        # Rule 3: Check action order
        if action.order < 1:
            raise ValueError(
                f"[VALIDATION ERROR] Action order must be >= 1, received: {action.order}"
            )

    return plan


# ==============================================================================
# SECTION 5: MAIN GENERATOR FUNCTION
# ==============================================================================

def generate_attack_plan(
    attacker: Dict[str, Any],
    defender_intel: Dict[str, Any],
    available_cards: List[Dict[str, Any]],
    game_rules: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None
) -> AttackPlan:
    """
    Main entrypoint used by your game backend.

    FLOW:
        Attacker & Defender Data
                 ↓
            Build Prompt
                 ↓
        Call Free Gemini LLM
                 ↓
        Parse into AttackPlan Schema
                 ↓
        Validate Rules & Cooldowns
                 ↓
        Return Validated Attack Plan
    """

    # 1. Build prompt
    prompt = build_attack_prompt(
        attacker=attacker,
        defender_intel=defender_intel,
        available_cards=available_cards,
        game_rules=game_rules
    )

    # 2. Call LLM
    raw_response = call_llm(prompt, available_cards=available_cards, api_key=api_key)

    # 3. Convert raw JSON into verified Pydantic model
    plan = AttackPlan.model_validate(raw_response)

    # 4. Strict domain validation
    plan = validate_attack_plan(
        plan=plan,
        attacker=attacker,
        available_cards=available_cards
    )

    return plan


# ==============================================================================
# SECTION 6: STANDALONE RUNNER / DEMONSTRATION
# ==============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print(" 🚀 RUNNING ATTACK AI (LLM A) DEMONSTRATION")
    print("=" * 80)

    # Sample Attacker (Jett)
    sample_attacker = {
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

    # Sample Defender Intel (Fog of War)
    sample_defender_intel = {
        "visible": True,
        "enemy_id": "player_b",
        "enemy_name": "Omen",
        "enemy_known_zone": "a_site",
        "intel_summary": "Enemy Omen spotted holding angle on A Site!"
    }

    # Sample Card Database
    sample_cards = [
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
        },
        {
            "id": "tailwind_dash",
            "name": "Tailwind Dash",
            "type": "mobility",
            "base_damage": 0,
            "energy_cost": 20,
            "cooldown_turns": 2,
            "description": "Quick dash to reposition across sightlines."
        }
    ]

    # Sample Game Rules
    sample_rules = {
        "round_turn_limit": 8,
        "fog_of_war_enabled": True
    }

    print("\n[STEP 1] Generating Attack Plan via Attack AI...")
    result_plan = generate_attack_plan(
        attacker=sample_attacker,
        defender_intel=sample_defender_intel,
        available_cards=sample_cards,
        game_rules=sample_rules
    )

    print("-" * 80)
    print(" 🎯 ATTACK AI OUTPUT RECEIVED & VALIDATED:")
    print("-" * 80)
    print(f"Strategy Summary: {result_plan.strategy_summary}\n")
    print("Attack Sequence:")
    for action in result_plan.sequence:
        print(f"  [{action.order}] Action: {action.action_type.upper():12} | Card: {action.card_id:16} | Target: {action.target}")
        print(f"      Reason: \"{action.reason}\"")

    print("\n" + "=" * 80)
    print(" ✅ Attack AI is completely functional and ready!")
    print("=" * 80 + "\n")
