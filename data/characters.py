"""
================================================================================
data/characters.py
================================================================================
Defines the two core combat characters for the game with full animation states,
emote manifests, Godot AnimationPlayer triggers, and audio cue identifiers.
================================================================================
"""

from typing import Dict, Any, List

CHARACTERS_DATABASE: Dict[str, Dict[str, Any]] = {
    "char_phantom_9": {
        "id": "char_phantom_9",
        "name": "PHANTOM-9",
        "title": "The Cyber Infiltrator",
        "archetype": "High-Speed Duelist / Stealth Assassin",
        "description": "A lethal synthetic operative wielding neon cipher daggers and optical distortion fields. Excels at high-tempo entry fragging, blinding dashes, and elusive retakes.",
        "color_primary": "#00f2ff",
        "color_secondary": "#a855f7",
        "avatar_badge": "🗡️",
        "base_stats": {
            "hp": 100,
            "shield": 50,
            "speed": 1.25,
            "agility": 95,
            "power": 88
        },
        "combat_animations": [
            {"name": "idle", "godot_trigger": "anim_idle", "duration_sec": 1.0, "desc": "Combat ready stance with spinning cyber-dagger"},
            {"name": "run", "godot_trigger": "anim_run", "duration_sec": 0.6, "desc": "Low-profile cyber sprint with particle trails"},
            {"name": "cast_attack_1", "godot_trigger": "anim_cast_slash", "duration_sec": 1.2, "desc": "Rapid forward dash with twin blade slash"},
            {"name": "cast_attack_2", "godot_trigger": "anim_cast_teleport", "duration_sec": 1.4, "desc": "Phase-shift blink strike behind enemy target"},
            {"name": "deploy_smoke", "godot_trigger": "anim_deploy_smoke", "duration_sec": 1.0, "desc": "Throws holographic cipher smoke orb"},
            {"name": "dodge_roll", "godot_trigger": "anim_dodge_roll", "duration_sec": 0.8, "desc": "Acrobatic evasive roll with invulnerability frames"},
            {"name": "hit_stagger", "godot_trigger": "anim_hit_react", "duration_sec": 0.5, "desc": "Shield absorption flash and stumble reaction"},
            {"name": "victory_pose", "godot_trigger": "anim_victory", "duration_sec": 2.5, "desc": "Sheathes daggers and activates optical cloak flicker"},
            {"name": "defeat_fall", "godot_trigger": "anim_defeat", "duration_sec": 2.0, "desc": "Kneels with glitching holographic armor breakdown"}
        ],
        "emotes": [
            {
                "id": "emote_dance",
                "name": "Cyber Breakdance",
                "icon": "🕺",
                "godot_trigger": "anim_emote_dance",
                "sound_cue": "sfx_synth_beat",
                "duration_sec": 3.2,
                "description": "Executes a fast-paced electronic windmill breakdance with neon light trails."
            },
            {
                "id": "emote_taunt",
                "name": "Blade Spin & Point",
                "icon": "🗡️",
                "godot_trigger": "anim_emote_taunt",
                "sound_cue": "sfx_blade_whoosh",
                "duration_sec": 2.4,
                "description": "Spins daggers between fingers and points directly at the opponent."
            },
            {
                "id": "emote_celebrate",
                "name": "Holo-Trophy Cheer",
                "icon": "🎉",
                "godot_trigger": "anim_emote_celebrate",
                "sound_cue": "sfx_victory_fanfare",
                "duration_sec": 2.8,
                "description": "Conjures a glowing neon trophy and raises it triumphantly into the air."
            },
            {
                "id": "emote_flex",
                "name": "Dual Blaster Flex",
                "icon": "💪",
                "godot_trigger": "anim_emote_flex",
                "sound_cue": "sfx_power_charge",
                "duration_sec": 2.2,
                "description": "Charges energy into cybernetic arms and strikes an athletic combat flex."
            },
            {
                "id": "emote_salute",
                "name": "Spec-Ops Salute",
                "icon": "🫡",
                "godot_trigger": "anim_emote_salute",
                "sound_cue": "sfx_holo_beep",
                "duration_sec": 2.0,
                "description": "Snaps a crisp military salute with a glowing visor salute animation."
            },
            {
                "id": "emote_gg",
                "name": "Respectful GG Wave",
                "icon": "👋",
                "godot_trigger": "anim_emote_gg",
                "sound_cue": "sfx_friendly_chime",
                "duration_sec": 2.1,
                "description": "Waves respectfully at the rival with a 'GG' holographic projection above."
            },
            {
                "id": "emote_defeat",
                "name": "Disappointed Shrug",
                "icon": "🤦",
                "godot_trigger": "anim_emote_defeat",
                "sound_cue": "sfx_glitch_down",
                "duration_sec": 2.5,
                "description": "Shakes head and shrugs hands with glitching visor static."
            }
        ]
    },

    "char_sol_vanguard": {
        "id": "char_sol_vanguard",
        "name": "SOL-VANGUARD",
        "title": "The Molten Titan",
        "archetype": "Heavy Sentinel / Fortified Juggernaut",
        "description": "A heavily armored solar guardian encased in molten alloy plating. Dominates site defense with unyielding energy barriers, devastating ground pounds, and impenetrable fortresses.",
        "color_primary": "#ff5e00",
        "color_secondary": "#ffd700",
        "avatar_badge": "🛡️",
        "base_stats": {
            "hp": 100,
            "shield": 50,
            "speed": 0.95,
            "agility": 75,
            "power": 98
        },
        "combat_animations": [
            {"name": "idle", "godot_trigger": "anim_idle", "duration_sec": 1.0, "desc": "Imposing stance with glowing molten core pulse"},
            {"name": "run", "godot_trigger": "anim_run", "duration_sec": 0.7, "desc": "Heavy armored strides shaking the battlefield"},
            {"name": "cast_attack_1", "godot_trigger": "anim_cast_slam", "duration_sec": 1.5, "desc": "Overhead heavy hammer slam unleashing solar shockwave"},
            {"name": "cast_attack_2", "godot_trigger": "anim_cast_cannon", "duration_sec": 1.6, "desc": "Fires a concentrated plasma beam from chest reactor"},
            {"name": "deploy_barrier", "godot_trigger": "anim_deploy_barrier", "duration_sec": 1.2, "desc": "Plants tower shield into ground, creating radiant barrier"},
            {"name": "parry_stance", "godot_trigger": "anim_parry_stance", "duration_sec": 0.9, "desc": "Braces fortress shield to deflect incoming projectile"},
            {"name": "hit_stagger", "godot_trigger": "anim_hit_react", "duration_sec": 0.5, "desc": "Armor sparks absorb impact without losing ground"},
            {"name": "victory_pose", "godot_trigger": "anim_victory", "duration_sec": 2.5, "desc": "Plants shield firmly and lets out an apex titan roar"},
            {"name": "defeat_fall", "godot_trigger": "anim_defeat", "duration_sec": 2.0, "desc": "Drops down to one knee as molten reactor vents steam"}
        ],
        "emotes": [
            {
                "id": "emote_dance",
                "name": "Titan Robot Popping",
                "icon": "🤖",
                "godot_trigger": "anim_emote_dance",
                "sound_cue": "sfx_hydraulic_gear",
                "duration_sec": 3.4,
                "description": "Performs mechanical robotic isolations with hydraulic servo sound effects."
            },
            {
                "id": "emote_taunt",
                "name": "Chest Thump Roar",
                "icon": "🦍",
                "godot_trigger": "anim_emote_taunt",
                "sound_cue": "sfx_titan_roar",
                "duration_sec": 2.6,
                "description": "Thumps armored chest twice with metallic clang, daring enemy to advance."
            },
            {
                "id": "emote_celebrate",
                "name": "Ground Slam Fireworks",
                "icon": "🏆",
                "godot_trigger": "anim_emote_celebrate",
                "sound_cue": "sfx_molten_burst",
                "duration_sec": 3.0,
                "description": "Pounds both fists to the ground, ejecting solar flare fireworks into the sky."
            },
            {
                "id": "emote_flex",
                "name": "Molten Bicep Flex",
                "icon": "💥",
                "godot_trigger": "anim_emote_flex",
                "sound_cue": "sfx_furnace_blast",
                "duration_sec": 2.3,
                "description": "Flexes massive titanium biceps, venting glowing molten heat from forearm vents."
            },
            {
                "id": "emote_salute",
                "name": "Shield Heart Tap",
                "icon": "🛡️",
                "godot_trigger": "anim_emote_salute",
                "sound_cue": "sfx_shield_thump",
                "duration_sec": 2.0,
                "description": "Taps shield fist over heart reactor in an honorable warrior salute."
            },
            {
                "id": "emote_gg",
                "name": "Heavy Fist Bump",
                "icon": "👊",
                "godot_trigger": "anim_emote_gg",
                "sound_cue": "sfx_metal_impact",
                "duration_sec": 2.2,
                "description": "Extends a heavy armored fist forward for a virtual 'Good Game' fist bump."
            },
            {
                "id": "emote_defeat",
                "name": "Kneeling Shield Drop",
                "icon": "💔",
                "godot_trigger": "anim_emote_defeat",
                "sound_cue": "sfx_steam_release",
                "duration_sec": 2.6,
                "description": "Slumps to one knee and rests forehead against the grounded shield."
            }
        ]
    }
}


def get_all_characters() -> List[Dict[str, Any]]:
    """Returns list of all available characters with full animation and emote manifests."""
    return list(CHARACTERS_DATABASE.values())


def get_character_by_id(char_id: str) -> Dict[str, Any]:
    """Retrieves character by ID with safe default fallback."""
    if char_id in CHARACTERS_DATABASE:
        return CHARACTERS_DATABASE[char_id]
    return CHARACTERS_DATABASE["char_phantom_9"]
