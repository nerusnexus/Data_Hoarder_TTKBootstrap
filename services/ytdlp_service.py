import typing
from yt_dlp import YoutubeDL


class YtDlpService:
    def __init__(self):
        pass

    @staticmethod
    def fetch_channel_public_info(channel_input: str) -> dict:
        """Fetches flat metadata for a channel to be used in the My Account tab."""
        channel_input = channel_input.strip()

        if not channel_input.startswith("http"):
            channel_input = channel_input.lstrip("@")
            channel_input = f"https://www.youtube.com/@{channel_input}"

        opts: dict[str, typing.Any] = {
            "quiet": True,
            "skip_download": True,
            "extract_flat": True,
            "js_runtimes": {"deno": {"path": None}},
            "remote_components": ["ejs:github"] # <--- NEW FIX
        }

        with YoutubeDL(opts) as ydl:  # type: ignore
            raw_info = ydl.extract_info(channel_input, download=False)
            info = dict(raw_info) if raw_info else {}

        return {
            "url": channel_input,
            "title": info.get("title"),
            "uploader_id": info.get("uploader_id"),
            "handle": info.get("uploader_id") or info.get("id"),
            "channel_id": info.get("channel_id"),
            "subscriber_count": info.get("subscriber_count", "Hidden"),
            "video_count": info.get("video_count", "Unknown")
        }