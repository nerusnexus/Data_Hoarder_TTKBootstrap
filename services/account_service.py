import json
import warnings
from config import ACCOUNT_PATH

class AccountService:
    def __init__(self):
        self.account_file = ACCOUNT_PATH

        self.data = {
            "channel_handle": "",
            "channel_url": "",
            "channel_id": "",
            "subscribers": 0,
            "subscribed_to": 0,
            "video_count": 0
        }

        self.load()

    def load(self):
        if not self.account_file.exists():
            return

        try:
            data = json.loads(self.account_file.read_text())
            if not isinstance(data, dict):
                raise ValueError("Settings file does not contain a JSON object")
            self.data.update(data)
        except json.JSONDecodeError:
            warnings.warn(f"Settings file {self.account_file} is corrupted. Reverting to defaults.", RuntimeWarning)
        except Exception as e:
            warnings.warn(f"Failed to load settings from {self.account_file}: {e}", RuntimeWarning)

    def save(self):
        self.account_file.write_text(json.dumps(self.data, indent=4))

    def update_field(self, key, value):
        self.data[key] = value
        self.save()

    def get(self, key):
        return self.data.get(key)