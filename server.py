"""
================================================================================
server.py
================================================================================

Production-grade Python Web & REST API Server.
- Serves the Cute 3D Web Frontend from `public/`
- API Endpoints:
  - `GET  /api/cards`: Returns all 120 cards (Sanitized of all Tier & Power data).
  - `POST /api/submit-match`: Validates 2 Attack + 2 Defence cards, records to
    database, executes AI adjudication in background, and returns "Processing the result...".
  - `GET  /api/matches`: Lists stored match database records.
  - `GET  /api/matches/<id>`: Returns specific evaluated match record.
================================================================================
"""

import os
import json
import random
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
from typing import Any

from data.cards import get_public_cards, get_all_cards
from database.db import save_match_submission, update_match_result, get_all_matches, get_match_by_id
from match_engine import PlayerLoadoutInput, run_1v1_match

PORT = 8000
PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")


def _run_ai_pipeline_background(match_id: str, player_a_input: PlayerLoadoutInput, player_b_input: PlayerLoadoutInput):
    """Executes AI adjudication and saves result to database."""
    try:
        match_result = run_1v1_match(
            player_a_input=player_a_input,
            player_b_input=player_b_input
        )
        update_match_result(match_id, match_result.model_dump())
        print(f"[AI PIPELINE] Successfully evaluated match: {match_id} (Winner: {match_result.winner_name})")
    except Exception as e:
        print(f"[AI PIPELINE ERROR] Failed to adjudicate match {match_id}: {e}")
        update_match_result(match_id, {"error": str(e), "status": "failed"})


class GameRequestHandler(SimpleHTTPRequestHandler):
    """Handles static web requests and REST API endpoints."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    def _send_json(self, data: Any, status: int = 200):
        """Helper to send JSON HTTP responses."""
        response_bytes = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_OPTIONS(self):
        """Handle CORS pre-flight requests."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)

        # 1. API: Get Public Cards (TIERS STRICTLY HIDDEN)
        if parsed.path == "/api/cards":
            cards = get_public_cards()
            return self._send_json({"count": len(cards), "cards": cards})

        # 2. API: Get Database Matches
        if parsed.path == "/api/matches":
            matches = get_all_matches()
            return self._send_json({"matches": matches})

        # 3. API: Get Single Match Status
        if parsed.path.startswith("/api/matches/"):
            match_id = parsed.path.split("/api/matches/")[-1]
            match_record = get_match_by_id(match_id)
            if match_record:
                return self._send_json(match_record)
            return self._send_json({"error": "Match not found"}, status=404)

        # Default: Serve static files from public/
        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)

        # API: Submit Match
        if parsed.path == "/api/submit-match":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8")
                payload = json.loads(body)

                player_name = payload.get("player_name", "Agent Alpha").strip() or "Agent Alpha"
                attack_cards = payload.get("attack_cards", [])
                defence_cards = payload.get("defence_cards", [])

                # Strict Validation: 2 Attack + 2 Defence cards
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

                # Generate balanced opponent loadout if not provided
                opp_name = payload.get("opponent_name", "Boba-Bot (AI Opponent)")
                atk_pool = [c["id"] for c in all_cards.values() if c["category"] == "attack"]
                def_pool = [c["id"] for c in all_cards.values() if c["category"] == "defence"]
                opp_atk_cards = payload.get("opponent_attack_cards") or random.sample(atk_pool, 2)
                opp_def_cards = payload.get("opponent_defence_cards") or random.sample(def_pool, 2)

                # Save match submission to database
                db_record = save_match_submission(
                    player_name=player_name,
                    attack_card_ids=attack_cards,
                    defence_card_ids=defence_cards,
                    opponent_name=opp_name,
                    status="processing"
                )

                # Prepare Pydantic inputs for match engine
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
                    attack_card_ids=opp_atk_cards,
                    defence_card_ids=opp_def_cards
                )

                # Launch AI adjudication asynchronously in background thread
                t = threading.Thread(
                    target=_run_ai_pipeline_background,
                    args=(db_record["match_id"], p_a_input, p_b_input),
                    daemon=True
                )
                t.start()

                # Client response strictly returns "processing the result"
                return self._send_json({
                    "status": "processing",
                    "message": "Processing the result...",
                    "match_id": db_record["match_id"],
                    "player_name": player_name,
                    "submitted_cards": {
                        "attack": attack_cards,
                        "defence": defence_cards
                    }
                }, status=202)

            except Exception as e:
                return self._send_json({"error": f"Invalid request: {str(e)}"}, status=400)

        self._send_json({"error": "Endpoint not found"}, status=404)


def start_server(port: int = PORT):
    """Starts the HTTP server."""
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    server_address = ("", port)
    httpd = HTTPServer(server_address, GameRequestHandler)
    print("\n" + "=" * 80)
    print(f" 🚀 TACTICAL CARD GAME SERVER RUNNING")
    print(f" 🌐 URL: http://localhost:{port}")
    print(f" 📦 REST Endpoints: /api/cards, /api/submit-match, /api/matches")
    print("=" * 80 + "\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] Server shutting down.")
        httpd.server_close()


if __name__ == "__main__":
    start_server()
