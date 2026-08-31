"""
================================================================================
api/index.py
================================================================================
Vercel Serverless Function Entrypoint for Veer Survivor REST API.
Dispatches serverless HTTP requests to the centralized GameRequestHandler.
================================================================================
"""

import os
import sys

# Ensure root workspace directory is in sys.path for serverless function execution
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from server import GameRequestHandler

class handler(GameRequestHandler):
    """Vercel Python Serverless Request Handler."""
    pass
