
"""Application configuration and setup."""

import logging
import os
from pathlib import Path

# Project structure
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "app.log"),
        logging.StreamHandler()
    ]
)

# Database paths
DB_PATH = DATA_DIR / "tokens.db"
COIN_HISTORY_PATH = DATA_DIR / "coin_history.json"
META_SCORES_PATH = DATA_DIR / "meta_scores.json"
