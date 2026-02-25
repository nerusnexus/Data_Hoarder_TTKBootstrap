import sqlite3
from pathlib import Path


class AddChannelService:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def add_channel(self, group_name: str, channel_name: str):
        if not channel_name:
            raise ValueError("Channel name cannot be empty")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO channels (group_name, name) VALUES (?, ?)",
                (group_name, channel_name)
            )
        except sqlite3.IntegrityError:
            conn.close()
            raise Exception("Channel already exists in this group")

        conn.commit()
        conn.close()

        return channel_name

    def get_channels_by_group(self, group_name: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM channels WHERE group_name = ?",
            (group_name,)
        )

        channels = cursor.fetchall()
        conn.close()

        return [c[0] for c in channels]

    def delete_channel(self, channel_name: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM channels WHERE name = ?", (channel_name,))

        conn.commit()
        conn.close()