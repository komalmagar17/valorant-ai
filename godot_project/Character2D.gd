# ==============================================================================
# Character2D.gd
# ==============================================================================
# Controls 2D visual character rendering in Godot with SpriteSheet keyframe
# animations, combat movement tweening, dual-layer health bars, damage popups,
# tactical card callout banners, and full emote suites.
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
@onready var sprite: Sprite2D = $SpriteAnchor/CharacterSprite if has_node("SpriteAnchor/CharacterSprite") else null
@onready var name_label: Label = $UI/NameLabel
@onready var hp_bar: ProgressBar = $UI/HealthBar
@onready var hp_ghost_bar: ProgressBar = $UI/HealthGhostBar if has_node("UI/HealthGhostBar") else null
@onready var shield_bar: ProgressBar = $UI/ShieldBar
@onready var emote_bubble: PanelContainer = $UI/EmoteBubble
@onready var emote_label: Label = $UI/EmoteBubble/EmoteLabel
@onready var card_badge: PanelContainer = $UI/CardCallout if has_node("UI/CardCallout") else null
@onready var card_badge_label: Label = $UI/CardCallout/CardLabel if has_node("UI/CardCallout/CardLabel") else null
@onready var damage_popup_anchor: Node2D = $DamagePopupAnchor

var base_pos: Vector2 = Vector2.ZERO
var anim_tween: Tween = null
var ghost_tween: Tween = null

func _ready() -> void:
	base_pos = position
	if emote_bubble:
		emote_bubble.visible = false
	if card_badge:
		card_badge.visible = false
	update_ui(false)
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
	if card_badge:
		card_badge.visible = false
	_set_sprite_row(0)
	update_ui(false)

func update_ui(animate_ghost: bool = true) -> void:
	if hp_bar:
		hp_bar.value = current_hp
	if hp_ghost_bar:
		if animate_ghost:
			if ghost_tween and ghost_tween.is_valid():
				ghost_tween.kill()
			ghost_tween = create_tween()
			ghost_tween.tween_interval(0.2)
			ghost_tween.tween_property(hp_ghost_bar, "value", current_hp, 0.4).set_trans(Tween.TRANS_SINE)
		else:
			hp_ghost_bar.value = current_hp
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
# CARD CALLOUT BANNER
# ------------------------------------------------------------------------------

func show_card_callout(card_name: String, action_type: String) -> void:
	if not card_badge or not card_badge_label or card_name == "":
		return
	
	var is_attack = action_type.contains("attack") or action_type.contains("strike") or action_type.contains("slash")
	var prefix = "⚔️ ATTACK: " if is_attack else "🛡️ DEFENCE: "
	card_badge_label.text = prefix + card_name
	
	var badge_color = Color(1.0, 0.25, 0.25) if is_attack else Color(0.1, 0.85, 1.0)
	card_badge_label.modulate = badge_color
	
	card_badge.visible = true
	card_badge.scale = Vector2(0.6, 0.6)
	card_badge.modulate = Color.TRANSPARENT
	
	var tween = create_tween()
	tween.tween_property(card_badge, "modulate", Color.WHITE, 0.15)
	tween.parallel().tween_property(card_badge, "scale", Vector2(1.0, 1.0), 0.15).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tween.tween_interval(1.8)
	tween.tween_property(card_badge, "modulate", Color.TRANSPARENT, 0.25)
	tween.tween_callback(func(): card_badge.visible = false)

# ------------------------------------------------------------------------------
# COMBAT ACTION ANIMATIONS
# ------------------------------------------------------------------------------

func play_action(action_type: String, anim_trigger: String, damage: int = 0, card_name: String = "") -> void:
	if card_name != "":
		show_card_callout(card_name, action_type)
	
	match anim_trigger:
		"anim_cast_slash", "anim_cast_slam", "anim_cast_cannon", "anim_cast_teleport":
			_anim_attack_dash(anim_trigger == "anim_cast_teleport")
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

func _anim_attack_dash(is_teleport: bool = false) -> void:
	_cycle_sprite_frames(1, 8, 0.05, 1)
	var target_dir = 1.0 if is_player_a else -1.0
	var dash_dist = 180.0 if is_teleport else 130.0
	
	var tween = create_tween()
	if is_teleport:
		tween.tween_property(self, "modulate:a", 0.3, 0.08)
		tween.parallel().tween_property(self, "position:x", base_pos.x + (dash_dist * target_dir), 0.15).set_trans(Tween.TRANS_EXPO)
		tween.tween_property(self, "modulate:a", 1.0, 0.08)
	else:
		tween.tween_property(self, "position:x", base_pos.x + (dash_dist * target_dir), 0.2).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	
	tween.tween_property(self, "position:x", base_pos.x, 0.25).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)

