import re
from datetime import datetime, timezone, timedelta
from typing import List, Tuple

BRASIL_TZ = timezone(timedelta(hours=-3))

FORBIDDEN_PATTERNS = [
    (r'\d{1,3}\s*%\s*(de\s*)?desconto', 'promoção com desconto percentual'),
    (r'promo[cç][aã]o', 'palavra promoção'),
    (r'liquida[cç][aã]o', 'palavra liquidação'),
    (r'black\s*friday', 'black friday'),
    (r'(últimas|ultimas)\s*unidades', 'urgência de estoque'),
    (r'(acaba|termina)\s*hoje', 'urgência de tempo'),
    (r'super\s*desconto', 'super desconto'),
    (r'oferta\s*relâmpago', 'oferta relâmpago'),
    (r'frete\s*gr[aá]tis', 'frete grátis não confirmado'),
    (r'sorteio', 'menção a sorteio'),
    (r'ganhe\s*brinde', 'menção a brinde não confirmado'),
]

MAX_HASHTAGS = 30
MAX_CAPTION_LENGTH = 2200
MAX_SCHEDULE_DAYS = 30
VALID_SIZES = {'P', 'PP', 'M', 'G', 'GG', 'XG', 'XGG', 'U', 'Ú',
               '34', '36', '38', '40', '42', '44', '46', '48',
               '1', '2', '3', '4', '5', '6', '7', '8'}


def validate_post(post_data: dict, original_price: float = None,
                  original_sizes: str = "") -> Tuple[bool, List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    caption = (post_data.get('final_caption', '') or
               post_data.get('ai_caption', '')).strip()
    hashtags = (post_data.get('final_hashtags', '') or
                post_data.get('ai_hashtags', '')).strip()
    scheduled_at = post_data.get('scheduled_at', '')

    if not caption:
        errors.append("Legenda não pode estar vazia.")

    if len(caption) > MAX_CAPTION_LENGTH:
        warnings.append(f"Legenda tem {len(caption)} caracteres "
                        f"(máx. {MAX_CAPTION_LENGTH} do Instagram).")

    if not hashtags:
        warnings.append("Nenhuma hashtag informada.")
    else:
        ht_list = [h.strip() for h in hashtags.replace(',', ' ').split() if h.strip().startswith('#')]
        if len(ht_list) > MAX_HASHTAGS:
            warnings.append(f"{len(ht_list)} hashtags (máx. recomendado: {MAX_HASHTAGS}).")

    if not scheduled_at:
        errors.append("Data de agendamento é obrigatória.")
    else:
        try:
            sched = datetime.fromisoformat(scheduled_at)
            now = datetime.now(BRASIL_TZ)
            if sched.tzinfo is None:
                sched = sched.replace(tzinfo=BRASIL_TZ)
            if sched <= now:
                errors.append("Data de agendamento deve ser no futuro.")
            max_date = now + timedelta(days=MAX_SCHEDULE_DAYS)
            if sched > max_date:
                warnings.append(f"Data de agendamento está a mais de "
                                f"{MAX_SCHEDULE_DAYS} dias. Token pode expirar.")
        except (ValueError, TypeError):
            errors.append("Data de agendamento em formato inválido.")

    if original_price is not None:
        if 'price' in post_data and post_data['price'] is not None:
            if post_data['price'] < 0:
                errors.append("Preço não pode ser negativo.")
        all_text = f"{caption} {hashtags}".lower()
        price_patterns = re.findall(r'r\$\s*(\d+[\.,]?\d*)', all_text)
        for found in price_patterns:
            try:
                found_val = float(found.replace(',', '.'))
                if original_price and abs(found_val - original_price) > 0.01:
                    errors.append(f"Preço R${found_val} no texto difere do "
                                  f"informado R${original_price}.")
            except ValueError:
                pass

    if original_sizes:
        claimed_sizes = set(original_sizes.upper().replace(' ', '').split(','))
        if not claimed_sizes.issubset(VALID_SIZES):
            invalid = claimed_sizes - VALID_SIZES
            warnings.append(f"Tamanhos não reconhecidos: {', '.join(invalid)}.")

    for pattern, desc in FORBIDDEN_PATTERNS:
        if re.search(pattern, caption, re.IGNORECASE):
            errors.append(f"Texto contém linguagem proibida: {desc}.")

    return len(errors) == 0, errors, warnings