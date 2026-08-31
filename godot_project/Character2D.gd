# ==============================================================================
# Character2D.gd
# ==============================================================================
# Controls 2D visual character rendering with SpriteSheet keyframe animation,
# combat movements, health display, damage popups, and full emote suites.
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

@onready var sprite: Sprite2D = $SpriteAnchor/CharacterSprite if has_node("SpriteAnchor/CharacterSprite") else null
@onready var name_label: Label = $UI/NameLabel
@onready var hp_bar: ProgressBar = $UI/HealthBar
@onready var shield_bar: ProgressBar = $UI/ShieldBar
@onready var emote_bubble: PanelContainer = $UI/EmoteBubble
@onready var emote_label: Label = $UI/EmoteBubble/EmoteLabel
@onready var damage_popup_anchor: Node2D = $DamagePopupAnchor

var base_pos: Vector2 = Vector2.ZERO
var anim_tween: Tween = null

func _ready() -> void:
	base_pos = position
	if emote_bubble:
		emote_bubble.visible = false
	update_ui()
	_set_sprite_row(0) # Idle row

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
	_set_sprite_row(0)
	update_ui()

func update_ui() -> void:
	if hp_bar:
		hp_bar.value = current_hp
	if shield_bar:
		shield_bar.value = current_shield

func _set_sprite_row(row_idx: int) -> void:
	if sprite:
		var h_frames = sprite.hframes if sprite.hframes > 0 else 8
		sprite.frame = row_idx * h_frames

func _cycle_sprite_frames(row_idx: int, frame_count: int = 8, speed: float = 0.08, loops: int = 1) -> void:
	if not sprite:
		return
	var h_frames = sprite.hframes if sprite.hframes > 0 else 8
	var start_f = row_idx * h_frames

	if anim_tween and anim_tween.is_valid():
		anim_tween.kill()

	anim_tween = create_tween().set_loops(loops)
	for i in range(frame_count):
		anim_tween.tween_callback(func(): sprite.frame = start_f + i).set_delay(speed)
	anim_tween.tween_callback(func(): _set_sprite_row(0)).set_delay(speed) # Return to idle

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
			_set_sprite_row(0)

func _anim_attack_dash() -> void:
	_cycle_sprite_frames(1, 8, 0.06, 1)
	var target_dir = 1.0 if is_player_a else -1.0
	var tween = create_tween()
	tween.tween_property(self, "position:x", base_pos.x + (140.0 * target_dir), 0.25).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tween.tween_property(self, "position:x", base_pos.x, 0.3).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)

func _anim_defence_barrier() -> void:
	_cycle_sprite_frames(2 if character_id == "char_sol_vanguard" else 0, 8, 0.08, 1)
	var tween = create_tween()
	var barrier_color = Color(0, 0.95, 1.0, 1.0) if is_player_a else Color(1.0, 0.4, 0.0, 1.0)
	tween.tween_property(self, "modulate", barrier_color * 1.5, 0.2)
	tween.tween_property(self, "scale", Vector2(1.15, 1.15), 0.2)
	tween.tween_property(self, "modulate", Color.WHITE, 0.4)
	tween.parallel().tween_property(self, "scale", Vector2(1.0, 1.0), 0.4)
	_spawn_floating_text("🛡️ DEFENCE ACTIVE", barrier_color)

func _anim_dodge() -> void:
	_cycle_sprite_frames(2, 8, 0.05, 1)
	var tween = create_tween()
	tween.tween_property(self, "position:y", base_pos.y - 60.0, 0.2).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.tween_property(self, "position:y", base_pos.y, 0.2).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
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
	_cycle_sprite_frames(3, 8, 0.1, 3)
	var tween = create_tween().set_loops(3)
	tween.tween_property(self, "position:y", base_pos.y - 40.0, 0.25).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.tween_property(self, "position:y", base_pos.y, 0.25).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	_spawn_floating_text("🏆 VICTORY!", Color(1.0, 0.85, 0.0, 1.0))

func _anim_defeat() -> void:
	var row = 7 if character_id == "char_phantom_9" else 8
	_cycle_sprite_frames(row, 8, 0.1, 1)
	var tween = create_tween()
	tween.tween_property(self, "position:y", base_pos.y + 35.0, 0.5).set_trans(Tween.TRANS_BOUNCE).set_ease(Tween.EASE_OUT)
	tween.parallel().tween_property(self, "modulate", Color(0.5, 0.5, 0.5, 0.7), 0.5)
	_spawn_floating_text("💔 DEFEATED", Color(0.8, 0.3, 0.3, 1.0))

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
	_show_bubble("🕺 CYBER BREAKDANCE!" if character_id == "char_phantom_9" else "🤖 TITAN ROBOT DANCE!")
	_cycle_sprite_frames(4, 8, 0.08, 3)

func _emote_taunt() -> void:
	_show_bubble("🗡️ STEP FORWARD IF YOU DARE!" if character_id == "char_phantom_9" else "🦍 CHEST THUMP ROAR!")
	_cycle_sprite_frames(5, 8, 0.09, 2)

func _emote_celebrate() -> void:
	_show_bubble("🎉 CHAMPION STATUS!")
	_anim_victory()

func _emote_flex() -> void:
	_show_bubble("💪 BLASTER FLEX!" if character_id == "char_phantom_9" else "💥 MOLTEN BICEP FLEX!")
	_cycle_sprite_frames(6, 8, 0.09, 2)

func _emote_salute() -> void:
	_show_bubble("🫡 HONORABLE WARRIOR SALUTE.")
	var row = 7 if character_id == "char_sol_vanguard" else 0
	_cycle_sprite_frames(row, 8, 0.1, 1)

func _emote_gg() -> void:
	_show_bubble("👋 RESPECT! GOOD GAME.")
	_cycle_sprite_frames(0, 8, 0.1, 2)

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
	label.position = Vector2(-50, -120)
	add_child(label)

	var tween = create_tween()
	tween.tween_property(label, "position:y", label.position.y - 45.0, 0.8).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.parallel().tween_property(label, "modulate:a", 0.0, 0.8)
	tween.tween_callback(label.queue_free)
