"""
Rosee Instagram Automation — Main Entry Point.

Usage:
    # Start backend
    python main.py backend

    # Start frontend
    python main.py frontend

    # Start both (Windows: two terminal windows)
    python main.py all
"""

import sys
import subprocess
import os
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"


def ensure_template_configs():
    """Create default template config files if they don't exist."""
    image_templates = {
        "feed_01": {
            "name": "Feed Padrão",
            "target_width": 1080,
            "target_height": 1080,
            "background_color": "#FFFFFF",
            "image_x": 0,
            "image_y": 0,
            "image_width": 1080,
            "image_height": 1080,
            "store_name_x": 40,
            "store_name_y": 40,
            "price_x": 40,
            "price_y": 1000,
            "sizes_x": 40,
            "sizes_y": 1040,
            "text_color": "#000000",
            "price_color": "#E91E63",
            "font_size": 32,
        },
        "story_01": {
            "name": "Story Padrão",
            "target_width": 1080,
            "target_height": 1920,
            "background_color": "#FFFFFF",
            "image_x": 0,
            "image_y": 0,
            "image_width": 1080,
            "image_height": 1080,
            "store_name_x": 40,
            "store_name_y": 40,
            "price_x": 40,
            "price_y": 1840,
            "sizes_x": 40,
            "sizes_y": 1880,
            "text_color": "#FFFFFF",
            "price_color": "#E91E63",
            "font_size": 40,
        },
    }

    for folder_name, config in image_templates.items():
        folder = TEMPLATES_DIR / "image" / folder_name
        folder.mkdir(parents=True, exist_ok=True)
        config_path = folder / "config.json"
        if not config_path.exists():
            with open(str(config_path), "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)

            # Create a minimal base image (white)
            try:
                from PIL import Image
                base_img = Image.new(
                    "RGB",
                    (config["target_width"], config["target_height"]),
                    (255, 255, 255),
                )
                base_img.save(str(folder / "base.png"))
            except ImportError:
                pass  # Pillow not installed yet

    # Video template configs
    video_templates = {
        "video_01": {
            "name": "Reels Básico",
            "duration": 30,
        },
    }
    for folder_name, config in video_templates.items():
        folder = TEMPLATES_DIR / "video" / folder_name
        folder.mkdir(parents=True, exist_ok=True)
        config_path = folder / "config.json"
        if not config_path.exists():
            with open(str(config_path), "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)


def main():
    if len(sys.argv) < 2:
        print("Uso: python main.py [backend|frontend|all]")
        print("")
        print("  backend   - Inicia o servidor FastAPI na porta 8000")
        print("  frontend  - Inicia o Streamlit na porta 8501")
        print("  all       - Inicia ambos (requer terminais separados)")
        return

    ensure_template_configs()

    command = sys.argv[1]

    if command == "backend":
        print("Iniciando backend FastAPI em http://localhost:8000 ...")
        os.chdir(str(PROJECT_ROOT))
        subprocess.run([
            sys.executable, "-m", "uvicorn", "backend.main:app",
            "--reload", "--host", "0.0.0.0", "--port", "8000",
        ])

    elif command == "frontend":
        print("Iniciando frontend Streamlit em http://localhost:8501 ...")
        os.chdir(str(PROJECT_ROOT))
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "frontend/app.py",
            "--server.port", "8501",
        ])

    elif command == "all":
        print("Para iniciar ambos, abra dois terminais:")
        print("  Terminal 1: python main.py backend")
        print("  Terminal 2: python main.py frontend")

    elif command == "init":
        print("Inicializando templates...")
        ensure_template_configs()
        print("Pronto! Templates criados.")

    else:
        print(f"Comando desconhecido: {command}")
        print("Use: python main.py [backend|frontend|all|init]")


if __name__ == "__main__":
    main()