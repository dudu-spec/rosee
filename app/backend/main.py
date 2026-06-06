"""
FastAPI backend — Instagram Automation for Clothing Store.
Run with: uvicorn backend.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
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


INDEX_HTML_CONTENT: str | None = None

@app.on_event("startup")
def startup():
    global INDEX_HTML_CONTENT
    init_db()
    p = Path("public/index.html").resolve()
    if p.exists():
        INDEX_HTML_CONTENT = p.read_text(encoding="utf-8")
    try:
        from app.scheduler.jobs import run_pending_posts
        run_pending_posts()
    except Exception:
        pass


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "Rosee Instagram Automation"}


@app.get("/")
async def serve_root():
    if INDEX_HTML_CONTENT is not None:
        return HTMLResponse(content=INDEX_HTML_CONTENT, status_code=200)
    return JSONResponse(status_code=404, content={"detail": "Frontend not built"})


@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    if full_path.startswith("api/"):
        return JSONResponse(status_code=404, content={"detail": "Not found"})
    if INDEX_HTML_CONTENT is not None:
        return HTMLResponse(content=INDEX_HTML_CONTENT, status_code=200)
    return JSONResponse(status_code=404, content={"detail": "Frontend not built"})