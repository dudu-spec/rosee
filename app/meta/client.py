"""Meta Business API integration module.

Before using:
1. Register an app at https://developers.facebook.com
2. Enable Instagram Basic Display + Instagram Content Publishing
3. Get a long-lived access token
4. Get your Instagram Business Account ID

Set these values via the /api/settings endpoint or directly in the DB.
"""

import json
import time
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlencode

import requests

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 5


class MetaClient:
    def __init__(self, access_token: str = "", ig_user_id: str = "",
                 app_id: str = "", app_secret: str = ""):
        self.access_token = access_token
        self.ig_user_id = ig_user_id
        self.app_id = app_id
        self.app_secret = app_secret
        self.session = requests.Session()
        self.session.timeout = DEFAULT_TIMEOUT

    def is_configured(self) -> bool:
        return bool(self.access_token) and bool(self.ig_user_id)

    def _request(self, method: str, endpoint: str,
                 data: Dict = None, params: Dict = None) -> Dict[str, Any]:
        if params is None:
            params = {}
        params["access_token"] = self.access_token

        url = f"{GRAPH_API_BASE}/{endpoint}"
        kwargs = {"params": params, "timeout": DEFAULT_TIMEOUT}

        if data:
            kwargs["data"] = data

        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.request(method, url, **kwargs)
                result = response.json()

                if response.status_code == 200:
                    return result

                error = result.get("error", {})
                code = error.get("code", 0)
                message = error.get("message", "")

                # Token expired
                if code == 190:
                    raise TokenExpiredError(message)

                # Rate limit
                if code == 4 or code == 17 or code == 100:
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY * (attempt + 1))
                        continue
                    raise RateLimitError(message)

                # Media still processing
                if code == 9007:
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(5)
                        continue
                    raise MediaProcessingError(message)

                last_error = MetaAPIError(f"HTTP {response.status_code}: {message}", code)
                break

            except (requests.ConnectionError, requests.Timeout) as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                    continue
                last_error = ConnectionError(f"Falha na conexão após {MAX_RETRIES} tentativas: {e}")
                break

        raise last_error or MetaAPIError("Erro desconhecido na API do Meta", -1)

    def create_media_container(self, media_path: str, caption: str,
                               media_type: str = "IMAGE",
                               is_reel: bool = False) -> Dict:
        """
        Step 1: Create a media container.
        Returns container ID. Then call publish_media().
        """
        import os

        params = {
            "caption": caption,
        }

        if media_type.upper() == "IMAGE":
            params["image_url"] = self._upload_image(media_path)
        elif media_type.upper() == "VIDEO" or is_reel:
            params["media_type"] = "REELS" if is_reel else "VIDEO"
            params["video_url"] = self._upload_video(media_path)
            if is_reel:
                params["media_type"] = "REELS"

        result = self._request("POST", f"{self.ig_user_id}/media", params=params)
        return result

    def publish_media(self, container_id: str) -> Dict:
        """
        Step 2: Publish the media container.
        """
        data = {
            "creation_id": container_id,
        }
        result = self._request("POST", f"{self.ig_user_id}/media_publish", data=data)
        return result

    def get_media_status(self, container_id: str) -> Dict:
        """Check if media container is ready for publishing."""
        return self._request("GET", f"{container_id}",
                             params={"fields": "status_code,id"})

    def get_instagram_account(self) -> Optional[Dict]:
        """Get Instagram Business Account ID from Facebook Page."""
        if not self.app_id:
            return None
        params = {"fields": "instagram_business_account"}
        return self._request("GET", "me/accounts", params=params)

    def refresh_token(self) -> Optional[str]:
        """Exchange short-lived token for long-lived (60 days)."""
        if not all([self.app_id, self.app_secret, self.access_token]):
            return None
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "fb_exchange_token": self.access_token,
        }
        result = self._request("GET", "/oauth/access_token", params=params)
        self.access_token = result.get("access_token", self.access_token)
        return self.access_token

    def get_token_expiry(self) -> Optional[int]:
        """Check days until token expiry. Returns None if unknown."""
        try:
            result = self._request("GET", "/debug_token",
                                   params={"input_token": self.access_token})
            data = result.get("data", {})
            expires_at = data.get("expires_at", 0)
            if not expires_at:
                return None
            remaining = expires_at - time.time()
            return int(remaining / 86400)  # days
        except Exception:
            return None

    def _upload_image(self, media_path: str) -> str:
        """Upload image to Supabase Storage and return public URL."""
        url = self._upload_to_supabase(media_path)
        if url:
            return url
        # Fallback: file:// (will fail, but better than crashing)
        return f"file://{media_path}"

    def _upload_video(self, media_path: str) -> str:
        """Upload video to Supabase Storage and return public URL."""
        url = self._upload_to_supabase(media_path)
        if url:
            return url
        return f"file://{media_path}"

    def _upload_to_supabase(self, file_path: str) -> Optional[str]:
        """Upload a local file to Supabase Storage bucket 'media' and return public URL."""
        try:
            import os
            from pathlib import Path
            from dotenv import load_dotenv

            dotenv_path = Path(__file__).resolve().parent.parent.parent / ".env"
            if dotenv_path.exists():
                load_dotenv(str(dotenv_path))

            supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("SUPABASE_ANON_KEY", "")
            if not supabase_url or not supabase_key:
                logger.warning("Supabase não configurado para upload de mídia")
                return None

            local_path = Path(file_path)
            if not local_path.exists():
                logger.error(f"Arquivo não encontrado: {file_path}")
                return None

            bucket = "media"
            dest_path = f"posts/{local_path.name}"
            auth_header = {"Authorization": f"Bearer {supabase_key}"}

            # Ensure bucket exists
            try:
                requests.post(
                    f"{supabase_url}/storage/v1/bucket",
                    headers={**auth_header, "Content-Type": "application/json"},
                    json={"name": bucket, "public": True},
                    timeout=10,
                )
            except Exception:
                pass  # bucket may already exist

            # Upload file
            with open(local_path, "rb") as f:
                file_data = f.read()

            resp = requests.post(
                f"{supabase_url}/storage/v1/object/{bucket}/{dest_path}",
                headers=auth_header,
                files={"file": (local_path.name, file_data, "image/jpeg")},
                timeout=120,
            )

            if resp.status_code in (200, 201):
                public_url = f"{supabase_url}/storage/v1/object/public/{bucket}/{dest_path}"
                logger.info(f"Upload feito: {public_url}")
                return public_url
            else:
                logger.error(f"Falha no upload Supabase: {resp.status_code} {resp.text[:200]}")
                return None

        except Exception as e:
            logger.exception(f"Erro no upload Supabase: {e}")
            return None


class MetaAPIError(Exception):
    def __init__(self, message: str, code: int = -1):
        self.code = code
        super().__init__(message)


class TokenExpiredError(MetaAPIError):
    pass


class RateLimitError(MetaAPIError):
    pass


class MediaProcessingError(MetaAPIError):
    pass