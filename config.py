from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "Data"
METADATA_DIR = DATA_DIR / "Metadata"
VIDEOS_DIR = DATA_DIR / "Videos" # <-- NEW: Videos directory

# Asset Paths
ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
ICONS_DIR = ASSETS_DIR / "icons"

# File paths
DB_PATH = DATA_DIR / "database.db"
SETTINGS_PATH = DATA_DIR / "settings.json"
ACCOUNT_PATH = DATA_DIR / "account.json"
DATABASE_ICON_PATH = ICONS_DIR / "database.ico"

# YouTube Data API v3 Key
YOUTUBE_API_KEY = ""

# Ensure directories exist upon import
DATA_DIR.mkdir(parents=True, exist_ok=True)
METADATA_DIR.mkdir(parents=True, exist_ok=True)
VIDEOS_DIR.mkdir(parents=True, exist_ok=True) # <-- NEW
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
FONTS_DIR.mkdir(parents=True, exist_ok=True)
ICONS_DIR.mkdir(parents=True, exist_ok=True)