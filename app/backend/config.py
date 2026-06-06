import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STORAGE_DIR = PROJECT_ROOT / "storage"
PROCESSED_DIR = STORAGE_DIR / "processed"
DB_PATH = STORAGE_DIR / "instagram_automation.db"

try:
    os.makedirs(str(PROCESSED_DIR), exist_ok=True)
except PermissionError:
    pass  # Vercel: filesystem is read-only

# If true, publish job just prints instead of calling Meta API
MOCK_META_API = False

# OpenRouter
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")