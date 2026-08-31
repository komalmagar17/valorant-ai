# ==============================================================================
# MainCombatArena.gd - Local Combat Arena Controller for Veer Survivor
# ==============================================================================
# Full in-engine Godot 4.x controller featuring:
# - Native procedural audio playback via AudioSynth
# - Dynamic camera shake trauma & impact VFX
# - Animated 2D character combat with dual health/ghost bars & damage popups
# - Real-time card loadout HUD & ability cast popouts
# - Interactive timeline playback controls (Play/Pause, Scrub, 0.5x-2x Speed)
# - Interactive on-screen Emote suite triggers
# - Built-in offline AI Duel Simulator + REST backend live synchronization
# - Victory / MVP trophy breakdown modal
# ==============================================================================

extends Node2D

@export var api_url: String = "http://localhost:8000/api/matches/latest/godot-sequence"
@export var autoplay: bool = true

# Node References
@onready var audio_synth: AudioSynth = $AudioSynth
@onready var http_request: HTTPRequest = $HTTPRequest
@onready var camera: Camera2D = $Camera2D
@onready var player_a: Character2D = $PlayerA
@onready var player_b: Character2D = $PlayerB
@onready var laser_line: Line2D = $LaserLine
@onready var impact_sparks: CPUParticles2D = $ImpactSparks

# HUD References
@onready var match_title_label: Label = $CanvasLayer/TopBar/MatchTitle
@onready var score_label: Label = $CanvasLayer/TopBar/ScoreLabel
@onready var status_badge: Label = $CanvasLayer/TopBar/StatusBadge
@onready var commentary_label: Label = $CanvasLayer/BottomBar/CommentaryLabel
@onready var progress_bar: ProgressBar = $CanvasLayer/PlaybackControls/HBox/TimelineBar
@onready var time_label: Label = $CanvasLayer/PlaybackControls/HBox/TimeLabel
@onready var btn_play_pause: Button = $CanvasLayer/PlaybackControls/HBox/BtnPlayPause

# Loadout HUD
@onready var p_a_atk1: Label = $CanvasLayer/LeftLoadoutPanel/VBox/Atk1
@onready var p_a_atk2: Label = $CanvasLayer/LeftLoadoutPanel/VBox/Atk2
@onready var p_a_def1: Label = $CanvasLayer/LeftLoadoutPanel/VBox/Def1
@onready var p_a_def2: Label = $CanvasLayer/LeftLoadoutPanel/VBox/Def2

@onready var p_b_atk1: Label = $CanvasLayer/RightLoadoutPanel/VBox/Atk1
@onready var p_b_atk2: Label = $CanvasLayer/RightLoadoutPanel/VBox/Atk2
@onready var p_b_def1: Label = $CanvasLayer/RightLoadoutPanel/VBox/Def1
@onready var p_b_def2: Label = $CanvasLayer/RightLoadoutPanel/VBox/Def2

# Victory Modal
@onready var victory_modal: PanelContainer = $CanvasLayer/VictoryModal
@onready var victory_winner_label: Label = $CanvasLayer/VictoryModal/VBox/WinnerLabel
@onready var victory_combo_label: Label = $CanvasLayer/VictoryModal/VBox/ComboLabel
@onready var victory_reason_label: Label = $CanvasLayer/VictoryModal/VBox/ReasonLabel

# State Variables
var timeline_events: Array = []
var current_step_index: int = 0
var is_playing: bool = false
var is_paused: bool = false
var playback_speed: float = 1.0
var elapsed_match_time: float = 0.0
var total_match_duration: float = 14.5
var current_match_data: Dictionary = {}

# Camera Shake
var camera_trauma: float = 0.0
var camera_trauma_decay: float = 1.4
var camera_max_offset: Vector2 = Vector2(18.0, 14.0)

