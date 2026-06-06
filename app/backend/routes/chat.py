from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.backend.services.command_parser import parse_command, parse_datetime
from app.backend.services import post_service, media_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


class InterpretRequest(BaseModel):
    text: str
    photos: List[Dict[str, Any]]


class InterpretResponse(BaseModel):
    interpretation: Dict[str, Any]
    preview: str
    needs_confirmation: bool = True


class ExecuteRequest(BaseModel):
    interpretation: Dict[str, Any]
    photo_files: List[Dict[str, Any]]


def _format_datetime_preview(dt_str: Optional[str]) -> str:
    if not dt_str:
        return "sem data"
    try:
        dt = datetime.fromisoformat(dt_str)
        days = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
        day_name = days[dt.weekday()]
        return f"{day_name} {dt.day:02d}/{dt.month:02d} às {dt.hour:02d}:{dt.minute:02d}"
    except Exception:
        return dt_str


@router.post("/interpret", response_model=InterpretResponse)
def interpret_command(req: InterpretRequest):
    descriptions = [p.get("ai_description", "") or p.get("description", "") for p in req.photos]
    result = parse_command(req.text, descriptions)

    target_str = result.get("target_str") or "foto desconhecida"
    action_str = result.get("action", "gerar")
    datetime_str = _format_datetime_preview(result.get("datetime"))

    if action_str == "agendar":
        preview = f"📅 Agendar {target_str} para {datetime_str}"
    elif action_str == "gerar":
        preview = f"✨ Gerar conteúdo para {target_str}"
    elif action_str == "cancelar":
        preview = f"🗑️ Cancelar {target_str}"
    else:
        preview = f"🔄 {action_str} {target_str}"

    if result.get("price"):
        preview += f" — R$ {result['price']:.2f}"
    if result.get("sizes"):
        preview += f" — Tam: {result['sizes']}"

    preview += "\n\nConfirma?"
    needs_confirmation = True

    return InterpretResponse(
        interpretation=result,
        preview=preview,
        needs_confirmation=needs_confirmation,
    )


class ActionPlan(BaseModel):
    action: str
    target_index: Optional[int]
    datetime: Optional[str] = None
    price: Optional[float] = None
    sizes: Optional[str] = None


@router.post("/execute")
def execute_command(req: ExecuteRequest):
    interp = req.interpretation
    action = interp.get("action", "gerar")
    target_idx = interp.get("target_index")
    dt_str = interp.get("datetime")
    price = interp.get("price")
    sizes = interp.get("sizes")
    photos = req.photo_files

    if target_idx == -999:
        indices = list(range(len(photos)))
    elif target_idx is not None and 0 <= target_idx < len(photos):
        indices = [target_idx]
    else:
        return {"success": False, "message": "Nenhuma foto alvo identificada."}

    results = []

    for idx in indices:
        photo = photos[idx]
        user_input = photo.get("user_input", "")
        file_bytes = photo.get("file_bytes")
        filename = photo.get("filename", f"photo_{idx}.jpg")

        if action == "agendar":
            if not dt_str:
                return {"success": False, "message": "Nenhuma data informada para agendar."}
            try:
                dt = datetime.fromisoformat(dt_str)
                if dt.tzinfo is None:
                    from datetime import timezone, timedelta
                    dt = dt.replace(tzinfo=timezone(timedelta(hours=-3)))
                schedule_str = dt.isoformat()
            except Exception:
                return {"success": False, "message": f"Data inválida: {dt_str}"}

            if file_bytes:
                valid, msg = media_service.validate_upload(file_bytes, filename)
                if not valid:
                    results.append({"index": idx, "error": msg})
                    continue
                media_path, media_type, _ = media_service.save_upload(file_bytes, filename)
            else:
                media_path = photo.get("media_path", "")
                media_type = photo.get("media_type", "image")

            try:
                post = post_service.create_post(
                    media_path=media_path,
                    media_type=media_type,
                    user_input=user_input,
                    price=price,
                    sizes=sizes or "",
                    template_id=photo.get("template_id", "tpl_feed_01"),
                )
                success, message, issues = post_service.approve_post(
                    post_id=post["id"],
                    final_caption=post.get("final_caption") or post.get("ai_caption", ""),
                    final_cta=post.get("final_cta") or post.get("ai_cta", ""),
                    final_hashtags=post.get("final_hashtags") or post.get("ai_hashtags", ""),
                    final_category=post.get("final_category") or post.get("ai_category", "look"),
                    scheduled_at=schedule_str,
                    template_id=photo.get("template_id", "tpl_feed_01"),
                )
                results.append({
                    "index": idx,
                    "post_id": post["id"],
                    "success": success,
                    "message": message,
                })
            except Exception as e:
                results.append({"index": idx, "error": str(e)})

        elif action == "gerar":
            if file_bytes:
                valid, msg = media_service.validate_upload(file_bytes, filename)
                if not valid:
                    results.append({"index": idx, "error": msg})
                    continue
                media_path, media_type, _ = media_service.save_upload(file_bytes, filename)
            else:
                media_path = photo.get("media_path", "")
                media_type = photo.get("media_type", "image")

            try:
                post = post_service.create_post(
                    media_path=media_path,
                    media_type=media_type,
                    user_input=user_input,
                    price=price,
                    sizes=sizes or "",
                    template_id=photo.get("template_id", "tpl_feed_01"),
                )
                results.append({
                    "index": idx,
                    "post_id": post["id"],
                    "success": True,
                    "status": "rascunho",
                })
            except Exception as e:
                results.append({"index": idx, "error": str(e)})

        else:
            results.append({"index": idx, "error": f"Ação '{action}' não implementada."})

    success_count = sum(1 for r in results if r.get("success"))
    return {
        "success": all(r.get("success", False) for r in results),
        "message": f"{success_count}/{len(indices)} operações concluídas.",
        "results": results,
    }
