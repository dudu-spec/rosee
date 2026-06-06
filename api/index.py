"""Vercel serverless entry point."""
import os
os.environ["VERCEL"] = "1"

import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_root))

from fastapi import FastAPI

app = FastAPI(title="Rosee")

@app.get("/api/health")
def health():
    return {"status": "ok"}
