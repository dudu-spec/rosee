import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict

from app.database.connection import table, get_connection
from app.validators.rules import validate_post
from app.ai_engine.interface import analyze_image, generate_caption
from app.templates.engine import apply_image_template, apply_video_template

BRASIL_TZ = timezone(timedelta(hours=-3))


def create_post(media_path: str, media_type: str,
                user_input: str = "", price: float = None,
                sizes: str = "", template_id: str = "tpl_feed_01",
                initial_status: str = "revisao") -> dict:
    """Create a new post: save to DB, run AI, apply template."""
    post_id = str(uuid.uuid4())
    now = datetime.now(BRASIL_TZ).isoformat()

    ai_analysis = analyze_image(media_path)
    ai_content = generate_caption(
        description=ai_analysis.description,
        user_input=user_input,
        price=price,
        sizes=sizes,
    )

    if media_type == "video":
        processed_path = apply_video_template(media_path, template_id, price, sizes)
    else:
        processed_path = apply_image_template(media_path, template_id, price, sizes)

    data = {
        "id": post_id,
        "status": initial_status,
        "created_at": now,
        "updated_at": now,
        "user_input": user_input or "",
        "price": price,
        "sizes": sizes or "",
        "media_type": media_type,
        "media_path": media_path,
        "media_processed_path": processed_path or "",
        "ai_description": ai_analysis.description or "",
        "ai_caption": ai_content.caption or "",
        "ai_cta": ai_content.cta or "",
        "ai_hashtags": ",".join(ai_content.hashtags) if ai_content.hashtags else "",
        "ai_category": ai_content.category or "look",
    }

    table("posts").insert(data)
    return get_post(post_id)


def get_post(post_id: str) -> dict:
    """Fetch a single post by ID."""
    rows = table("posts").select(eq={"id": post_id})
    return rows[0] if rows else {}


def update_post(post_id: str, **kwargs) -> dict:
    """Update post fields. Returns updated post."""
    now = datetime.now(BRASIL_TZ).isoformat()

    allowed = {
        'final_caption', 'final_cta', 'final_hashtags',
        'final_category', 'final_template_id', 'scheduled_at',
        'status', 'error_log', 'instagram_post_id',
        'meta_response', 'published_at', 'approved_by',
        'user_input', 'price', 'sizes', 'media_processed_path',
    }

    updates = {"updated_at": now}
    for key, val in kwargs.items():
        if key in allowed and val is not None:
            updates[key] = val

    if updates:
        table("posts").update(updates, eq={"id": post_id})

    return get_post(post_id)


def regenerate_ai_content(post_id: str) -> dict:
    """Re-run AI analysis and caption generation for a post."""
    post = get_post(post_id)
    if not post:
        return {}

    media_path = post.get("media_path", "")
    media_type = post.get("media_type", "image")
    user_input = post.get("user_input", "")
    price = post.get("price")
    sizes = post.get("sizes", "")

    ai_analysis = analyze_image(media_path)
    ai_content = generate_caption(
        description=ai_analysis.description,
        user_input=user_input,
        price=price,
        sizes=sizes,
    )

    updates = {
        "ai_description": ai_analysis.description,
        "ai_caption": ai_content.caption,
        "ai_cta": ai_content.cta,
        "ai_hashtags": ",".join(ai_content.hashtags) if ai_content.hashtags else "",
        "ai_category": ai_content.category or "look",
    }
    update_post(post_id, **updates)
    return get_post(post_id)


def approve_post(post_id: str, final_caption: str, final_cta: str,
                 final_hashtags: str, final_category: str,
                 scheduled_at: str, template_id: str = "") -> tuple[bool, str, list]:
    """Approve and schedule a post."""
    post = get_post(post_id)
    if not post:
        return False, "Post não encontrado.", []

    data = {
        'final_caption': final_caption,
        'final_cta': final_cta,
        'final_hashtags': final_hashtags,
        'final_category': final_category,
        'scheduled_at': scheduled_at,
    }

    valid, errors, warnings = validate_post(data,
                                            original_price=post.get('price'),
                                            original_sizes=post.get('sizes', ''))

    if not valid:
        return False, "Validação falhou.", errors + warnings

    now = datetime.now(BRASIL_TZ).isoformat()

    table("posts").update({
        "status": "agendado",
        "final_caption": final_caption,
        "final_cta": final_cta,
        "final_hashtags": final_hashtags,
        "final_category": final_category,
        "scheduled_at": scheduled_at,
        "final_template_id": template_id or post.get('final_template_id', ''),
        "updated_at": now,
    }, eq={"id": post_id})

    table("approvals").insert({
        "post_id": post_id,
        "approved_at": now,
        "final_caption": final_caption,
        "final_cta": final_cta,
        "final_hashtags": final_hashtags,
        "final_category": final_category,
        "scheduled_at": scheduled_at,
    })

    from app.scheduler.jobs import schedule_post
    schedule_post(post_id, scheduled_at)

    return True, "Post aprovado e agendado com sucesso.", warnings


def list_posts(status: str = None, limit: int = 50, offset: int = 0) -> List[dict]:
    """List posts with optional status filter."""
    params = dict(limit=limit, offset=offset, order="updated_at.desc")
    if status:
        params["eq"] = {"status": status}
    return table("posts").select(**params)


def delete_post(post_id: str) -> bool:
    """Soft-delete: set status to 'descartado'."""
    now = datetime.now(BRASIL_TZ).isoformat()
    table("posts").update({"status": "descartado", "updated_at": now}, eq={"id": post_id})
    return True


def get_settings() -> dict:
    """Get all settings."""
    rows = table("settings").select()
    return {r["key"]: r["value"] for r in rows}


def update_setting(key: str, value: str):
    """Update a setting value."""
    now = datetime.now(BRASIL_TZ).isoformat()
    table("settings").upsert({"key": key, "value": value, "updated_at": now}, on_conflict="key")
