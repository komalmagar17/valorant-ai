# ==============================================================================
# MainCombatArena.gd
# ==============================================================================
# Main Godot Local Combat Arena Controller.
# Connects to Veer Survivor REST backend (or reads local JSON), orchestrates
# 2D character combat, plays audio cues, and displays esports commentary.
# ==============================================================================

extends Node2D

@export var api_url: String = "http://localhost:8000/api/matches/latest/godot-sequence"
@export var autoplay: bool = true

@onready var player_a: Character2D = $PlayerA
@onready var player_b: Character2D = $PlayerB
@onready var http_request: HTTPRequest = $HTTPRequest
@onready var match_title_label: Label = $CanvasLayer/TopBar/MatchTitle
@onready var score_label: Label = $CanvasLayer/TopBar/ScoreLabel
@onready var commentary_label: Label = $CanvasLayer/BottomBar/CommentaryLabel
@onready var status_badge: Label = $CanvasLayer/TopBar/StatusBadge
@onready var progress_bar: ProgressBar = $CanvasLayer/TimelineBar

var timeline_events: Array = []
var current_step_index: int = 0
var is_playing: bool = false
var elapsed_match_time: float = 0.0
var total_match_duration: float = 14.5
var current_match_data: Dictionary = {}

func _ready() -> void:
	if http_request:
		http_request.request_completed.connect(_on_http_request_completed)
	
	if autoplay:
		fetch_latest_match()

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_accept"): # Spacebar
		if not is_playing and timeline_events.size() > 0:
			restart_match_playback()
		else:
			fetch_latest_match()

# ------------------------------------------------------------------------------
# MATCH DATA LOADING (REST API OR LOCAL JSON)
# ------------------------------------------------------------------------------

func fetch_latest_match() -> void:
	status_badge.text = "FETCHING LATEST MATCH..."
	if http_request:
		var err = http_request.request(api_url)
		if err != OK:
			print("[GODOT] HTTP request failed, falling back to local JSON file.")
			_load_local_json_fallback()
	else:
		_load_local_json_fallback()

func _on_http_request_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray) -> void:
	if response_code == 200:
		var json = JSON.new()
		var parse_err = json.parse(body.get_string_from_utf8())
		if parse_err == OK and json.get_data() is Dictionary:
			load_sequence_data(json.get_data())
			return
	
	print("[GODOT] Network fetch unsuccessful (%d). Loading local fallback." % response_code)
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
	
	status_badge.text = "READY - NO MATCH DATA"
	commentary_label.text = "Waiting for match adjudication from admin.html..."

func load_sequence_data(data: Dictionary) -> void:
	current_match_data = data
	timeline_events = data.get("timeline", [])
	total_match_duration = float(data.get("total_duration_sec", 14.5))

	var p_a = data.get("player_a", {})
	var p_b = data.get("player_b", {})
	var p_a_name = p_a.get("name", "Agent Alpha")
	var p_b_name = p_b.get("name", "Agent Omega")
	var p_a_char = p_a.get("character", "PHANTOM-9")
	var p_b_char = p_b.get("character", "SOL-VANGUARD")

	if player_a:
		player_a.setup_character(p_a.get("character_id", "char_phantom_9"), p_a_char, p_a_name)
	if player_b:
		player_b.setup_character(p_b.get("character_id", "char_sol_vanguard"), p_b_char, p_b_name)

	match_title_label.text = "%s vs %s" % [p_a_name, p_b_name]
	score_label.text = "%d - %d" % [p_a.get("score", 13), p_b.get("score", 9)]

	restart_match_playback()

func restart_match_playback() -> void:
	if player_a:
		player_a.reset_stats()
	if player_b:
		player_b.reset_stats()
	
	current_step_index = 0
	elapsed_match_time = 0.0
	is_playing = true
	status_badge.text = "LIVE BATTLE IN PROGRESS"
	commentary_label.text = "Round begins! Tactical agents engage on site."

# ------------------------------------------------------------------------------
# TIMELINE PROCESSOR
# ------------------------------------------------------------------------------

func _process(delta: float) -> void:
	if not is_playing:
		return
	
	elapsed_match_time += delta
	if progress_bar:
		progress_bar.value = (elapsed_match_time / total_match_duration) * 100.0
	
	if current_step_index < timeline_events.size():
		var next_event = timeline_events[current_step_index]
		var event_time = float(next_event.get("timestamp_sec", 0.0))
		
		if elapsed_match_time >= event_time:
			_execute_keyframe(next_event)
			current_step_index += 1
	
	if elapsed_match_time >= total_match_duration:
		is_playing = false
		status_badge.text = "MATCH COMPLETED"
		var winner_name = current_match_data.get("winner_name", "Champion")
		var win_reason = current_match_data.get("win_reason", "")
		commentary_label.text = "🏆 VICTORY: %s wins! %s" % [winner_name, win_reason]

func _execute_keyframe(event: Dictionary) -> void:
	var actor_str = event.get("actor", "player_a")
	var actor_node = player_a if actor_str == "player_a" else player_b
	var opposing_node = player_b if actor_str == "player_a" else player_a
	
	var action_type = event.get("action_type", "")
	var anim_trigger = event.get("animation_trigger", "anim_idle")
	var emote_trigger = event.get("emote_trigger", "")
	var damage = int(event.get("damage_dealt", 0))
	var commentary = event.get("commentary", "")

	if commentary_label and commentary != "":
		commentary_label.text = "[%.1fs] %s" % [event.get("timestamp_sec", 0.0), commentary]

	# Execute Emotes or Combat Animations
	if emote_trigger != "" and emote_trigger != null:
		if actor_node:
			actor_node.play_emote(emote_trigger)
	else:
		if actor_node:
			actor_node.play_action(action_type, anim_trigger, damage)
		if damage > 0 and opposing_node:
			opposing_node.apply_damage(damage)
