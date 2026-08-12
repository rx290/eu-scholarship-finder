"""Load applicant/search config: config.local.yaml if present, else the example template."""
import shutil
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
LOCAL_CONFIG = ROOT / "config.local.yaml"
EXAMPLE_CONFIG = ROOT / "config.example.yaml"


def ensure_local_config() -> tuple[Path, bool]:
    """Return (path, created). Copies the example template if config.local.yaml is missing."""
    if LOCAL_CONFIG.exists():
        return LOCAL_CONFIG, False
    shutil.copy(EXAMPLE_CONFIG, LOCAL_CONFIG)
    return LOCAL_CONFIG, True


def load_config() -> dict:
    path = LOCAL_CONFIG if LOCAL_CONFIG.exists() else EXAMPLE_CONFIG
    with open(path) as f:
        return yaml.safe_load(f)
