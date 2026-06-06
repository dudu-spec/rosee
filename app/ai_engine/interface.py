"""
AI Engine — Real model inference via Ollama API + Qwen.

Architecture:
  1. Primary: Moondream + Llama 3.2 via Ollama API — always works (fast, low RAM)
  2. Fallback: Qwen2.5-VL-3B (CPU bfloat16) — if ≥10GB RAM + torch available
  3. Last resort: mock — no model needed

The engine auto-selects the best available backend.
"""

import base64
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import requests

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
VISION_MODEL = "moondream:latest"
TEXT_MODEL = "llama3.2:latest"
QWEN_MODEL_PATH = str(
    Path.home() / ".cache" / "huggingface" / "hub" /
    "models--Qwen--Qwen2.5-VL-3B-Instruct" / "snapshots" /
    "66285546d2b821cf421d4f5eb2576359d3770cd3"
)
OPENROUTER_BASE = "https://openrouter.ai/api/v1"

# ── Interface types ──

@dataclass
class ImageAnalysis:
    description: str = ""
    garment_type: str = ""
    primary_color: str = ""
    secondary_colors: List[str] = field(default_factory=list)
    pattern: str = ""
    style: str = ""
    features: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "description": self.description,
            "garment_type": self.garment_type,
            "primary_color": self.primary_color,
            "secondary_colors": self.secondary_colors,
            "pattern": self.pattern,
            "style": self.style,
            "features": self.features,
        }


@dataclass
class GeneratedContent:
    caption: str = ""
    cta: str = ""
    hashtags: List[str] = field(default_factory=list)
    category: str = ""

    def to_dict(self) -> dict:
        return {
            "caption": self.caption,
            "cta": self.cta,
            "hashtags": self.hashtags,
            "category": self.category,
        }


# ── Backend detection ──

_MODEL_BACKEND = None
_IS_VERCEL = os.environ.get("VERCEL", "").lower() == "1"


def _openrouter_key() -> str | None:
    """Busca a API key do OpenRouter no Supabase settings."""
    from app.backend.services.post_service import get_settings
    key = get_settings().get("openrouter_key", "")
    return key.strip() or None


def _detect_backend():
    global _MODEL_BACKEND
    if _MODEL_BACKEND:
        return _MODEL_BACKEND

    # Vercel: sem Ollama nem Qwen, vai direto pro OpenRouter
    if _IS_VERCEL:
        if _openrouter_key():
            _MODEL_BACKEND = "openrouter"
        else:
            _MODEL_BACKEND = None
        return _MODEL_BACKEND

    # Priority 1: Ollama
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            if any("moondream" in m or "llava" in m for m in models):
                _MODEL_BACKEND = "ollama"
                return _MODEL_BACKEND
    except Exception:
        pass

    # Priority 2: Qwen via transformers (only if enough RAM)
    try:
        import torch
        import psutil
        if os.path.exists(QWEN_MODEL_PATH) and psutil.virtual_memory().total >= 10 * 1024**3:
            _MODEL_BACKEND = "qwen"
            return _MODEL_BACKEND
    except ImportError:
        pass

    # Priority 3: OpenRouter (se tiver API key configurada)
    if _openrouter_key():
        _MODEL_BACKEND = "openrouter"
        return _MODEL_BACKEND

    _MODEL_BACKEND = None
    return _MODEL_BACKEND

    # Fallback: mock
    _MODEL_BACKEND = "mock"
    return _MODEL_BACKEND


# ── Ollama helpers ──


def _ollama_vision(prompt: str, image_path: str, model: str = VISION_MODEL) -> str:
    """Send image + prompt to vision model via Ollama."""
    import base64
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
                "images": [b64],
            }
        ],
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 256},
        "keep_alive": "0s",
    }

    resp = requests.post(f"{OLLAMA_HOST}/api/chat", json=payload, timeout=600)
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def _ollama_text(prompt: str, model: str = TEXT_MODEL,
                 temperature: float = 0.5) -> str:
    """Send text-only prompt to text model via Ollama."""
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": temperature, "num_predict": 256},
        "keep_alive": "0s",
    }
    resp = requests.post(f"{OLLAMA_HOST}/api/chat", json=payload, timeout=300)
    resp.raise_for_status()
    return resp.json()["message"]["content"]


