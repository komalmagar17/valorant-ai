"""
================================================================================
data/cards.py
================================================================================

Complete registry of all 120 Tactical Cards:
- 60 Attack Cards
- 60 Defence Cards

DESIGN PRINCIPLE:
-----------------
Internal mechanics contain tactical power & protection values used by the AI engine.
The public API method `get_public_cards()` strips internal tier/power labels so
players see only the clean card names, tactical descriptions, and categories.
================================================================================
"""

from typing import Dict, Any, List, Optional
import re


def _slugify(name: str) -> str:
    """Helper to convert card name to clean unique ID."""
    clean = re.sub(r'[^a-zA-Z0-9\s]', '', name)
    return clean.strip().lower().replace(' ', '_')


# ==============================================================================
# SECTION 1: ALL 60 ATTACK CARDS
# ==============================================================================

RAW_ATTACK_CARDS = [
    # Tier 1 (1-15)
    {"num": 1, "tier": 1, "name": "Quick Peek", "power": 15, "description": "Briefly challenge an angle to gather information and potentially tag an opponent."},
    {"num": 2, "tier": 1, "name": "Double Peek", "power": 20, "description": "Two attackers challenge the same angle together, making it harder for the defender to isolate one player."},
    {"num": 3, "tier": 1, "name": "Contact Push", "power": 20, "description": "Attackers move quietly and only commit when they reach close range."},
    {"num": 4, "tier": 1, "name": "Lane Pressure", "power": 18, "description": "Apply pressure to one lane without fully committing to the site."},
    {"num": 5, "tier": 1, "name": "Utility Clear", "power": 22, "description": "Use basic utility to force an opponent away from a common position."},
    {"num": 6, "tier": 1, "name": "Choke Pressure", "power": 20, "description": "Occupy an important entrance and force defenders to give up space."},
    {"num": 7, "tier": 1, "name": "Slow Advance", "power": 18, "description": "Gradually take territory while checking positions."},
    {"num": 8, "tier": 1, "name": "Angle Isolation", "power": 23, "description": "Use positioning or utility to reduce the number of angles that must be checked."},
    {"num": 9, "tier": 1, "name": "Fake Pressure", "power": 15, "description": "Make enough noise/utility to suggest an attack without fully committing."},
    {"num": 10, "tier": 1, "name": "Probe Attack", "power": 20, "description": "Small initial attack designed primarily to discover the defensive setup."},
    {"num": 11, "tier": 1, "name": "Controlled Entry", "power": 25, "description": "Enter slowly with teammates covering different angles."},
    {"num": 12, "tier": 1, "name": "Side Pressure", "power": 22, "description": "Pressure a secondary route to make the defense uncomfortable."},
    {"num": 13, "tier": 1, "name": "Early Map Control", "power": 24, "description": "Secure a small area before attempting the main attack."},
    {"num": 14, "tier": 1, "name": "Corner Clear", "power": 17, "description": "Systematically clear common hiding positions."},
    {"num": 15, "tier": 1, "name": "Retreat-and-Reattack", "power": 21, "description": "Make a small commitment, withdraw, then attack again from another timing."},

    # Tier 2 (16-30)
    {"num": 16, "tier": 2, "name": "Flash Entry", "power": 35, "description": "Use a blinding effect or distraction before entering an area."},
    {"num": 17, "tier": 2, "name": "Smoke Entry", "power": 32, "description": "Block important defensive sightlines before pushing."},
    {"num": 18, "tier": 2, "name": "Stun Entry", "power": 38, "description": "Disrupt defenders before attempting to take their position."},
    {"num": 19, "tier": 2, "name": "Recon Push", "power": 34, "description": "Gather information immediately before committing to the attack."},
    {"num": 20, "tier": 2, "name": "Utility Combo", "power": 42, "description": "Combine two pieces of utility to make the entry harder to stop."},
    {"num": 21, "tier": 2, "name": "Two-Lane Push", "power": 40, "description": "Attack through two nearby routes simultaneously."},
    {"num": 22, "tier": 2, "name": "Delayed Push", "power": 37, "description": "One group enters first while another group waits for the right timing."},
    {"num": 23, "tier": 2, "name": "Split Pressure", "power": 43, "description": "Attackers divide their pressure between two routes."},
    {"num": 24, "tier": 2, "name": "Mid Pressure", "power": 39, "description": "Control the central route to threaten multiple areas."},
    {"num": 25, "tier": 2, "name": "Rotation Bait", "power": 35, "description": "Create pressure on one side to encourage defenders to rotate away."},
    {"num": 26, "tier": 2, "name": "Fake Execute", "power": 33, "description": "Use substantial utility but intentionally delay the actual commitment."},
    {"num": 27, "tier": 2, "name": "Site Isolation", "power": 45, "description": "Block defensive sightlines and isolate part of the site."},
    {"num": 28, "tier": 2, "name": "Crossfire Break", "power": 44, "description": "Coordinate movement specifically to break a defensive crossfire."},
    {"num": 29, "tier": 2, "name": "Lurk Pressure", "power": 36, "description": "One player quietly pressures another area while the team creates noise elsewhere."},
    {"num": 30, "tier": 2, "name": "Timing Push", "power": 40, "description": "Wait for defensive utility or abilities to expire before committing."},

    # Tier 3 (31-45)
    {"num": 31, "tier": 3, "name": "Full Site Execute", "power": 58, "description": "Team commits together with coordinated utility and positioning."},
    {"num": 32, "tier": 3, "name": "Three-Lane Execute", "power": 62, "description": "Apply simultaneous pressure from three routes."},
    {"num": 33, "tier": 3, "name": "A-Split Style Execute", "power": 60, "description": "One group attacks from the main route while another attacks from a secondary route."},
    {"num": 34, "tier": 3, "name": "B-Split Style Execute", "power": 60, "description": "Same concept as a split attack directed toward another objective area."},
    {"num": 35, "tier": 3, "name": "Mid-to-Site Split", "power": 64, "description": "Gain central control and use it to attack the site from multiple directions."},
    {"num": 36, "tier": 3, "name": "Flash-Smoke Execute", "power": 61, "description": "Combine vision denial and disruption before entering."},
    {"num": 37, "tier": 3, "name": "Recon-Flash Execute", "power": 57, "description": "Locate defenders and immediately disrupt their positions."},
    {"num": 38, "tier": 3, "name": "Stun-Smoke Execute", "power": 59, "description": "Reduce defender effectiveness while blocking their vision."},
    {"num": 39, "tier": 3, "name": "Delayed Split", "power": 63, "description": "Start an attack from one side, then introduce the second attack at an unexpected moment."},
    {"num": 40, "tier": 3, "name": "Contact Execute", "power": 55, "description": "Minimize early noise before suddenly committing as a group."},
    {"num": 41, "tier": 3, "name": "Rotation Trap", "power": 58, "description": "Force defenders to rotate and then attack the space they abandoned."},
    {"num": 42, "tier": 3, "name": "Double Fake", "power": 52, "description": "Threaten two locations before committing to the actual target."},
    {"num": 43, "tier": 3, "name": "Lurk + Execute", "power": 60, "description": "A hidden attacker creates pressure behind the expected defensive setup."},
    {"num": 44, "tier": 3, "name": "Utility Drain", "power": 56, "description": "Repeatedly pressure defenders until their defensive resources are reduced."},
    {"num": 45, "tier": 3, "name": "Late Execute", "power": 65, "description": "Hold the attack until defenders have fewer resources and less time to respond."},

    # Tier 4 (46-60)
    {"num": 46, "tier": 4, "name": "Full-Team Rush", "power": 78, "description": "Almost the entire attacking team commits rapidly toward one objective."},
    {"num": 47, "tier": 4, "name": "Perfect Split", "power": 82, "description": "Coordinated groups attack from multiple directions at nearly the same time."},
    {"num": 48, "tier": 4, "name": "Triple-Side Execute", "power": 85, "description": "Pressure arrives from three separate directions simultaneously."},
    {"num": 49, "tier": 4, "name": "Full Utility Execute", "power": 80, "description": "The team spends a large portion of its resources to overwhelm the defense."},
    {"num": 50, "tier": 4, "name": "Multi-Fake Execute", "power": 76, "description": "Several false threats are created before the actual attack."},
    {"num": 51, "tier": 4, "name": "Rotation Punish", "power": 79, "description": "Attackers deliberately manipulate defender rotations and immediately exploit the weak area."},
    {"num": 52, "tier": 4, "name": "Perfect Timing Attack", "power": 84, "description": "Attack begins exactly when defensive resources are unavailable or recovering."},
    {"num": 53, "tier": 4, "name": "Information Overload", "power": 81, "description": "Multiple simultaneous threats make it difficult for defenders to determine the real attack."},
    {"num": 54, "tier": 4, "name": "Lurk + Triple Push", "power": 83, "description": "A hidden player combines with a coordinated multi-route attack."},
    {"num": 55, "tier": 4, "name": "Resource Exhaustion Execute", "power": 77, "description": "Attackers deliberately drain defensive resources before making the final commitment."},
    {"num": 56, "tier": 4, "name": "Adaptive Execute", "power": 86, "description": "Attack begins with one plan but changes immediately based on defensive reactions."},
    {"num": 57, "tier": 4, "name": "Full Map Pressure", "power": 80, "description": "Attackers threaten multiple areas simultaneously, forcing the defense to spread out."},
    {"num": 58, "tier": 4, "name": "Counter-Rotation Attack", "power": 78, "description": "Attackers deliberately wait for defensive movement and attack during the rotation."},
    {"num": 59, "tier": 4, "name": "Timed Final Execute", "power": 88, "description": "A carefully coordinated final push uses timing, positioning and remaining resources together."},
    {"num": 60, "tier": 4, "name": "Master Execute", "power": 92, "description": "A highly coordinated combination of split pressure, utility, timing and deception."}
]


