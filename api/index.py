"""
================================================================================
api/index.py
================================================================================
Vercel Serverless Function Entrypoint for Veer Survivor REST API.
Dispatches serverless HTTP requests to the centralized GameRequestHandler with
defensive path resolution for Vercel edge rewrites.
================================================================================
"""

import os
import sys
from urllib.parse import urlparse

# Ensure root workspace directory is in sys.path for serverless function execution
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from server import GameRequestHandler

class handler(GameRequestHandler):
    """Vercel Python Serverless Request Handler with path normalization."""

    def _normalize_vercel_path(self):
        # Check standard Vercel forwarded headers
        matched = self.headers.get("x-matched-path") or self.headers.get("x-forwarded-uri") or self.headers.get("x-real-path")
        if matched and matched.startswith("/api"):
            self.path = matched
        elif self.path.startswith("/api/index.py"):
            # If path was rewritten with query or trailing
            rest = self.path[len("/api/index.py"):]
            if rest.startswith("/"):
                self.path = "/api" + rest
            elif rest.startswith("?"):
                self.path = "/api" + rest

    def do_GET(self):
        self._normalize_vercel_path()
        super().do_GET()

    def do_POST(self):
        self._normalize_vercel_path()
        super().do_POST()

    def do_DELETE(self):
        self._normalize_vercel_path()
        super().do_DELETE()

    def do_OPTIONS(self):
        self._normalize_vercel_path()
        super().do_OPTIONS()