# ── Qwen 4-bit backend ──

_QWEN_MODEL = None
_QWEN_PROC = None


def _qwen_load():
    global _QWEN_MODEL, _QWEN_PROC
    if _QWEN_MODEL is not None:
        return _QWEN_MODEL, _QWEN_PROC

    import torch
    from transformers import (
        Qwen2_5_VLForConditionalGeneration,
        AutoProcessor,
    )

    print("[AI Engine] Loading Qwen2.5-VL-3B on CPU...")
    _QWEN_PROC = AutoProcessor.from_pretrained(QWEN_MODEL_PATH, trust_remote_code=True)

    # Try 4-bit if CUDA available, else CPU bfloat16
    try:
        from transformers import BitsAndBytesConfig
        if torch.cuda.is_available():
            bnb = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
            )
            _QWEN_MODEL = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                QWEN_MODEL_PATH, quantization_config=bnb,
                device_map="auto", torch_dtype=torch.bfloat16,
                trust_remote_code=True,
            )
            print("[AI Engine] Qwen loaded in 4-bit (CUDA).")
            return _QWEN_MODEL, _QWEN_PROC
    except Exception:
        pass

    _QWEN_MODEL = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        QWEN_MODEL_PATH, device_map="cpu",
        torch_dtype=torch.bfloat16,
        trust_remote_code=True, low_cpu_mem_usage=True,
    )
    print("[AI Engine] Qwen loaded on CPU (bfloat16).")
    return _QWEN_MODEL, _QWEN_PROC


def _qwen_infer(image_path: str, instruction: str) -> str:
    """Run inference with Qwen2.5-VL on CPU."""
    import torch
    from PIL import Image as PILImage

    model, proc = _qwen_load()
    img = PILImage.open(image_path).convert("RGB")

    conv = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": img},
                {"type": "text", "text": instruction},
            ],
        }
    ]

    text = proc.apply_chat_template(conv, tokenize=False, add_generation_prompt=True)
    inputs = proc(text=[text], images=[img], padding=True, return_tensors="pt").to(model.device)

    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.6,
            top_p=0.9,
            do_sample=True,
        )

    return proc.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()


# ── OpenRouter ──

_OPENROUTER_TIMEOUT = int(os.environ.get("OPENROUTER_TIMEOUT", "8"))
_LAST_OR_ERROR = None


def _openrouter_vision(instruction: str, image_path: str) -> str:
    """Envia imagem para modelo de visão via OpenRouter."""
    global _LAST_OR_ERROR
    api_key = _openrouter_key()
    if not api_key:
        _LAST_OR_ERROR = "OpenRouter: chave API não encontrada nas configurações"
        raise ValueError(_LAST_OR_ERROR)

    from PIL import Image as PILImage
    import io

    try:
        img = PILImage.open(image_path).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        _LAST_OR_ERROR = f"OpenRouter: erro ao processar imagem localmente: {e}"
        raise

    payload = {
        "model": os.environ.get("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free"),
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": instruction},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                ],
            }
        ],
        "max_tokens": 512,
        "temperature": 0.6,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/rosee-bot",
        "X-Title": "Rosee Instagram Automation",
    }

    try:
        r = requests.post(
            f"{OPENROUTER_BASE}/chat/completions",
            json=payload, headers=headers,
            timeout=_OPENROUTER_TIMEOUT,
        )
        r.raise_for_status()
        _LAST_OR_ERROR = None
        return r.json()["choices"][0]["message"]["content"].strip()
    except requests.Timeout:
        _LAST_OR_ERROR = (
            f"OpenRouter: servidor não respondeu em {_OPENROUTER_TIMEOUT}s. "
            "Pode ser lentidão da rede ou do modelo gratuito (Gemini Flash). "
            "Tente novamente ou aumente OPENROUTER_TIMEOUT."
        )
        raise
    except requests.HTTPError as e:
        status = r.status_code
        if status == 401:
            _LAST_OR_ERROR = "OpenRouter: chave API inválida. Vá em Configurações > IA e atualize a chave."
        elif status == 402:
            _LAST_OR_ERROR = "OpenRouter: saldo insuficiente. O modelo gratuito pode ter expirado."
        elif status == 429:
            _LAST_OR_ERROR = "OpenRouter: muitos pedidos em pouco tempo. Aguarde alguns segundos e tente novamente."
        else:
            _LAST_OR_ERROR = f"OpenRouter: erro HTTP {status} — {r.text[:200]}"
        raise
    except requests.ConnectionError:
        _LAST_OR_ERROR = (
            "OpenRouter: sem conexão com a internet. "
            "Verifique se o WiFi está funcionando."
        )
        raise
    except Exception as e:
        _LAST_OR_ERROR = f"OpenRouter: erro inesperado — {e}"
        raise