func _ready() -> void:
	if http_request:
		http_request.request_completed.connect(_on_http_request_completed)
	
	_connect_ui_buttons()
	
	if autoplay:
		fetch_latest_match()

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_accept"): # Spacebar
		toggle_play_pause()
	elif event is InputEventKey and event.pressed:
		match event.keycode:
			KEY_F:
				fetch_latest_match()
			KEY_R:
				restart_match_playback()
			KEY_S:
				simulate_ai_duel()
			KEY_F11:
				toggle_fullscreen()
			KEY_1:
				if player_a: player_a.play_emote("emote_dance")
			KEY_2:
				if player_a: player_a.play_emote("emote_taunt")
			KEY_3:
				if player_a: player_a.play_emote("emote_celebrate")
			KEY_4:
				if player_a: player_a.play_emote("emote_flex")
			KEY_7:
				if player_b: player_b.play_emote("emote_dance")
			KEY_8:
				if player_b: player_b.play_emote("emote_taunt")
			KEY_9:
				if player_b: player_b.play_emote("emote_celebrate")
			KEY_0:
				if player_b: player_b.play_emote("emote_flex")

# ------------------------------------------------------------------------------
# UI BUTTON SIGNALS SETUP
# ------------------------------------------------------------------------------

func _connect_ui_buttons() -> void:
	# Controls
	btn_play_pause.pressed.connect(toggle_play_pause)
	$CanvasLayer/PlaybackControls/HBox/BtnStepBack.pressed.connect(step_backward)
	$CanvasLayer/PlaybackControls/HBox/BtnStepNext.pressed.connect(step_forward)
	$CanvasLayer/PlaybackControls/HBox/BtnSpeed05.pressed.connect(func(): set_playback_speed(0.5))
	$CanvasLayer/PlaybackControls/HBox/BtnSpeed1.pressed.connect(func(): set_playback_speed(1.0))
	$CanvasLayer/PlaybackControls/HBox/BtnSpeed2.pressed.connect(func(): set_playback_speed(2.0))
	$CanvasLayer/PlaybackControls/HBox/BtnFetch.pressed.connect(fetch_latest_match)
	$CanvasLayer/PlaybackControls/HBox/BtnSimDuel.pressed.connect(simulate_ai_duel)
	$CanvasLayer/PlaybackControls/HBox/BtnFullscreen.pressed.connect(toggle_fullscreen)
	
	# Emote Action Bar
	var eb = $CanvasLayer/PlaybackControls/EmoteBar
	eb.get_node("BtnDanceA").pressed.connect(func(): if player_a: player_a.play_emote("emote_dance"))
	eb.get_node("BtnTauntA").pressed.connect(func(): if player_a: player_a.play_emote("emote_taunt"))
	eb.get_node("BtnCelebrateA").pressed.connect(func(): if player_a: player_a.play_emote("emote_celebrate"))
	eb.get_node("BtnFlexA").pressed.connect(func(): if player_a: player_a.play_emote("emote_flex"))
	eb.get_node("BtnDanceB").pressed.connect(func(): if player_b: player_b.play_emote("emote_dance"))
	eb.get_node("BtnTauntB").pressed.connect(func(): if player_b: player_b.play_emote("emote_taunt"))
	eb.get_node("BtnCelebrateB").pressed.connect(func(): if player_b: player_b.play_emote("emote_celebrate"))
	eb.get_node("BtnFlexB").pressed.connect(func(): if player_b: player_b.play_emote("emote_flex"))
	eb.get_node("BtnSalute").pressed.connect(func(): 
		if player_a: player_a.play_emote("emote_salute")
		if player_b: player_b.play_emote("emote_salute")
	)
	eb.get_node("BtnGG").pressed.connect(func(): 
		if player_a: player_a.play_emote("emote_gg")
		if player_b: player_b.play_emote("emote_gg")
	)
	
	# Victory Modal Buttons
	$CanvasLayer/VictoryModal/VBox/HBoxBtns/BtnReplayMatch.pressed.connect(restart_match_playback)
	$CanvasLayer/VictoryModal/VBox/HBoxBtns/BtnSimulateNew.pressed.connect(simulate_ai_duel)
	$CanvasLayer/VictoryModal/VBox/HBoxBtns/BtnCloseModal.pressed.connect(func(): victory_modal.visible = false)

# ------------------------------------------------------------------------------
# MATCH DATA LOADING (REST API, LOCAL JSON, OR PROCEDURAL SIMULATION)
# ------------------------------------------------------------------------------

