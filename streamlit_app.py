"""Entry point for Streamlit Community Cloud."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.frontend.app import main
main()