def _ultimo_erro_openrouter() -> str | None:
    """Retorna o último erro do OpenRouter para exibir na UI."""
    return _LAST_OR_ERROR


# ── Public API ──

def analyze_image(image_path: str) -> ImageAnalysis:
    """
    Analyze a fashion image using the best available backend.
    Returns structured analysis: description, garment type, color, style.
    """
    backend = _detect_backend()
    ext = os.path.splitext(image_path)[1].lower()
    is_video = ext in (".mp4", ".mov")

    if is_video:
        return ImageAnalysis(
            description="Vídeo de moda feminina.",
            garment_type="peça de vestuário",
            primary_color="não identificada",
            style="não identificado",
        )

    if not os.path.exists(image_path):
        return ImageAnalysis(description="Imagem não encontrada.")

    prompt = (
        "Você é um assistente de moda especializado em roupas femininas. "
        "Descreva esta imagem de forma objetiva e detalhada.\n\n"
        "Identifique:\n"
        "- Tipo da peça (vestido, blusa, calça, saia, conjunto, etc.)\n"
        "- Cor predominante e cores secundárias\n"
        "- Estampa ou textura (liso, floral, listrado, etc.)\n"
        "- Estilo (casual, formal, festa, praia, fitness)\n"
        "- Características notáveis (manga curta/longa, decote, comprimento, tecido)\n\n"
        "Responda APENAS em português brasileiro.\n"
        "NÃO invente preços, promoções ou tamanhos."
    )

    # Tenta backend escolhido
    try:
        if backend == "openrouter":
            raw = _openrouter_vision(prompt, image_path)
        elif backend == "qwen":
            raw = _qwen_infer(image_path, prompt)
        elif backend == "ollama":
            raw = _ollama_vision(prompt, image_path)
        else:
            raw = None

        if raw:
            return _parse_analysis(raw)
    except Exception as e:
        print(f"[AI Engine] analyze_image error: {e}")

    # Fallback: análise via Pillow (sem ML, sem RAM extra)
    fallback_desc = _analisar_imagem_pillow(image_path)
    return fallback_desc