func _anim_defence_barrier() -> void:
	_cycle_sprite_frames(2 if character_id == "char_sol_vanguard" else 0, 8, 0.08, 1)
	var tween = create_tween()
	var barrier_color = Color(0.0, 0.95, 1.0, 1.0) if is_player_a else Color(1.0, 0.5, 0.0, 1.0)
	tween.tween_property(self, "modulate", barrier_color * 1.6, 0.15)
	tween.parallel().tween_property(self, "scale", Vector2(1.15, 1.15), 0.15)
	tween.tween_property(self, "modulate", Color.WHITE, 0.35)
	tween.parallel().tween_property(self, "scale", Vector2(1.0, 1.0), 0.35)
	_spawn_floating_text("🛡️ DEFENCE ACTIVE", barrier_color)

func _anim_dodge() -> void:
	_cycle_sprite_frames(2, 8, 0.05, 1)
	var tween = create_tween()
	tween.tween_property(self, "position:y", base_pos.y - 70.0, 0.18).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.parallel().tween_property(self, "rotation_degrees", 15.0 if is_player_a else -15.0, 0.18)
	tween.tween_property(self, "position:y", base_pos.y, 0.18).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	tween.parallel().tween_property(self, "rotation_degrees", 0.0, 0.18)
	_spawn_floating_text("💨 EVASION", Color.YELLOW)

func apply_damage(amount: int, is_critical: bool = false) -> void:
	if amount <= 0:
		return
	if current_shield > 0:
		var shield_absorb = min(current_shield, float(amount))
		current_shield -= shield_absorb
		amount -= int(shield_absorb)
	current_hp = max(0.0, current_hp - float(amount))
	update_ui(true)
	_anim_hit_reaction(amount, is_critical)

func _anim_hit_reaction(amount: int, is_critical: bool = false) -> void:
	var tween = create_tween()
	var flash_color = Color(1.0, 0.1, 0.1, 1.0) if is_critical else Color(1.0, 0.4, 0.4, 1.0)
	tween.tween_property(self, "modulate", flash_color, 0.08)
	var dir = -1.0 if is_player_a else 1.0
	var knockback = 45.0 if is_critical else 22.0
	tween.parallel().tween_property(self, "position:x", base_pos.x + (knockback * dir), 0.08)
	tween.tween_property(self, "modulate", Color.WHITE, 0.2)
	tween.parallel().tween_property(self, "position:x", base_pos.x, 0.2)
	
	var label_text = "⚡ CRITICAL -%d HP!" % amount if is_critical else "-%d HP" % amount
	var text_color = Color(1.0, 0.85, 0.1, 1.0) if is_critical else Color(1.0, 0.25, 0.25, 1.0)
	_spawn_floating_text(label_text, text_color, is_critical)

func _anim_victory() -> void:
	_cycle_sprite_frames(3, 8, 0.1, 3)
	var tween = create_tween().set_loops(3)
	tween.tween_property(self, "position:y", base_pos.y - 45.0, 0.22).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.tween_property(self, "position:y", base_pos.y, 0.22).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	_spawn_floating_text("🏆 VICTORY!", Color(1.0, 0.9, 0.1, 1.0), true)

func _anim_defeat() -> void:
	var row = 7 if character_id == "char_phantom_9" else 8
	_cycle_sprite_frames(row, 8, 0.1, 1)
	var tween = create_tween()
	tween.tween_property(self, "position:y", base_pos.y + 35.0, 0.4).set_trans(Tween.TRANS_BOUNCE).set_ease(Tween.EASE_OUT)
	tween.parallel().tween_property(self, "modulate", Color(0.4, 0.4, 0.5, 0.7), 0.4)
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
	emote_bubble.scale = Vector2(0.7, 0.7)
	
	var tween = create_tween()
	tween.tween_property(emote_bubble, "modulate", Color.WHITE, 0.15)
	tween.parallel().tween_property(emote_bubble, "scale", Vector2(1.0, 1.0), 0.15).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tween.tween_interval(2.2)
	tween.tween_property(emote_bubble, "modulate", Color.TRANSPARENT, 0.25)
	tween.tween_callback(func(): emote_bubble.visible = false)

func _spawn_floating_text(text: String, color: Color, is_big: bool = false) -> void:
	var label = Label.new()
	label.text = text
	label.modulate = color
	label.add_theme_font_size_override("font_size", 22 if is_big else 16)
	label.position = Vector2(-70, -135)
	add_child(label)

	var tween = create_tween()
	tween.tween_property(label, "position:y", label.position.y - (55.0 if is_big else 40.0), 0.8).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.parallel().tween_property(label, "modulate:a", 0.0, 0.8)
	tween.tween_callback(label.queue_free)