func fetch_latest_match() -> void:
	if audio_synth: audio_synth.play_cue("sfx_button_click")
	status_badge.text = "FETCHING LATEST MATCH..."
	status_badge.modulate = Color.YELLOW
	if http_request:
		var err = http_request.request(api_url)
		if err != OK:
			print("[GODOT] HTTP fetch failed, reading local JSON sequence.")
			_load_local_json_fallback()
	else:
		_load_local_json_fallback()

func _on_http_request_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray) -> void:
	if response_code == 200:
		var json = JSON.new()
		var parse_err = json.parse(body.get_string_from_utf8())
		if parse_err == OK and json.get_data() is Dictionary:
			print("[GODOT] Successfully fetched latest match sequence from server!")
			load_sequence_data(json.get_data())
			return
	
	print("[GODOT] Network fetch returned status %d. Loading local fallback." % response_code)
	_load_local_json_fallback()

func _load_local_json_fallback() -> void:
	var path = "res://godot_match_sequence.json"
	if FileAccess.file_exists(path):
		var file = FileAccess.open(path, FileAccess.READ)
		var text = file.get_as_text()
		file.close()
		var json = JSON.new()
		if json.parse(text) == OK:
			load_sequence_data(json.get_data())
			return
	
	status_badge.text = "OFFLINE MODE - SIMULATING DUEL"
	simulate_ai_duel()

func load_sequence_data(data: Dictionary) -> void:
	current_match_data = data
	timeline_events = data.get("timeline", [])
	total_match_duration = float(data.get("total_duration_sec", 14.5))

	var p_a = data.get("player_a", {})
	var p_b = data.get("player_b", {})
	var p_a_name = p_a.get("name", "TenZ#NA1")
	var p_b_name = p_b.get("name", "Boaster#IGL")
	var p_a_char = p_a.get("character", "PHANTOM-9")
	var p_b_char = p_b.get("character", "SOL-VANGUARD")

	if player_a:
		player_a.setup_character(p_a.get("character_id", "char_phantom_9"), p_a_char, p_a_name)
	if player_b:
		player_b.setup_character(p_b.get("character_id", "char_sol_vanguard"), p_b_char, p_b_name)

	match_title_label.text = "%s vs %s" % [p_a_name, p_b_name]
	score_label.text = "%d - %d" % [p_a.get("score", 13), p_b.get("score", 9)]

	# Update Loadout Card Panels
	_update_loadout_panel(p_a, p_a_atk1, p_a_atk2, p_a_def1, p_a_def2)
	_update_loadout_panel(p_b, p_b_atk1, p_b_atk2, p_b_def1, p_b_def2)

	restart_match_playback()

func _update_loadout_panel(p_data: Dictionary, atk1_lbl: Label, atk2_lbl: Label, def1_lbl: Label, def2_lbl: Label) -> void:
	var atks = p_data.get("attack_cards", ["Quick Peek", "Double Peek"])
	var defs = p_data.get("defence_cards", ["Basic Hold", "Defensive Smoke"])
	if atks.size() > 0: atk1_lbl.text = "• " + str(atks[0]).replace("atk_", "").replace("_", " ").capitalize()
	if atks.size() > 1: atk2_lbl.text = "• " + str(atks[1]).replace("atk_", "").replace("_", " ").capitalize()
	if defs.size() > 0: def1_lbl.text = "• " + str(defs[0]).replace("def_", "").replace("_", " ").capitalize()
	if defs.size() > 1: def2_lbl.text = "• " + str(defs[1]).replace("def_", "").replace("_", " ").capitalize()

# ------------------------------------------------------------------------------
# BUILT-IN AI DUEL SIMULATOR (OFFLINE GENERATOR)
# ------------------------------------------------------------------------------

