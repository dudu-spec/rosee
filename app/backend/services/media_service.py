import shutil
import uuid
from pathlib import Path

STORAGE_DIR = Path(__file__).resolve().parent.parent.parent / "storage"
MEDIA_DIR = STORAGE_DIR / "uploads"
PROCESSED_DIR = STORAGE_DIR / "processed"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".mp4", ".mov"}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


def save_upload(file_bytes: bytes, original_filename: str) -> tuple[str, str, str]:
    """
    Save uploaded file to storage.
    Returns (media_path, media_type, file_id).
    """
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    ext = Path(original_filename).suffix.lower()
    file_id = str(uuid.uuid4())
    safe_name = f"{file_id}{ext}"
    dest_path = MEDIA_DIR / safe_name

    with open(str(dest_path), "wb") as f:
        f.write(file_bytes)

    if ext in (".mp4", ".mov"):
        media_type = "video"
    else:
        media_type = "image"

    return str(dest_path), media_type, file_id


def delete_media(file_path: str):
    """Delete a media file from storage."""
    if file_path and Path(file_path).exists():
        Path(file_path).unlink(missing_ok=True)


def validate_upload(file_bytes: bytes, filename: str) -> tuple[bool, str]:
    """Validate uploaded file."""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Formato '{ext}' não suportado. Use: {', '.join(ALLOWED_EXTENSIONS)}"
    if len(file_bytes) > MAX_FILE_SIZE:
        return False, f"Arquivo muito grande (máx. 100MB)"
    return True, "OK"