"""
FastAPI backend — Instagram Automation for Clothing Store.
Run with: uvicorn backend.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.database.connection import init_db
from app.backend.routes import posts, templates, meta, settings, chat

app = FastAPI(
    title="Rosee Instagram Automation",
    description="Sistema de automação de postagens para loja de roupas no Instagram.",
    version="1.0.0",
)

# CORS — allow any origin (Vercel backend + local frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve processed media files
storage_path = Path(__file__).resolve().parent.parent / "storage"
if storage_path.exists():
    app.mount("/media", StaticFiles(directory=str(storage_path)), name="media")

# Routers
app.include_router(posts.router)
app.include_router(templates.router)
app.include_router(meta.router)
app.include_router(settings.router)
app.include_router(chat.router)


@app.on_event("startup")
def startup():
    init_db()
    # Publish any posts that were scheduled while backend was offline
    try:
        from app.scheduler.jobs import run_pending_posts
        run_pending_posts()
    except Exception:
        pass


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "Rosee Instagram Automation"}