func simulate_ai_duel() -> void:
	if audio_synth: audio_synth.play_cue("sfx_button_click")
	var sim_names = ["TenZ#NA1", "Boaster#IGL", "Aspas#LEB", "Derke#FNTC", "Chronicle#M3C", "ScreaM#EDG"]
	var atk_pool = ["Quick Peek", "Double Peek", "Split Pressure", "Flash Entry", "Flank Infiltration", "Crossfire Setup"]
	var def_pool = ["Basic Hold", "Defensive Smoke", "Layered Defense", "Antirush Setup", "Anchor Protocol", "Counter Angle"]
	
	atk_pool.shuffle()
	def_pool.shuffle()
	sim_names.shuffle()

	var p_a_cards_atk = [atk_pool[0], atk_pool[1]]
	var p_a_cards_def = [def_pool[0], def_pool[1]]
	var p_b_cards_atk = [atk_pool[2], atk_pool[3]]
	var p_b_cards_def = [def_pool[2], def_pool[3]]

	var a_wins = randf() > 0.5
	var winner_name = sim_names[0] if a_wins else sim_names[1]

	var sim_data = {
		"match_id": "sim_%d" % Time.get_unix_time_from_system(),
		"total_duration_sec": 13.0,
		"player_a": {
			"name": sim_names[0],
			"character": "PHANTOM-9",
			"character_id": "char_phantom_9",
			"score": 13 if a_wins else 11,
			"attack_cards": p_a_cards_atk,
			"defence_cards": p_a_cards_def
		},
		"player_b": {
			"name": sim_names[1],
			"character": "SOL-VANGUARD",
			"character_id": "char_sol_vanguard",
			"score": 11 if a_wins else 13,
			"attack_cards": p_b_cards_atk,
			"defence_cards": p_b_cards_def
		},
		"winner_name": winner_name,
		"win_reason": "High-velocity angle breach and tactical utility combo.",
		"mvp_combo": "%s + %s" % [p_a_cards_atk[0] if a_wins else p_b_cards_atk[0], p_a_cards_def[0] if a_wins else p_b_cards_def[0]],
		"timeline": [
			{"step": 1, "timestamp_sec": 0.0, "actor": "player_a", "action_type": "emote", "emote_trigger": "emote_taunt", "sound_cue": "sfx_blade_whoosh", "commentary": "%s tests readiness with a tactical taunt." % sim_names[0]},
			{"step": 2, "timestamp_sec": 1.2, "actor": "player_b", "action_type": "emote", "emote_trigger": "emote_flex", "sound_cue": "sfx_power_charge", "commentary": "%s powers up defenses with an armored flex." % sim_names[1]},
			{"step": 3, "timestamp_sec": 2.8, "actor": "player_a", "action_type": "attack", "card_name": p_a_cards_atk[0], "animation_trigger": "anim_cast_slash", "damage_dealt": 30, "sound_cue": "sfx_gunfire_burst", "commentary": "%s initiates with %s dealing 30 damage." % [sim_names[0], p_a_cards_atk[0]]},
			{"step": 4, "timestamp_sec": 4.6, "actor": "player_b", "action_type": "defence", "card_name": p_b_cards_def[0], "animation_trigger": "anim_deploy_barrier", "damage_dealt": 0, "sound_cue": "sfx_shield_thump", "commentary": "%s deploys %s absorbing incoming fire." % [sim_names[1], p_b_cards_def[0]]},
			{"step": 5, "timestamp_sec": 6.2, "actor": "player_b", "action_type": "attack", "card_name": p_b_cards_atk[0], "animation_trigger": "anim_cast_cannon", "damage_dealt": 35, "sound_cue": "sfx_energy_blast", "commentary": "%s retaliates with %s for 35 damage." % [sim_names[1], p_b_cards_atk[0]]},
			{"step": 6, "timestamp_sec": 8.0, "actor": "player_a", "action_type": "defence", "card_name": p_a_cards_def[0], "animation_trigger": "anim_dodge_roll", "damage_dealt": 0, "sound_cue": "sfx_dodge_woosh", "commentary": "%s evades with %s." % [sim_names[0], p_a_cards_def[0]]},
			{"step": 7, "timestamp_sec": 9.5, "actor": "player_a" if a_wins else "player_b", "action_type": "climax", "card_name": p_a_cards_atk[1] if a_wins else p_b_cards_atk[1], "animation_trigger": "anim_cast_teleport", "damage_dealt": 70, "sound_cue": "sfx_critical_hit", "commentary": "CRITICAL FINISHER! %s strikes for 70 lethal damage!" % winner_name},
			{"step": 8, "timestamp_sec": 11.2, "actor": "player_b" if a_wins else "player_a", "action_type": "defeat", "animation_trigger": "anim_defeat", "emote_trigger": "emote_defeat", "damage_dealt": 0, "sound_cue": "sfx_defeat", "commentary": "Fatal blow landed! Combat shields completely depleted."},
			{"step": 9, "timestamp_sec": 12.2, "actor": "player_a" if a_wins else "player_b", "action_type": "victory", "animation_trigger": "anim_victory", "emote_trigger": "emote_celebrate", "damage_dealt": 0, "sound_cue": "sfx_victory_fanfare", "commentary": "🏆 MATCH VICTORY! %s dominates the arena!" % winner_name}
		]
	}

	load_sequence_data(sim_data)

