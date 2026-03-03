import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.widgets.scrolled import ScrolledFrame
from ttkbootstrap.dialogs import Messagebox
from pathlib import Path
from PIL import Image, ImageTk
import os
import sys
import subprocess
import threading
from config import METADATA_DIR, FONTS_DIR
from gui.components.video_card import VideoCard


class LibraryTab(ttk.Frame):
    def __init__(self, parent, add_group_service, add_channel_service):
        super().__init__(parent)
        self.add_group_service = add_group_service
        self.add_channel_service = add_channel_service
        self.tree = None
        self.notebook = None
        self.tab_frames = {}
        self._search_timer = None
        self.check_progress_var = None
        self.check_progress = None
        self.check_status_btn = None

        self.current_videos = []
        self.search_var = ttk.StringVar()
        self.sort_by_var = ttk.StringVar(value="Date")
        self.sort_order_var = ttk.StringVar(value="Descending")
        self.image_queue = []
        self.is_loading_images = False
        self.current_thumb_dir = None

        self.has_icon_font = (FONTS_DIR / "MaterialSymbolsRounded.ttf").exists()
        if self.has_icon_font:
            style = ttk.Style()
            for color in ["primary", "secondary", "success", "info", "warning", "danger", "light", "dark"]:
                style.configure(f"Icon.{color}.Outline.TButton", font=("Material Symbols Rounded", 16))

        self.build_ui()
        self.load_tree_data()
        self.winfo_toplevel().bind("<<DataUpdated>>", self.refresh_tree, add="+")

    def build_ui(self):
        sidebar = ttk.Frame(self, width=280)
        sidebar.pack(side=LEFT, fill=Y, padx=5, pady=5)
        sidebar.pack_propagate(False)

        ttk.Label(sidebar, text="Channels", font=("Segoe UI", 10, "bold")).pack(pady=5)

        tree_frame = ttk.Frame(sidebar)
        tree_frame.pack(fill=BOTH, expand=True, pady=(0, 10))

        tree_scroll = ttk.Scrollbar(tree_frame, orient=VERTICAL)
        tree_scroll.pack(side=RIGHT, fill=Y)

        self.tree = ttk.Treeview(tree_frame, show="tree", yscrollcommand=tree_scroll.set)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        tree_scroll.config(command=self.tree.yview)
        self.tree.bind("<<TreeviewSelect>>", self.on_channel_selected)

        controls_frame = ttk.Labelframe(sidebar, text="Filters & Sorting", padding=10)
        controls_frame.pack(fill=X, side=BOTTOM, pady=5)

        ttk.Label(controls_frame, text="Search:").pack(anchor=W)
        search_entry = ttk.Entry(controls_frame, textvariable=self.search_var)
        search_entry.pack(fill=X, pady=(0, 10))
        search_entry.bind("<KeyRelease>", self.on_search_typing)

        ttk.Label(controls_frame, text="Sort by:").pack(anchor=W)
        sort_cb = ttk.Combobox(controls_frame, textvariable=self.sort_by_var, values=["Date", "Views", "Title"],
                               state="readonly")
        sort_cb.pack(fill=X, pady=(0, 5))
        sort_cb.bind("<<ComboboxSelected>>", self.on_sort_changed)

        order_cb = ttk.Combobox(controls_frame, textvariable=self.sort_order_var, values=["Ascending", "Descending"],
                                state="readonly")
        order_cb.pack(fill=X)
        order_cb.bind("<<ComboboxSelected>>", self.on_sort_changed)

        self.check_status_btn = ttk.Button(controls_frame, text="Check online status", bootstyle="info",
                                           command=self.start_online_check)
        self.check_status_btn.pack(fill=X, pady=(15, 0))

        self.check_progress_var = ttk.DoubleVar()
        self.check_progress = ttk.Progressbar(controls_frame, variable=self.check_progress_var, maximum=100,
                                              bootstyle="success")

        main_content = ttk.Frame(self)
        main_content.pack(side=RIGHT, fill=BOTH, expand=True)

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

    def refresh_tree(self, _event=None):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.load_tree_data()

    def load_tree_data(self):
        groups = self.add_group_service.get_all_groups()
        for group in groups:
            group_id = self.tree.insert("", "end", text=group, tags=("group",), open=True)
            channels = self.add_channel_service.get_channels_by_group(group)
            for channel in channels:
                self.tree.insert(group_id, "end", text=channel, tags=("channel",))

    def on_channel_selected(self, _event):
        selected = self.tree.selection()
        if not selected: return
        item = self.tree.item(selected[0])
        if "channel" not in item["tags"]: return

        channel_name = item["text"]
        self.current_videos = self.add_channel_service.get_videos_by_channel(channel_name)

        channel_info = self.add_channel_service.get_channel_details(channel_name)
        cid = channel_info.get("channel_id")
        handle = channel_info.get("handle")
        folder_name = f"{cid} ({handle})" if handle and handle != cid else cid
        self.current_thumb_dir = METADATA_DIR / folder_name / "Videos"

        self.apply_filters_and_render()

    def on_search_typing(self, _event=None):
        if self._search_timer is not None:
            self.after_cancel(self._search_timer)
        self._search_timer = self.after(1000, lambda: self.apply_filters_and_render()) # type: ignore

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

            # Use the new Component!
            card = VideoCard(self.tab_frames[v_type], video, self.current_thumb_dir, self.has_icon_font,
                             self.image_queue, self.play_video, self.reveal_file)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            counters[v_type] += 1

        if not self.is_loading_images:
            self.process_image_queue()

    def start_online_check(self):
        if not self.current_videos:
            return

        self.check_status_btn.config(state="disabled", text="Checking...")
        self.check_progress.pack(fill=X, pady=(5, 0))
        self.check_progress_var.set(0)

        threading.Thread(target=self._run_online_check, daemon=True).start()

    def _run_online_check(self):
        def update_progress(current, total):
            pct = (current / total) * 100
            self.winfo_toplevel().after(0, self.check_progress_var.set, pct)

        self.add_channel_service.check_videos_online_status(self.current_videos, progress_callback=update_progress)
        self.winfo_toplevel().after(0, self._finish_online_check) # type: ignore

    def _finish_online_check(self):
        self.check_progress.pack_forget()
        self.check_status_btn.config(state="normal", text="Check online status")

        selected = self.tree.selection()
        if selected:
            channel_name = self.tree.item(selected[0])["text"]
            self.current_videos = self.add_channel_service.get_videos_by_channel(channel_name)
            self.apply_filters_and_render()

    @staticmethod
    def reveal_file(filepath_str):
        if not filepath_str:
            Messagebox.show_warning("Not Found", "Video file not found in database.")
            return

        target = Path(f"{filepath_str}.info.json")
        if not target.exists():
            target = Path(f"{filepath_str}.webp")
            if not target.exists():
                target = Path(filepath_str).parent

        if not target.exists():
            Messagebox.show_warning("Not Found", "Files have not been downloaded yet.")
            return

        if sys.platform.startswith("win"):
            if target.is_file():
                subprocess.run(["explorer", "/select,", str(target)])
            else:
                os.startfile(target)
        elif sys.platform == "darwin":
            if target.is_file():
                subprocess.run(["open", "-R", str(target)])
            else:
                subprocess.run(["open", str(target)])
        else:
            subprocess.run(["xdg-open", str(target.parent if target.is_file() else target)])

    @staticmethod
    def open_local_path(path):
        if not path or not path.exists():
            Messagebox.show_warning("Not Found", "File does not exist yet.")
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
        except OSError:  # Fixed broad exception and unused 'e'
            pass

        self.after(5, self.process_image_queue)  # type: ignore