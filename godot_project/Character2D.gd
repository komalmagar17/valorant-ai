# ==============================================================================
# Character2D.gd
# ==============================================================================
# Controls 2D visual character rendering, combat animations, health display,
# floating damage text, and all emote triggers (Dance, Taunt, Celebrate, Flex, etc.).
# Compatible with Godot 4.x / 3.x.
# ==============================================================================

extends Node2D
class_name Character2D

@export var character_id: String = "char_phantom_9"
@export var character_name: String = "PHANTOM-9"
@export var is_player_a: bool = true

var max_hp: float = 100.0
var current_hp: float = 100.0
var max_shield: float = 50.0
var current_shield: float = 50.0

@onready var sprite_anchor: Node2D = $SpriteAnchor
@onready var name_label: Label = $UI/NameLabel
@onready var hp_bar: ProgressBar = $UI/HealthBar
@onready var shield_bar: ProgressBar = $UI/ShieldBar
@onready var emote_bubble: PanelContainer = $UI/EmoteBubble
@onready var emote_label: Label = $UI/EmoteBubble/EmoteLabel
@onready var damage_popup_anchor: Node2D = $DamagePopupAnchor

var base_pos: Vector2 = Vector2.ZERO

func _ready() -> void:
	base_pos = position
	if emote_bubble:
		emote_bubble.visible = false
	update_ui()

func setup_character(id: String, c_name: String, p_name: String) -> void:
	character_id = id
	character_name = c_name
	if name_label:
		name_label.text = "%s (%s)" % [p_name, c_name]
	reset_stats()

func reset_stats() -> void:
	current_hp = max_hp
	current_shield = max_shield
	position = base_pos
	rotation = 0
	modulate = Color.WHITE
	if emote_bubble:
		emote_bubble.visible = false
	update_ui()

func update_ui() -> void:
	if hp_bar:
		hp_bar.value = current_hp
	if shield_bar:
		shield_bar.value = current_shield

# ------------------------------------------------------------------------------
# COMBAT ACTION ANIMATIONS
# ------------------------------------------------------------------------------

func play_action(action_type: String, anim_trigger: String, damage: int = 0) -> void:
	match anim_trigger:
		"anim_cast_slash", "anim_cast_slam", "anim_cast_cannon", "anim_cast_teleport":
			_anim_attack_dash()
		"anim_deploy_barrier", "anim_deploy_smoke", "anim_parry_stance":
			_anim_defence_barrier()
		"anim_dodge_roll":
			_anim_dodge()
		"anim_hit_react":
			_anim_hit_reaction(damage)
		"anim_defeat":
			_anim_defeat()
		"anim_victory":
			_anim_victory()
		_:
			_anim_pulse()

func _anim_attack_dash() -> void:
	var target_dir = 1.0 if is_player_a else -1.0
	var tween = create_tween()
	tween.tween_property(self, "position:x", base_pos.x + (120.0 * target_dir), 0.25).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tween.tween_property(self, "rotation_degrees", 8.0 * target_dir, 0.15)
	tween.tween_property(self, "position:x", base_pos.x, 0.35).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tween.parallel().tween_property(self, "rotation_degrees", 0.0, 0.35)

func _anim_defence_barrier() -> void:
	var tween = create_tween()
	var barrier_color = Color(0, 0.95, 1.0, 1.0) if is_player_a else Color(1.0, 0.4, 0.0, 1.0)
	tween.tween_property(self, "modulate", barrier_color * 1.5, 0.2)
	tween.tween_property(self, "scale", Vector2(1.15, 1.15), 0.2)
	tween.tween_property(self, "modulate", Color.WHITE, 0.4)
	tween.parallel().tween_property(self, "scale", Vector2(1.0, 1.0), 0.4)
	_spawn_floating_text("🛡️ DEFENCE ACTIVE", barrier_color)

func _anim_dodge() -> void:
	var tween = create_tween()
	tween.tween_property(self, "position:y", base_pos.y - 60.0, 0.2).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.tween_property(self, "rotation_degrees", 360.0 * (1 if is_player_a else -1), 0.3)
	tween.tween_property(self, "position:y", base_pos.y, 0.2).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	tween.tween_property(self, "rotation_degrees", 0.0, 0.05)
	_spawn_floating_text("💨 DODGE", Color.YELLOW)

func apply_damage(amount: int) -> void:
	if amount <= 0:
		return
	if current_shield > 0:
		var shield_absorb = min(current_shield, float(amount))
		current_shield -= shield_absorb
		amount -= int(shield_absorb)
	current_hp = max(0.0, current_hp - float(amount))
	update_ui()
	_anim_hit_reaction(amount)

func _anim_hit_reaction(amount: int) -> void:
	var tween = create_tween()
	tween.tween_property(self, "modulate", Color.RED, 0.1)
	var dir = -1.0 if is_player_a else 1.0
	tween.parallel().tween_property(self, "position:x", base_pos.x + (25.0 * dir), 0.1)
	tween.tween_property(self, "modulate", Color.WHITE, 0.25)
	tween.parallel().tween_property(self, "position:x", base_pos.x, 0.25)
	_spawn_floating_text("💥 -%d HP" % amount, Color(1.0, 0.2, 0.2, 1.0))

