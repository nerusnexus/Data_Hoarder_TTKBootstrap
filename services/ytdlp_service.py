from pathlib import Path
import sqlite3
import threading
from yt_dlp import YoutubeDL


class YtDlpService:
    def __init__(self, data_dir: Path):
        self.db_path = data_dir / "db.db"
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            handle TEXT NOT NULL,
            url TEXT NOT NULL,
            title TEXT,
            uploader_id TEXT,
            FOREIGN KEY(group_id) REFERENCES groups(id)
        )
        """)

        conn.commit()
        conn.close()

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

        cur.execute("SELECT id FROM groups WHERE name=?", (group_name,))
        group_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO channels (group_id, handle, url, title, uploader_id)
            VALUES (?, ?, ?, ?, ?)
        """, (
            group_id,
            meta["handle"],
            meta["url"],
            meta["title"],
            meta["uploader_id"],
        ))

        conn.commit()
        conn.close()

    def delete_channel(self, handle: str):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("DELETE FROM channels WHERE handle=?", (handle,))
        conn.commit()
        conn.close()


    def fetch_channel_public_info(self, channel_input: str):
        import yt_dlp

        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "extract_flat": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel_input, download=False)

        return {
            "title": info.get("title"),
            "channel_id": info.get("channel_id"),
            "subscriber_count": info.get("channel_follower_count")
                or info.get("subscriber_count"),
            "video_count": info.get("playlist_count")
        }