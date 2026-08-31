# 🎯 VEER SURVIVOR — TACTICAL CARD COMBAT & GODOT ENGINE SEQUENCER

> **Admin-Controlled 1v1 Tactical Combat Simulator with Godot 4.x Sequence Generation, Manual Match Adjudication, and 2 Fully Animated Characters.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-red.svg)](https://docs.pydantic.dev/)
[![Godot](https://img.shields.io/badge/Godot-4.x%20%2F%203.x-478cbf.svg)](https://godotengine.org/)
[![Vercel](https://img.shields.io/badge/Vercel-Deployed-black.svg)](https://vercel.com/)

---

## ⚡ Overview

**Veer Survivor** is a competitive tactical card combat engine. Real players draft a **4-Card Loadout (2 Attack + 2 Defence Tactics)** from a 120-card master arsenal.

In the **Admin Command Center** (`/admin.html`), matches are **100% manually adjudicated** (no unilateral AI predictions). The Admin decides the Winner, Scores, Characters, and Win Factors. The AI then compiles the complete **Godot Action Sequence Timeline** (with timestamps, abilities, damage, SFX cues, and emote triggers) ready for local Godot Engine playback!

---

## 🔐 Admin Command Center Access

- **URL**: `http://localhost:8000/admin.html` (or `https://your-domain.vercel.app/admin.html`)
- **Required Admin Passcode**: `K0lst@rno.1`

All administrative actions (match adjudication, queue clearing, API key management) are strictly password-protected.

---

## 🦸 2 Playable Characters & Full Emote Suite

The game features two distinct combat characters with animation and emote sets:

| Character | Archetype | Combat Animations | Emotes Supported |
|---|---|---|---|
| **🗡️ PHANTOM-9** | High-Speed Duelist / Assassin | `idle`, `run`, `cast_attack_1`, `cast_attack_2`, `deploy_smoke`, `dodge_roll`, `hit_stagger`, `victory_pose`, `defeat_fall` | 🕺 **Cyber Breakdance**<br>🗡️ **Blade Spin Taunt**<br>🎉 **Holo-Trophy Cheer**<br>💪 **Blaster Flex**<br>🫡 **Spec-Ops Salute**<br>👋 **GG Wave**<br>🤦 **Disappointed Defeat** |
| **🛡️ SOL-VANGUARD** | Heavy Sentinel / Molten Titan | `idle`, `run`, `cast_attack_1`, `cast_attack_2`, `deploy_barrier`, `parry_stance`, `hit_stagger`, `victory_pose`, `defeat_fall` | 🤖 **Titan Robot Dance**<br>🦍 **Chest Thump Roar**<br>🏆 **Ground Slam Fireworks**<br>💥 **Molten Flex**<br>🛡️ **Shield Tap Salute**<br>👊 **Heavy Fist Bump**<br>💔 **Kneeling Defeat** |

*You can test all character emotes and audio cues interactively in the Admin Command Center!*

---

## 🎮 Godot Engine Integration

When a match is adjudicated in the Admin panel, the AI generates a keyframe action sequence:

### 1. Download or Fetch JSON
- **1-Click Download**: Download `godot_match_sequence.json` directly from the Admin UI.
- **REST API Endpoint**:
  ```http
  GET /api/matches/<match_id>/godot-sequence
  GET /api/matches/latest/godot-sequence
  ```

### 2. Drop-in GDScript Player
Attach [`godot/godot_combat_timeline_player.gd`](godot/godot_combat_timeline_player.gd) to your Godot scene root. It will parse the timeline, play character animations on `AnimationPlayer`, emit audio cues, and display synchronized commentary!

---

## 🚀 Quick Start

### 1. Run Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Start Server
python server.py
```
- 🌐 **Arena UI**: [http://localhost:8000/arena.html](http://localhost:8000/arena.html)
- 🛠️ **Admin Command**: [http://localhost:8000/admin.html](http://localhost:8000/admin.html) (Passcode: `K0lst@rno.1`)

### 2. Run Tests
```bash
python -m unittest test_server.py
```

---

## 🌐 Deploy to Vercel

1. Commit and push your code to GitHub:
   ```bash
   git add .
   git commit -m "Configure manual adjudication, Godot sequence exporter, and 2-character emote system"
   git push origin main
   ```
2. Import repo into [Vercel](https://vercel.com/new).
3. (Optional) Set Environment Variables:
   - `ADMIN_PASSWORD`: `K0lst@rno.1`
   - `GEMINI_API_KEY`: Your Gemini API Key from [Google AI Studio](https://aistudio.google.com).
4. Click **Deploy**!
