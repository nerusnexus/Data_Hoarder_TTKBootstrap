import yt_dlp
import traceback
from pathlib import Path
from config import METADATA_DIR


class FetchMetadataLogger:
    """Helper class to redirect yt-dlp output to UI and a persistent file."""

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
              status_callback=None):
        """Processes a list of individual video dictionaries directly from the database."""
        target_dir = self.metadata_dir / folder_name
        target_dir.mkdir(parents=True, exist_ok=True)

        # Unique log file per channel
        log_file_path = target_dir / f"{handle} Logs.txt"

        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            # ERROR 2 FIXED: This tells yt-dlp NOT to complain if JS challenges fail for formats!
            'ignore_no_formats_error': True,
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
            'ignoreerrors': True,  # Keep going even if a video was deleted/privated
        }

        if params.get("use_cookies", True):
            ydl_opts['cookiesfrombrowser'] = ('firefox',)

        if log_callback:
            log_callback(f"\n--- Starting metadata extraction for {len(videos)} videos from {channel_name} ---")

        # ERROR 4 FIXED: We group the videos by the folder they belong to (Videos vs Shorts vs Lives)
        # Your DB already knows exactly where they should go based on their filepath!
        groups = {}
        for video in videos:
            if not video.get('url') or not video.get('filepath'):
                continue

            parent_dir = str(Path(video['filepath']).parent)
            if parent_dir not in groups:
                groups[parent_dir] = []
            groups[parent_dir].append(video)

        processed_count = 0
        total_videos = len(videos)

        for parent_dir, video_group in groups.items():
            # Dynamically set the output template for this specific folder (e.g. Shorts)
            ydl_opts['outtmpl'] = {'default': parent_dir + "/%(upload_date|00000000)s_%(title)s.%(ext)s"}

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    for video in video_group:
                        url = video['url']
                        if status_callback:
                            status_callback(f"Extracting {video.get('title', 'video')}...", processed_count,
                                            total_videos)

                        try:
                            ydl.extract_info(url, download=False)
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