from fastapi import APIRouter, HTTPException

from app.templates.engine import get_available_templates

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("/")
def list_templates(template_type: str = None):
    templates = get_available_templates(template_type)
    return {"templates": templates}