func _anim_victory() -> void:
	var tween = create_tween().set_loops(3)
	tween.tween_property(self, "position:y", base_pos.y - 40.0, 0.25).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.tween_property(self, "position:y", base_pos.y, 0.25).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	_spawn_floating_text("🏆 VICTORY!", Color(1.0, 0.85, 0.0, 1.0))

func _anim_defeat() -> void:
	var tween = create_tween()
	tween.tween_property(self, "position:y", base_pos.y + 40.0, 0.5).set_trans(Tween.TRANS_BOUNCE).set_ease(Tween.EASE_OUT)
	tween.parallel().tween_property(self, "rotation_degrees", -45.0 if is_player_a else 45.0, 0.5)
	tween.parallel().tween_property(self, "modulate", Color(0.5, 0.5, 0.5, 0.7), 0.5)
	_spawn_floating_text("💔 DEFEATED", Color(0.8, 0.3, 0.3, 1.0))

func _anim_pulse() -> void:
	var tween = create_tween()
	tween.tween_property(self, "scale", Vector2(1.1, 1.1), 0.15)
	tween.tween_property(self, "scale", Vector2(1.0, 1.0), 0.2)

# ------------------------------------------------------------------------------
# FULL EMOTE SUITE (Dance, Taunt, Celebrate, Flex, Salute, GG, Defeat)
# ------------------------------------------------------------------------------

func play_emote(emote_id: String) -> void:
	match emote_id:
		"emote_dance":
			_emote_dance()
		"emote_taunt":
			_emote_taunt()
		"emote_celebrate":
			_emote_celebrate()
		"emote_flex":
			_emote_flex()
		"emote_salute":
			_emote_salute()
		"emote_gg":
			_emote_gg()
		"emote_defeat":
			_anim_defeat()
		_:
			_show_bubble("⚡ %s" % emote_id)

func _emote_dance() -> void:
	_show_bubble("🕺 CYBER BREAKDANCE!")
	var tween = create_tween().set_loops(4)
	tween.tween_property(self, "rotation_degrees", 20.0, 0.15)
	tween.tween_property(self, "rotation_degrees", -20.0, 0.15)
	tween.tween_property(self, "position:y", base_pos.y - 20.0, 0.15)
	tween.tween_property(self, "position:y", base_pos.y, 0.15)

func _emote_taunt() -> void:
	_show_bubble("🗡️ STEP FORWARD IF YOU DARE!")
	var tween = create_tween()
	var dir = 1.0 if is_player_a else -1.0
	tween.tween_property(self, "position:x", base_pos.x + (50.0 * dir), 0.2)
	tween.tween_property(self, "scale", Vector2(1.2, 1.2), 0.2)
	tween.tween_interval(0.8)
	tween.tween_property(self, "position:x", base_pos.x, 0.3)
	tween.parallel().tween_property(self, "scale", Vector2(1.0, 1.0), 0.3)

func _emote_celebrate() -> void:
	_show_bubble("🎉 CHAMPION STATUS!")
	_anim_victory()

func _emote_flex() -> void:
	_show_bubble("💪 MOLTEN FORGE POWER!")
	var tween = create_tween()
	tween.tween_property(self, "scale", Vector2(1.3, 1.3), 0.3).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)
	tween.tween_property(self, "modulate", Color(1.0, 0.6, 0.1, 1.0), 0.2)
	tween.tween_interval(0.6)
	tween.tween_property(self, "scale", Vector2(1.0, 1.0), 0.3)
	tween.parallel().tween_property(self, "modulate", Color.WHITE, 0.3)

func _emote_salute() -> void:
	_show_bubble("🫡 HONORABLE COMBAT.")
	var tween = create_tween()
	tween.tween_property(self, "position:y", base_pos.y - 15.0, 0.2)
	tween.tween_interval(0.8)
	tween.tween_property(self, "position:y", base_pos.y, 0.2)

func _emote_gg() -> void:
	_show_bubble("👋 RESPECT! GOOD GAME.")
	var tween = create_tween().set_loops(3)
	tween.tween_property(self, "rotation_degrees", 10.0, 0.15)
	tween.tween_property(self, "rotation_degrees", 0.0, 0.15)

func _show_bubble(text: String) -> void:
	if not emote_bubble or not emote_label:
		return
	emote_label.text = text
	emote_bubble.visible = true
	emote_bubble.modulate = Color.TRANSPARENT
	var tween = create_tween()
	tween.tween_property(emote_bubble, "modulate", Color.WHITE, 0.2)
	tween.tween_interval(2.2)
	tween.tween_property(emote_bubble, "modulate", Color.TRANSPARENT, 0.3)
	tween.tween_callback(func(): emote_bubble.visible = false)

func _spawn_floating_text(text: String, color: Color) -> void:
	var label = Label.new()
	label.text = text
	label.modulate = color
	label.add_theme_font_size_override("font_size", 18)
	label.position = Vector2(-40, -100)
	add_child(label)

	var tween = create_tween()
	tween.tween_property(label, "position:y", label.position.y - 45.0, 0.8).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.parallel().tween_property(label, "modulate:a", 0.0, 0.8)
	tween.tween_callback(label.queue_free)
