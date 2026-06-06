"""Vercel serverless entry point."""
import sys, os
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

os.environ["VERCEL"] = "1"
os.environ.setdefault("OPENROUTER_TIMEOUT", "5")

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    from app.backend.main import app
    logger.info("App imported successfully")
except Exception as e:
    logger.exception("Failed to import app")
    raise
