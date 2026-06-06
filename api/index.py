"""Vercel serverless entry point."""
import os
os.environ["VERCEL"] = "1"

import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_root))

from fastapi import FastAPI

app = FastAPI(title="Rosee")

# Step-test which import breaks
errors = {}
try:
    from app.database.connection import init_db
except Exception as e:
    errors["connection"] = f"{type(e).__name__}: {str(e)[:200]}"

try:
    from app.backend.config import MOCK_META_API
except Exception as e:
    errors["config"] = f"{type(e).__name__}: {str(e)[:200]}"

try:
    from app.backend.services.post_service import get_settings
except Exception as e:
    errors["post_service"] = f"{type(e).__name__}: {str(e)[:200]}"

try:
    from app.ai_engine.interface import analyze_image, generate_caption
except Exception as e:
    errors["interface"] = f"{type(e).__name__}: {str(e)[:200]}"

try:
    from app.backend.main import app as main_app
    app.mount("", main_app)
except Exception as e:
    errors["main_app"] = f"{type(e).__name__}: {str(e)[:200]}"

@app.get("/api/health")
def health():
    if errors:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=500, content={"errors": errors})
    return {"status": "ok", "app": "Rosee"}
