import re
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from dateutil import parser as dateparser

BRASIL_TZ = timezone(timedelta(hours=-3))

_DAY_MAP = {
    "segunda": 0, "segunda-feira": 0, "segundou": 0,
    "terça": 1, "terca": 1, "terça-feira": 1, "terca-feira": 1,
    "quarta": 2, "quarta-feira": 2,
    "quinta": 3, "quinta-feira": 3,
    "sexta": 4, "sexta-feira": 4, "sextou": 4,
    "sábado": 5, "sabado": 5,
    "domingo": 6,
}

_MONTH_MAP = {
    "janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3,
    "abril": 4, "maio": 5, "junho": 6, "julho": 7,
    "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
}


def parse_datetime(text: str) -> Optional[datetime]:
    """Parse Portuguese date/time expressions into a datetime."""
    now = datetime.now(BRASIL_TZ)
    lower = text.lower().strip()

    # "agora" = now
    if "agora" in lower or "já" in lower or "ja" in lower:
        return now

    # "daqui X min/minutos/minutinhos"
    m = re.search(r"daqui\s+(\d+)\s*(min|minuto|minutos|minutinhos)", lower)
    if m:
        return now + timedelta(minutes=int(m.group(1)))

    # "daqui X hora/horas"
    m = re.search(r"daqui\s+(\d+)\s*(hora|horas)", lower)
    if m:
        return now + timedelta(hours=int(m.group(1)))

    # "daqui X dia/dias"
    m = re.search(r"daqui\s+(\d+)\s*(dia|dias)", lower)
    if m:
        return now + timedelta(days=int(m.group(1)))

    # "em X min/minutos"
    m = re.search(r"em\s+(\d+)\s*(min|minuto|minutos)", lower)
    if m:
        return now + timedelta(minutes=int(m.group(1)))

    # "hoje às HH:MM" or "hoje as HH:MM"
    m = re.search(r"hoje\s+(à|as|as)\s*(\d{1,2})[h:.](\d{2})", lower)
    if m:
        hour, minute = int(m.group(2)), int(m.group(3))
        dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if dt < now:
            dt += timedelta(days=1)
        return dt

    # "hoje às HH" or "hoje as HH"
    m = re.search(r"hoje\s+(à|as|as)\s*(\d{1,2})\s*(h|horas)?", lower)
    if m:
        hour = _infer_hour_from_period(text, int(m.group(2)))
        dt = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if dt < now:
            dt += timedelta(days=1)
        return dt

    # "amanhã às HH:MM" or "amanhã as HH:MM"
    m = re.search(r"amanh[ãa]s?\s+(à|as|as)\s*(\d{1,2})[h:.](\d{2})", lower)
    if m:
        hour, minute = int(m.group(2)), int(m.group(3))
        dt = (now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
        return dt

    # "amanhã às HH" or "amanhã as HH"
    m = re.search(r"amanh[ãa]s?\s+(à|as|as)\s*(\d{1,2})\s*(h|horas)?", lower)
    if m:
        hour = _infer_hour_from_period(text, int(m.group(2)))
        dt = (now + timedelta(days=1)).replace(hour=hour, minute=0, second=0, microsecond=0)
        return dt

    # "depois de amanhã às HH:MM"
    m = re.search(r"depois\s+de\s+amanh[ãa]s?\s+(à|as|as)\s*(\d{1,2})[h:.](\d{2})", lower)
    if m:
        hour, minute = int(m.group(2)), int(m.group(3))
        dt = (now + timedelta(days=2)).replace(hour=hour, minute=minute, second=0, microsecond=0)
        return dt

    # "sexta às HH:MM" / "segunda às HH" etc
    for name, idx in _DAY_MAP.items():
        m = re.search(rf"{name}\s+(à|as|as)\s*(\d{{1,2}})[h:.](\d{{2}})", lower)
        if m:
            hour, minute = int(m.group(2)), int(m.group(3))
            days_ahead = idx - now.weekday()
            if days_ahead <= 0 or (days_ahead == 0 and now.hour >= hour):
                days_ahead += 7
            dt = (now + timedelta(days=days_ahead)).replace(hour=hour, minute=minute, second=0, microsecond=0)
            return dt
        m = re.search(rf"{name}\s+(à|as|as)\s*(\d{{1,2}})\s*(h|horas)?", lower)
        if m:
            hour = _infer_hour_from_period(text, int(m.group(2)))
            days_ahead = idx - now.weekday()
            if days_ahead <= 0 or (days_ahead == 0 and now.hour >= hour):
                days_ahead += 7
            dt = (now + timedelta(days=days_ahead)).replace(hour=hour, minute=0, second=0, microsecond=0)
            return dt

    # "sexta" (no time) → sexta 10h (default)
    for name, idx in _DAY_MAP.items():
        if re.search(rf"\b{name}\b", lower):
            days_ahead = idx - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            dt = (now + timedelta(days=days_ahead)).replace(hour=10, minute=0, second=0, microsecond=0)
            return dt

    # "HH:MM" alone (no day)
    m = re.search(r"(\d{1,2})[h:.](\d{2})", lower)
    if m:
        hour, minute = int(m.group(1)), int(m.group(2))
        dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if dt < now:
            dt += timedelta(days=1)
        return dt

    # Try generic dateutil parser as last resort
    try:
        dt = dateparser.parse(lower, fuzzy=True, default=now)
        if dt:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=BRASIL_TZ)
            return dt
    except Exception:
        pass

    return None


