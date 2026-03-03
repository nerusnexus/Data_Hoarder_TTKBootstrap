import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from pathlib import Path
import webbrowser


class VideoCard(ttk.Frame):
    def __init__(self, parent, video, thumb_dir, has_icon_font, image_queue, play_cb, reveal_cb, **kwargs):
        super().__init__(parent, bootstyle="light", **kwargs)

        card = ttk.Frame(self, padding=10, bootstyle="dark")
        card.pack(fill=BOTH, expand=True, padx=1, pady=1)

        thumb_path = None
        db_thumb = video.get("thumb_filepath")
        filepath_str = video.get("filepath")

        candidates = []
        if db_thumb:
            candidates.append(Path(db_thumb))
            candidates.append(Path(db_thumb).with_suffix('.jpg'))
        if filepath_str:
            candidates.append(Path(f"{filepath_str}.webp"))
            candidates.append(Path(f"{filepath_str}.jpg"))

        candidates.append(thumb_dir / f"{video['video_id']}.webp")
        candidates.append(thumb_dir / f"{video['video_id']}.jpg")

        for cand in candidates:
            if cand.exists():
                thumb_path = cand
                break

        img_label = ttk.Label(card, text="[No Thumbnail]", bootstyle="inverse-secondary", anchor=CENTER)
        img_label.pack(side=TOP, fill=X)

        if thumb_path:
            img_label.config(text="[Loading...]")
            image_queue.append((img_label, thumb_path))  # Queue image for async loading

        title_text = video.get("title", "Unknown Title")
        ttk.Label(card, text=title_text, font=("Segoe UI", 9, "bold"), wraplength=280, justify=LEFT).pack(
            side=TOP, anchor=NW, pady=(8, 5), fill=X)

        info_row = ttk.Frame(card, bootstyle="dark")
        info_row.pack(side=TOP, fill=X, pady=(5, 0))

        views = video.get("view_count") or 0
        date_str = video.get("upload_date", "")
        date_formatted = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}" if date_str and len(
            date_str) == 8 else "Unknown Date"

        ttk.Label(info_row, text=f"{views:,} views • {date_formatted}", font=("Segoe UI", 8), bootstyle="light").pack(
            side=LEFT)

        status_label = ttk.Label(info_row)
        status_label.pack(side=RIGHT)

        online_status_label = ttk.Label(info_row)
        online_status_label.pack(side=RIGHT, padx=(0, 5))

        is_lost = video.get("is_lost_media")

        if has_icon_font:
            status_label.config(font=("Material Symbols Rounded", 16))
            online_status_label.config(font=("Material Symbols Rounded", 16))

            if video.get("is_downloaded"):
                status_label.config(text="data_check", bootstyle="success")
            elif video.get("is_metadata_downloaded"):
                status_label.config(text="data_info_alert", bootstyle="warning")
            else:
                status_label.config(text="captive_portal", bootstyle="info")

            if is_lost == 1:
                online_status_label.config(text="cloud_alert", bootstyle="danger")
            elif is_lost == 0:
                online_status_label.config(text="cloud_done", bootstyle="success")
            else:
                online_status_label.config(text="cloud_sync", bootstyle="warning")
        else:
            if is_lost == 1:
                online_status_label.config(text="[Lost]", bootstyle="danger")
            elif is_lost == 0:
                online_status_label.config(text="[Online]", bootstyle="success")
            else:
                online_status_label.config(text="[Unchecked]", bootstyle="warning")

        btn_row = ttk.Frame(card, bootstyle="dark")
        btn_row.pack(side=TOP, fill=X, pady=(10, 0))

        if has_icon_font:
            ttk.Button(btn_row, text="public", style="Icon.info.Outline.TButton",
                       command=lambda u=video.get("url"): webbrowser.open(u) if u else None).pack(side=LEFT,
                                                                                                  padx=(0, 5))
            ttk.Button(btn_row, text="folder", style="Icon.warning.Outline.TButton",
                       command=lambda p=filepath_str: reveal_cb(p)).pack(side=LEFT, padx=5)
            ttk.Button(btn_row, text="play_arrow", style="Icon.success.Outline.TButton",
                       command=lambda p=filepath_str: play_cb(p)).pack(side=LEFT, padx=5)
        else:
            ttk.Button(btn_row, text="Browser", bootstyle="info-outline",
                       command=lambda u=video.get("url"): webbrowser.open(u) if u else None).pack(side=LEFT,
                                                                                                  padx=(0, 5))
            ttk.Button(btn_row, text="Folder", bootstyle="warning-outline",
                       command=lambda p=filepath_str: reveal_cb(p)).pack(side=LEFT, padx=5)
            ttk.Button(btn_row, text="Play", bootstyle="success-outline",
                       command=lambda p=filepath_str: play_cb(p)).pack(side=LEFT, padx=5)