"""
================================================================================
server.py
================================================================================

Production-grade Python Web & REST API Server.
- Serves Web Frontends from `public/` (Arena, Landing, Admin Command Center)
- Decoupled Player Submission Queue: Web users submit 4-card tactical loadouts
  into a persistent SQLite queue without triggering instant AI or random bots.
- Admin-Controlled Matchmaking & Manual Adjudication: Admin controls match outcome
  manually (no automatic AI prediction) and triggers AI Godot sequence generation.
- Password-gated Admin Panel with required passcode: `K0lst@rno.1`.
- Godot 4.x / 3.x Combat Sequence Generator & REST Exporter.
- 2 Playable Characters with full animation and emote manifest.

REST Endpoints:
  - `GET  /api/cards`: Returns all 120 cards (Sanitized of all Tier & Power data).
  - `GET  /api/characters`: Returns all 2 characters with complete animation/emote suites.
  - `POST /api/submit-match` / `POST /api/submit-loadout`: Queues a player loadout.
  - `GET  /api/submissions`: Lists all queued player loadouts.
  - `DELETE /api/submissions/<id>`: Removes a submission from queue (Admin).
  - `POST /api/submissions/clear`: Clears queued submissions (Admin).
  - `GET  /api/admin/auth-status`: Returns whether admin passcode is required.
  - `POST /api/admin/verify`: Verifies admin passcode (`K0lst@rno.1`).
  - `GET  /api/admin/keys`: Returns status/masked preview of 3 AI API keys (Admin).
  - `POST /api/admin/keys`: Saves dynamic API keys for Attack, Defence, Evaluation (Admin).
  - `POST /api/admin/manual-adjudicate`: Manually adjudicates match & generates Godot sequence (Admin).
  - `POST /api/admin/execute-match`: Executes AI combat adjudication for selected players (Admin).
  - `POST /api/admin/execute-sequence`: Executes tournament rounds sequentially across queue (Admin).
  - `GET  /api/matches`: Lists stored match database records.
  - `GET  /api/matches/<id>`: Returns specific evaluated match record.
  - `GET  /api/matches/<id>/godot-sequence`: Returns pure Godot-ready timeline JSON.
================================================================================
"""

import os
import sys
import json
import time
import random
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Any, Dict, List, Optional

from data.cards import get_public_cards, get_all_cards
from data.characters import get_all_characters, get_character_by_id
from database.db import (
    save_player_submission,
    get_all_submissions,
    get_submission_by_id,
    delete_submission,
    clear_all_submissions,
    update_submission_status,
    get_admin_api_keys,
    save_admin_api_keys,
    create_match_record,
    update_match_result,
    get_all_matches,
    get_match_by_id,
    check_username_available,
    register_player,
    get_all_players,
    get_player_by_username,
    record_match_for_players
)
from match_engine import (
    PlayerLoadoutInput,
    run_1v1_match,
    generate_godot_match_sequence
)

PORT = 8000
PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")
DEFAULT_ADMIN_PASSWORD = "K0lst@rno.1"

# ------------------------------------------------------------------------------
# IN-MEMORY RATE LIMITING STORE
# ------------------------------------------------------------------------------
_RATE_LIMIT_STORE: Dict[str, List[float]] = {}
_RATE_LIMIT_LOCK = threading.Lock()


def _check_rate_limit(client_ip: str, limit: int = 30, window_sec: int = 60) -> bool:
    """
    In-memory sliding window rate limiter.
    Returns True if request is allowed, False if rate limited.
    """
    now = time.time()
    with _RATE_LIMIT_LOCK:
        history = _RATE_LIMIT_STORE.get(client_ip, [])
        # Evict timestamps older than the window
        history = [t for t in history if now - t < window_sec]
        if len(history) >= limit:
            _RATE_LIMIT_STORE[client_ip] = history
            return False
        history.append(now)
        _RATE_LIMIT_STORE[client_ip] = history
        return True


def _mask_key(key: Optional[str]) -> Dict[str, Any]:
    """Returns a masked preview and active boolean for an API key."""
    if not key or not key.strip():
        return {"configured": False, "preview": "Not Set (Offline Mock Mode)"}
    k = key.strip()
    if len(k) <= 8:
        preview = "••••••••"
    else:
        preview = f"{k[:4]}••••••••{k[-4:]}"
    return {"configured": True, "preview": preview}


