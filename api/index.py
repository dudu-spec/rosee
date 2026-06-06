"""Vercel serverless entry point."""
import os
os.environ["VERCEL"] = "1"

import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from app.database.connection import init_db

from fastapi import FastAPI
app = FastAPI(title="Rosee")

@app.get("/api/health")
def health():
    return {"status": "ok", "app": "Rosee on Vercel"}
