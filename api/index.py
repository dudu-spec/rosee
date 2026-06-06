"""Vercel serverless entry point."""
import os
os.environ["VERCEL"] = "1"

import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from app.backend.main import app
