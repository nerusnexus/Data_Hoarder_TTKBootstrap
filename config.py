from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "Data"
METADATA_DIR = DATA_DIR / "Metadata"

# File paths
DB_PATH = DATA_DIR / "database.db"
SETTINGS_PATH = DATA_DIR / "settings.json"
ACCOUNT_PATH = DATA_DIR / "account.json"

# Ensure directories exist upon import
DATA_DIR.mkdir(parents=True, exist_ok=True)
METADATA_DIR.mkdir(parents=True, exist_ok=True)