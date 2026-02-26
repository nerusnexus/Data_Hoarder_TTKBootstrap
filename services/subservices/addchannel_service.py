import json
import sqlite3
import yt_dlp
import re
import traceback
import typing
from config import METADATA_DIR
from services.db.db_manager import DatabaseManager
from yt_dlp.utils import DownloadError

def sanitize_filename(name):
    """Replaces characters that are invalid in Windows/Linux file paths."""
    return re.sub(r'[\\/*?:"<>|]', '_', name)


class AddChannelService:
    def __init__(self, ytdlp=None):
        self.ytdlp = ytdlp
        self.metadata_folder = METADATA_DIR

    @staticmethod
    def get_connection():
        """Static method to get a DB connection. Does not take 'self'."""
        conn = DatabaseManager.get_connection()
        conn.row_factory = sqlite3.Row
        return conn

    def get_all_groups(self):
        with self.get_connection() as conn:
            return [row["name"] for row in conn.execute("SELECT name FROM groups").fetchall()]

    def get_channels_by_group(self, group):
        with self.get_connection() as conn:
            return [row["name"] for row in
                    conn.execute("SELECT name FROM channels WHERE group_name = ?", (group,)).fetchall()]

    def get_channel_details(self, name):
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM channels WHERE name = ?", (name,)).fetchone()
            return dict(row) if row else None

    def get_videos_by_channel(self, name):
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM videos WHERE channel_name = ?", (name,)).fetchall()
            return [dict(row) for row in rows]

    def add_channel(self, group_name: str, url: str) -> str:
        success, message = self.fetch_channel_info(url, group_name)
        if not success:
            raise Exception(message)
        return message.replace("Successfully added ", "")

    def delete_channel(self, channel_name: str):
        with self.get_connection() as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("DELETE FROM channels WHERE name = ?", (channel_name,))
            conn.commit()

    def fetch_channel_info(self, url, group, progress_callback=None):
        # Fix: Explicitly define the type for ydl_opts to satisfy strict IDE typing
        ydl_opts: dict[str, typing.Any] = {
            'quiet': True,
            'extract_flat': 'in_playlist',
            'dump_single_json': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
            try:
                if progress_callback:
                    progress_callback("Fetching channel metadata...")

                raw_info = ydl.extract_info(url, download=False)
                # Fix: Convert TypedDict to standard dict to find 'channel_id' key
                info = dict(raw_info) if raw_info else {}

                channel_name = info.get("uploader") or info.get("channel") or info.get("title") or "Unknown_Channel"
                channel_id = info.get("channel_id") or "Unknown_ID"
                handle = info.get("uploader_id") or "Unknown_Handle"

                if handle and handle != "Unknown_Handle":
                    safe_handle = handle if handle.startswith('@') else f"@{handle}"
                else:
                    safe_handle = f"@{channel_id}"

                with self.get_connection() as conn:
                    cursor = conn.cursor()

                    cursor.execute("SELECT id FROM channels WHERE group_name = ? AND name = ?", (group, channel_name))
                    if cursor.fetchone():
                        cursor.execute("""
                            UPDATE channels SET handle=?, channel_id=?, url=?, title=?
                            WHERE group_name=? AND name=?
                        """, (handle, channel_id, info.get("uploader_url") or url, info.get("title"), group,
                              channel_name))
                    else:
                        cursor.execute("""
                            INSERT INTO channels (group_name, name, handle, channel_id, url, title)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (group, channel_name, handle, channel_id, info.get("uploader_url") or url,
                              info.get("title")))

                    def extract_all_videos(data):
                        videos = []
                        if not data:
                            return videos
                        if data.get("id") and data.get("_type") != "playlist" and data.get("url"):
                            videos.append(data)
                        if "entries" in data and data["entries"]:
                            for entry_item in data["entries"]:  # Fix: renamed to avoid shadowing 'entry'
                                videos.extend(extract_all_videos(entry_item))
                        return videos

                    all_videos = extract_all_videos(info)
                    total = len(all_videos)

                    folder_name = f"{channel_id} ({handle})" if handle and handle != "Unknown_Handle" else channel_id
                    channel_folder = self.metadata_folder / folder_name

                    for i, video_entry in enumerate(all_videos):
                        if not video_entry:
                            continue

                        url_chk = video_entry.get("url") or video_entry.get("webpage_url") or ""
                        live_status = video_entry.get("live_status")

                        if live_status in ["is_live", "was_live", "is_upcoming"]:
                            v_type = "Lives"
                        elif "/shorts/" in url_chk:
                            v_type = "Shorts"
                        else:
                            v_type = "Videos"

                        video_id = video_entry.get("id") or f"unknown_{i}"
                        title = video_entry.get("title") or "Unknown Title"
                        view_count = video_entry.get("view_count") or 0
                        upload_date = video_entry.get("upload_date") or "00000000"
                        thumbnails_json = json.dumps(video_entry.get("thumbnails", []))

                        subfolder_name = f"({safe_handle}) {v_type}"
                        video_folder = channel_folder / subfolder_name
                        video_folder.mkdir(parents=True, exist_ok=True)

                        clean_title = sanitize_filename(title)
                        expected_filename_base = f"{upload_date}_{clean_title}"
                        filepath_base = video_folder / expected_filename_base

                        is_downloaded = 0
                        for ext in ['.mp4', '.mkv', '.webm', '.avi', '.mov']:
                            if (video_folder / f"{expected_filename_base}{ext}").exists():
                                is_downloaded = 1
                                break

                        cursor.execute("SELECT id FROM videos WHERE video_id = ? AND channel_name = ?",
                                       (video_id, channel_name))
                        if cursor.fetchone():
                            cursor.execute("""
                                UPDATE videos SET title=?, url=?, view_count=?, video_type=?, upload_date=?, thumbnails=?, filepath=?, is_downloaded=?
                                WHERE video_id=? AND channel_name=?
                            """, (title, url_chk, view_count, v_type, upload_date, thumbnails_json, str(filepath_base),
                                  is_downloaded, video_id, channel_name))
                        else:
                            cursor.execute("""
                                INSERT INTO videos (channel_name, video_id, title, url, view_count, is_downloaded, video_type, upload_date, thumbnails, filepath)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (channel_name, video_id, title, url_chk, view_count, is_downloaded, v_type,
                                  upload_date, thumbnails_json, str(filepath_base)))

                        if progress_callback and i % 10 == 0:
                            progress_callback(f"Processing video {i}/{total}...")

                    conn.commit()

                if handle and handle != "Unknown_Handle":
                    filename = f"{channel_id}_({safe_handle}).json"
                else:
                    filename = f"{channel_id}.json"

                save_path = channel_folder / filename
                save_path.parent.mkdir(parents=True, exist_ok=True)

                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(info, f, indent=4)

                return True, f"Successfully added {channel_name}"

            except DownloadError as net_err:
                # specifically catches network, 404, or private video errors
                print(f"NETWORK/YTDLP ERROR: {net_err}")
                return False, f"CONNECTION ERROR:\nCould not reach YouTube or find the channel.\n\nDetails: {net_err}"

            except sqlite3.Error as db_err:
                # specifically catches database locks or schema mismatches
                full_traceback = traceback.format_exc()
                print(f"DATABASE ERROR: {db_err}\n{full_traceback}")
                return False, f"DATABASE ERROR:\nFailed to save data to the library.\n\nDetails: {db_err}"

            except Exception as err:
                # the final safety net for unexpected logic crashes
                full_traceback = traceback.format_exc()
                error_type = type(err).__name__
                print(f"UNEXPECTED ERROR [{error_type}]: {err}\n{full_traceback}")
                return False, f"UNEXPECTED SYSTEM ERROR ({error_type}):\n{full_traceback}"