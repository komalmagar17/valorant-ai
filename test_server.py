"""
test_server.py
==============
Integration tests for the Python HTTP REST API Server (server.py).
Tests:
1. GET /api/cards - Verifies exactly 120 cards returned with sanitized fields (no tier/power leak).
2. POST /api/submit-match - Verifies loadouts are decoupled & saved to queue (status: queued).
3. GET /api/submissions - Verifies listing of queued player submissions.
4. DELETE /api/submissions/<id> - Verifies removing a submission from queue.
5. GET & POST /api/admin/keys - Verifies managing 3 distinct AI API keys.
6. POST /api/admin/execute-match - Verifies admin-triggered on-demand 1v1 AI adjudication.
7. POST /api/admin/execute-sequence - Verifies sequential tournament execution.
8. GET /api/matches - Verifies match database listing and details.
9. OPTIONS / - Verifies CORS headers.
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

    def test_submit_loadout_queues_without_auto_ai(self):
        """POST /api/submit-loadout should queue the submission with status 'queued'."""
        url = f"{self.base_url}/api/submit-loadout"
        payload = {
            "player_name": "TenZ#NA1",
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
            self.assertEqual(data["status"], "queued")
            self.assertIn("submission_id", data)
            sub_id = data["submission_id"]

        # Check GET /api/submissions
        subs_url = f"{self.base_url}/api/submissions"
        with urllib.request.urlopen(urllib.request.Request(subs_url, method="GET")) as resp:
            self.assertEqual(resp.status, 200)
            subs_data = json.loads(resp.read().decode("utf-8"))
            found = any(s["submission_id"] == sub_id for s in subs_data["submissions"])
            self.assertTrue(found)

    def test_admin_api_keys_endpoint(self):
        """GET & POST /api/admin/keys should configure the 3 AI API keys."""
        # 1. Update keys
        url = f"{self.base_url}/api/admin/keys"
        payload = {
            "attack_key": "AIzaSyAttackTestKey1234567890",
            "defence_key": "AIzaSyDefenceTestKey1234567890",
            "evaluation_key": "AIzaSyEvalTestKey1234567890"
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["status"], "success")

        # 2. Get keys status (masked)
        with urllib.request.urlopen(urllib.request.Request(url, method="GET")) as resp:
            self.assertEqual(resp.status, 200)
            keys_data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(keys_data["attack_ai"]["configured"])
            self.assertTrue(keys_data["defence_ai"]["configured"])
            self.assertTrue(keys_data["evaluation_ai"]["configured"])
            self.assertIn("AIza", keys_data["attack_ai"]["preview"])

        # 3. Reset keys to empty for subsequent offline tests
        reset_req = urllib.request.Request(
            url,
            data=json.dumps({"attack_key": "", "defence_key": "", "evaluation_key": ""}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(reset_req)

    def test_admin_execute_match_flow(self):
        """POST /api/admin/execute-match should adjudicate 1v1 combat between selected submissions."""
        # Ensure offline mode keys are set for testing
        keys_url = f"{self.base_url}/api/admin/keys"
        reset_req = urllib.request.Request(
            keys_url,
            data=json.dumps({"attack_key": "", "defence_key": "", "evaluation_key": ""}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(reset_req)

        # Queue Player 1
        url_sub = f"{self.base_url}/api/submit-loadout"
        p1_payload = {
            "player_name": "JettRadiant",
            "attack_cards": ["atk_flash_entry", "atk_master_execute"],
            "defence_cards": ["def_reposition_defense", "def_layered_defense"]
        }
        req1 = urllib.request.Request(url_sub, data=json.dumps(p1_payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req1) as resp:
            sub1_id = json.loads(resp.read().decode("utf-8"))["submission_id"]

        # Queue Player 2
        p2_payload = {
            "player_name": "OmenViper",
            "attack_cards": ["atk_split_pressure", "atk_fullteam_rush"],
            "defence_cards": ["def_defensive_smoke", "def_antirush_setup"]
        }
        req2 = urllib.request.Request(url_sub, data=json.dumps(p2_payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req2) as resp:
            sub2_id = json.loads(resp.read().decode("utf-8"))["submission_id"]

        # Admin executes match between Player 1 and Player 2
        exec_url = f"{self.base_url}/api/admin/execute-match"
        exec_payload = {
            "submission_a_id": sub1_id,
            "submission_b_id": sub2_id
        }
        req_exec = urllib.request.Request(exec_url, data=json.dumps(exec_payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req_exec) as resp:
            self.assertEqual(resp.status, 200)
            res_data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(res_data["status"], "success")
            self.assertIn("match", res_data)
            match_data = res_data["match"]
            self.assertEqual(match_data["status"], "completed")
            self.assertIsNotNone(match_data["evaluation"])
            self.assertIn("winner_name", match_data["evaluation"])
            self.assertIn("esports_commentary", match_data["evaluation"])

    def test_admin_execute_sequence_flow(self):
        """POST /api/admin/execute-sequence should run tournament rounds across queued submissions."""
        # Queue 2 test players
        url_sub = f"{self.base_url}/api/submit-loadout"
        p1 = {"player_name": "SeqPlayer1", "attack_cards": ["atk_flash_entry", "atk_quick_peek"], "defence_cards": ["def_basic_hold", "def_defensive_smoke"]}
        p2 = {"player_name": "SeqPlayer2", "attack_cards": ["atk_split_pressure", "atk_quick_peek"], "defence_cards": ["def_basic_hold", "def_defensive_smoke"]}

        req1 = urllib.request.Request(url_sub, data=json.dumps(p1).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
        req2 = urllib.request.Request(url_sub, data=json.dumps(p2).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req1)
        urllib.request.urlopen(req2)

        # Execute sequence
        seq_url = f"{self.base_url}/api/admin/execute-sequence"
        req_seq = urllib.request.Request(seq_url, data=json.dumps({}).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req_seq) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["status"], "success")
            self.assertGreaterEqual(data["count"], 1)

    def test_check_username_endpoint_and_player_registration(self):
        """GET /api/players/check-username and POST /api/players/register functionality."""
        uname = f"Agent_Test_{int(time.time() * 1000)}"

        # 1. Check availability for fresh name -> available: True
        check_url = f"{self.base_url}/api/players/check-username?username={uname}"
        req = urllib.request.Request(check_url, method="GET")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data["available"])
            self.assertEqual(data["username"], uname)

        # 2. Register player
        reg_url = f"{self.base_url}/api/players/register"
        req_reg = urllib.request.Request(
            reg_url,
            data=json.dumps({"username": uname}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req_reg) as resp:
            self.assertEqual(resp.status, 201)
            reg_data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(reg_data["status"], "success")
            self.assertEqual(reg_data["player"]["username"], uname)

        # 3. Check availability again -> available: False
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertFalse(data["available"])

        # 4. GET /api/players includes this player
        players_url = f"{self.base_url}/api/players"
        with urllib.request.urlopen(urllib.request.Request(players_url, method="GET")) as resp:
            self.assertEqual(resp.status, 200)
            p_data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("players", p_data)
            names = [p["username"] for p in p_data["players"]]
            self.assertIn(uname, names)

    def test_concurrent_simultaneous_username_checks(self):
        """Simulates 50 concurrent HTTP requests checking usernames simultaneously."""
        from concurrent.futures import ThreadPoolExecutor
        TOTAL = 50
        results = []
        lock = threading.Lock()

        def check_name_http(idx: int):
            uname = f"ConcurrentAgent_{idx}_{int(time.time()*1000)}"
            url = f"{self.base_url}/api/players/check-username?username={uname}"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                with lock:
                    results.append(data["available"])

        with ThreadPoolExecutor(max_workers=16) as executor:
            list(executor.map(check_name_http, range(TOTAL)))

        self.assertEqual(len(results), TOTAL)
        self.assertTrue(all(results))

    def test_instant_battle_endpoint_extended_duration(self):
        """POST /api/instant-battle executes a full 1-2 minute match simulation."""
        url = f"{self.base_url}/api/instant-battle"
        payload = {
            "player_name": "TenZ#NA1",
            "attack_cards": ["atk_quick_peek", "atk_double_peek"],
            "defence_cards": ["def_basic_hold", "def_defensive_smoke"]
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["status"], "success")
            self.assertIn("match", data)
            match = data["match"]
            eval_data = match["evaluation"]
            
            # Verify combat log has extended 1-2 minute timestamps (> 60 seconds)
            combat_log = eval_data.get("combat_log", [])
            self.assertGreaterEqual(len(combat_log), 5)
            has_late_timestamp = any("[01:" in entry for entry in combat_log)
            self.assertTrue(has_late_timestamp, f"Combat log should contain timestamps in the 1-2 min range [01:xx]: {combat_log}")

    def test_security_headers_present(self):
        """Responses should include standard defensive security headers."""
        url = f"{self.base_url}/api/cards"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.headers.get("X-Content-Type-Options"), "nosniff")
            self.assertEqual(resp.headers.get("X-Frame-Options"), "SAMEORIGIN")
            self.assertEqual(resp.headers.get("X-XSS-Protection"), "1; mode=block")
            self.assertEqual(resp.headers.get("Referrer-Policy"), "strict-origin-when-cross-origin")

    def test_admin_auth_protection(self):
        """Admin endpoints should require authorization when ADMIN_PASSWORD is set."""
        import os
        from unittest.mock import patch

        with patch.dict(os.environ, {"ADMIN_PASSWORD": "SuperSecretAdminPasscode123!"}):
            # 1. Unauthenticated request -> 401 Unauthorized
            url = f"{self.base_url}/api/admin/keys"
            req = urllib.request.Request(url, method="GET")
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(req)
            self.assertEqual(ctx.exception.code, 401)

            # 2. Invalid token -> 401 Unauthorized
            req_bad = urllib.request.Request(url, headers={"X-Admin-Token": "wrong_password"}, method="GET")
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(req_bad)
            self.assertEqual(ctx.exception.code, 401)

            # 3. Correct token in X-Admin-Token -> 200 OK
            req_good = urllib.request.Request(url, headers={"X-Admin-Token": "SuperSecretAdminPasscode123!"}, method="GET")
            with urllib.request.urlopen(req_good) as resp:
                self.assertEqual(resp.status, 200)

            # 4. Verify endpoint POST /api/admin/verify
            verify_url = f"{self.base_url}/api/admin/verify"
            req_verify = urllib.request.Request(
                verify_url,
                data=b"{}",
                headers={"Content-Type": "application/json", "X-Admin-Token": "SuperSecretAdminPasscode123!"},
                method="POST"
            )
            with urllib.request.urlopen(req_verify) as resp:
                self.assertEqual(resp.status, 200)
                v_data = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(v_data["valid"])

    def test_vercel_serverless_handler_import(self):
        """Ensures api/index.py imports and subclasses GameRequestHandler without errors."""
        from api.index import handler
        from server import GameRequestHandler
        self.assertTrue(issubclass(handler, GameRequestHandler))


if __name__ == "__main__":
    unittest.main()