def _execute_ai_combat_sync(
    match_id: str,
    player_a_input: PlayerLoadoutInput,
    player_b_input: PlayerLoadoutInput,
    attack_key: Optional[str] = None,
    defence_key: Optional[str] = None,
    eval_key: Optional[str] = None
) -> Dict[str, Any]:
    """Synchronously executes the 3-AI pipeline and records the outcome."""
    try:
        keys_cfg = get_admin_api_keys()
        final_atk_key = attack_key or keys_cfg.get("attack_key") or None
        final_def_key = defence_key or keys_cfg.get("defence_key") or None
        final_eval_key = eval_key or keys_cfg.get("evaluation_key") or None

        match_result = run_1v1_match(
            player_a_input=player_a_input,
            player_b_input=player_b_input,
            attack_api_key=final_atk_key,
            defence_api_key=final_def_key,
            evaluation_api_key=final_eval_key
        )
        res_dict = match_result.model_dump()
        if "full_evaluation" in res_dict and isinstance(res_dict["full_evaluation"], dict):
            for k, v in res_dict["full_evaluation"].items():
                if k not in res_dict:
                    res_dict[k] = v
        update_match_result(match_id, res_dict)
        
        # Update player database stats
        record_match_for_players(
            player_a_name=player_a_input.player_name,
            player_b_name=player_b_input.player_name,
            winner_id=match_result.winner_id,
            p_a_score=match_result.player_a_score,
            p_b_score=match_result.player_b_score
        )

        print(f"[AI PIPELINE] Evaluated match: {match_id} | Winner: {match_result.winner_name}")
        return {"match_id": match_id, "status": "completed", "result": res_dict}
    except Exception as e:
        print(f"[AI PIPELINE ERROR] Failed to adjudicate match {match_id}: {e}")
        err_dict = {"error": str(e), "status": "failed"}
        update_match_result(match_id, err_dict)
        return {"match_id": match_id, "status": "failed", "error": str(e)}


