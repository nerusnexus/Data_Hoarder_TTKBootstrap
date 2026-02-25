import json
import sqlite3
import yt_dlp
from pathlib import Path

class AddChannelService:
    # 1. Fixed the __init__ to accept the 3 arguments your services.py is sending
    def __init__(self, db_path, metadata_folder, ytdlp=None):
        self.db_path = db_path
        self.metadata_folder = Path(metadata_folder)
        self.ytdlp = ytdlp

    def get_connection(self):
        # This allows us to return rows as dictionaries, which your UI expects
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_all_groups(self):
        with self.get_connection() as conn:
            return [row["name"] for row in conn.execute("SELECT name FROM groups").fetchall()]

    def get_channels_by_group(self, group):
        with self.get_connection() as conn:
            return [row["name"] for row in conn.execute("SELECT name FROM channels WHERE group_name = ?", (group,)).fetchall()]

    def get_channel_details(self, name):
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM channels WHERE name = ?", (name,)).fetchone()
            return dict(row) if row else None

    def get_videos_by_channel(self, name):
        with self.get_connection() as conn:
            # Matches your schema: your videos table links to channels via 'channel_name'
            rows = conn.execute("SELECT * FROM videos WHERE channel_name = ?", (name,)).fetchall()
            return [dict(row) for row in rows]

    def fetch_channel_info(self, url, group, progress_callback=None):
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,  # Don't download videos, just metadata
            'dump_single_json': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                if progress_callback: progress_callback("Fetching channel metadata...")
                info = ydl.extract_info(url, download=False)

                # CORREÇÃO 1: Fallbacks mais robustos para evitar que fique None
                channel_name = info.get("uploader") or info.get("channel") or info.get("title") or "Unknown_Channel"
                channel_id = info.get("id") or "Unknown_ID"
                handle = info.get("uploader_id") or channel_id

                with self.get_connection() as conn:
                    cursor = conn.cursor()

                    # 1. Save Channel Info (Update if it exists, insert if it doesn't)
                    cursor.execute("SELECT id FROM channels WHERE group_name = ? AND name = ?", (group, channel_name))
                    if cursor.fetchone():
                        cursor.execute("""
                            UPDATE channels SET handle=?, channel_id=?, url=?, title=?
                            WHERE group_name=? AND name=?
                        """, (handle, channel_id, info.get("uploader_url") or url, info.get("title"), group, channel_name))
                    else:
                        cursor.execute("""
                            INSERT INTO channels (group_name, name, handle, channel_id, url, title)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (group, channel_name, handle, channel_id, info.get("uploader_url") or url, info.get("title")))

                    # 2. Process Videos
                    if "entries" in info:
                        total = len(info["entries"])
                        for i, entry in enumerate(info["entries"]):
                            if not entry: continue

                            # --- DETECT VIDEO TYPE ---
                            url_chk = entry.get("url", "") or entry.get("original_url", "") or entry.get("webpage_url", "")
                            live_status = entry.get("live_status")
                            duration = entry.get("duration", 9999)

                            if live_status in ["is_live", "was_live", "is_upcoming"]:
                                v_type = "Lives"
                            elif "/shorts/" in url_chk or (duration and duration <= 61):
                                v_type = "Shorts"
                            else:
                                v_type = "Videos"

                            # Prevenindo IDs vazios para os vídeos
                            video_id = entry.get("id") or f"unknown_{i}"
                            title = entry.get("title") or "Unknown Title"
                            view_count = entry.get("view_count") or 0
                            upload_date = entry.get("upload_date") or "00000000"

                            # Insert or Update the video to avoid duplicates
                            cursor.execute("SELECT id FROM videos WHERE video_id = ? AND channel_name = ?", (video_id, channel_name))
                            if cursor.fetchone():
                                cursor.execute("""
                                    UPDATE videos SET title=?, url=?, view_count=?, video_type=?, upload_date=?
                                    WHERE video_id=? AND channel_name=?
                                """, (title, url_chk, view_count, v_type, upload_date, video_id, channel_name))
                            else:
                                cursor.execute("""
                                    INSERT INTO videos (channel_name, video_id, title, url, view_count, is_downloaded, video_type, upload_date)
                                    VALUES (?, ?, ?, ?, ?, 0, ?, ?)
                                """, (channel_name, video_id, title, url_chk, view_count, v_type, upload_date))

                            if progress_callback and i % 10 == 0:
                                progress_callback(f"Processing video {i}/{total}...")

                    conn.commit()

                # 3. Save JSON to disk (Optional, for backup)
                folder_name = f"{channel_id} ({handle})" if handle and handle != channel_id else channel_id
                save_path = self.metadata_folder / folder_name / "channel_info.json"
                save_path.parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(info, f, indent=4)

                return True, f"Successfully added {channel_name}"


            except Exception as e:
                import traceback
                erro_completo = traceback.format_exc()
                print("ERRO DETALHADO:")
                print(erro_completo)
                # Retorna a string gigantesca para forçar a caixa de aviso a mostrar tudo
                return False, f"ERRO FATAL:\n{erro_completo}"