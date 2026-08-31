# 🎮 GODOT 4.X LOCAL COMBAT ARENA — VEER SURVIVOR

This folder contains the complete, native **Godot Engine 2D Combat Game** for Veer Survivor.
All combat rendering, animations, procedural sound synthesis, particle VFX, card loadout HUDs, character emotes, and duel simulation run **100% natively inside Godot Engine**.

---

## ⚡ Key Features in Godot Engine

1. **Native 2D Combat Arena**:
   - Cyberpunk battle arena with ambient energy embers (`CPUParticles2D`), glowing platforms, and dynamic laser beam projectile effects.
   - Screen shake camera trauma on heavy impacts and critical strikes.
2. **2D Animated Agents (PHANTOM-9 & SOL-VANGUARD)**:
   - Full 8-frame spritesheet animations for idle, dash slashes, cannon blasts, barrier deployments, evasion rolls, hit reactions, and victory/defeat sequences.
   - Dual-layer health bars with Street Fighter-style smooth trailing ghost damage bars.
   - Dynamic floating combat damage numbers (with critical strike scaling & colors).
   - In-game Ability Card popouts (e.g. `[ATTACK] Quick Peek`, `[DEFENCE] Defensive Smoke`).
3. **Procedural Audio Synthesizer (`AudioSynth.gd`)**:
   - Built-in real-time PCM audio generator that synthesizes slashes, gunfire bursts, shield thumps, laser beams, critical impacts, and victory fanfare natively. No missing `.wav` dependencies!
4. **Complete Character Emote Suite**:
   - 7 Full Emotes: *Dance, Taunt, Celebrate, Flex, Salute, GG, Defeat* with animated speech bubbles and sprite cycling.
   - Dedicated on-screen Emote Buttons and hotkeys to trigger emotes for either character anytime.
5. **Interactive In-Engine Playback HUD**:
   - Play/Pause, Step Backward, Step Forward, Timeline progress bar, Speed multipliers (`0.5x`, `1x`, `2x`).
   - **`[Simulate AI Duel]` Button**: Instantly generates and simulates a tactical match with randomized card combos offline without needing any server running.
   - **`[Fetch Live]` Button**: Pulls the latest live adjudicated match from the backend REST API (`http://localhost:8000/api/matches/latest/godot-sequence`).
6. **Victory & MVP Modal**:
   - End-of-round championship summary displaying the winning agent, MVP ability combo, tactical win reason, and replay/rematch buttons.

---

## 🚀 How to Run in Godot

1. Open **Godot Engine (Godot 4.x)**.
2. Click **Import** -> Browse to this `godot_project/` folder -> Select `project.godot`.
3. Click **Import & Edit**.
4. Press **`F5`** (or click the **Play** icon in the top right corner).
5. The combat arena runs immediately in windowed or fullscreen mode!

### ⌨️ Keyboard Shortcuts
- **`[Spacebar]`**: Toggle Play / Pause (or replay finished battle).
- **`[S]`**: Simulate a new randomized AI Tactical Duel immediately.
- **`[F]`**: Fetch the latest adjudicated match from the live server.
- **`[R]`**: Restart / replay the current match from 0.0s.
- **`[F11]`**: Toggle Fullscreen mode.
- **`[1] / [2] / [3] / [4]`**: Trigger Dance, Taunt, Celebrate, Flex on Player A.
- **`[7] / [8] / [9] / [0]`**: Trigger Dance, Taunt, Celebrate, Flex on Player B.

---

## 📂 Project Structure

- `project.godot`: Godot 4.x project settings (1280x720 auto-scaling canvas).
- `MainCombatArena.tscn`: Main 2D scene with platform, particles, characters, laser nodes, HUD, and victory modal.
- `MainCombatArena.gd`: Main combat controller, timeline processor, camera shake, and UI logic.
- `Character2D.gd`: 2D character controller with spritesheet frame cycles, health/ghost bars, and emotes.
- `AudioSynth.gd`: Real-time procedural audio engine generating all combat SFX.
- `assets/phantom9_spritesheet.png`: 8-frame 8-row spritesheet for PHANTOM-9.
- `assets/solvanguard_spritesheet.png`: 8-frame 9-row spritesheet for SOL-VANGUARD.
- `godot_match_sequence.json`: Local fallback sequence file for offline combat playback.