# ==============================================================================
# SECTION 2: ALL 60 DEFENCE CARDS
# ==============================================================================

RAW_DEFENCE_CARDS = [
    # Tier 1 (1-15)
    {"num": 1, "tier": 1, "name": "Basic Hold", "protection": 15, "description": "Stay in position and defend the expected entrance."},
    {"num": 2, "tier": 1, "name": "Angle Hold", "protection": 20, "description": "Maintain an advantageous angle against approaching attackers."},
    {"num": 3, "tier": 1, "name": "Double Hold", "protection": 22, "description": "Two defenders cover the same important area."},
    {"num": 4, "tier": 1, "name": "Passive Hold", "protection": 18, "description": "Avoid unnecessary fights and preserve position."},
    {"num": 5, "tier": 1, "name": "Choke Hold", "protection": 21, "description": "Defend an important entrance into the area."},
    {"num": 6, "tier": 1, "name": "Early Information", "protection": 17, "description": "Gather information before the attackers commit."},
    {"num": 7, "tier": 1, "name": "Position Change", "protection": 20, "description": "Change position after being spotted to avoid being predictable."},
    {"num": 8, "tier": 1, "name": "Close Defense", "protection": 19, "description": "Hold a position where attackers must get close before challenging."},
    {"num": 9, "tier": 1, "name": "Long Defense", "protection": 22, "description": "Maintain distance and make the attackers cross open space."},
    {"num": 10, "tier": 1, "name": "Basic Retreat", "protection": 16, "description": "Give up some space rather than taking an unfavorable fight."},
    {"num": 11, "tier": 1, "name": "Utility Stall", "protection": 24, "description": "Use a small amount of utility to slow the attack."},
    {"num": 12, "tier": 1, "name": "Crossfire Setup", "protection": 25, "description": "Two defenders cover each other from different angles."},
    {"num": 13, "tier": 1, "name": "Trap Position", "protection": 23, "description": "Place a defender or defensive resource where attackers are likely to enter."},
    {"num": 14, "tier": 1, "name": "Flank Watch", "protection": 18, "description": "Keep one player watching for attackers coming from behind."},
    {"num": 15, "tier": 1, "name": "Reposition Defense", "protection": 21, "description": "Move to a different defensive location after detecting pressure."},

    # Tier 2 (16-30)
    {"num": 16, "tier": 2, "name": "Defensive Smoke", "protection": 34, "description": "Block an attacking route and delay their advance."},
    {"num": 17, "tier": 2, "name": "Flash Retardation", "protection": 36, "description": "Disrupt attackers as they attempt to enter."},
    {"num": 18, "tier": 2, "name": "Stun Defense", "protection": 38, "description": "Reduce attacking effectiveness before they reach the objective."},
    {"num": 19, "tier": 2, "name": "Recon Defense", "protection": 33, "description": "Gather information about the attacking formation."},
    {"num": 20, "tier": 2, "name": "Utility Combination", "protection": 42, "description": "Combine multiple defensive resources to stop an entry."},
    {"num": 21, "tier": 2, "name": "Crossfire Defense", "protection": 43, "description": "Coordinate two or more defenders to punish an entry."},
    {"num": 22, "tier": 2, "name": "Choke Stall", "protection": 39, "description": "Repeatedly delay attackers at an important entrance."},
    {"num": 23, "tier": 2, "name": "Early Rotation", "protection": 35, "description": "Move defensive resources toward the threatened area quickly."},
    {"num": 24, "tier": 2, "name": "Controlled Retreat", "protection": 37, "description": "Give up the first area while preparing a stronger second position."},
    {"num": 25, "tier": 2, "name": "Anti-Rush Setup", "protection": 44, "description": "Specifically prepare for a fast coordinated attack."},
    {"num": 26, "tier": 2, "name": "Fake Rotation", "protection": 34, "description": "Appear to rotate while secretly maintaining defensive coverage."},
    {"num": 27, "tier": 2, "name": "Information Trap", "protection": 40, "description": "Allow limited enemy movement to learn their actual plan."},
    {"num": 28, "tier": 2, "name": "Mid Control", "protection": 41, "description": "Maintain control over the central route to restrict attacker movement."},
    {"num": 29, "tier": 2, "name": "Lurk Detection", "protection": 36, "description": "Position resources specifically to detect hidden attackers."},
    {"num": 30, "tier": 2, "name": "Timing Defense", "protection": 45, "description": "Save defensive resources until the attacker's commitment is clear."},

    # Tier 3 (31-45)
    {"num": 31, "tier": 3, "name": "Full Site Hold", "protection": 58, "description": "Multiple defenders coordinate to protect the objective directly."},
    {"num": 32, "tier": 3, "name": "Layered Defense", "protection": 62, "description": "Defenders create several defensive positions that attackers must break through."},
    {"num": 33, "tier": 3, "name": "Three-Point Defense", "protection": 60, "description": "Defenders cover three important approaches simultaneously."},
    {"num": 34, "tier": 3, "name": "Split Defense", "protection": 57, "description": "Defensive players divide between the main objective and secondary threat."},
    {"num": 35, "tier": 3, "name": "Mid-Control Defense", "protection": 63, "description": "Maintain central control while still protecting the objective."},
    {"num": 36, "tier": 3, "name": "Utility Retake", "protection": 61, "description": "Allow limited entry and then use coordinated utility to reclaim the area."},
    {"num": 37, "tier": 3, "name": "Crossfire Network", "protection": 65, "description": "Several defenders create overlapping lines of support."},
    {"num": 38, "tier": 3, "name": "Delayed Retake", "protection": 56, "description": "Avoid immediately committing and wait for teammates before reclaiming."},
    {"num": 39, "tier": 3, "name": "Rotation Trap", "protection": 59, "description": "Attackers are allowed to commit while defenders prepare to punish their positioning."},
    {"num": 40, "tier": 3, "name": "Anti-Split Defense", "protection": 64, "description": "Defensive positioning specifically covers multiple simultaneous entrances."},
    {"num": 41, "tier": 3, "name": "Resource Conservation", "protection": 55, "description": "Save important defensive resources for the final stage of the attack."},
    {"num": 42, "tier": 3, "name": "Information Network", "protection": 58, "description": "Multiple information sources continuously track attacker movement."},
    {"num": 43, "tier": 3, "name": "Flank Containment", "protection": 54, "description": "Prevent hidden attackers from creating an unexpected secondary threat."},
    {"num": 44, "tier": 3, "name": "Retake Formation", "protection": 62, "description": "Several defenders coordinate their positions before attempting to retake."},
    {"num": 45, "tier": 3, "name": "Adaptive Defense", "protection": 66, "description": "Defensive formation changes according to the attacker's choices."},

    # Tier 4 (46-60)
    {"num": 46, "tier": 4, "name": "Full Anti-Rush", "protection": 78, "description": "Entire defense is prepared for an immediate coordinated attack."},
    {"num": 47, "tier": 4, "name": "Perfect Crossfire", "protection": 82, "description": "Multiple defenders create extremely strong overlapping coverage."},
    {"num": 48, "tier": 4, "name": "Multi-Layer Defense", "protection": 80, "description": "Attackers must overcome several defensive layers before reaching the objective."},
    {"num": 49, "tier": 4, "name": "Triple-Site Coverage", "protection": 77, "description": "Defense simultaneously protects three important approaches."},
    {"num": 50, "tier": 4, "name": "Full Utility Defense", "protection": 81, "description": "Large amounts of defensive resources are coordinated to stop the attack."},
    {"num": 51, "tier": 4, "name": "Rotation Punish", "protection": 79, "description": "Defenders deliberately allow a predictable commitment and then respond from advantageous positions."},
    {"num": 52, "tier": 4, "name": "Perfect Retake", "protection": 84, "description": "Defenders coordinate timing, positioning and utility for a unified retake."},
    {"num": 53, "tier": 4, "name": "Information Lockdown", "protection": 76, "description": "Defenders maintain extremely strong awareness of attacker movement."},
    {"num": 54, "tier": 4, "name": "Anti-Lurk Network", "protection": 78, "description": "Defensive positions specifically prevent hidden attackers from influencing the round."},
    {"num": 55, "tier": 4, "name": "Resource Denial", "protection": 75, "description": "Defenders preserve key resources specifically to counter the final attack."},
    {"num": 56, "tier": 4, "name": "Adaptive Fortress", "protection": 86, "description": "Defensive setup constantly changes based on the attacker's behavior."},
    {"num": 57, "tier": 4, "name": "Multi-Route Counter", "protection": 83, "description": "Defense simultaneously responds to attacks from multiple directions."},
    {"num": 58, "tier": 4, "name": "Counter-Rotation", "protection": 80, "description": "Defenders deliberately manipulate their positioning to punish attacking rotations."},
    {"num": 59, "tier": 4, "name": "Timed Retake", "protection": 88, "description": "The defense waits for the optimal moment and then executes a coordinated retake."},
    {"num": 60, "tier": 4, "name": "Master Defense", "protection": 92, "description": "A highly coordinated combination of information, positioning, utility, timing and adaptation."}
]


