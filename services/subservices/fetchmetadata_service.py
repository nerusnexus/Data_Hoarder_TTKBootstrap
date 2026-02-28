import json
import yt_dlp
from pathlib import Path
from config import METADATA_DIR
from services.db.db_manager import DatabaseManager


class FetchMetadataLogger:
    def __init__(self, log_callback, log_file_path):
        self.log_callback = log_callback
        self.log_file_path = log_file_path

    def _write_to_file(self, msg):
        try:
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(msg + '\n')
        except Exception:
            pass

    def debug(self, msg):
        if not msg.startswith('[debug] '):
            self.info(msg)

    def info(self, msg):
        if self.log_callback:
            self.log_callback(msg)
        self._write_to_file(msg)

    def warning(self, msg):
        formatted = f"WARNING: {msg}"
        if self.log_callback:
            self.log_callback(formatted)
        self._write_to_file(formatted)

    def error(self, msg):
        formatted = f"ERROR: {msg}"
        if self.log_callback:
            self.log_callback(formatted)
        self._write_to_file(formatted)


class FetchMetadataService:
    def __init__(self):
        self.metadata_dir = METADATA_DIR

    def fetch(self, videos: list, channel_name: str, params: dict, folder_name: str, handle: str, log_callback=None,
              status_callback=None, stop_event=None):
        target_dir = self.metadata_dir / folder_name
        target_dir.mkdir(parents=True, exist_ok=True)
        log_file_path = target_dir / f"{handle} Logs.txt"

        deno_path = params.get("deno_path", "").strip()
        js_runtimes = {'deno': {'path': deno_path if deno_path else None}}

        skip_downloaded = params.get("skip_downloaded", False)

        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'ignore_no_formats_error': True,
            'js_runtimes': js_runtimes,
            'remote_components': ['ejs:github'],
            'writeinfojson': params.get("--write-info-json", True),
            'writedescription': params.get("--write-description", True),
            'writethumbnail': params.get("--write-thumbnail", True),
            'getcomments': params.get("--get-comments", False),
            'sleep_interval': int(params.get("--sleep-interval", 10)),
            'max_sleep_interval': int(params.get("--max-sleep-interval", 30)),
            'sleep_interval_requests': int(params.get("--sleep-requests", 1)),
            'sleep_interval_subtitles': int(params.get("--sleep-subtitles", 5)),
            'retries': int(params.get("--retries", 10)),
            'fragment_retries': int(params.get("--fragment-retries", 10)),
            'logger': FetchMetadataLogger(log_callback, log_file_path),
            'ignoreerrors': True,
        }

        if params.get("use_cookies", True):
            ydl_opts['cookiesfrombrowser'] = ('firefox',)

        if log_callback:
            log_callback(f"\n--- Starting metadata extraction for {len(videos)} videos from {channel_name} ---")

        groups = {}
        for video in videos:
            if skip_downloaded and video.get('is_metadata_downloaded') == 1:
                if log_callback: log_callback(f"Skipped {video.get('title')} - Metadata already downloaded.")
                continue

            vid_url = video.get('url')
            if not vid_url:
                if video.get('video_id'):
                    vid_url = f"https://www.youtube.com/watch?v={video['video_id']}"
                else:
                    continue

            video['url'] = vid_url

            filepath = video.get('filepath')
            if not filepath:
                vid_type = video.get('video_type', 'Videos')
                filepath = str(target_dir / f"({handle}) {vid_type}" / f"{video.get('video_id', 'unknown')}")

            parent_dir = str(Path(filepath).parent)
            if parent_dir not in groups:
                groups[parent_dir] = []
            groups[parent_dir].append(video)

        total_videos = sum(len(group) for group in groups.values())
        processed_count = 0

        if total_videos == 0:
            if log_callback: log_callback("No videos required processing (all skipped).")
            if status_callback: status_callback("Finished", 0, 0)
            return True, "Success"

        for parent_dir, video_group in groups.items():
            ydl_opts['outtmpl'] = {'default': parent_dir + "/%(upload_date|00000000)s_%(title)s.%(ext)s"}

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    for video in video_group:
                        if stop_event and stop_event.is_set():
                            if log_callback: log_callback("Worker stopped by user.")
                            return False, "Stopped"

                        url = video['url']
                        title = video.get('title', 'video')
                        video_id = video.get('video_id')
                        filepath = video.get('filepath')

                        if log_callback:
                            log_callback(f"Extracting metadata for: {title}")

                        if status_callback:
                            status_callback(f"Extracting {title}...", processed_count, total_videos)

                        try:
                            info_dict = ydl.extract_info(url, download=True)

                            # --- NEW: Real-time DB population from memory ---
                            if info_dict:
                                duration = info_dict.get('duration', 0)
                                description = info_dict.get('description', '')
                                tags_json = json.dumps(info_dict.get('tags', []))
                                like_count = info_dict.get('like_count', 0)
                                comment_count = info_dict.get('comment_count', 0)
                                thumb_path = f"{filepath}.webp"

                                with DatabaseManager.get_connection() as conn:
                                    conn.execute("""
                                        UPDATE videos 
                                        SET is_metadata_downloaded = 1, duration = ?, description = ?, tags = ?, like_count = ?, comment_count = ?, thumb_filepath = ?
                                        WHERE video_id = ?
                                    """, (duration, description, tags_json, like_count, comment_count, thumb_path,
                                          video_id))
                                    conn.commit()

                        except Exception as e:
                            if log_callback:
                                log_callback(f"Error on {url}: {e}")

                        processed_count += 1

            except Exception as e:
                if log_callback:
                    log_callback(f"Critical System Error processing folder {parent_dir}: {str(e)}")

        if log_callback:
            log_callback(f"\n--- Finished {channel_name} ---")

        if status_callback:
            status_callback(f"Finished", total_videos, total_videos)

        return True, "Success"