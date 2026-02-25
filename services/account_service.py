import json
from pathlib import Path
import warnings


class AccountService:
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.account_file = self.root_path / "account.json"

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
            if isinstance(data, dict):
                self.data.update(data)
        except Exception as e:
            warnings.warn(
                f"Failed to load account.json: {e}",
                RuntimeWarning
            )

    def save(self):
        self.account_file.write_text(json.dumps(self.data, indent=4))

    def update_field(self, key, value):
        self.data[key] = value
        self.save()

    def get(self, key):
        return self.data.get(key)