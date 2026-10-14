"""Ko'z core: recipe checks, the recipe runner and the OpenCV 5 blocks.

Lane: Claude (see CLAUDE.md). The contract with the web app is in contracts/."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS = ROOT / "contracts"
MODELS = Path(__file__).resolve().parent / "models"