# ==============================================================================
# SECTION 3: MASTER INDEX (120 Cards)
# ==============================================================================

ALL_CARDS_MAP: Dict[str, Dict[str, Any]] = {}

for item in RAW_ATTACK_CARDS:
    cid = f"atk_{_slugify(item['name'])}"
    ALL_CARDS_MAP[cid] = {
        "id": cid,
        "name": item["name"],
        "category": "attack",
        "type": "attack_tactic",
        "description": item["description"],
        "_internal_tier": item["tier"],
        "_internal_power": item["power"]
    }

for item in RAW_DEFENCE_CARDS:
    cid = f"def_{_slugify(item['name'])}"
    ALL_CARDS_MAP[cid] = {
        "id": cid,
        "name": item["name"],
        "category": "defence",
        "type": "defence_tactic",
        "description": item["description"],
        "_internal_tier": item["tier"],
        "_internal_protection": item["protection"]
    }


# Backwards compatibility legacy aliases
ALL_CARDS_MAP["vandal_rifle"] = ALL_CARDS_MAP.get("atk_master_execute", list(ALL_CARDS_MAP.values())[0])
ALL_CARDS_MAP["curveball_flash"] = ALL_CARDS_MAP.get("atk_flash_entry", list(ALL_CARDS_MAP.values())[15])
ALL_CARDS_MAP["dark_cover_smoke"] = ALL_CARDS_MAP.get("def_defensive_smoke", list(ALL_CARDS_MAP.values())[75])
ALL_CARDS_MAP["heavy_shield"] = ALL_CARDS_MAP.get("def_layered_defense", list(ALL_CARDS_MAP.values())[90])
ALL_CARDS_MAP["tailwind_dash"] = ALL_CARDS_MAP.get("def_reposition_defense", list(ALL_CARDS_MAP.values())[74])


def get_all_cards() -> Dict[str, Dict[str, Any]]:
    """Returns the complete internal cards registry (with power/protection)."""
    return ALL_CARDS_MAP


def get_public_cards() -> List[Dict[str, Any]]:
    """
    Returns public card list for frontend clients.
    STRICTLY HIDES ALL TIERS AND POWER NUMBERS.
    """
    public_list = []
    seen = set()
    for cid, card in ALL_CARDS_MAP.items():
        if cid in seen or cid in ["vandal_rifle", "curveball_flash", "dark_cover_smoke", "heavy_shield", "tailwind_dash"]:
            continue
        seen.add(cid)
        public_list.append({
            "id": card["id"],
            "name": card["name"],
            "category": card["category"],
            "description": card["description"]
        })
    return public_list


def get_card_by_id(card_id: str) -> Optional[Dict[str, Any]]:
    """Fetches a single card by its ID."""
    return ALL_CARDS_MAP.get(card_id)
