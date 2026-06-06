from fastapi import APIRouter
from pydantic import BaseModel

from app.backend.services.post_service import get_settings, update_setting

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingUpdate(BaseModel):
    key: str
    value: str


@router.get("/")
def list_settings():
    return get_settings()


@router.post("/")
def save_setting(req: SettingUpdate):
    update_setting(req.key, req.value)
    return {"success": True, "message": f"{req.key} atualizado."}