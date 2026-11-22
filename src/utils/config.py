"""Configuration loading utility."""

import os
from pathlib import Path
from typing import Any
import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / '.env')


def load_yaml(file_path: str | Path) -> dict[str, Any]:
    """Load and parse a YAML file."""
    p = Path(file_path)
    if not p.exists():
        return {}
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


class AppConfig:
    """Central access point for application and model configurations."""

    def __init__(self):
        self.settings = load_yaml(PROJECT_ROOT / "config/settings.yaml")
        self.model_config = load_yaml(PROJECT_ROOT / "config/model_config.yaml")
        self.mode = os.getenv("DATASET_MODE", "small")

    @property
    def mode_settings(self) -> dict[str, Any]:
        """Return parameters for active dataset mode (small, medium, large)."""
        return self.settings.get("modes", {}).get(self.mode, {})


app_config = AppConfig()
