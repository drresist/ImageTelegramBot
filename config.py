"""Configuration module for the Telegram image bot."""
import os
from pathlib import Path

# Bot configuration
API_TOKEN = os.environ.get("IMAGE_BOT_API")
if not API_TOKEN:
    raise ValueError("IMAGE_BOT_API environment variable is not set")

# Bot options (no leading spaces — used as callback prefixes: "{option}:{id}")
BOT_OPTIONS = ("exif", "cropx2", "score", "geo")
OPTION_LABELS = {
    "exif": "Show EXIF",
    "cropx2": "Crop photo x2",
    "score": "Score",
    "geo": "Show on map",
}

# Paths
BASE_DIR = Path(__file__).parent
CACHE_DIR = BASE_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)
FILE_STORE_PATH = CACHE_DIR / "file_index.json"
FILE_STORE_TTL_HOURS = float(os.environ.get("FILE_STORE_TTL_HOURS", "24"))

# File settings
SUPPORTED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE_MB = 10

# Logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