class GameRequestHandler(SimpleHTTPRequestHandler):
    """Handles static web requests and REST API endpoints."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    def _get_client_ip(self) -> str:
        """Extracts client IP from proxy headers or socket address."""
        forwarded = self.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = self.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        if hasattr(self, "client_address") and self.client_address:
            return str(self.client_address[0])
        return "127.0.0.1"

    def _is_admin_authorized(self) -> bool:
        """
        Validates Admin Passcode against configured password (defaults to K0lst@rno.1).
        """
        admin_secret = os.getenv("ADMIN_PASSWORD") or os.getenv("ADMIN_SECRET_KEY") or os.getenv("ADMIN_SECRET") or DEFAULT_ADMIN_PASSWORD

        token = self.headers.get("X-Admin-Token", "").strip()
        if not token:
            auth = self.headers.get("Authorization", "").strip()
            if auth.lower().startswith("bearer "):
                token = auth[7:].strip()

        return token == admin_secret.strip()

    def _send_json(self, data: Any, status: int = 200):
        """Helper to send JSON HTTP responses with defensive security headers."""
        response_bytes = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Admin-Token")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("X-XSS-Protection", "1; mode=block")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.end_headers()
        self.wfile.write(response_bytes)

    def _read_body_json(self) -> Dict[str, Any]:
        """Helper to parse JSON request body with max size guard."""
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        if content_length > 1024 * 1024:  # 1MB limit
            raise ValueError("Payload size limit exceeded (max 1MB)")
        body = self.rfile.read(content_length).decode("utf-8")
        return json.loads(body)

    def do_OPTIONS(self):
        """Handle CORS pre-flight requests with security headers."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Admin-Token")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)

        # 1. API: Get Public Cards (Sanitized 120 tactics)
        if parsed.path == "/api/cards":
            cards = get_public_cards()
            return self._send_json({"count": len(cards), "cards": cards})

        # 2. API: Get Characters & Emotes
        if parsed.path == "/api/characters":
            chars = get_all_characters()
            return self._send_json({"count": len(chars), "characters": chars})

        # 3. API: Real-time Check Username Availability (High-concurrency indexed lookup)
        if parsed.path == "/api/players/check-username":
            query_params = parse_qs(parsed.query)
            username = query_params.get("username", [""])[0].strip()
            if not username:
                return self._send_json({"error": "username parameter required", "available": False}, status=400)
            avail = check_username_available(username)
            return self._send_json({
                "username": username,
                "available": avail,
                "message": "Username is available!" if avail else "Username is already taken."
            })

        # 4. API: Get Player Leaderboard / Roster
        if parsed.path == "/api/players":
            players = get_all_players()
            return self._send_json({"count": len(players), "players": players})

        # 5. API: Get Single Player Profile
        if parsed.path.startswith("/api/players/"):
            uname = parsed.path.split("/api/players/")[-1]
            player = get_player_by_username(uname)
            if player:
                return self._send_json(player)
            return self._send_json({"error": f"Player '{uname}' not found"}, status=404)

        # 6. API: Get Queued Player Submissions
        if parsed.path == "/api/submissions":
            subs = get_all_submissions()
            return self._send_json({"count": len(subs), "submissions": subs})

        # 7. API: Admin Auth Status Check
        if parsed.path == "/api/admin/auth-status":
            return self._send_json({"auth_required": True, "protected_panel": True})

        # 8. API: Get Admin 3 AI API Keys Status (Masked, Admin Protected)
        if parsed.path == "/api/admin/keys":
            if not self._is_admin_authorized():
                return self._send_json({"error": "Unauthorized: Admin passcode required (K0lst@rno.1)"}, status=401)
            keys = get_admin_api_keys()
            return self._send_json({
                "attack_ai": _mask_key(keys.get("attack_key")),
                "defence_ai": _mask_key(keys.get("defence_key")),
                "evaluation_ai": _mask_key(keys.get("evaluation_key"))
            })

        # 9. API: Get Matches Database
        if parsed.path == "/api/matches":
            matches = get_all_matches()
            return self._send_json({"matches": matches})

        # 10. API: Get Godot Combat Sequence for Match
        if parsed.path.startswith("/api/matches/") and parsed.path.endswith("/godot-sequence"):
            parts = parsed.path.strip("/").split("/")
            # e.g., ["api", "matches", "<match_id>", "godot-sequence"]
            if len(parts) >= 4:
                match_id = parts[2]
                if match_id == "latest":
                    all_m = get_all_matches()
                    if not all_m:
                        return self._send_json({"error": "No matches found"}, status=404)
                    match_record = all_m[0]
                else:
                    match_record = get_match_by_id(match_id)

                if not match_record:
                    return self._send_json({"error": "Match not found"}, status=404)

                eval_data = match_record.get("evaluation") or {}
                godot_seq = eval_data.get("godot_sequence")
                if not godot_seq:
                    p_a = match_record.get("player_a") or {}
                    p_b = match_record.get("player_b") or {}
                    godot_seq = generate_godot_match_sequence(
                        match_id=match_record.get("match_id", match_id),
                        player_a_name=p_a.get("name", "Player A"),
                        player_a_attack_cards=p_a.get("attack_cards", []),
                        player_a_defence_cards=p_a.get("defence_cards", []),
                        player_a_character_id=p_a.get("character_id", "char_phantom_9"),
                        player_b_name=p_b.get("name", "Player B"),
                        player_b_attack_cards=p_b.get("attack_cards", []),
                        player_b_defence_cards=p_b.get("defence_cards", []),
                        player_b_character_id=p_b.get("character_id", "char_sol_vanguard"),
                        winner_id=match_record.get("winner_id", "player_a"),
                        player_a_score=match_record.get("player_a_score", 13),
                        player_b_score=match_record.get("player_b_score", 9),
                        win_reason=match_record.get("win_reason", "Tactical round completion.")
                    )
                return self._send_json(godot_seq)

        # 11. API: Get Single Match
        if parsed.path.startswith("/api/matches/"):
            match_id = parsed.path.split("/api/matches/")[-1]
            match_record = get_match_by_id(match_id)
            if match_record:
                return self._send_json(match_record)
            return self._send_json({"error": "Match not found"}, status=404)

        # Default: Serve static files from public/
        super().do_GET()

    def do_DELETE(self):
        parsed = urlparse(self.path)

        # API: Delete single submission from queue (Admin Protected)
        if parsed.path.startswith("/api/submissions/"):
            if not self._is_admin_authorized():
                return self._send_json({"error": "Unauthorized: Admin passcode required (K0lst@rno.1)"}, status=401)
            sub_id = parsed.path.split("/api/submissions/")[-1]
            success = delete_submission(sub_id)
            if success:
                return self._send_json({"status": "deleted", "submission_id": sub_id})
            return self._send_json({"error": "Submission not found"}, status=404)

        self._send_json({"error": "Endpoint not found"}, status=404)

    def do_POST(self):
        parsed = urlparse(self.path)

        # ----------------------------------------------------------------------
        # 1. API: Verify Admin Passcode (Must match K0lst@rno.1)
        # ----------------------------------------------------------------------
        if parsed.path == "/api/admin/verify":
            if not self._is_admin_authorized():
                return self._send_json({"valid": False, "error": "Invalid admin passcode"}, status=401)
            return self._send_json({"valid": True, "message": "Admin authorization verified"})

        # ----------------------------------------------------------------------
        # 2. API: Manual Match Adjudication + AI Godot Sequence Generation (Admin Protected)
        # ----------------------------------------------------------------------
        if parsed.path == "/api/admin/manual-adjudicate":
            try:
                if not self._is_admin_authorized():
                    return self._send_json({"error": "Unauthorized: Admin passcode required (K0lst@rno.1)"}, status=401)

                payload = self._read_body_json()
                all_cards = get_all_cards()

                p_a_name = (payload.get("player_a_name") or "Agent Alpha").strip()
                p_a_atk = payload.get("player_a_attack_cards", [])
                p_a_def = payload.get("player_a_defence_cards", [])
                p_a_char = payload.get("player_a_character_id", "char_phantom_9")

                p_b_name = (payload.get("player_b_name") or "Agent Omega").strip()
                p_b_atk = payload.get("player_b_attack_cards", [])
                p_b_def = payload.get("player_b_defence_cards", [])
                p_b_char = payload.get("player_b_character_id", "char_sol_vanguard")

                winner_id = payload.get("winner_id", "player_a")  # "player_a", "player_b", or "draw"
                score_a = int(payload.get("player_a_score", 13))
                score_b = int(payload.get("player_b_score", 9))
                win_reason = payload.get("win_reason", "Manual tactical adjudication by match admin.")
                mvp_combo = payload.get("mvp_combo")

                # If submission IDs provided, mark queue items as completed
                sub_a_id = payload.get("submission_a_id")
                sub_b_id = payload.get("submission_b_id")
                if sub_a_id:
                    update_submission_status(sub_a_id, "completed")
                if sub_b_id:
                    update_submission_status(sub_b_id, "completed")

                # Ensure players exist in registry
                register_player(p_a_name)
                register_player(p_b_name)

                # Create match record
                match_rec = create_match_record(
                    player_a_name=p_a_name,
                    player_a_attack_cards=p_a_atk,
                    player_a_defence_cards=p_a_def,
                    player_b_name=p_b_name,
                    player_b_attack_cards=p_b_atk,
                    player_b_defence_cards=p_b_def,
                    status="completed"
                )
                match_id = match_rec["match_id"]

                # Generate AI Godot Combat Action Timeline
                godot_sequence = generate_godot_match_sequence(
                    match_id=match_id,
                    player_a_name=p_a_name,
                    player_a_attack_cards=p_a_atk,
                    player_a_defence_cards=p_a_def,
                    player_a_character_id=p_a_char,
                    player_b_name=p_b_name,
                    player_b_attack_cards=p_b_atk,
                    player_b_defence_cards=p_b_def,
                    player_b_character_id=p_b_char,
                    winner_id=winner_id,
                    player_a_score=score_a,
                    player_b_score=score_b,
                    win_reason=win_reason,
                    mvp_combo=mvp_combo
                )

                # Persist full outcome & Godot timeline
                eval_payload = {
                    "winner_id": winner_id,
                    "winner_name": p_a_name if winner_id == "player_a" else (p_b_name if winner_id == "player_b" else "Tie / Draw"),
                    "win_reason": win_reason,
                    "player_a_score": {"total_score": score_a, "synergy_score": 85},
                    "player_b_score": {"total_score": score_b, "synergy_score": 80},
                    "mvp_combo": godot_sequence.get("mvp_combo"),
                    "play_by_play_commentary": f"Admin manual outcome: {winner_id.upper()} takes the victory ({score_a}-{score_b}). {win_reason}",
                    "combat_log": [f"[{e['timestamp_sec']:.1f}s] {e['commentary']}" for e in godot_sequence.get("timeline", [])],
                    "godot_sequence": godot_sequence,
                    "character_a": p_a_char,
                    "character_b": p_b_char
                }

                update_match_result(match_id, eval_payload)

                # Update player stats
                record_match_for_players(
                    player_a_name=p_a_name,
                    player_b_name=p_b_name,
                    winner_id=winner_id,
                    p_a_score=score_a,
                    p_b_score=score_b
                )

                updated_match = get_match_by_id(match_id)
                return self._send_json({
                    "status": "success",
                    "message": "Manual match adjudicated and Godot timeline generated successfully!",
                    "match": updated_match,
                    "godot_sequence": godot_sequence
                }, status=201)

            except Exception as e:
                return self._send_json({"error": f"Manual adjudication failed: {str(e)}"}, status=400)

        # ----------------------------------------------------------------------
        # 3. API: Register or Fetch Player Profile
        # ----------------------------------------------------------------------
        if parsed.path == "/api/players/register":
            try:
                client_ip = self._get_client_ip()
                if not _check_rate_limit(f"reg_{client_ip}", limit=30, window_sec=60):
                    return self._send_json({"error": "Rate limit exceeded. Please wait a moment."}, status=429)

                payload = self._read_body_json()
                username = payload.get("username", "").strip()
                if not username:
                    return self._send_json({"error": "Username cannot be empty"}, status=400)
                player_rec = register_player(username)
                return self._send_json({
                    "status": "success",
                    "message": "Player registered successfully",
                    "player": player_rec
                }, status=201)
            except Exception as e:
                return self._send_json({"error": str(e)}, status=400)

        # ----------------------------------------------------------------------
        # 4. API: Submit Player Loadout (Decoupled into queue - NO auto AI run)
        # ----------------------------------------------------------------------
        if parsed.path in ["/api/submit-match", "/api/submit-loadout"]:
            try:
                client_ip = self._get_client_ip()
                if not _check_rate_limit(f"sub_{client_ip}", limit=30, window_sec=60):
                    return self._send_json({"error": "Rate limit exceeded. Please wait a moment before submitting another loadout."}, status=429)

                payload = self._read_body_json()

                player_name = payload.get("player_name", "").strip() or "Agent Alpha"
                attack_cards = payload.get("attack_cards", [])
                defence_cards = payload.get("defence_cards", [])

                # Strict Validation: exactly 2 Attack + 2 Defence cards
                if len(attack_cards) != 2:
                    return self._send_json({
                        "error": f"You must select EXACTLY 2 Attack cards! (Received {len(attack_cards)})"
                    }, status=400)

                if len(defence_cards) != 2:
                    return self._send_json({
                        "error": f"You must select EXACTLY 2 Defence cards! (Received {len(defence_cards)})"
                    }, status=400)

                all_cards = get_all_cards()
                for cid in attack_cards + defence_cards:
                    if cid not in all_cards:
                        return self._send_json({
                            "error": f"Card ID '{cid}' does not exist in the tactical card database!"
                        }, status=400)

                # Ensure player exists in dedicated Player Database
                register_player(player_name)

                # Persist to database submissions queue (Status: queued)
                db_record = save_player_submission(
                    player_name=player_name,
                    attack_card_ids=attack_cards,
                    defence_card_ids=defence_cards,
                    status="queued"
                )

                return self._send_json({
                    "status": "queued",
                    "message": "Tactical loadout registered in queue! Waiting for Admin to trigger combat sequence.",
                    "submission_id": db_record["submission_id"],
                    "player_name": player_name,
                    "submitted_cards": {
                        "attack": attack_cards,
                        "defence": defence_cards
                    }
                }, status=202)

            except Exception as e:
                return self._send_json({"error": f"Invalid request: {str(e)}"}, status=400)

        # ----------------------------------------------------------------------
        # 5. API: Instant 1v1 Arena Battle (Direct Play & 1-2 Min Simulation)
        # ----------------------------------------------------------------------
        if parsed.path == "/api/instant-battle":
            try:
                client_ip = self._get_client_ip()
                if not _check_rate_limit(f"battle_{client_ip}", limit=15, window_sec=60):
                    return self._send_json({"error": "Rate limit exceeded. Please wait a moment before launching another combat simulation."}, status=429)

                payload = self._read_body_json()
                all_cards = get_all_cards()

                player_name = payload.get("player_name", "").strip() or "Agent Alpha"
                attack_cards = payload.get("attack_cards", [])
                defence_cards = payload.get("defence_cards", [])

                if len(attack_cards) != 2 or len(defence_cards) != 2:
                    return self._send_json({
                        "error": "You must select EXACTLY 2 Attack and 2 Defence cards!"
                    }, status=400)

                for cid in attack_cards + defence_cards:
                    if cid not in all_cards:
                        return self._send_json({
                            "error": f"Card ID '{cid}' not found in Card Database!"
                        }, status=400)

                # Opponent loadout
                opp_name = payload.get("opponent_name", "").strip()
                opp_atk = payload.get("opponent_attack_cards", [])
                opp_def = payload.get("opponent_defence_cards", [])

                if not opp_name or len(opp_atk) != 2 or len(opp_def) != 2:
                    queued = [s for s in get_all_submissions() if s.get("status") == "queued" and s.get("player_name") != player_name]
                    if queued:
                        rival_sub = random.choice(queued)
                        opp_name = rival_sub["player_name"]
                        opp_atk = rival_sub["attack_cards"]
                        opp_def = rival_sub["defence_cards"]
                    else:
                        rival_names = ["Derke#FNTC", "Chronicle#EMEA", "Boaster#IGL", "Yay#DIABLO", "Aspas#LEV", "ScreaM#ONE", "cNed#FUT"]
                        opp_name = random.choice(rival_names)
                        atk_pool = [c["id"] for c in all_cards.values() if c["category"] == "attack" and c["id"] not in attack_cards]
                        def_pool = [c["id"] for c in all_cards.values() if c["category"] == "defence" and c["id"] not in defence_cards]
                        opp_atk = random.sample(atk_pool, 2)
                        opp_def = random.sample(def_pool, 2)

                # Register both players
                register_player(player_name)
                register_player(opp_name)

                # Create match record
                match_rec = create_match_record(
                    player_a_name=player_name,
                    player_a_attack_cards=attack_cards,
                    player_a_defence_cards=defence_cards,
                    player_b_name=opp_name,
                    player_b_attack_cards=opp_atk,
                    player_b_defence_cards=opp_def,
                    status="in_progress"
                )

                p_a_input = PlayerLoadoutInput(
                    player_id="player_a",
                    player_name=player_name,
                    hp=100,
                    shield=50,
                    attack_card_ids=attack_cards,
                    defence_card_ids=defence_cards
                )

                p_b_input = PlayerLoadoutInput(
                    player_id="player_b",
                    player_name=opp_name,
                    hp=100,
                    shield=50,
                    attack_card_ids=opp_atk,
                    defence_card_ids=opp_def
                )

                execution_result = _execute_ai_combat_sync(
                    match_id=match_rec["match_id"],
                    player_a_input=p_a_input,
                    player_b_input=p_b_input
                )

                full_match = get_match_by_id(match_rec["match_id"])
                return self._send_json({
                    "status": "success",
                    "match": full_match,
                    "execution": execution_result
                })

            except Exception as e:
                return self._send_json({"error": f"Instant battle failed: {str(e)}"}, status=400)

        # ----------------------------------------------------------------------
        # 6. API: Clear All Submissions (Admin Protected)
        # ----------------------------------------------------------------------
        if parsed.path == "/api/submissions/clear":
            try:
                if not self._is_admin_authorized():
                    return self._send_json({"error": "Unauthorized: Admin passcode required (K0lst@rno.1)"}, status=401)
                clear_all_submissions()
                return self._send_json({"status": "cleared", "message": "All submissions cleared."})
            except Exception as e:
                return self._send_json({"error": str(e)}, status=500)

        # ----------------------------------------------------------------------
        # 7. API: Save Admin 3 AI API Keys (Admin Protected)
        # ----------------------------------------------------------------------
        if parsed.path == "/api/admin/keys":
            try:
                if not self._is_admin_authorized():
                    return self._send_json({"error": "Unauthorized: Admin passcode required (K0lst@rno.1)"}, status=401)

                payload = self._read_body_json()
                atk_key = payload.get("attack_key")
                def_key = payload.get("defence_key")
                eval_key = payload.get("evaluation_key")

                save_admin_api_keys(
                    attack_key=atk_key,
                    defence_key=def_key,
                    evaluation_key=eval_key
                )

                keys = get_admin_api_keys()
                return self._send_json({
                    "status": "success",
                    "message": "Admin AI API keys updated successfully!",
                    "keys": {
                        "attack_ai": _mask_key(keys.get("attack_key")),
                        "defence_ai": _mask_key(keys.get("defence_key")),
                        "evaluation_ai": _mask_key(keys.get("evaluation_key"))
                    }
                })
            except Exception as e:
                return self._send_json({"error": str(e)}, status=400)

        # ----------------------------------------------------------------------
        # 8. API: Admin Execute 1v1 Match Between Chosen Players (Admin Protected)
        # ----------------------------------------------------------------------
        if parsed.path == "/api/admin/execute-match":
            try:
                if not self._is_admin_authorized():
                    return self._send_json({"error": "Unauthorized: Admin passcode required (K0lst@rno.1)"}, status=401)

                payload = self._read_body_json()
                all_cards = get_all_cards()

                sub_a_id = payload.get("submission_a_id")
                sub_b_id = payload.get("submission_b_id")

                p_a_name = payload.get("player_a_name")
                p_a_atk = payload.get("player_a_attack_cards")
                p_a_def = payload.get("player_a_defence_cards")

                p_b_name = payload.get("player_b_name")
                p_b_atk = payload.get("player_b_attack_cards")
                p_b_def = payload.get("player_b_defence_cards")

                if sub_a_id:
                    sub_a = get_submission_by_id(sub_a_id)
                    if not sub_a:
                        return self._send_json({"error": f"Submission A '{sub_a_id}' not found"}, status=404)
                    p_a_name = sub_a["player_name"]
                    p_a_atk = sub_a["attack_cards"]
                    p_a_def = sub_a["defence_cards"]
                    update_submission_status(sub_a_id, "matched")

                if sub_b_id:
                    sub_b = get_submission_by_id(sub_b_id)
                    if not sub_b:
                        return self._send_json({"error": f"Submission B '{sub_b_id}' not found"}, status=404)
                    p_b_name = sub_b["player_name"]
                    p_b_atk = sub_b["attack_cards"]
                    p_b_def = sub_b["defence_cards"]
                    update_submission_status(sub_b_id, "matched")

                p_a_name = (p_a_name or "Agent Alpha").strip()
                p_b_name = (p_b_name or "Agent Omega").strip()

                atk_pool = [c["id"] for c in all_cards.values() if c["category"] == "attack"]
                def_pool = [c["id"] for c in all_cards.values() if c["category"] == "defence"]

                p_a_atk = p_a_atk or random.sample(atk_pool, 2)
                p_a_def = p_a_def or random.sample(def_pool, 2)
                p_b_atk = p_b_atk or random.sample(atk_pool, 2)
                p_b_def = p_b_def or random.sample(def_pool, 2)

                match_rec = create_match_record(
                    player_a_name=p_a_name,
                    player_a_attack_cards=p_a_atk,
                    player_a_defence_cards=p_a_def,
                    player_b_name=p_b_name,
                    player_b_attack_cards=p_b_atk,
                    player_b_defence_cards=p_b_def,
                    status="in_progress"
                )

                p_a_input = PlayerLoadoutInput(
                    player_id="player_a",
                    player_name=p_a_name,
                    hp=100,
                    shield=50,
                    attack_card_ids=p_a_atk,
                    defence_card_ids=p_a_def
                )

                p_b_input = PlayerLoadoutInput(
                    player_id="player_b",
                    player_name=p_b_name,
                    hp=100,
                    shield=50,
                    attack_card_ids=p_b_atk,
                    defence_card_ids=p_b_def
                )

                execution_result = _execute_ai_combat_sync(
                    match_id=match_rec["match_id"],
                    player_a_input=p_a_input,
                    player_b_input=p_b_input,
                    attack_key=payload.get("attack_key"),
                    defence_key=payload.get("defence_key"),
                    eval_key=payload.get("evaluation_key")
                )

                full_match = get_match_by_id(match_rec["match_id"])
                return self._send_json({
                    "status": "success",
                    "match": full_match,
                    "execution": execution_result
                })

            except Exception as e:
                return self._send_json({"error": f"Match execution failed: {str(e)}"}, status=400)

        # ----------------------------------------------------------------------
        # 9. API: Admin Execute Sequence (Tournament Round across queued players, Admin Protected)
        # ----------------------------------------------------------------------
        if parsed.path == "/api/admin/execute-sequence":
            try:
                if not self._is_admin_authorized():
                    return self._send_json({"error": "Unauthorized: Admin passcode required (K0lst@rno.1)"}, status=401)

                payload = self._read_body_json()
                all_cards = get_all_cards()

                submissions = get_all_submissions(status="queued")
                if len(submissions) < 2:
                    return self._send_json({
                        "error": f"Need at least 2 queued submissions to run a sequence! (Currently have {len(submissions)})"
                    }, status=400)

                executed_matches = []
                for i in range(0, len(submissions) - 1, 2):
                    sub_a = submissions[i]
                    sub_b = submissions[i + 1]

                    match_rec = create_match_record(
                        player_a_name=sub_a["player_name"],
                        player_a_attack_cards=sub_a["attack_cards"],
                        player_a_defence_cards=sub_a["defence_cards"],
                        player_b_name=sub_b["player_name"],
                        player_b_attack_cards=sub_b["attack_cards"],
                        player_b_defence_cards=sub_b["defence_cards"],
                        status="in_progress"
                    )

                    update_submission_status(sub_a["submission_id"], "completed")
                    update_submission_status(sub_b["submission_id"], "completed")

                    p_a_input = PlayerLoadoutInput(
                        player_id="player_a",
                        player_name=sub_a["player_name"],
                        hp=100,
                        shield=50,
                        attack_card_ids=sub_a["attack_cards"],
                        defence_card_ids=sub_a["defence_cards"]
                    )

                    p_b_input = PlayerLoadoutInput(
                        player_id="player_b",
                        player_name=sub_b["player_name"],
                        hp=100,
                        shield=50,
                        attack_card_ids=sub_b["attack_cards"],
                        defence_card_ids=sub_b["defence_cards"]
                    )

                    exec_res = _execute_ai_combat_sync(
                        match_id=match_rec["match_id"],
                        player_a_input=p_a_input,
                        player_b_input=p_b_input,
                        attack_key=payload.get("attack_key"),
                        defence_key=payload.get("defence_key"),
                        eval_key=payload.get("evaluation_key")
                    )
                    full_match = get_match_by_id(match_rec["match_id"])
                    executed_matches.append(full_match)

                return self._send_json({
                    "status": "success",
                    "count": len(executed_matches),
                    "matches": executed_matches
                })

            except Exception as e:
                return self._send_json({"error": f"Sequence execution failed: {str(e)}"}, status=400)

        self._send_json({"error": "Endpoint not found"}, status=404)


def start_server(port: int = PORT):
    """Starts the HTTP server."""
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    server_address = ("", port)
    httpd = HTTPServer(server_address, GameRequestHandler)
    print("\n" + "=" * 80)
    print(f" 🚀 TACTICAL CARD GAME & TOURNAMENT SERVER RUNNING")
    print(f" 🌐 Arena UI : http://localhost:{port}/arena.html")
    print(f" 🛠️ Admin UI : http://localhost:{port}/admin.html (Passcode: K0lst@rno.1)")
    print(f" 📦 REST API : /api/cards, /api/characters, /api/admin/manual-adjudicate")
    print("=" * 80 + "\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] Server shutting down.")
        httpd.server_close()


if __name__ == "__main__":
    start_server()
