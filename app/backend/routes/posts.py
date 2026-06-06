from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional, List
from pydantic import BaseModel

from app.backend.services import media_service, post_service

router = APIRouter(prefix="/api/posts", tags=["posts"])


class ApproveRequest(BaseModel):
    final_caption: str
    final_cta: str
    final_hashtags: str
    final_category: str
    scheduled_at: str
    final_template_id: str = ""

    from pydantic import validator
    @validator("scheduled_at")
    def validate_date(cls, v):
        from datetime import datetime
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError(f"Data inválida: '{v}'. Use formato ISO (YYYY-MM-DDTHH:MM).")
        return v


@router.post("/upload")
async def upload_post(
    file: UploadFile = File(...),
    user_input: str = Form(""),
    price: Optional[float] = Form(None),
    sizes: str = Form(""),
    template_id: str = Form("tpl_feed_01"),
):
    file_bytes = await file.read()

    valid, msg = media_service.validate_upload(file_bytes, file.filename)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)

    media_path, media_type, file_id = media_service.save_upload(file_bytes, file.filename)

    try:
        post = post_service.create_post(
            media_path=media_path,
            media_type=media_type,
            user_input=user_input,
            price=price,
            sizes=sizes,
            template_id=template_id,
        )
    except Exception as e:
        media_service.delete_media(media_path)
        raise HTTPException(status_code=500, detail=f"Erro ao processar post: {str(e)}")

    return post


@router.get("/ai-status")
def ai_status():
    """Retorna status atual do sistema de IA, útil para debug."""
    from app.ai_engine.interface import _detect_backend, _ultimo_erro_openrouter, _openrouter_key
    backend = _detect_backend()
    has_key = bool(_openrouter_key())
    last_error = _ultimo_erro_openrouter()
    return {
        "backend": backend,
        "has_openrouter_key": has_key,
        "last_error": last_error,
        "using_cloud_ai": backend == "openrouter",
    }


@router.get("/{post_id}")
def get_post(post_id: str):
    post = post_service.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado.")
    return post


@router.put("/{post_id}/review")
def update_review(post_id: str, data: dict):
    """Save user edits to a post in review."""
    allowed = {
        'final_caption', 'final_cta', 'final_hashtags',
        'final_category', 'scheduled_at', 'final_template_id',
    }
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        raise HTTPException(status_code=400, detail="Nenhum campo válido para atualizar.")
    post = post_service.update_post(post_id, **updates)
    return post


@router.post("/{post_id}/approve")
def approve_post(post_id: str, req: ApproveRequest):
    success, message, issues = post_service.approve_post(
        post_id=post_id,
        final_caption=req.final_caption,
        final_cta=req.final_cta,
        final_hashtags=req.final_hashtags,
        final_category=req.final_category,
        scheduled_at=req.scheduled_at,
        template_id=req.final_template_id,
    )
    if not success:
        raise HTTPException(status_code=400, detail={"message": message, "issues": issues})
    return {"success": True, "message": message, "warnings": issues}


@router.post("/{post_id}/cancel")
def cancel_schedule(post_id: str):
    post = post_service.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado.")
    post_service.update_post(post_id, status='revisao', scheduled_at='')
    from app.scheduler.jobs import cancel_schedule as cancel_job
    cancel_job(post_id)
    return {"success": True, "message": "Agendamento cancelado."}


@router.post("/{post_id}/regenerate")
def regenerate_post(post_id: str):
    """Re-run AI analysis and caption generation for a post."""
    post = post_service.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado.")
    try:
        updated = post_service.regenerate_ai_content(post_id)
        return {"success": True, "post": updated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao regenerar: {str(e)}")


@router.delete("/{post_id}")
def discard_post(post_id: str):
    post = post_service.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado.")
    media_service.delete_media(post.get('media_path', ''))
    media_service.delete_media(post.get('media_processed_path', ''))
    post_service.delete_post(post_id)
    return {"success": True, "message": "Post descartado."}


@router.get("/")
def list_posts(status: str = None, limit: int = 50, offset: int = 0):
    posts = post_service.list_posts(status, limit, offset)
    return {"posts": posts, "total": len(posts)}


@router.get("/upcoming")
def list_upcoming():
    """Return upcoming scheduled posts, newest first."""
    from app.scheduler.jobs import list_scheduled_jobs
    jobs = list_scheduled_jobs()
    posts = post_service.list_posts(status="agendado", limit=50, offset=0)
    posts.sort(key=lambda p: p.get("scheduled_at", ""))
    return {"posts": posts, "scheduled_jobs": jobs}


@router.get("/{post_id}/full")
def get_full_post(post_id: str):
    post = post_service.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado.")
    return post


class BatchUploadRequest(BaseModel):
    folder_path: str = ""
    user_input: str = ""
    price: Optional[float] = None
    sizes: str = ""
    template_id: str = "tpl_feed_01"


@router.post("/batch")
def batch_upload(req: BatchUploadRequest):
    """Process all images in a folder, creating posts in status 'rascunho'."""
    import os
    from pathlib import Path

    folder = Path(req.folder_path)
    if not folder.exists() or not folder.is_dir():
        raise HTTPException(status_code=400, detail="Pasta não encontrada.")

    # Security: resolve real path and restrict to known directories
    folder = folder.resolve()
    allowed_prefixes = [
        Path.home() / "Desktop",
        Path.home() / "Documents",
        Path.home() / "Pictures",
        Path.home() / "Downloads",
        Path.home() / "OneDrive",
    ]
    if not any(str(folder).startswith(str(p)) for p in allowed_prefixes if p.exists()):
        raise HTTPException(status_code=403, detail="Acesso negado: pasta fora dos diretórios permitidos (Desktop, Documents, Pictures, Downloads).")

    valid_exts = {'.jpg', '.jpeg', '.png'}
    image_files = [f for f in folder.iterdir()
                   if f.suffix.lower() in valid_exts and f.is_file()]

    if not image_files:
        raise HTTPException(status_code=400, detail="Nenhuma imagem encontrada na pasta.")

    results = []
    errors = []

    for img_path in image_files:
        try:
            post = post_service.create_post(
                media_path=str(img_path),
                media_type="image",
                user_input=req.user_input or "",
                price=req.price,
                sizes=req.sizes or "",
                template_id=req.template_id,
                initial_status="rascunho",
            )
            results.append({
                "post_id": post["id"],
                "file": img_path.name,
                "caption": post.get("ai_caption", "")[:80],
                "status": post.get("status", "rascunho"),
            })
        except Exception as e:
            errors.append({"file": img_path.name, "error": str(e)})

    return {
        "processed": len(results),
        "errors": len(errors),
        "posts": results,
        "error_details": errors,
    }