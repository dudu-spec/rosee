import os
import requests
from pathlib import Path
from dotenv import load_dotenv

dotenv_path = Path(__file__).resolve().parent.parent.parent / ".env"
if dotenv_path.exists():
    load_dotenv(str(dotenv_path))

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("SUPABASE_ANON_KEY", "")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}


class SupabaseTable:
    def __init__(self, table_name: str):
        self.url = f"{SUPABASE_URL}/rest/v1/{table_name}"

    def select(self, columns="*", eq=None, order=None, limit=None, offset=None, gte=None, lte=None):
        params = [f"select={columns}"]
        if eq:
            for k, v in eq.items():
                params.append(f"{k}=eq.{v}")
        if gte:
            for k, v in gte.items():
                params.append(f"{k}=gte.{v}")
        if lte:
            for k, v in lte.items():
                params.append(f"{k}=lte.{v}")
        if order:
            params.append(f"order={order}")
        if limit:
            params.append(f"limit={limit}")
        if offset:
            params.append(f"offset={offset}")
        url = f"{self.url}?{'&'.join(params)}"
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r.json()

    def insert(self, data):
        r = requests.post(self.url, headers=HEADERS, json=data, timeout=15)
        r.raise_for_status()
        return r.json()

    def update(self, data, eq):
        params = "&".join(f"{k}=eq.{v}" for k, v in eq.items())
        r = requests.patch(f"{self.url}?{params}", headers=HEADERS, json=data, timeout=15)
        r.raise_for_status()
        return r.json()

    def upsert(self, data, on_conflict="key"):
        headers = {**HEADERS, "Prefer": "return=representation,resolution=merge-duplicates"}
        r = requests.post(f"{self.url}?on_conflict={on_conflict}", headers=headers, json=data, timeout=15)
        r.raise_for_status()
        return r.json()


_client = {}

def get_connection():
    return _client

def table(name: str) -> SupabaseTable:
    return SupabaseTable(name)


def init_db():
    """Verify Supabase connection and ensure tables exist.
    Tables must be created via Supabase dashboard SQL editor first.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[DB] SUPABASE_URL ou SUPABASE_KEY não configurados no .env")
        return False

    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/posts?select=id&limit=1",
            headers=HEADERS, timeout=10,
        )
        if r.status_code == 200:
            print("[DB] Conectado ao Supabase OK")
            return True
        else:
            print(f"[DB] Erro ao conectar: {r.status_code} {r.text[:100]}")
            return False
    except Exception as e:
        safe = str(e).encode('ascii', errors='replace').decode()
        print(f"[DB] Falha ao conectar: {safe}")
        return False
