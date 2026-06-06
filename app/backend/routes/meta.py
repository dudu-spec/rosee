from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.meta.client import MetaClient
from app.backend.services.post_service import get_settings, update_setting
from app.backend.config import MOCK_META_API

router = APIRouter(prefix="/api/meta", tags=["meta"])


class MetaSettingsRequest(BaseModel):
    access_token: str = ""
    ig_user_id: str = ""
    app_id: str = ""
    app_secret: str = ""


@router.get("/status")
def meta_status():
    settings = get_settings()
    client = MetaClient(
        access_token=settings.get("meta_access_token", ""),
        ig_user_id=settings.get("meta_ig_user_id", ""),
        app_id=settings.get("meta_app_id", ""),
        app_secret=settings.get("meta_app_secret", ""),
    )

    if not client.is_configured():
        return {
            "configured": False,
            "message": "Meta Business não configurado. Configure token e IG User ID."
        }

    if MOCK_META_API:
        return {
            "configured": True,
            "mode": "mock",
            "message": "Meta API em modo MOCK. Para publicar de verdade, desative MOCK_META_API em config.py."
        }

    try:
        expiry_days = client.get_token_expiry()
        return {
            "configured": True,
            "mode": "live",
            "token_expiry_days": expiry_days,
            "needs_refresh": expiry_days is not None and expiry_days < 7,
        }
    except Exception as e:
        return {
            "configured": True,
            "mode": "live",
            "error": str(e),
        }


@router.post("/configure")
def configure_meta(req: MetaSettingsRequest):
    if req.access_token:
        update_setting("meta_access_token", req.access_token)
    if req.ig_user_id:
        update_setting("meta_ig_user_id", req.ig_user_id)
    if req.app_id:
        update_setting("meta_app_id", req.app_id)
    if req.app_secret:
        update_setting("meta_app_secret", req.app_secret)
    return {"success": True, "message": "Configurações salvas."}


@router.post("/test")
def test_connection():
    settings = get_settings()
    client = MetaClient(
        access_token=settings.get("meta_access_token", ""),
        ig_user_id=settings.get("meta_ig_user_id", ""),
    )

    if not client.is_configured():
        raise HTTPException(status_code=400, detail="Meta não configurado.")

    if MOCK_META_API:
        return {"success": True, "mode": "mock", "message": "Conexão simulada (MOCK)."}

    try:
        result = client.get_instagram_account()
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/settings")
def get_meta_settings():
    settings = get_settings()
    return {
        "meta_app_id": settings.get("meta_app_id", ""),
        "meta_ig_user_id": settings.get("meta_ig_user_id", ""),
        "has_token": bool(settings.get("meta_access_token", "")),
    }