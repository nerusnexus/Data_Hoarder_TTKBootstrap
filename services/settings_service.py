import json
import os
import sys
import subprocess
import datetime
from pathlib import Path
from config import SETTINGS_PATH, DATA_DIR


class SettingsService:
    def __init__(self, style_instance=None):
        self.settings_path = SETTINGS_PATH
        self.style = style_instance
        self.default_settings = {
            "theme": "darkly",
            "close_to_tray": False,
            "start_with_system": False,
            "youtube_api_key": "",
            "quota_date": "",
            "quota_used": 0,
            "ig_username": "",  # NEW
            "ig_password": ""   # NEW
        }
        self.settings = self.load_settings()

    def load_settings(self):
        if not self.settings_path.exists():
            self.save_settings(self.default_settings)
            return self.default_settings
        try:
            with open(self.settings_path, 'r') as f:
                data = json.load(f)
                for key, val in self.default_settings.items():
                    if key not in data:
                        data[key] = val
                return data
        except Exception:
            return self.default_settings

    def save_settings(self, settings_data):
        with open(self.settings_path, 'w') as f:
            json.dump(settings_data, f, indent=4)
        self.settings = settings_data

    def get_theme(self):
        return self.settings.get("theme", "darkly")

    def set_theme(self, theme_name):
        self.settings["theme"] = theme_name
        self.save_settings(self.settings)

    def get_close_to_tray(self):
        return self.settings.get("close_to_tray", False)

    def set_close_to_tray(self, value):
        self.settings["close_to_tray"] = value
        self.save_settings(self.settings)

    def get_start_with_system(self):
        return self.settings.get("start_with_system", False)

    def set_start_with_system(self, value):
        self.settings["start_with_system"] = value
        self.save_settings(self.settings)

    def open_data_folder(self):
        if sys.platform.startswith("win"):
            os.startfile(DATA_DIR)
        elif sys.platform == "darwin":
            subprocess.run(["open", DATA_DIR])
        else:
            subprocess.run(["xdg-open", DATA_DIR])

    def get_youtube_api_key(self):
        return self.settings.get("youtube_api_key", "")

    def set_youtube_api_key(self, key):
        self.settings["youtube_api_key"] = key
        self.save_settings(self.settings)

    # --- NEW: Instagram Credentials ---
    def get_ig_username(self):
        return self.settings.get("ig_username", "")

    def set_ig_username(self, username):
        self.settings["ig_username"] = username
        self.save_settings(self.settings)

    def get_ig_password(self):
        return self.settings.get("ig_password", "")

    def set_ig_password(self, password):
        self.settings["ig_password"] = password
        self.save_settings(self.settings)

    # --- Quota Tracking Methods ---
    def get_remaining_quota(self):
        today = datetime.date.today().isoformat()
        saved_date = self.settings.get("quota_date", "")

        if saved_date != today:
            self.settings["quota_date"] = today
            self.settings["quota_used"] = 0
            self.save_settings(self.settings)

        used = self.settings.get("quota_used", 0)
        return max(0, 10000 - used)

    def increment_quota_usage(self):
        today = datetime.date.today().isoformat()
        saved_date = self.settings.get("quota_date", "")

        if saved_date != today:
            self.settings["quota_date"] = today
            self.settings["quota_used"] = 1
        else:
            self.settings["quota_used"] = self.settings.get("quota_used", 0) + 1

        self.save_settings(self.settings)