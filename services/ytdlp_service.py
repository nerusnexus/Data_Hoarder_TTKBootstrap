from pathlib import Path
import sqlite3
import threading
from yt_dlp import YoutubeDL


class YtDlpService:
    def __init__(self, db_path: Path):
        # Store the unified database path directly
        self.db_path = db_path

    # ---------- Groups ----------

    def add_group(self, name: str):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("INSERT INTO groups (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()

    def delete_group(self, name: str):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("DELETE FROM groups WHERE name=?", (name,))
        conn.commit()
        conn.close()

    # ---------- Channels ----------

    def fetch_channel_metadata(self, channel_input: str) -> dict:
        channel_input = channel_input.strip()

        if not channel_input.startswith("http"):
            channel_input = channel_input.lstrip("@")
            channel_input = f"https://www.youtube.com/@{channel_input}"

        opts = {
            "quiet": True,
            "skip_download": True,
            "extract_flat": True,
        }

        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(channel_input, download=False)

        return {
            "url": channel_input,
            "title": info.get("title"),
            "uploader_id": info.get("uploader_id"),
            "handle": info.get("uploader_id") or info.get("id"),
        }

    def add_channel(self, group_name: str, meta: dict):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # Insert channel using the new unified schema logic
        cur.execute("""
            INSERT INTO channels (group_name, name, handle, url, title, uploader_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            group_name,
            meta.get("title") or meta.get("handle"),
            meta.get("handle"),
            meta.get("url"),
            meta.get("title"),
            meta.get("uploader_id"),
        ))

        conn.commit()
        conn.close()

    def delete_channel(self, handle: str):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("DELETE FROM channels WHERE handle=?", (handle,))
        conn.commit()
        conn.close()

    def fetch_channel_metadata(self, channel_input: str) -> dict:
        channel_input = channel_input.strip()

        # Options matching: yt-dlp -J --flat-playlist
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "extract_flat": True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            # Returns the full metadata dictionary
            info = ydl.extract_info(channel_input, download=False)

        return info