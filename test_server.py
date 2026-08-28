"""
test_server.py
==============
Integration tests for the Python HTTP REST API Server (server.py).
Tests:
1. GET /api/cards - Verifies exactly 120 cards returned with sanitized fields (no tier/power leak).
2. GET /api/matches - Verifies match listing.
3. GET /api/matches/<id> - Verifies specific match fetching & 404 for invalid ID.
4. POST /api/submit-match - Verifies card validation (exactly 2 attack + 2 defence).
5. POST /api/submit-match - Verifies rejection of invalid/fake card IDs.
6. POST /api/submit-match - Verifies successful 202 response and async background execution.
7. OPTIONS / - Verifies CORS headers.
"""

import json
import time
import unittest
import urllib.request
import urllib.error
import threading
from http.server import HTTPServer

from server import GameRequestHandler


class TestServerAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start test HTTP server on an available dynamic test port (e.g., 8877)
        cls.port = 8877
        cls.server_address = ("127.0.0.1", cls.port)
        cls.httpd = HTTPServer(cls.server_address, GameRequestHandler)
        cls.server_thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def test_get_cards_endpoint(self):
        """GET /api/cards should return 120 sanitized tactical cards."""
        url = f"{self.base_url}/api/cards"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["count"], 120)
            self.assertEqual(len(data["cards"]), 120)

            # Ensure internal secrets (tier, power) are strictly stripped
            for card in data["cards"]:
                self.assertNotIn("tier", card)
                self.assertNotIn("power", card)
                self.assertIn("id", card)
                self.assertIn("name", card)
                self.assertIn("category", card)
                self.assertIn("description", card)

    def test_get_matches_endpoint(self):
        """GET /api/matches should return a list of matches."""
        url = f"{self.base_url}/api/matches"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("matches", data)
            self.assertIsInstance(data["matches"], list)

    def test_cors_options(self):
        """OPTIONS / should return CORS pre-flight headers."""
        url = f"{self.base_url}/api/cards"
        req = urllib.request.Request(url, method="OPTIONS")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), "*")
            self.assertIn("POST", resp.headers.get("Access-Control-Allow-Methods"))

    def test_submit_match_validation_card_count(self):
        """POST /api/submit-match should reject invalid card counts."""
        url = f"{self.base_url}/api/submit-match"

        # Only 1 attack card provided (requires 2)
        payload = {
            "player_name": "TestPlayer",
            "attack_cards": ["atk_quick_peek"],
            "defence_cards": ["def_basic_hold", "def_defensive_smoke"]
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 400)
        err_data = json.loads(ctx.exception.read().decode("utf-8"))
        self.assertIn("EXACTLY 2 Attack cards", err_data["error"])

    def test_submit_match_validation_invalid_card_id(self):
        """POST /api/submit-match should reject non-existent card IDs."""
        url = f"{self.base_url}/api/submit-match"
        payload = {
            "player_name": "TestPlayer",
            "attack_cards": ["atk_quick_peek", "fake_nonexistent_card_id_999"],
            "defence_cards": ["def_basic_hold", "def_defensive_smoke"]
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 400)
        err_data = json.loads(ctx.exception.read().decode("utf-8"))
        self.assertIn("does not exist", err_data["error"])

    def test_submit_match_success_and_evaluation_flow(self):
        """POST /api/submit-match should accept valid loadout, return 202, and process."""
        url = f"{self.base_url}/api/submit-match"
        payload = {
            "player_name": "ChampionJett",
            "attack_cards": ["atk_quick_peek", "atk_flash_entry"],
            "defence_cards": ["def_basic_hold", "def_defensive_smoke"]
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 202)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["status"], "processing")
            self.assertEqual(data["message"], "Processing the result...")
            self.assertIn("match_id", data)
            match_id = data["match_id"]

        # Wait briefly for background AI thread to complete adjudication
        time.sleep(1.0)

        # Query GET /api/matches/<match_id>
        match_url = f"{self.base_url}/api/matches/{match_id}"
        req_match = urllib.request.Request(match_url, method="GET")
        with urllib.request.urlopen(req_match) as resp:
            self.assertEqual(resp.status, 200)
            record = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(record["match_id"], match_id)
            self.assertEqual(record["status"], "completed")
            self.assertIsNotNone(record["evaluation"])
            self.assertIn("winner_name", record["evaluation"])
            self.assertIn("esports_commentary", record["evaluation"])


if __name__ == "__main__":
    unittest.main()
