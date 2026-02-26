import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.widgets.scrolled import ScrolledFrame
from ttkbootstrap.dialogs import Messagebox
from pathlib import Path
from PIL import Image, ImageTk
import webbrowser
import os
import sys
import subprocess
from config import METADATA_DIR


class LibraryTab(ttk.Frame):
    def __init__(self, parent, services):
        super().__init__(parent)
        self.services = services
        self.tree = None
        self.library_label = None
        self.notebook = None
        self.tab_frames = {}
        self._search_timer = None

        self.current_videos = []
        self.search_var = ttk.StringVar()
        self.sort_by_var = ttk.StringVar(value="Date")
        self.sort_order_var = ttk.StringVar(value="Descending")
        self.image_queue = []
        self.is_loading_images = False
        self.current_thumb_dir = None

        self.build_ui()
        self.load_tree_data()

    def build_ui(self):
        sidebar = ttk.Frame(self, width=290)
        sidebar.pack(side=LEFT, fill=Y, padx=5, pady=5)
        sidebar.pack_propagate(False)

        ttk.Label(sidebar, text="Channels", font=("Segoe UI", 10, "bold")).pack(pady=5)
        self.tree = ttk.Treeview(sidebar, show="tree")
        self.tree.pack(fill=BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_channel_selected)

        main_content = ttk.Frame(self)
        main_content.pack(side=RIGHT, fill=BOTH, expand=True)

        self.library_label = ttk.Label(main_content, text="Select a channel to view library", font=("Segoe UI", 12))
        self.library_label.pack(pady=(10, 5))

        controls_frame = ttk.Frame(main_content)
        controls_frame.pack(fill=X, padx=10, pady=5)

        ttk.Label(controls_frame, text="Search:").pack(side=LEFT, padx=(0, 5))
        search_entry = ttk.Entry(controls_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=LEFT)
        search_entry.bind("<KeyRelease>", self.on_search_typing)

        ttk.Frame(controls_frame).pack(side=LEFT, fill=X, expand=True)

        order_cb = ttk.Combobox(controls_frame, textvariable=self.sort_order_var, values=["Ascending", "Descending"],
                                state="readonly", width=10)
        order_cb.pack(side=RIGHT, padx=5)
        order_cb.bind("<<ComboboxSelected>>", self.on_sort_changed)

        ttk.Label(controls_frame, text="Sort by:").pack(side=RIGHT, padx=(10, 5))
        sort_cb = ttk.Combobox(controls_frame, textvariable=self.sort_by_var, values=["Date", "Views", "Title"],
                               state="readonly", width=10)
        sort_cb.pack(side=RIGHT)
        sort_cb.bind("<<ComboboxSelected>>", self.on_sort_changed)

        self.notebook = ttk.Notebook(main_content)
        self.notebook.pack(fill=BOTH, expand=True, padx=10, pady=10)

        for tab_name in ["Videos", "Shorts", "Lives"]:
            tab_frame = ttk.Frame(self.notebook)
            self.notebook.add(tab_frame, text=tab_name)
            sf = ScrolledFrame(tab_frame, autohide=True)
            sf.pack(fill=BOTH, expand=True)
            for i in range(3):
                sf.columnconfigure(i, weight=1)
            self.tab_frames[tab_name] = sf

    def load_tree_data(self):
        groups = self.services.add_group.get_all_groups()
        for group in groups:
            group_id = self.tree.insert("", "end", text=group, tags=("group",), open=True)
            channels = self.services.add_channel.get_channels_by_group(group)
            for channel in channels:
                self.tree.insert(group_id, "end", text=channel, tags=("channel",))

    def on_channel_selected(self, _event):
        selected = self.tree.selection()
        if not selected: return
        item = self.tree.item(selected[0])
        if "channel" not in item["tags"]: return

        channel_name = item["text"]
        self.library_label.config(text=f"Library: {channel_name}")
        self.current_videos = self.services.add_channel.get_videos_by_channel(channel_name)

        # Fallback thumb dir (in case the new filepath structure fails)
        channel_info = self.services.add_channel.get_channel_details(channel_name)
        cid = channel_info.get("channel_id")
        handle = channel_info.get("handle")
        folder_name = f"{cid} ({handle})" if handle and handle != cid else cid
        self.current_thumb_dir = METADATA_DIR / folder_name / "Videos"

        self.apply_filters_and_render()

    def on_search_typing(self, _event=None):
        if self._search_timer is not None:
            self.after_cancel(self._search_timer)
        self._search_timer = self.after(1000, lambda: self.apply_filters_and_render())  # type: ignore

    def on_sort_changed(self, _event=None):
        if self.current_videos:
            self.apply_filters_and_render()

    def apply_filters_and_render(self):
        for sf in self.tab_frames.values():
            for child in sf.winfo_children():
                child.destroy()
            sf.update_idletasks()
            sf.container.event_generate("<Configure>")

        query = self.search_var.get().lower()
        filtered_videos = [v for v in self.current_videos if query in v.get("title", "").lower()]

        sort_key = self.sort_by_var.get()
        reverse_order = (self.sort_order_var.get() == "Descending")

        if sort_key == "Views":
            filtered_videos.sort(key=lambda x: x.get("view_count") or 0, reverse=reverse_order)
        elif sort_key == "Title":
            filtered_videos.sort(key=lambda x: x.get("title", "").lower(), reverse=reverse_order)
        else:
            filtered_videos.sort(key=lambda x: x.get("upload_date") or "00000000", reverse=reverse_order)

        counters = {"Videos": 0, "Shorts": 0, "Lives": 0}

        for video in filtered_videos:
            v_type = video.get("video_type", "Videos")
            if v_type not in self.tab_frames: v_type = "Videos"
            row, col = divmod(counters[v_type], 3)
            self.create_video_card(self.tab_frames[v_type], video, self.current_thumb_dir, row, col)
            counters[v_type] += 1

        if not self.is_loading_images:
            self.process_image_queue()

    def create_video_card(self, parent, video, thumb_dir, row, col):
        card = ttk.Frame(parent, padding=10, bootstyle="secondary")
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        # 1. Thumbnail Placeholder
        filepath_str = video.get("filepath")
        if filepath_str:
            thumb_path = Path(f"{filepath_str}.jpg")
        else:
            thumb_path = thumb_dir / f"{video['video_id']}.jpg"

        # Defaults to No Thumbnail unless the image file exists
        img_label = ttk.Label(card, text="[No Thumbnail]", bootstyle="inverse-secondary", anchor=CENTER)
        img_label.pack(side=TOP, fill=X)

        if thumb_path.exists():
            img_label.config(text="[Loading...]")
            self.image_queue.append((img_label, thumb_path))

        # 2. Title
        title_text = video.get("title", "Unknown Title")
        ttk.Label(card, text=title_text, font=("Segoe UI", 9, "bold"), wraplength=280, justify=LEFT).pack(side=TOP,
                                                                                                          anchor=NW,
                                                                                                          pady=(8, 5),
                                                                                                          fill=X)

        # 3. Info Row
        info_row = ttk.Frame(card, bootstyle="secondary")
        info_row.pack(side=TOP, fill=X, pady=(5, 0))

        views = video.get("view_count") or 0
        date_str = video.get("upload_date", "")
        date_formatted = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}" if date_str and len(
            date_str) == 8 else "Unknown Date"

        ttk.Label(info_row, text=f"{views:,} views • {date_formatted}", font=("Segoe UI", 8), bootstyle="light").pack(
            side=LEFT)
        status_sym = "✅" if video.get("is_downloaded") else "🌐"
        ttk.Label(info_row, text=status_sym, font=("Segoe UI", 10)).pack(side=RIGHT)

        # 4. Buttons Row
        btn_row = ttk.Frame(card, bootstyle="secondary")
        btn_row.pack(side=TOP, fill=X, pady=(10, 0))

        ttk.Button(
            btn_row, text="Folder", bootstyle="outline",
            command=lambda p=filepath_str: self.open_local_path(Path(p).parent if p else None)
        ).pack(side=LEFT, padx=(0, 5))

        ttk.Button(
            btn_row, text="Browser", bootstyle="outline",
            command=lambda u=video.get("url"): webbrowser.open(u) if u else None
        ).pack(side=LEFT, padx=5)

        ttk.Button(
            btn_row, text="Play", bootstyle="outline",
            command=lambda p=filepath_str: self.play_video(p)
        ).pack(side=LEFT, padx=5)

    @staticmethod
    def open_local_path(path):
        if not path or not path.exists():
            Messagebox.show_warning("Not Found", "Folder does not exist yet. You might need to download files first.")
            return
        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.run(["open", path])
        else:
            subprocess.run(["xdg-open", path])

    def play_video(self, base_path_str):
        if not base_path_str:
            Messagebox.show_warning("Not Found", "Video file not found in database.")
            return

        base_path = Path(base_path_str)
        dir_path = base_path.parent
        name_pattern = base_path.name + ".*"

        if dir_path.exists():
            for file in dir_path.glob(name_pattern):
                if file.suffix.lower() in ['.mp4', '.mkv', '.webm', '.avi', '.mov']:
                    self.open_local_path(file)
                    return

        Messagebox.show_warning("Not Found", "Video media file not found on disk.\nHave you downloaded it yet?")

    def process_image_queue(self):
        if not self.image_queue:
            self.is_loading_images = False
            return

        self.is_loading_images = True
        label, path = self.image_queue.pop(0)

        try:
            if label.winfo_exists():
                img = Image.open(path).resize((300, 169))
                photo = ImageTk.PhotoImage(img)
                label.config(image=photo, text="")
                label.image = photo
        except Exception as e: # Silently log thumbnail errors instead of crashing the UI loop
            print(f"Failed to load thumbnail from {path}: {e}")

        self.after(5, self.process_image_queue)  # type: ignore