def _parse_analysis(raw: str) -> ImageAnalysis:
    """Parse LLM output into structured ImageAnalysis."""
    raw_lower = raw.lower()

    # Garment type — Portuguese + English
    garment_map = {
        "vestido": "vestido", "dress": "vestido",
        "blusa": "blusa", "blouse": "blusa", "camisa": "camisa", "shirt": "camisa",
        "calça": "calça", "calca": "calça", "pants": "calça", "trousers": "calça",
        "saia": "saia", "skirt": "saia",
        "short": "short", "shorts": "short",
        "jaqueta": "jaqueta", "jacket": "jaqueta", "casaco": "casaco", "coat": "casaco",
        "macacão": "macacão", "macacao": "macacão", "jumpsuit": "macacão",
        "conjunto": "conjunto", "set": "conjunto",
        "blazer": "blazer", "cropped": "cropped", "cropped top": "cropped",
        "body": "body", "regata": "regata", "tank top": "regata",
        "moletom": "moletom", "sweatshirt": "moletom",
        "vestido longo": "vestido longo", "long dress": "vestido longo",
        "vestido curto": "vestido curto", "short dress": "vestido curto",
        "top": "blusa", "camiseta": "camisa", "t-shirt": "camisa",
    }
    garment = "peça de vestuário"
    for keyword, value in garment_map.items():
        if keyword in raw_lower:
            garment = value
            break

    # Color extraction — Portuguese + English
    colors = [
        "preto", "black", "branco", "white", "vermelho", "red",
        "azul", "blue", "verde", "green", "amarelo", "yellow",
        "rosa", "pink", "roxo", "purple", "laranja", "orange",
        "marrom", "brown", "cinza", "gray", "grey", "bege", "beige",
        "creme", "cream", "vinho", "wine", "marinho", "navy",
        "camuflado", "camo", "estampado", "printed",
        "floral", "listrado", "striped", "xadrez", "plaid",
        "poá", "polka",
    ]
    found_colors = [c for c in colors if c in raw_lower]
    primary = found_colors[0] if found_colors else "não identificada"
    secondary = found_colors[1:] if len(found_colors) > 1 else []

    # Pattern
    pattern = "liso"
    for p in ["floral", "listrado", "striped", "xadrez", "plaid", "estampado", "printed",
              "poá", "polka", "camuflado", "camo", "geometrico", "geometric"]:
        if p in raw_lower:
            pattern = p
            break
    if pattern == "striped": pattern = "listrado"
    if pattern == "plaid": pattern = "xadrez"
    if pattern == "printed": pattern = "estampado"
    if pattern == "polka": pattern = "poá"
    if pattern == "camo": pattern = "camuflado"
    if pattern == "geometric": pattern = "geometrico"

    # Style
    style = "casual"
    for s in ["formal", "festa", "party", "praia", "beach", "fitness", "esporte", "sport",
              "elegante", "elegant", "romantico", "romântico", "romantic", "vintage", "moderno",
              "modern", "esportivo", "social", "sofisticado", "sophisticated"]:
        if s in raw_lower:
            style = s
            break
    if style == "party": style = "festa"
    if style == "beach": style = "praia"
    if style == "sport": style = "esportivo"
    if style == "elegant": style = "elegante"
    if style == "romantic": style = "romântico"
    if style == "modern": style = "moderno"
    if style == "sophisticated": style = "sofisticado"

    # Features — Portuguese + English
    features = []
    feature_map = {
        "manga curta": "manga curta", "short sleeve": "manga curta",
        "manga longa": "manga longa", "long sleeve": "manga longa",
        "decote": "decote", "neckline": "decote",
        "gola": "gola", "collar": "gola",
        "bolso": "bolso", "pocket": "bolso",
        "cinto": "cinto", "belt": "cinto",
        "renda": "renda", "lace": "renda",
        "bordado": "bordado", "embroidery": "bordado",
        "brilho": "brilho", "shine": "brilho",
        "transparente": "transparente", "sheer": "transparente",
        "leve": "leve", "lightweight": "leve",
        "fluido": "fluido", "flowy": "fluido",
        "justo": "justo", "tight": "justo",
        "solto": "solto", "loose": "solto",
        "comprimento midi": "comprimento midi", "midi length": "comprimento midi",
        "comprimento longo": "comprimento longo", "long length": "comprimento longo",
        "comprimento curto": "comprimento curto", "short length": "comprimento curto",
    }
    for keyword, label in feature_map.items():
        if keyword in raw_lower:
            features.append(label)

    return ImageAnalysis(
        description=raw[:300],
        garment_type=garment,
        primary_color=primary,
        secondary_colors=secondary,
        pattern=pattern,
        style=style,
        features=features,
    )


def generate_caption(description: str, user_input: str,
                     price: Optional[float] = None,
                     sizes: str = "") -> GeneratedContent:
    """Generate complete Instagram caption from image description."""
    try:
        return _generate_with_ollama(description, user_input, price, sizes)
    except Exception as e:
        print(f"[AI Engine] generate_caption error: {e}")
        return _generate_manual(description, user_input, price, sizes)


