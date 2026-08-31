# ==============================================================================
# AudioSynth.gd - Procedural Sound Synthesizer for Godot 4.x / 3.x
# ==============================================================================
# Generates real-time procedural PCM AudioStreamWAV waveforms directly in GDScript.
# Provides instant, crisp combat sound effects (slashes, gunfire, shields,
# dodges, critical hits, victory fanfare, and emote jingles) out of the box.
# ==============================================================================

extends Node
class_name AudioSynth

var cached_streams: Dictionary = {}
var audio_players: Array[AudioStreamPlayer] = []
var max_voices: int = 8
var current_voice: int = 0

func _ready() -> void:
	# Instantiate polyphonic AudioStreamPlayer pool
	for i in range(max_voices):
		var p = AudioStreamPlayer.new()
		p.name = "Voice_%d" % i
		add_child(p)
		audio_players.append(p)
	
	# Pre-generate common sound effects
	_generate_all_cues()

func _generate_all_cues() -> void:
	cached_streams["sfx_blade_whoosh"] = _synth_whoosh(22050, 0.22, 650.0, 180.0)
	cached_streams["sfx_gunfire_burst"] = _synth_gunfire(22050, 0.28)
	cached_streams["sfx_shield_thump"] = _synth_shield(22050, 0.35, 120.0)
	cached_streams["sfx_dodge_woosh"] = _synth_whoosh(22050, 0.18, 250.0, 550.0)
	cached_streams["sfx_critical_hit"] = _synth_critical(22050, 0.55)
	cached_streams["sfx_energy_blast"] = _synth_laser(22050, 0.25, 900.0, 150.0)
	cached_streams["sfx_victory_fanfare"] = _synth_fanfare(22050)
	cached_streams["sfx_defeat"] = _synth_defeat_sound(22050)
	cached_streams["sfx_button_click"] = _synth_click(22050, 0.04, 1200.0)
	cached_streams["sfx_power_charge"] = _synth_charge(22050, 0.4)
	cached_streams["sfx_steam_release"] = _synth_noise(22050, 0.3, 0.4)

func play_cue(cue_name: String, volume_db: float = 0.0) -> void:
	if not cached_streams.has(cue_name):
		# Fallback match by pattern
		if cue_name.contains("slash") or cue_name.contains("whoosh"):
			cue_name = "sfx_blade_whoosh"
		elif cue_name.contains("gun") or cue_name.contains("burst"):
			cue_name = "sfx_gunfire_burst"
		elif cue_name.contains("shield") or cue_name.contains("thump"):
			cue_name = "sfx_shield_thump"
		elif cue_name.contains("crit") or cue_name.contains("slam"):
			cue_name = "sfx_critical_hit"
		elif cue_name.contains("fanfare") or cue_name.contains("victory"):
			cue_name = "sfx_victory_fanfare"
		elif cue_name.contains("blast") or cue_name.contains("laser") or cue_name.contains("cannon"):
			cue_name = "sfx_energy_blast"
		elif cue_name.contains("dodge"):
			cue_name = "sfx_dodge_woosh"
		else:
			cue_name = "sfx_blade_whoosh"

	var stream = cached_streams.get(cue_name, null)
	if stream and audio_players.size() > 0:
		var player = audio_players[current_voice]
		current_voice = (current_voice + 1) % max_voices
		player.stream = stream
		player.volume_db = volume_db
		player.play()

# ------------------------------------------------------------------------------
# PROCEDURAL WAVEFORM GENERATORS (8-bit PCM)
# ------------------------------------------------------------------------------

func _create_stream(bytes: PackedByteArray, sample_rate: int = 22050) -> AudioStreamWAV:
	var wav = AudioStreamWAV.new()
	wav.format = AudioStreamWAV.FORMAT_8_BITS
	wav.mix_rate = sample_rate
	wav.stereo = false
	wav.data = bytes
	return wav

func _synth_whoosh(sample_rate: int, duration: float, start_freq: float, end_freq: float) -> AudioStreamWAV:
	var total_samples = int(sample_rate * duration)
	var bytes = PackedByteArray()
	bytes.resize(total_samples)
	var phase = 0.0
	for i in range(total_samples):
		var t = float(i) / float(total_samples)
		var freq = lerp(start_freq, end_freq, t)
		phase += 2.0 * PI * freq / float(sample_rate)
		var env = sin(t * PI) # Parabolic volume envelope
		var sample = sin(phase) * 0.7 * env + (randf() * 2.0 - 1.0) * 0.3 * env
		bytes[i] = clampi(int((sample * 127.0) + 128.0), 0, 255)
	return _create_stream(bytes, sample_rate)

func _synth_gunfire(sample_rate: int, duration: float) -> AudioStreamWAV:
	var total_samples = int(sample_rate * duration)
	var bytes = PackedByteArray()
	bytes.resize(total_samples)
	var phase = 0.0
	for i in range(total_samples):
		var t = float(i) / float(total_samples)
		var env = exp(-t * 12.0)
		var punch_freq = lerp(260.0, 50.0, clampf(t * 3.0, 0.0, 1.0))
		phase += 2.0 * PI * punch_freq / float(sample_rate)
		var noise = (randf() * 2.0 - 1.0)
		var sample = (sin(phase) * 0.5 + noise * 0.5) * env
		bytes[i] = clampi(int((sample * 127.0) + 128.0), 0, 255)
	return _create_stream(bytes, sample_rate)