# ------------------------------------------------------------------------------
# PLAYBACK ENGINE & TIMELINE PROCESSING
# ------------------------------------------------------------------------------

func restart_match_playback() -> void:
	victory_modal.visible = false
	if player_a: player_a.reset_stats()
	if player_b: player_b.reset_stats()
	
	current_step_index = 0
	elapsed_match_time = 0.0
	is_playing = true
	is_paused = false
	btn_play_pause.text = "⏸ Pause"
	status_badge.text = "LIVE COMBAT IN PROGRESS"
	status_badge.modulate = Color(0.0, 0.95, 0.5, 1.0)
	commentary_label.text = "[0.0s] Round begins! Tactical agents engage on site."

func toggle_play_pause() -> void:
	if not is_playing and timeline_events.size() > 0:
		restart_match_playback()
		return
	
	is_paused = !is_paused
	btn_play_pause.text = "▶ Play" if is_paused else "⏸ Pause"
	status_badge.text = "PAUSED" if is_paused else "LIVE COMBAT IN PROGRESS"
	status_badge.modulate = Color.YELLOW if is_paused else Color(0.0, 0.95, 0.5, 1.0)

func set_playback_speed(speed: float) -> void:
	playback_speed = speed
	if audio_synth: audio_synth.play_cue("sfx_button_click")

func step_forward() -> void:
	if current_step_index < timeline_events.size():
		var event = timeline_events[current_step_index]
		elapsed_match_time = float(event.get("timestamp_sec", 0.0))
		_execute_keyframe(event)
		current_step_index += 1

func step_backward() -> void:
	if current_step_index > 0:
		current_step_index = max(0, current_step_index - 2)
		elapsed_match_time = float(timeline_events[current_step_index].get("timestamp_sec", 0.0)) if current_step_index < timeline_events.size() else 0.0

func toggle_fullscreen() -> void:
	if DisplayServer.window_get_mode() == DisplayServer.WINDOW_MODE_FULLSCREEN:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	else:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)

func _process(delta: float) -> void:
	# Update Camera Shake Trauma
	if camera and camera_trauma > 0.0:
		camera_trauma = max(0.0, camera_trauma - delta * camera_trauma_decay)
		var shake = camera_trauma * camera_trauma
		camera.offset = Vector2(
			randf_range(-1.0, 1.0) * camera_max_offset.x * shake,
			randf_range(-1.0, 1.0) * camera_max_offset.y * shake
		)
	elif camera:
		camera.offset = Vector2.ZERO

	if not is_playing or is_paused:
		return
	
	elapsed_match_time += delta * playback_speed
	
	if progress_bar:
		progress_bar.value = (elapsed_match_time / max(total_match_duration, 1.0)) * 100.0
	if time_label:
		time_label.text = "%.1fs / %.1fs" % [elapsed_match_time, total_match_duration]
	
	if current_step_index < timeline_events.size():
		var next_event = timeline_events[current_step_index]
		var event_time = float(next_event.get("timestamp_sec", 0.0))
		
		if elapsed_match_time >= event_time:
			_execute_keyframe(next_event)
			current_step_index += 1
	
	if elapsed_match_time >= total_match_duration:
		_on_match_completed()