def parse_price(text: str) -> Optional[float]:
    """Extract price from text."""
    m = re.search(r'(?:pre[cç]o|r\$\s*)?(\d+[.,]\d{2})', text.lower())
    if m:
        return float(m.group(1).replace(',', '.'))
    m = re.search(r'(\d+[.,]\d{2})', text.lower())
    if m:
        return float(m.group(1).replace(',', '.'))
    return None


def parse_sizes(text: str) -> Optional[str]:
    """Extract sizes from text."""
    m = re.search(r'(?:tamanhos?|tam\s*[:.]?\s*)([pPmMgGuU\d,\s/]+)', text)
    if m:
        raw = m.group(1).strip().upper().replace('/', ',')
        raw = re.sub(r'\s+', '', raw)
        return raw
    return None


def _infer_hour_from_period(text: str, current_hour: int) -> int:
    """Adjust hour based on period words like 'da tarde', 'da noite'."""
    lower = text.lower()
    if ("da tarde" in lower or "da noite" in lower) and current_hour < 12:
        return current_hour + 12
    return current_hour


def parse_target(text: str, photo_descriptions: List[str]) -> Optional[int]:
    """Identify which photo index the user is referring to."""
    lower = text.lower()

    # Direct index: "foto 1", "foto 2", "a 1", "a 2", "a primeira", "a segunda"
    m = re.search(r'(?:foto|a|o|da)\s*(\d+)', lower)
    if m:
        idx = int(m.group(1)) - 1
        if 0 <= idx < len(photo_descriptions):
            return idx

    ordinal_map = {
        "primeira": 0, "primeiro": 0, "segunda": 1, "segundo": 1,
        "terceira": 2, "terceiro": 2, "quarta": 3, "quarto": 3,
        "quinta": 4, "quinto": 4,
    }
    for word, idx in ordinal_map.items():
        if word in lower:
            if 0 <= idx < len(photo_descriptions):
                return idx

    # "todas" or "tudo" or "todas as fotos"
    if any(w in lower for w in ["todas", "tudo", "todas as", "todas as fotos", "todas fotos"]):
        return -999  # special: all

    return None


def parse_action(text: str) -> str:
    """Determine the action the user wants."""
    lower = text.lower()
    if any(w in lower for w in ["publica", "publicar", "postar", "agenda", "agendar", "marcar"]):
        return "agendar"
    if any(w in lower for w in ["edita", "editar", "muda", "mudar", "alterar"]):
        return "editar"
    if any(w in lower for w in ["gerar", "criar", "faz", "produzir"]):
        return "gerar"
    if any(w in lower for w in ["cancela", "cancelar", "excluir", "apaga", "apagar", "remove"]):
        return "cancelar"
    return "gerar"


def parse_caption_suggestion(text: str, existing_caption: str = "") -> Optional[str]:
    """Extract a caption snippet the user might have typed."""
    lower = text.lower()
    # Remove date/time/price/sizes/action words, keep the rest as caption
    tokens = re.sub(
        r'(publica|agenda|edita|muda|cria|daqui|amanh[aã]|hoje|sexta|segunda|ter[cç]a|quarta|quinta|s[aá]bado|domingo|'
        r'pre[cç]o|tamanho|r\$|foto|\d+[h:]\d+|\d+,\d{2})',
        '', lower, flags=re.IGNORECASE
    ).strip()
    if len(tokens) > 10 and tokens != existing_caption:
        return tokens[:200]
    return None


def parse_command(text: str, photo_descriptions: List[str]) -> Dict[str, Any]:
    """Parse a natural language command into structured action."""
    text = text.strip().strip('"').strip("'")
    action = parse_action(text)
    target_index = parse_target(text, photo_descriptions)
    target_str = f"foto {target_index + 1}" if target_index is not None and target_index >= 0 else "todas" if target_index == -999 else None
    dt = parse_datetime(text)
    price = parse_price(text)
    sizes = parse_sizes(text)
    return {
        "action": action,
        "target_index": target_index,
        "target_str": target_str,
        "datetime": dt.isoformat() if dt else None,
        "price": price,
        "sizes": sizes,
    }
