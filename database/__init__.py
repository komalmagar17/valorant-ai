"""
database/__init__.py
"""
from database.db import save_match_submission, update_match_result, get_all_matches, get_match_by_id

__all__ = ["save_match_submission", "update_match_result", "get_all_matches", "get_match_by_id"]