func _execute_keyframe(event: Dictionary) -> void:
	var actor_str = event.get("actor", "player_a")
	var actor_node = player_a if actor_str == "player_a" else player_b
	var opposing_node = player_b if actor_str == "player_a" else player_a
	
	var action_type = event.get("action_type", "")
	var anim_trigger = event.get("animation_trigger", "anim_idle")
	var emote_trigger = event.get("emote_trigger", "")
	var card_name = event.get("card_name", "")
	var damage = int(event.get("damage_dealt", 0))
	var sound_cue = event.get("sound_cue", "")
	var commentary = event.get("commentary", "")
	var is_critical = damage >= 50 or action_type.contains("climax")

	# Update Commentary
	if commentary_label and commentary != "":
		commentary_label.text = "[%.1fs] %s" % [event.get("timestamp_sec", 0.0), commentary]

	# Play Procedural Sound
	if audio_synth and sound_cue != "":
		audio_synth.play_cue(sound_cue)

	# Execute Emotes
	if emote_trigger != "" and emote_trigger != null:
		if actor_node:
			actor_node.play_emote(emote_trigger)
	else:
		if actor_node:
			actor_node.play_action(action_type, anim_trigger, damage, str(card_name if card_name != null else ""))
		
		# Laser Projectile FX
		if action_type.contains("attack") or action_type.contains("climax") or action_type.contains("strike"):
			_fire_laser_beam(actor_node.position, opposing_node.position, is_critical)
		
		# Apply Damage & Spark Burst
		if damage > 0 and opposing_node:
			opposing_node.apply_damage(damage, is_critical)
			_trigger_impact_sparks(opposing_node.position, is_critical)
			if is_critical:
				_add_camera_trauma(0.8)
			else:
				_add_camera_trauma(0.3)

func _fire_laser_beam(from_pos: Vector2, to_pos: Vector2, is_critical: bool) -> void:
	if not laser_line:
		return
	laser_line.points = PackedVector2Array([from_pos + Vector2(0, -60), to_pos + Vector2(0, -60)])
	laser_line.default_color = Color(1.0, 0.85, 0.2, 0.95) if is_critical else Color(0.0, 0.95, 1.0, 0.85)
	laser_line.width = 8.0 if is_critical else 4.5
	laser_line.visible = true
	
	var tween = create_tween()
	tween.tween_property(laser_line, "modulate:a", 0.0, 0.18)
	tween.tween_callback(func(): laser_line.visible = false; laser_line.modulate.a = 1.0)

func _trigger_impact_sparks(pos: Vector2, is_critical: bool) -> void:
	if not impact_sparks:
		return
	impact_sparks.position = pos + Vector2(0, -60)
	impact_sparks.color = Color(1.0, 0.9, 0.2, 1.0) if is_critical else Color(1.0, 0.3, 0.3, 1.0)
	impact_sparks.amount = 40 if is_critical else 20
	impact_sparks.restart()
	impact_sparks.emitting = true

func _add_camera_trauma(amount: float) -> void:
	camera_trauma = min(1.0, camera_trauma + amount)

func _on_match_completed() -> void:
	is_playing = false
	status_badge.text = "MATCH COMPLETED"
	status_badge.modulate = Color(1.0, 0.85, 0.0, 1.0)
	btn_play_pause.text = "🔁 Replay"
	
	var winner_name = current_match_data.get("winner_name", "TenZ#NA1")
	var win_reason = current_match_data.get("win_reason", "Tactical superiority.")
	var mvp_combo = current_match_data.get("mvp_combo", "Quick Peek + Flash Entry")
	
	commentary_label.text = "🏆 VICTORY: %s wins! %s" % [winner_name, win_reason]
	
	# Show Victory Modal
	if victory_modal:
		victory_winner_label.text = "CHAMPION: %s" % winner_name
		victory_combo_label.text = "MVP Combo: %s" % mvp_combo
		victory_reason_label.text = win_reason
		victory_modal.visible = true
		victory_modal.modulate = Color.TRANSPARENT
		var tween = create_tween()
		tween.tween_property(victory_modal, "modulate", Color.WHITE, 0.3)
