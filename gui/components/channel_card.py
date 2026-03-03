import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import webbrowser
from PIL import Image
from config import METADATA_DIR, VIDEOS_DIR
from gui.components.responsive_image import ResponsiveImage


def format_number(num):
    """Formats large numbers into readable K, M, B formats."""
    try:
        num = int(num)
    except (ValueError, TypeError):
        return "0"

    if num == 0: return "0"
    if num >= 1_000_000_000: return f"{num / 1_000_000_000:.1f}B".replace(".0B", "B")
    if num >= 1_000_000: return f"{num / 1_000_000:.1f}M".replace(".0M", "M")
    if num >= 1_000: return f"{num / 1_000:.1f}K".replace(".0K", "K")
    return str(num)


class ChannelCard(ttk.Frame):
    def __init__(self, parent, channel_info, add_channel_service, has_icon_font, open_dir_callback, **kwargs):
        super().__init__(parent, bootstyle="light", **kwargs)

        card = ttk.Frame(self, bootstyle="dark", padding=10)
        card.pack(fill=BOTH, expand=True, padx=1, pady=1)

        card.columnconfigure(0, weight=2, uniform="card_cols")
        card.columnconfigure(1, weight=12, uniform="card_cols")

        cid = channel_info.get("channel_id")
        handle = channel_info.get("handle", "")
        safe_handle = handle if handle.startswith('@') else f"@{handle}"
        folder_name = f"{cid} ({handle})" if handle and handle != cid else cid

        local_metadata_path = METADATA_DIR / folder_name
        local_videos_path = VIDEOS_DIR / folder_name

        profile_img_path = local_metadata_path / f"profile ({safe_handle}).jpg"
        banner_img_path = local_metadata_path / f"banner ({safe_handle}).jpg"

        # --- LEFT SIDE: Profile Picture ---
        left_container = ttk.Frame(card, bootstyle="dark")
        left_container.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        pfp_border = ttk.Frame(left_container, bootstyle="light")
        pfp_border.pack(fill=X, anchor=N)

        if profile_img_path.exists():
            try:
                img = Image.open(profile_img_path).convert("RGBA")
                pfp_canvas = ResponsiveImage(pfp_border, img, aspect_ratio=1.0, bg_color="#222")
                pfp_canvas.pack(fill=BOTH, expand=True, padx=1, pady=1)
            except OSError:  # Fixed broad exception
                pass
        else:
            pfp_label = ttk.Label(pfp_border, text="account_circle" if has_icon_font else "👤",
                                  font=("Material Symbols Rounded", 48) if has_icon_font else ("Segoe UI", 36),
                                  bootstyle="inverse-dark", anchor=CENTER)
            pfp_label.pack(fill=BOTH, expand=True, padx=1, pady=1, ipady=30)

        # --- RIGHT SIDE: Banner and Content ---
        right_container = ttk.Frame(card, bootstyle="dark")
        right_container.grid(row=0, column=1, sticky="nsew")

        banner_border = ttk.Frame(right_container, bootstyle="light")
        banner_border.pack(side=TOP, fill=X, anchor=NW)

        if banner_img_path.exists():
            try:
                img = Image.open(banner_img_path).convert("RGBA")
                banner_ratio = 1100 / 150.0
                banner_canvas = ResponsiveImage(banner_border, img, aspect_ratio=banner_ratio, bg_color="#222")
                banner_canvas.pack(fill=BOTH, expand=True, padx=1, pady=1)
            except OSError:  # Fixed broad exception
                pass
        else:
            banner_label = ttk.Label(banner_border, text="[No Banner Found]", font=("Segoe UI", 8), anchor=CENTER,
                                     bootstyle="inverse-dark")
            banner_label.pack(fill=BOTH, expand=True, padx=1, pady=1, ipady=40)

        content_frame = ttk.Frame(right_container, bootstyle="dark")
        content_frame.pack(side=TOP, fill=BOTH, expand=True, pady=(10, 0))
        content_frame.columnconfigure(0, weight=1, uniform="content_cols")
        content_frame.columnconfigure(1, weight=1, uniform="content_cols")

        name = channel_info.get("name", "Unknown")
        url = channel_info.get("url", "")
        subs_formatted = format_number(channel_info.get("follower_count", 0))

        videos = add_channel_service.get_videos_by_channel(name)
        v_count = sum(1 for v in videos if v.get("video_type") == "Videos")
        s_count = sum(1 for v in videos if v.get("video_type") == "Shorts")
        l_count = sum(1 for v in videos if v.get("video_type") == "Lives")

        creation_date = channel_info.get("creation_date") or ""
        date_str = "Unknown"
        if creation_date and len(str(creation_date)) == 8:
            date_str = f"{str(creation_date)[6:8]}/{str(creation_date)[4:6]}/{str(creation_date)[0:4]}"

        country = channel_info.get("country") or "Unknown"
        views_formatted = format_number(channel_info.get("view_count") or 0)

        # ====== COLUMN 1: STATS ======
        stats_frame = ttk.Frame(content_frame, bootstyle="dark")
        stats_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ttk.Label(stats_frame, text=f"{name} ({safe_handle})", font=("Segoe UI", 12, "bold"), bootstyle="light").pack(
            anchor=W)
        ttk.Label(stats_frame, text=f"{subs_formatted} subs • {v_count} Videos • {s_count} Shorts • {l_count} Lives",
                  font=("Segoe UI", 9), bootstyle="light").pack(anchor=W, pady=(2, 0))
        ttk.Label(stats_frame, text=f"Since {date_str} • {country} • {views_formatted} views",
                  font=("Segoe UI", 8), bootstyle="secondary").pack(anchor=W, pady=(0, 10))

        btn_frame = ttk.Frame(stats_frame, bootstyle="dark")
        btn_frame.pack(anchor=W)

        if has_icon_font:
            ttk.Button(btn_frame, text="public", style="Icon.TButton", bootstyle="outline-light",
                       command=lambda u=url: webbrowser.open(u)).pack(side=LEFT, padx=(0, 5))
            ttk.Button(btn_frame, text="folder", style="Icon.TButton", bootstyle="outline-light",
                       command=lambda p=local_videos_path: open_dir_callback(p)).pack(side=LEFT)
        else:
            ttk.Button(btn_frame, text="Web", bootstyle="outline-light", command=lambda u=url: webbrowser.open(u)).pack(
                side=LEFT, padx=(0, 5))
            ttk.Button(btn_frame, text="Dir", bootstyle="outline-light",
                       command=lambda p=local_videos_path: open_dir_callback(p)).pack(side=LEFT)

        # ====== COLUMN 2: DESCRIPTION ======
        desc_frame = ttk.Frame(content_frame, bootstyle="dark")
        desc_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        ttk.Label(desc_frame, text="Description:", font=("Segoe UI", 9, "bold"), bootstyle="light").pack(anchor=W,
                                                                                                         pady=(0, 2))

        desc_str = channel_info.get("description") or "No description available."
        desc_text = ttk.Text(desc_frame, height=4, wrap="word", font=("Segoe UI", 8), background="#222",
                             foreground="#eee", borderwidth=0, highlightthickness=0)
        desc_text.pack(fill=X, pady=2)
        desc_text.insert("1.0", desc_str)
        desc_text.configure(state="disabled")