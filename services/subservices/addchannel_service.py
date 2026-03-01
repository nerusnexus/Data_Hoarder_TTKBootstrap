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
        url = url.strip()

        # --- NEW: Convert handles to full URLs automatically ---
        if not url.startswith("http"):
            url = url.lstrip("@")
            url = f"https://www.youtube.com/@{url}"

        ydl_opts: dict[str, typing.Any] = {
            'quiet': True,
            'extract_flat': 'in_playlist',
            'dump_single_json': True,
            'js_runtimes': {'deno': {'path': None}},
            'remote_components': ['ejs:github']
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
            try:
                if progress_callback:
                    progress_callback("Fetching channel metadata...")

                raw_info = ydl.extract_info(url, download=False)
                info = dict(raw_info) if raw_info else {}

                channel_name = info.get("uploader") or info.get("channel") or info.get("title") or "Unknown_Channel"
                channel_id = info.get("channel_id") or "Unknown_ID"
                handle = info.get("uploader_id") or "Unknown_Handle"

                if handle and handle != "Unknown_Handle":
                    safe_handle = handle if handle.startswith('@') else f"@{handle}"
                else:
                    safe_handle = f"@{channel_id}"

                follower_count = info.get("channel_follower_count") or info.get("subscriber_count") or 0
                description = info.get("description") or ""
                tags_json = json.dumps(info.get("tags", []))
                chan_thumbnails_json = json.dumps(info.get("thumbnails", []))

                with self.get_connection() as conn:
                    cursor = conn.cursor()

                    cursor.execute("SELECT id FROM channels WHERE group_name = ? AND name = ?", (group, channel_name))
                    if cursor.fetchone():
                        cursor.execute("""
                            UPDATE channels SET handle=?, channel_id=?, url=?, title=?, follower_count=?, description=?, tags=?, thumbnails=?
                            WHERE group_name=? AND name=?
                        """, (handle, channel_id, info.get("uploader_url") or url, info.get("title"),
                              follower_count, description, tags_json, chan_thumbnails_json, group, channel_name))
                    else:
                        cursor.execute("""
                            INSERT INTO channels (group_name, name, handle, channel_id, url, title, follower_count, description, tags, thumbnails)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (group, channel_name, handle, channel_id, info.get("uploader_url") or url,
                              info.get("title"), follower_count, description, tags_json, chan_thumbnails_json))

                    def extract_all_videos(data):
                        videos = []
                        if not data:
                            return videos
                        if data.get("id") and data.get("_type") != "playlist" and data.get("url"):
                            videos.append(data)
                        if "entries" in data and data["entries"]:
                            for entry_item in data["entries"]:
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
                        video_id = video_entry.get("id") or f"unknown_{i}"

                        if not url_chk and video_id and not video_id.startswith("unknown"):
                            url_chk = f"https://www.youtube.com/watch?v={video_id}"

                        live_status = video_entry.get("live_status")

                        if live_status in ["is_live", "was_live", "is_upcoming"]:
                            v_type = "Lives"
                        elif "/shorts/" in url_chk:
                            v_type = "Shorts"
                        else:
                            v_type = "Videos"

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

                        # Verify if the info json file exists natively during library sync
                        is_metadata_downloaded = 1 if (
                                video_folder / f"{expected_filename_base}.info.json").exists() else 0

                        cursor.execute("SELECT id FROM videos WHERE video_id = ? AND channel_name = ?",
                                       (video_id, channel_name))
                        if cursor.fetchone():
                            cursor.execute("""
                                UPDATE videos SET title=?, url=?, view_count=?, video_type=?, upload_date=?, thumbnails=?, filepath=?, is_downloaded=?, is_metadata_downloaded=?
                                WHERE video_id=? AND channel_name=?
                            """, (title, url_chk, view_count, v_type, upload_date, thumbnails_json, str(filepath_base),
                                  is_downloaded, is_metadata_downloaded, video_id, channel_name))
                        else:
                            cursor.execute("""
                                INSERT INTO videos (channel_name, video_id, title, url, view_count, is_downloaded, is_metadata_downloaded, video_type, upload_date, thumbnails, filepath)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (channel_name, video_id, title, url_chk, view_count, is_downloaded,
                                  is_metadata_downloaded, v_type,
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
                print(f"NETWORK/YTDLP ERROR: {net_err}")
                return False, f"CONNECTION ERROR:\nCould not reach YouTube or find the channel.\n\nDetails: {net_err}"

            except sqlite3.Error as db_err:
                full_traceback = traceback.format_exc()
                print(f"DATABASE ERROR: {db_err}\n{full_traceback}")
                return False, f"DATABASE ERROR:\nFailed to save data to the library.\n\nDetails: {db_err}"

            except Exception as err:
                full_traceback = traceback.format_exc()
                error_type = type(err).__name__
                print(f"UNEXPECTED ERROR [{error_type}]: {err}\n{full_traceback}")
                return False, f"UNEXPECTED SYSTEM ERROR ({error_type}):\n{full_traceback}"