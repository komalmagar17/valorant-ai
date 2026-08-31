# 🎯 VALORANT TACTICAL MASTERCLASS — AI COMBAT ARENA

> **The First Fully LLM-Powered Ability-vs-Ability Tactical Card Combat Simulation Engine.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-red.svg)](https://docs.pydantic.dev/)
[![Gemini AI](https://img.shields.io/badge/Google-Gemini_AI-orange.svg)](https://aistudio.google.com/)
[![Three.js](https://img.shields.io/badge/Three.js-3D_Mascot-green.svg)](https://threejs.org/)

---

## ⚡ Overview

**Valorant Tactical Masterclass** is an industry-grade tactical card battle simulator where players draft a **4-Card Loadout (2 Attack + 2 Defence Tactics)** from a master 120-card arsenal.

A multi-agent AI pipeline orchestrates combat adjudication:
1. **⚔️ Attack AI (LLM A)**: Deconstructs offensive loadouts into optimal execution sequences.
2. **🛡️ Defence AI (LLM B)**: Structures defensive positioning, stall tactics, and retake strategies.
3. **⚖️ Evaluation AI / Master Referee (LLM C)**: Resolves dynamic synergy, damage/shield deltas, counter-mechanics, and outputs round-by-round esports commentary.

---

## 🎮 Features

- **Cinematic Welcome Screen (`index.html`)**: High-contrast, stylized 2D/3D concept graphics with particle clash systems, kinetic scanlines, and instant full-screen warp transitions.
- **Interactive 120-Card Arena (`arena.html`)**:
  - **Three.js 3D Mascot ("Boba-Bot")**: Interactive companion with mouse tracking.
  - **4-Card Loadout Dock**: Strictly validates 2 Attack + 2 Defence tactics.
  - **Instant Search & Category Filters**: Explore all 60 Attack + 60 Defence tactics.
  - **"Processing the Result..." Flow**: Real-time async match evaluation.
- **Persistent Database Queue**: JSON database store logging match records, health states, and MVP combos.
- **Offline + Online Dual-Mode**: Built-in deterministic tactical rule simulator when offline, with seamless Google Gemini API integration when an API key is provided.

---

## 🚀 Quick Start

### 1. Clone & Install Dependencies
```bash
# Clone the repository
git clone https://github.com/komalmagar17/valorant-ai.git
cd valorant-ai

# Install dependencies
pip install -r requirements.txt
```

### 2. (Optional) Set Google Gemini API Key
To enable live LLM commentary and dynamic AI strategy generation:
```bash
export GEMINI_API_KEY="your_api_key_from_aistudio.google.com"
```
*(If omitted, the engine automatically runs using the high-performance offline tactical simulator).*

### 3. Launch the Server
```bash
python server.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser!

---

## 📂 Project Structure

```text
├── ai/
│   ├── attack/              # Attack AI planner & test suite
│   ├── defence/             # Defence AI planner & test suite
│   └── evaluation/          # Master Referee AI evaluator & test suite
├── data/
│   └── cards.py             # 120-card tactical database (60 Atk + 60 Def)
├── database/
│   ├── db.py                # Thread-safe persistent match database
│   └── matches.json         # Match records & evaluations
├── public/
│   ├── index.html           # Cinematic Welcome & Landing Screen
│   ├── arena.html           # 120-Card Selection Arena & Dock
│   ├── welcome.css / .js    # Welcome page styles & warp audio synth
│   ├── style.css / app.js   # Arena styles & 3D Three.js mascot
│   └── assets/              # High-res concept art & media
├── match_engine.py          # 1v1 Match Engine orchestrator
├── server.py                # Production REST API & Web Server
├── requirements.txt         # Dependencies
└── README.md
```

---

## 🧪 Testing

Run all unit test suites across the AI pipeline:
```bash
python -m unittest discover -s ai -p "test_*.py"
```

Run a standalone 1v1 match simulation directly in the CLI:
```bash
python match_engine.py
```

---

## 📡 REST API Endpoints

- `GET  /api/cards` — Retrieve all 120 sanitized tactical cards (internal tiers hidden).
- `POST /api/submit-match` — Submit 2 Attack + 2 Defence card loadout.
- `GET  /api/matches` — List recent database matches.
- `GET  /api/matches/<match_id>` — Fetch detailed round evaluation for a specific match.

## 🌐 Deploy to Vercel

This application is 100% pre-configured and hardened for instantaneous deployment to **Vercel**:

1. **Push to GitHub**:
   Ensure all changes are committed and pushed to your repository.
2. **Import into Vercel**:
   Go to [vercel.com/new](https://vercel.com/new) and import your repository.
3. **Configure Environment Variables** *(Vercel Dashboard > Project Settings > Environment Variables)*:
   - `ADMIN_PASSWORD`: A secure passcode to protect the Admin Command Center (`/admin.html`).
   - `GEMINI_API_KEY`: *(Optional)* Your Google Gemini API Key from [Google AI Studio](https://aistudio.google.com). (If omitted, intelligent offline tactical simulation is used).
4. **Deploy**:
   Click **Deploy**. Vercel will serve your static UI from its global Edge CDN and route all API calls to the serverless Python functions (`/api/*`).

---

## 📜 License
MIT License. Created for the Tactical AI Masterclass.