def _generate_with_ollama(description: str, user_input: str,
                          price: Optional[float], sizes: str) -> GeneratedContent:
    """Use text model via Ollama to generate content."""
    price_str = f"R$ {price:.2f}".replace('.', ',') if price else "não informado"
    sizes_str = sizes if sizes else "não informado"

    # Settings from Supabase
    store_name = "Minha Loja"
    brand_voice = "amigavel"
    try:
        import os
        from pathlib import Path
        from dotenv import load_dotenv
        dotenv_path = Path(__file__).resolve().parent.parent.parent / ".env"
        if dotenv_path.exists():
            load_dotenv(str(dotenv_path))
        supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("SUPABASE_ANON_KEY", "")
        if supabase_url and supabase_key:
            r = requests.get(
                f"{supabase_url}/rest/v1/settings?select=key,value",
                headers={
                    "apikey": supabase_key,
                    "Authorization": f"Bearer {supabase_key}",
                    "Content-Type": "application/json",
                },
                timeout=10,
            )
            if r.status_code == 200:
                for row in r.json():
                    if row["key"] == "store_name": store_name = row["value"]
                    if row["key"] == "brand_voice": brand_voice = row["value"]
    except Exception:
        pass

    # Prompt for caption
    prompt = (
        f"Você é redator(a) da loja de roupas {store_name}.\n"
        f"Tom de voz: {brand_voice}.\n\n"
        "Com base nos dados abaixo, crie uma legenda para Instagram.\n"
        "Máximo 180 palavras. Use emojis com moderação.\n"
        "Escreva TUDO em português brasileiro.\n\n"
        f"DESCRIÇÃO DA IMAGEM:\n{description}\n\n"
        f"O QUE A DONA ESCREVEU:\n{user_input}\n\n"
        f"PREÇO: {price_str}\n"
        f"TAMANHOS: {sizes_str}\n\n"
        "REGRAS:\n"
        "- NÃO invente promoções, descontos ou liquidações\n"
        "- NÃO invente preços diferentes do informado\n"
        "- NÃO invente tamanhos que não foram informados\n"
        "- Se preço ou tamanhos não foram informados, não mencione\n"
        "- LEGENDA DEVE SER EM PORTUGUÊS BRASILEIRO\n\n"
        "Responda EXATAMENTE neste formato JSON:\n"
        f"{{\n"
        '  "legenda": "texto da legenda aqui",\n'
        '  "cta": "chamada para ação",\n'
        '  "hashtags": ["#tag1", "#tag2", ...],\n'
        '  "categoria": "look"\n'
        f"}}"
    )

    raw = _ollama_text(prompt, temperature=0.6)

    # Try to parse JSON from response
    import re
    json_match = re.search(r'\{.*"legenda".*"categoria".*\}', raw, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            return GeneratedContent(
                caption=data.get("legenda", ""),
                cta=data.get("cta", ""),
                hashtags=data.get("hashtags", []),
                category=data.get("categoria", "look"),
            )
        except json.JSONDecodeError:
            pass

    # Fallback: parse manually
    return _generate_manual(description, user_input, price, sizes)


def _analisar_imagem_pillow(image_path: str) -> ImageAnalysis:
    """Extrai informações visuais da imagem usando apenas Pillow (sem ML)."""
    from PIL import Image, ImageFilter, ImageStat
    import math

    img = Image.open(image_path).convert("RGB")
    w, h = img.size

    # ── Cor dominante (sample reduzido) ──
    pequeno = img.resize((32, 32), Image.LANCZOS)
    pixels = list(pequeno.getdata())
    total = len(pixels)

    # Quantização simples: agrupa cores em bins de 64
    bins: dict[tuple[int, int, int], int] = {}
    for r, g, b in pixels:
        chave = (r // 64 * 64, g // 64 * 64, b // 64 * 64)
        bins[chave] = bins.get(chave, 0) + 1

    top3 = sorted(bins.items(), key=lambda x: -x[1])[:3]
    pesos = [c / total for _, c in top3]

    def rgb_para_nome(r: int, g: int, b: int) -> str:
        """Mapeia RGB para nome de cor em português."""
        from math import sqrt

        paleta: list[tuple[int, int, int, str]] = [
            (0, 0, 0, "preto"),
            (255, 255, 255, "branco"),
            (255, 0, 0, "vermelho"),
            (200, 0, 0, "vinho"),
            (255, 100, 100, "rosa"),
            (255, 150, 200, "rosa claro"),
            (255, 0, 255, "rosa"),
            (255, 100, 0, "laranja"),
            (255, 200, 0, "amarelo"),
            (200, 200, 0, "mostarda"),
            (0, 255, 0, "verde"),
            (0, 150, 0, "verde escuro"),
            (100, 200, 100, "verde claro"),
            (0, 200, 200, "verde água"),
            (0, 100, 255, "azul"),
            (0, 0, 200, "azul escuro"),
            (100, 150, 255, "azul claro"),
            (200, 0, 200, "roxo"),
            (150, 100, 200, "lilás"),
            (150, 100, 50, "marrom"),
            (200, 180, 150, "bege"),
            (128, 128, 128, "cinza"),
            (200, 200, 200, "cinza claro"),
            (100, 100, 100, "cinza escuro"),
            (200, 180, 50, "dourado"),
            (180, 180, 190, "prateado"),
        ]

        melhor_dist = float("inf")
        melhor_nome = "não identificada"
        for pr, pg, pb, nome in paleta:
            d = sqrt((r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2)
            if d < melhor_dist:
                melhor_dist = d
                melhor_nome = nome
        return melhor_nome

    cor_dominante = rgb_para_nome(*top3[0][0])
    cores_secundarias = []
    for (cr, cg, cb), _ in top3[1:]:
        nome = rgb_para_nome(cr, cg, cb)
        if nome not in (cor_dominante,) + tuple(cores_secundarias):
            cores_secundarias.append(nome)

    # ── Brilho médio ──
    stat = ImageStat.Stat(img.convert("L"))
    brilho_medio = stat.mean[0]
    if brilho_medio < 80:
        tom = "escuro"
    elif brilho_medio > 180:
        tom = "claro"
    else:
        tom = "médio"

    # ── Saturação média ──
    hsv_img = img.convert("HSV")
    hsv_stat = ImageStat.Stat(hsv_img)
    saturacao_media = hsv_stat.mean[1]
    if saturacao_media < 30:
        saturacao = "neutro/apagado"
    elif saturacao_media > 150:
        saturacao = "vibrante"
    else:
        saturacao = "moderado"

    # ── Textura: variância local via desvio padrão ──
    stat_l = ImageStat.Stat(img.convert("L"))
    try:
        desvio = stat_l.stddev[0]
    except Exception:
        desvio = 0
    if desvio < 40:
        textura = "lisa/sem estampa"
    elif desvio < 70:
        textura = "estampa sutil"
    else:
        textura = "estampa marcante"

    # ── Detecção de listras via bordas horizontais/verticais ──
    gray = img.convert("L")
    try:
        kernel_h = ImageFilter.Kernel((3, 3), (
            -1, -1, -1,
            2,  2,  2,
            -1, -1, -1,
        ), scale=3)
        kernel_v = ImageFilter.Kernel((3, 3), (
            -1, 2, -1,
            -1, 2, -1,
            -1, 2, -1,
        ), scale=3)
        bordas_h = gray.filter(kernel_h)
        bordas_v = gray.filter(kernel_v)
        stat_h = ImageStat.Stat(bordas_h)
        stat_v = ImageStat.Stat(bordas_v)
        media_h = stat_h.mean[0] if stat_h.mean else 0
        media_v = stat_v.mean[0] if stat_v.mean else 0
        razao = (media_v + 1) / (media_h + 1)
        if razao > 2:
            textura = "listrado horizontal"
        elif razao < 0.5:
            textura = "listrado vertical"
    except Exception:
        pass

    # ── Detalhamento: densidade de bordas (Filtro Laplaciano) ──
    try:
        lap = gray.filter(ImageFilter.Kernel((3, 3), (
            -1, -1, -1,
            -1,  8, -1,
            -1, -1, -1,
        ), scale=1))
        stat_lap = ImageStat.Stat(lap)
        bordas = stat_lap.mean[0]
        if bordas > 60:
            detalhe = "muitos detalhes" if bordas > 100 else "detalhes moderados"
        else:
            detalhe = "poucos detalhes"
    except Exception:
        detalhe = "detalhe não analisado"

    # ── Construir descrição ──
    desc = f"Peça de roupa na cor {cor_dominante}"
    if cores_secundarias:
        desc += f" com detalhes em {', '.join(cores_secundarias)}"
    desc += f". Tom {tom}, saturação {saturacao}, textura {textura}."
    desc += " " + detalhe.capitalize() + "."

    # ── Inferir estilo básico ──
    if "listrado" in textura:
        estilo_inferido = "casual"
    elif cor_dominante in ("preto", "branco", "cinza") and saturacao == "neutro/apagado":
        estilo_inferido = "formal"
    elif cor_dominante in ("rosa", "vermelho", "lilás", "roxo"):
        estilo_inferido = "feminino"
    elif saturacao == "vibrante":
        estilo_inferido = "despojado"
    else:
        estilo_inferido = "casual"

    return ImageAnalysis(
        description=desc,
        garment_type="peça de vestuário",
        primary_color=cor_dominante,
        style=estilo_inferido,
    )



def _generate_manual(description: str, user_input: str,
                     price: Optional[float], sizes: str) -> GeneratedContent:
    """Manual generation when AI fails."""
    if user_input:
        caption = f"{user_input.capitalize()} 💕\n\n"
    else:
        caption = "Novidade que chegou na loja! ✨\n\n"
        caption += f"{description[:200]}\n\n"

    if price:
        caption += f"💰 R$ {price:.2f}\n".replace('.', ',')
    if sizes:
        caption += f"📏 Tam: {sizes}\n"

    cta = "Garanta já o seu no link da bio! 🛍️"
    hashtags = [
        "#modafeminina", "#lookdodia", "#instafashion",
        "#roupafeminina", "#estilofeminino",
    ]
    category = "look"

    return GeneratedContent(
        caption=caption.strip(),
        cta=cta,
        hashtags=hashtags,
        category=category,
    )


def generate_cta(caption: str, category: str) -> str:
    """Generate call-to-action."""
    try:
        prompt = (
            "Com base na legenda e categoria abaixo, gere uma chamada "
            "para ação (CTA) curta e direta para Instagram.\n"
            "Máximo 20 palavras. Única frase.\n"
            "Escreva em português brasileiro.\n\n"
            f"LEGENDA: {caption[:200]}\n"
            f"CATEGORIA: {category}\n\n"
            "Responda APENAS com o CTA, sem aspas."
        )
        cta = _ollama_text(prompt, temperature=0.4)
        return cta.strip().strip('"').strip("'")
    except Exception:
        ctas = {
            "look": "Garanta já o seu no link da bio! 🛍️",
            "dica": "Salve esse post para consultar depois! 📌",
            "lifestyle": "Compartilhe com aquela amiga! 💫",
            "social": "Já usou algo da loja? Marca a gente! 📸",
            "novidade": "Não perca no link da bio! 🔥",
        }
        return ctas.get(category, "Visite a loja no link da bio! ✨")


def generate_hashtags(description: str, category: str, caption: str) -> List[str]:
    """Generate relevant hashtags."""
    try:
        prompt = (
            "Gere 10 hashtags em português brasileiro para postagem "
            "de moda feminina.\n\n"
            f"DESCRIÇÃO: {description[:150]}\n"
            f"CATEGORIA: {category}\n\n"
            "Responda APENAS com as hashtags, uma por linha, "
            "todas começando com #."
        )
        raw = _ollama_text(prompt, temperature=0.3)
        tags = [t.strip() for t in raw.split("\n") if t.strip().startswith("#")]
        return tags[:15]
    except Exception:
        base = ["#modafeminina", "#lookdodia", "#instafashion",
                "#modabrasileira", "#roupafeminina"]
        extras = {
            "look": ["#outfit", "#produção", "#look"],
            "dica": ["#dicademoda", "#estilo", "#moda"],
            "lifestyle": ["#lifestyle", "#inspiração", "#fashion"],
            "social": ["#cliente", "#provasocial", "#resenha"],
            "novidade": ["#lançamento", "#novidade", "#coleção"],
        }
        return base + extras.get(category, [])


def classify_post(description: str, caption: str) -> str:
    """Classify post into editorial category."""
    try:
        prompt = (
            "Classifique esta postagem em UMA destas categorias:\n"
            "- look: foto de produto/roupa\n"
            "- dica: conteúdo educativo\n"
            "- lifestyle: inspiração, estilo de vida\n"
            "- social: prova social, cliente\n"
            "- novidade: lançamento, data especial\n\n"
            f"DESCRIÇÃO: {description[:200]}\n"
            f"LEGENDA: {caption[:200]}\n\n"
            "Responda APENAS com uma palavra em português: look, dica, lifestyle, social, novidade"
        )
        raw = _ollama_text(prompt, temperature=0.2).strip().lower()
        for c in ["look", "dica", "lifestyle", "social", "novidade"]:
            if c in raw:
                return c
        return "look"
    except Exception:
        return "look"