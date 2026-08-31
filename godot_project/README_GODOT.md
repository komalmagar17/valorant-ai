# 🎮 GODOT 4.X / 3.X LOCAL COMBAT ARENA

This folder contains the complete, ready-to-run **Godot Engine Local Combat Player** for Veer Survivor.

---

## ⚡ How It Works

1. **Players on Phones/Web**: Players pick their 4 tactics on their phone at `http://<your-ip>:8000/arena.html`.
2. **Admin on Laptop**: Admin opens `http://localhost:8000/admin.html` (Passcode: `K0lst@rno.1`), chooses the winner, and clicks **"Generate Godot Combat Sequence"**.
3. **Local Godot Game**: This Godot project runs on your PC screen / projector, automatically fetches the match timeline from `http://localhost:8000/api/matches/latest/godot-sequence`, and plays out the entire 2D battle between **PHANTOM-9** and **SOL-VANGUARD** with combat animations, damage numbers, and emotes!

---

## 🚀 How to Run in Godot

1. Open **Godot Engine (Godot 4.x or 3.x)**.
2. Click **Import** -> Browse to the `godot_project/` folder -> Select `project.godot`.
3. Click **Import & Edit**.
4. Press **F5** (or click the **Play** button in the top right).
5. The combat arena will open in fullscreen/windowed mode and begin playback!

### Keyboard Shortcuts
- **`[Spacebar]`**: Fetch and play the latest match from the backend (or replay current match).
- **`[F5]`**: Reload the scene.

---

## 📂 Project Structure

- `project.godot`: Project settings (1280x720 auto-scaling).
- `MainCombatArena.tscn`: Main 2D scene containing the arena, characters, health bars, top score bar, and commentary ticker.
- `MainCombatArena.gd`: Fetches timeline via REST HTTP / local JSON and steps through timestamps.
- `Character2D.gd`: Handles animations, dash attacks, shields, damage popups, and all 7+ emotes (*Dance, Taunt, Celebrate, Flex, Salute, GG, Defeat*).
- `godot_match_sequence.json`: Local fallback sequence file for offline playback.
