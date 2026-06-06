"""APScheduler-based scheduler for publishing Instagram posts."""

from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
import json
import logging

from app.database.connection import table
from app.meta.client import MetaClient
from app.backend.config import MOCK_META_API

logger = logging.getLogger(__name__)
BRASIL_TZ = timezone(timedelta(hours=-3))

_scheduler = None


def get_scheduler():
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone=BRASIL_TZ)
        _scheduler.start()
    return _scheduler


def publish_post(post_id: str):
    """Called by APScheduler at the scheduled time. Publishes via Meta API (or mock)."""
    rows = table("posts").select(eq={"id": post_id})
    if not rows:
        logger.error(f"Post {post_id} não encontrado para publicação.")
        return

    post = rows[0]
    if post.get("status") != "agendado":
        logger.warning(f"Post {post_id} não está agendado (status={post.get('status')}). Ignorando.")
        return

    if MOCK_META_API:
        logger.info(f"[MOCK] Publicando post {post_id}...")
        logger.info(f"  Legenda: {post.get('final_caption', '')[:80]}...")
        logger.info(f"  Mídia: {post.get('media_processed_path', '')}")
        logger.info(f"  Instagram Post ID (mock): {post_id[:8]}")

        table("posts").update({
            "status": "publicado",
            "published_at": datetime.now(BRASIL_TZ).isoformat(),
            "instagram_post_id": f"mock_{post_id[:8]}",
            "meta_response": '{"mock": true}',
        }, eq={"id": post_id})

        logger.info(f"Post {post_id} publicado (MOCK).")
        return

    # ── Real Meta API publishing ──
    from app.backend.services.post_service import get_settings
    settings = get_settings()

    client = MetaClient(
        access_token=settings.get("meta_access_token", ""),
        ig_user_id=settings.get("meta_ig_user_id", ""),
        app_id=settings.get("meta_app_id", ""),
        app_secret=settings.get("meta_app_secret", ""),
    )

    if not client.is_configured():
        table("posts").update({
            "status": "falha_publicacao",
            "error_log": "Meta não configurado.",
        }, eq={"id": post_id})
        logger.error(f"Post {post_id}: Meta não configurado.")
        return

    try:
        media_type = post.get("media_type", "image")
        caption = post.get("final_caption", "")

        if post.get("final_hashtags"):
            caption += "\n\n" + post["final_hashtags"]

        container = client.create_media_container(
            media_path=post.get("media_processed_path", ""),
            caption=caption,
            media_type="IMAGE" if media_type == "image" else "VIDEO",
        )

        container_id = container.get("id")
        if not container_id:
            raise Exception(f"Container ID não recebido: {json.dumps(container)}")

        result = client.publish_media(container_id)

        table("posts").update({
            "status": "publicado",
            "published_at": datetime.now(BRASIL_TZ).isoformat(),
            "instagram_post_id": result.get("id", ""),
            "meta_response": json.dumps(result),
        }, eq={"id": post_id})

    except Exception as e:
        logger.exception(f"Falha ao publicar post {post_id}")
        table("posts").update({
            "status": "falha_publicacao",
            "error_log": str(e),
        }, eq={"id": post_id})


def schedule_post(post_id: str, scheduled_at_iso: str):
    """Schedule a post for publishing."""
    try:
        sched_dt = datetime.fromisoformat(scheduled_at_iso)
        if sched_dt.tzinfo is None:
            sched_dt = sched_dt.replace(tzinfo=BRASIL_TZ)
    except (ValueError, TypeError) as e:
        logger.error(f"Data inválida para post {post_id}: {scheduled_at_iso}")
        return

    job_id = f"publish_{post_id}"
    sched = get_scheduler()

    existing = sched.get_job(job_id)
    if existing:
        sched.remove_job(job_id)

    sched.add_job(
        publish_post,
        trigger=DateTrigger(run_date=sched_dt),
        args=[post_id],
        id=job_id,
        replace_existing=True,
        name=f"Publicar post {post_id[:8]}",
    )

    logger.info(f"Post {post_id} agendado para {sched_dt.isoformat()}")


def cancel_schedule(post_id: str):
    """Cancel a scheduled post."""
    job_id = f"publish_{post_id}"
    existing = get_scheduler().get_job(job_id)
    if existing:
        get_scheduler().remove_job(job_id)
        logger.info(f"Agendamento cancelado para post {post_id}")


def run_pending_posts():
    """On startup, publish any overdue posts and re-schedule future pending ones."""
    now = datetime.now(BRASIL_TZ).isoformat()
    sched = get_scheduler()
    rows = table("posts").select(
        columns="id,scheduled_at",
        eq={"status": "agendado"},
    )
    for row in rows:
        if row.get("scheduled_at") and row["scheduled_at"] <= now:
            logger.info(f"Publicando post atrasado: {row['id']}")
            publish_post(row["id"])
        elif row.get("scheduled_at"):
            schedule_post(row["id"], row["scheduled_at"])


def list_scheduled_jobs():
    """List all scheduled jobs for display."""
    jobs = []
    for job in get_scheduler().get_jobs():
        if job.name.startswith("Publicar post "):
            jobs.append({
                "post_id": job.args[0],
                "scheduled_at": job.next_run_time.isoformat() if job.next_run_time else "",
                "name": job.name,
            })
    return jobs