func _synth_shield(sample_rate: int, duration: float, freq: float) -> AudioStreamWAV:
	var total_samples = int(sample_rate * duration)
	var bytes = PackedByteArray()
	bytes.resize(total_samples)
	var phase = 0.0
	for i in range(total_samples):
		var t = float(i) / float(total_samples)
		var env = sin(pow(t, 0.4) * PI) * exp(-t * 3.5)
		phase += 2.0 * PI * freq / float(sample_rate)
		var shimmer = sin(phase * 3.1) * 0.25
		var sample = (sin(phase) * 0.75 + shimmer) * env
		bytes[i] = clampi(int((sample * 127.0) + 128.0), 0, 255)
	return _create_stream(bytes, sample_rate)

func _synth_critical(sample_rate: int, duration: float) -> AudioStreamWAV:
	var total_samples = int(sample_rate * duration)
	var bytes = PackedByteArray()
	bytes.resize(total_samples)
	var phase1 = 0.0
	var phase2 = 0.0
	for i in range(total_samples):
		var t = float(i) / float(total_samples)
		var env = exp(-t * 6.0)
		var punch_freq = lerp(450.0, 45.0, clampf(t * 4.0, 0.0, 1.0))
		phase1 += 2.0 * PI * punch_freq / float(sample_rate)
		phase2 += 2.0 * PI * 880.0 / float(sample_rate) # High impact chime
		var noise = (randf() * 2.0 - 1.0) * 0.4
		var sample = (sin(phase1) * 0.5 + sin(phase2) * 0.25 * exp(-t * 15.0) + noise) * env
		bytes[i] = clampi(int((sample * 127.0) + 128.0), 0, 255)
	return _create_stream(bytes, sample_rate)

func _synth_laser(sample_rate: int, duration: float, start_freq: float, end_freq: float) -> AudioStreamWAV:
	var total_samples = int(sample_rate * duration)
	var bytes = PackedByteArray()
	bytes.resize(total_samples)
	var phase = 0.0
	for i in range(total_samples):
		var t = float(i) / float(total_samples)
		var freq = lerp(start_freq, end_freq, pow(t, 0.6))
		phase += 2.0 * PI * freq / float(sample_rate)
		var env = exp(-t * 7.0)
		var raw = 1.0 if sin(phase) > 0.0 else -1.0
		var sample = raw * 0.6 * env
		bytes[i] = clampi(int((sample * 127.0) + 128.0), 0, 255)
	return _create_stream(bytes, sample_rate)

func _synth_fanfare(sample_rate: int) -> AudioStreamWAV:
	var notes = [261.63, 329.63, 392.0, 523.25]
	var note_dur = 0.12
	var total_samples = int(sample_rate * (note_dur * 4.0 + 0.5))
	var bytes = PackedByteArray()
	bytes.resize(total_samples)
	
	for n_idx in range(notes.size()):
		var freq = notes[n_idx]
		var start_sample = int(n_idx * note_dur * sample_rate)
		var end_sample = int((n_idx + 1) * note_dur * sample_rate) if n_idx < 3 else total_samples
		var phase = 0.0
		for i in range(start_sample, end_sample):
			var local_t = float(i - start_sample) / float(end_sample - start_sample)
			var env = exp(-local_t * (3.0 if n_idx < 3 else 1.5))
			phase += 2.0 * PI * freq / float(sample_rate)
			var sample = (sin(phase) * 0.6 + sin(phase * 2.0) * 0.3) * env
			bytes[i] = clampi(int((sample * 127.0) + 128.0), 0, 255)
	return _create_stream(bytes, sample_rate)

func _synth_defeat_sound(sample_rate: int) -> AudioStreamWAV:
	var total_samples = int(sample_rate * 0.6)
	var bytes = PackedByteArray()
	bytes.resize(total_samples)
	var phase = 0.0
	for i in range(total_samples):
		var t = float(i) / float(total_samples)
		var freq = lerp(320.0, 110.0, t)
		phase += 2.0 * PI * freq / float(sample_rate)
		var env = (1.0 - t) * 0.7
		var sample = sin(phase) * env
		bytes[i] = clampi(int((sample * 127.0) + 128.0), 0, 255)
	return _create_stream(bytes, sample_rate)

func _synth_click(sample_rate: int, duration: float, freq: float) -> AudioStreamWAV:
	var total_samples = int(sample_rate * duration)
	var bytes = PackedByteArray()
	bytes.resize(total_samples)
	var phase = 0.0
	for i in range(total_samples):
		var t = float(i) / float(total_samples)
		var env = exp(-t * 25.0)
		phase += 2.0 * PI * freq / float(sample_rate)
		var sample = sin(phase) * env * 0.8
		bytes[i] = clampi(int((sample * 127.0) + 128.0), 0, 255)
	return _create_stream(bytes, sample_rate)

func _synth_charge(sample_rate: int, duration: float) -> AudioStreamWAV:
	var total_samples = int(sample_rate * duration)
	var bytes = PackedByteArray()
	bytes.resize(total_samples)
	var phase = 0.0
	for i in range(total_samples):
		var t = float(i) / float(total_samples)
		var freq = lerp(120.0, 680.0, pow(t, 2.0))
		phase += 2.0 * PI * freq / float(sample_rate)
		var env = pow(t, 0.7) * 0.6
		var sample = sin(phase) * env
		bytes[i] = clampi(int((sample * 127.0) + 128.0), 0, 255)
	return _create_stream(bytes, sample_rate)

func _synth_noise(sample_rate: int, duration: float, decay: float) -> AudioStreamWAV:
	var total_samples = int(sample_rate * duration)
	var bytes = PackedByteArray()
	bytes.resize(total_samples)
	for i in range(total_samples):
		var t = float(i) / float(total_samples)
		var env = exp(-t / max(decay, 0.01))
		var sample = (randf() * 2.0 - 1.0) * env * 0.5
		bytes[i] = clampi(int((sample * 127.0) + 128.0), 0, 255)
	return _create_stream(bytes, sample_rate)
