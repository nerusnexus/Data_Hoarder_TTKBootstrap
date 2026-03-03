import yt_dlp
from pathlib import Path
from datetime import datetime, timedelta
from config import METADATA_DIR
from services.db.db_manager import DatabaseManager


class DownloadLogger:
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


class DlpDownloadService:
    def __init__(self):
        self.metadata_dir = METADATA_DIR

    def fetch(self, videos: list, channel_name: str, params: dict, folder_name: str, handle: str, log_callback=None,
              status_callback=None, stop_event=None):
        target_dir = self.metadata_dir / folder_name
        target_dir.mkdir(parents=True, exist_ok=True)
        log_file_path = target_dir / f"{handle} Download_Logs.txt"

        js_runtimes = {'deno': {'path': None}}
        skip_mode = params.get("skip_mode", "Skip already downloaded")

        # Parse Resolution Limit
        raw_format = params.get("format", "bestvideo+bestaudio/best")
        max_res = params.get("max_res", "2160p").replace('p', '')

        # Inject height filter dynamically if using the standard bestvideo selector
        if "bestvideo+bestaudio" in raw_format and "[" not in raw_format:
            final_format = f"bestvideo[height<={max_res}]+bestaudio/best"
        else:
            final_format = raw_format

        # Parse Rate Limit (-r)
        rate_limit_str = params.get("-r", "8M")
        rate_limit_bytes = None
        if rate_limit_str != "No Limit":
            try:
                if rate_limit_str.endswith("M"):
                    rate_limit_bytes = float(rate_limit_str[:-1]) * 1024 * 1024
                elif rate_limit_str.endswith("K"):
                    rate_limit_bytes = float(rate_limit_str[:-1]) * 1024
                else:
                    rate_limit_bytes = float(rate_limit_str)
            except Exception:
                rate_limit_bytes = None

        # Fetch embedding parameters
        embed_metadata = params.get("embed_metadata", True)
        embed_chapters = params.get("embed_chapters", True)
        embed_infojson = params.get("embed_info_json", True)
        embed_thumbnail = params.get("embed_thumbnail", True)

        ydl_opts = {
            'quiet': True,
            'skip_download': False,
            'ignore_no_formats_error': True,
            'js_runtimes': js_runtimes,
            'remote_components': ['ejs:github'],

            'format': final_format,
            'merge_output_format': params.get("container", "mkv"),

            # These must be True so yt-dlp fetches them temporarily to embed them.
            'writeinfojson': embed_infojson,
            'writethumbnail': embed_thumbnail,
            'writedescription': False,  # Description gets embedded via FFmpegMetadata, no standalone file needed

            # This is the magic flag! It forces yt-dlp to delete the .info.json after embedding
            'clean_infojson': True,

            'sleep_interval': int(params.get("--sleep-interval", 5)),
            'max_sleep_interval': int(params.get("--max-sleep-interval", 15)),
            'sleep_interval_requests': int(params.get("--sleep-requests", 1)),
            'retries': int(params.get("--retries", 10)),
            'fragment_retries': int(params.get("--fragment-retries", 10)),

            'concurrent_fragment_downloads': int(params.get("-N", 4)),
            'ratelimit': rate_limit_bytes,

            'logger': DownloadLogger(log_callback, log_file_path),
            'ignoreerrors': True,
            'postprocessors': []
        }

        # Apply FFmpeg postprocessors for embedding metadata, chapters, and info.json inside the media container
        if embed_metadata or embed_chapters or embed_infojson:
            ydl_opts['postprocessors'].append({
                'key': 'FFmpegMetadata',
                'add_chapters': embed_chapters,
                'add_metadata': embed_metadata,
                'add_infojson': embed_infojson,
            })

        # Apply Thumbnail embedding (EmbedThumbnail automatically deletes the thumbnail after processing)
        if embed_thumbnail:
            ydl_opts['postprocessors'].append({
                'key': 'EmbedThumbnail',
                'already_have_thumbnail': False,
            })

        if params.get("use_cookies", True):
            ydl_opts['cookiesfrombrowser'] = ('firefox',)

        if log_callback:
            log_callback(f"\n--- Starting media download for {len(videos)} videos from {channel_name} ---")

        # Threshold date for Re-Fetch policy
        now = datetime.now()
        threshold_date = None

        if skip_mode == "Download 1 week old":
            threshold_date = now - timedelta(days=7)
        elif skip_mode == "Download 1 month old":
            threshold_date = now - timedelta(days=30)
        elif skip_mode == "Download 1 year old":
            threshold_date = now - timedelta(days=365)

        groups = {}
        for video in videos:
            is_downloaded = video.get('is_downloaded') == 1
            last_fetch_str = video.get('last_download_date')

            should_skip = False
            if is_downloaded:
                if skip_mode == "Skip already downloaded":
                    should_skip = True
                elif threshold_date and last_fetch_str:
                    try:
                        last_fetch = datetime.fromisoformat(last_fetch_str)
                        if last_fetch > threshold_date:
                            should_skip = True  # Too recent, skip it
                    except ValueError:
                        should_skip = False  # Bad date data, force re-download
                elif threshold_date and not last_fetch_str:
                    # If we don't have a specific download date stored but it's marked as downloaded,
                    # we do not skip so it establishes a fetch date this time.
                    should_skip = False

            if should_skip:
                if log_callback: log_callback(f"Skipped {video.get('title')} - Media is up to date.")
                continue

            vid_url = video.get('url')
            if not vid_url:
                if video.get('video_id'):
                    vid_url = f"https://www.youtube.com/watch?v={video['video_id']}"
                else:
                    continue

            video['url'] = vid_url

            # Force all videos straight into the (Handle) Videos folder.
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
            if log_callback: log_callback("No videos required downloading (all skipped).")
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

                        if log_callback:
                            log_callback(f"Downloading Media: {title}")

                        if status_callback:
                            status_callback(f"Downloading {title}...", processed_count, total_videos)

                        try:
                            # Setting download=True pulls the actual heavy media file based on format!
                            ydl.extract_info(url, download=True)

                            # --- Update Database to show MEDIA is downloaded ---
                            with DatabaseManager.get_connection() as conn:
                                fetch_date_iso = datetime.now().isoformat()
                                try:
                                    conn.execute("""
                                        UPDATE videos SET is_downloaded = 1, last_download_date = ? WHERE video_id = ?
                                    """, (fetch_date_iso, video_id))
                                except Exception:
                                    # Fallback if the last_download_date column doesn't exist in the database yet
                                    conn.execute("""
                                        UPDATE videos SET is_downloaded = 1 WHERE video_id = ?
                                    """, (video_id,))
                                conn.commit()

                            if log_callback:
                                log_callback(f"SUCCESS: Completed {title} and cleaned up temp files.")

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