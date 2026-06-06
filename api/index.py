"""Vercel serverless entry point."""
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import os

# Flag para o interface.py detectar que está no Vercel
os.environ["VERCEL"] = "1"
# Timeout menor pro OpenRouter no Vercel (limite de 10s)
os.environ.setdefault("OPENROUTER_TIMEOUT", "5")

# Tenta carregar .env local (opcional, seguranca em .gitignore)
_env_file = _root / ".env"
if _env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_file)
    except ImportError:
        pass

from app.backend.main import app
