# ==============================================================================
# godot_combat_timeline_player.gd
# ==============================================================================
# Drop-in Godot 4.x / 3.x Script for playback of AI-generated combat sequences.
# Connects to Veer Survivor REST API or loads godot_match_sequence.json directly.
# ==============================================================================

extends Node2D

signal combat_sequence_started
signal action_step_triggered(step_data)
signal combat_sequence_completed(winner_id)

@export var api_match_url: String = "http://localhost:8000/api/matches/latest/godot-sequence"
@export var autoplay_on_ready: bool = true

# Character Node References (Set in Inspector or automatically resolved)
@onready var player_a_anim: AnimationPlayer = $PlayerA/AnimationPlayer if has_node("PlayerA/AnimationPlayer") else null
@onready var player_b_anim: AnimationPlayer = $PlayerB/AnimationPlayer if has_node("PlayerB/AnimationPlayer") else null
@onready var audio_player: AudioStreamPlayer = $AudioStreamPlayer if has_node("AudioStreamPlayer") else null

var timeline_events: Array = []
var current_step_index: int = 0
var is_playing: bool = false
var elapsed_match_time: float = 0.0

func _ready() -> void:
	if autoplay_on_ready:
		load_sequence_from_local_or_network()

func load_sequence_from_json_string(json_text: String) -> void:
	var json = JSON.new()
	var parse_err = json.parse(json_text)
	if parse_err == OK:
		var data = json.get_data()
		if data.has("timeline"):
			timeline_events = data["timeline"]
			current_step_index = 0
			elapsed_match_time = 0.0
			is_playing = true
			emit_signal("combat_sequence_started")
			print("[GODOT COMBAT] Timeline loaded: %d keyframe events" % timeline_events.size())

func _process(delta: float) -> void:
	if not is_playing or current_step_index >= timeline_events.size():
		return
	
	elapsed_match_time += delta
	var next_event = timeline_events[current_step_index]
	var event_time = float(next_event.get("timestamp_sec", 0.0))
	
	if elapsed_match_time >= event_time:
		_execute_timeline_event(next_event)
		current_step_index += 1
		if current_step_index >= timeline_events.size():
			is_playing = false
			emit_signal("combat_sequence_completed", next_event.get("winner_id", ""))
			print("[GODOT COMBAT] Match sequence completed successfully!")

func _execute_timeline_event(event: Dictionary) -> void:
	var actor = event.get("actor", "player_a") # player_a or player_b
	var anim_trigger = event.get("animation_trigger", "anim_idle")
	var emote_trigger = event.get("emote_trigger", "")
	var target_anim = player_a_anim if actor == "player_a" else player_b_anim
	var sound_cue = event.get("sound_cue", "")
	var commentary = event.get("commentary", "")

	print("[%.2fs] [%s] Action: %s | Anim: %s | Emote: %s | %s" % [
		elapsed_match_time,
		actor.to_upper(),
		event.get("action_type", ""),
		anim_trigger,
		emote_trigger,
		commentary
	])

	# Play Animation on Target Character
	if target_anim:
		if emote_trigger != "" and target_anim.has_animation(emote_trigger):
			target_anim.play(emote_trigger)
		elif target_anim.has_animation(anim_trigger):
			target_anim.play(anim_trigger)

	emit_signal("action_step_triggered", event)

func load_sequence_from_local_or_network() -> void:
	# Check for local file first
	if FileAccess.file_exists("res://godot_match_sequence.json"):
		var f = FileAccess.open("res://godot_match_sequence.json", FileAccess.READ)
		var content = f.get_as_text()
		f.close()
		load_sequence_from_json_string(content)
