from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import os
import json

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
STORAGE_DIR = Path(__file__).resolve().parent.parent / "storage"
PROCESSED_DIR = STORAGE_DIR / "processed"

FALLBACK_COLOR = (255, 255, 255)
FALLBACK_FONT_SIZE = 32


def _hex_to_rgb(hex_color: str):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def apply_image_template(media_path: str, template_id: str,
                         price: float = None, sizes: str = "",
                         store_name: str = "Minha Loja") -> str:
    os.makedirs(str(PROCESSED_DIR), exist_ok=True)

    template_dir = TEMPLATES_DIR / "image" / template_id.replace("tpl_", "")
    base_path = template_dir / "base.png"
    overlay_path = template_dir / "overlay.png"
    config_path = template_dir / "config.json"

    # Load config
    config = {}
    if config_path.exists():
        with open(str(config_path), 'r', encoding='utf-8') as f:
            config = json.load(f)

    output_filename = f"{Path(media_path).stem}_{template_id}_processed.png"
    output_path = str(PROCESSED_DIR / output_filename)

    # Open user media
    img = Image.open(media_path).convert("RGBA")

    # Resize to target size (default 1080x1080 for feed)
    target_w = config.get("target_width", 1080)
    target_h = config.get("target_height", 1080)

    # Create canvas with background color
    bg_hex = config.get("background_color", "#FFFFFF")
    bg_rgb = _hex_to_rgb(bg_hex)

    canvas = Image.new("RGBA", (target_w, target_h), bg_rgb)

    # Paste user image centered, maintaining aspect ratio
    user_x = config.get("image_x", 0)
    user_y = config.get("image_y", 0)
    user_w = config.get("image_width", target_w)
    user_h = config.get("image_height", target_h)

    img_resized = img.resize((user_w, user_h), Image.LANCZOS)
    canvas.paste(img_resized, (user_x, user_y), img_resized if img_resized.mode == 'RGBA' else None)

    # Apply overlay
    if overlay_path.exists():
        overlay = Image.open(str(overlay_path)).convert("RGBA")
        overlay = overlay.resize((target_w, target_h), Image.LANCZOS)
        canvas = Image.alpha_composite(canvas, overlay)

    # Draw text (price, sizes, store name)
    draw = ImageDraw.Draw(canvas)

    # Try to load font
    font_path = config.get("font_path", "")
    font_size = config.get("font_size", FALLBACK_FONT_SIZE)
    try:
        if font_path and os.path.exists(font_path):
            font = ImageFont.truetype(font_path, font_size)
        else:
            try:
                font = ImageFont.load_default(font_size)
            except TypeError:
                font = ImageFont.load_default()
    except Exception:
        try:
            font = ImageFont.load_default(font_size)
        except TypeError:
            font = ImageFont.load_default()

    # Draw store name
    if store_name:
        name_x = config.get("store_name_x", 40)
        name_y = config.get("store_name_y", 40)
        color_hex = config.get("text_color", "#000000")
        color_rgb = _hex_to_rgb(color_hex)
        draw.text((name_x, name_y), store_name, fill=color_rgb, font=font)

    # Draw price
    if price is not None:
        price_x = config.get("price_x", 40)
        price_y = config.get("price_y", target_h - 80)
        price_color = _hex_to_rgb(config.get("price_color", "#000000"))
        draw.text((price_x, price_y),
                  f"R$ {price:.2f}".replace('.', ','),
                  fill=price_color, font=font)

    # Draw sizes
    if sizes:
        sizes_x = config.get("sizes_x", 40)
        sizes_y = config.get("sizes_y", target_h - 40)
        draw.text((sizes_x, sizes_y),
                  f"Tam: {sizes}",
                  fill=color_rgb, font=font)

    canvas.save(output_path, "PNG")
    return output_path


def apply_video_template(media_path: str, template_id: str,
                         price: float = None, sizes: str = "",
                         store_name: str = "Minha Loja") -> str:
    """Apply video template using MoviePy.

    Returns the path to the processed video.
    Falls back to copying the original if MoviePy fails.
    """
    try:
        from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip, concatenate_videoclips
    except ImportError:
        # Fallback: copy original
        import shutil
        os.makedirs(str(PROCESSED_DIR), exist_ok=True)
        output = str(PROCESSED_DIR / f"{Path(media_path).stem}_{template_id}_processed.mp4")
        shutil.copy2(media_path, output)
        return output

    os.makedirs(str(PROCESSED_DIR), exist_ok=True)
    output = str(PROCESSED_DIR / f"{Path(media_path).stem}_{template_id}_processed.mp4")

    try:
        template_dir = TEMPLATES_DIR / "video" / template_id.replace("tpl_", "")
        intro_path = template_dir / "intro.mp4"
        outro_path = template_dir / "outro.mp4"

        clips = []

        # Intro
        if intro_path.exists():
            intro = VideoFileClip(str(intro_path))
            clips.append(intro)

        # Main content
        main = VideoFileClip(media_path)
        target_duration = 30
        if main.duration > target_duration:
            main = main.subclip(0, target_duration)
        clips.append(main)

        # Outro
        if outro_path.exists():
            outro = VideoFileClip(str(outro_path))
            clips.append(outro)

        final = concatenate_videoclips(clips, method="compose")
        final.write_videofile(output, codec="libx264", audio_codec="aac",
                              preset="ultrafast", logger=None)
        return output

    except Exception:
        # Fallback on failure
        import shutil
        shutil.copy2(media_path, output)
        return output


def get_available_templates(template_type: str = None):
    """Return list of available templates."""
    templates = []
    for kind in ["image", "video"]:
        if template_type and template_type != kind:
            continue
        templates_dir = TEMPLATES_DIR / kind
        if not templates_dir.exists():
            continue
        for folder in sorted(templates_dir.iterdir()):
            if folder.is_dir():
                config_path = folder / "config.json"
                config = {}
                if config_path.exists():
                    with open(str(config_path), encoding='utf-8') as f:
                        config = json.load(f)
                templates.append({
                    "id": f"tpl_{folder.name}",
                    "name": config.get("name", folder.name),
                    "type": kind,
                    "path": str(folder),
                })
    return templates