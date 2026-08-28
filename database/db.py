"""
================================================================================
database/db.py
================================================================================

Lightweight persistent JSON match store for production match queuing & recording.
Thread-safe file locking with timestamp tracking.
================================================================================
"""

import os
import json
import time
import uuid
import threading
from typing import Dict, Any, List, Optional

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(DB_DIR, "matches.json")
_LOCK = threading.Lock()


def _init_db():
    """Ensures database file exists."""
    os.makedirs(DB_DIR, exist_ok=True)
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)


def get_all_matches() -> List[Dict[str, Any]]:
    """Retrieves all stored match records."""
    _init_db()
    with _LOCK:
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []


def get_match_by_id(match_id: str) -> Optional[Dict[str, Any]]:
    """Fetches a specific match record."""
    matches = get_all_matches()
    for m in matches:
        if m.get("match_id") == match_id:
            return m
    return None


def save_match_submission(
    player_name: str,
    attack_card_ids: List[str],
    defence_card_ids: List[str],
    opponent_name: str = "Tactical AI Bot",
    status: str = "processing"
) -> Dict[str, Any]:
    """
    Persists a new player match submission into the database.
    """
    _init_db()
    match_id = f"match_{uuid.uuid4().hex[:10]}"
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    new_record = {
        "match_id": match_id,
        "created_at": timestamp,
        "status": status,
        "player_a": {
            "name": player_name,
            "attack_cards": attack_card_ids,
            "defence_cards": defence_card_ids
        },
        "player_b": {
            "name": opponent_name
        },
        "evaluation": None
    }

    with _LOCK:
        try:
            matches = []
            if os.path.exists(DB_FILE):
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    matches = json.load(f)
            matches.insert(0, new_record)
            # Keep last 200 matches
            matches = matches[:200]
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump(matches, f, indent=2)
        except Exception as e:
            print(f"[DB ERROR] Could not save match: {e}")

    return new_record


def update_match_result(match_id: str, evaluation_data: Dict[str, Any]) -> bool:
    """Updates an existing match record with evaluated result."""
    _init_db()
    with _LOCK:
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                matches = json.load(f)

            updated = False
            for m in matches:
                if m.get("match_id") == match_id:
                    m["status"] = "completed"
                    m["evaluation"] = evaluation_data
                    updated = True
                    break

            if updated:
                with open(DB_FILE, "w", encoding="utf-8") as f:
                    json.dump(matches, f, indent=2)
            return updated
        except Exception as e:
            print(f"[DB ERROR] Could not update match {match_id}: {e}")
            return False
