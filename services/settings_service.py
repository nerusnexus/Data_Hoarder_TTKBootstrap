import json
from pathlib import Path
import warnings
import sys
import os
import subprocess


class SettingsService:
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.config_file = self.root_path / "settings.json"

        self.data = {
            "theme": "darkly",
            "start_with_system": False,
            "close_to_tray": False,
        }

        self.root_folder = self.root_path

        self.load()

    def load(self):
        if not self.config_file.exists():
            return

        try:
            data = json.loads(self.config_file.read_text())
            if not isinstance(data, dict):
                raise ValueError("Settings file does not contain a JSON object")
            self.data.update(data)

        except Exception as e:
            warnings.warn(
                f"Failed to load settings from {self.config_file}: {e}",
                RuntimeWarning,
            )

    def save(self):
        self.config_file.write_text(json.dumps(self.data, indent=4))

    # --- getters ---
    def get_theme(self):
        return self.data["theme"]

    def get_start_with_system(self):
        return self.data["start_with_system"]

    # --- setters ---
    def set_theme(self, theme: str):
        self.data["theme"] = theme
        self.save()

    def set_start_with_system(self, value: bool):
        self.data["start_with_system"] = value
        self.save()

    def open_data_folder(self):
        path = self.root_folder

        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.run(["open", path])
        else:
            subprocess.run(["xdg-open", path])

    def get_close_to_tray(self) -> bool:
        return self.data.get("close_to_tray", False)

    def set_close_to_tray(self, value: bool):
        self.data["close_to_tray"] = value
        self.save()