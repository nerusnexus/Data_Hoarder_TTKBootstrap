import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from pathlib import Path
from PIL import Image, ImageTk
from datetime import datetime


class LibraryTab(ttk.Frame):
    def __init__(self, parent, services):
        super().__init__(parent)
        self.services = services
        self.tree = None
        self.library_label = None
        self.notebook = None
        self.tab_frames = {}
        self._search_timer = None

        # State variables
        self.current_videos = []  # Holds the raw list from DB
        self.search_var = ttk.StringVar()
        self.sort_by_var = ttk.StringVar(value="Date")
        self.sort_order_var = ttk.StringVar(value="Descending")
        self.image_queue = []
        self.is_loading_images = False

        self.build_ui()
        self.load_tree_data()

    def build_ui(self):
        # --- LEFT SIDEBAR ---
        sidebar = ttk.Frame(self, width=290)
        sidebar.pack(side=LEFT, fill=Y, padx=5, pady=5)
        sidebar.pack_propagate(False)

        ttk.Label(sidebar, text="Channels", font=("Segoe UI", 10, "bold")).pack(pady=5)
        self.tree = ttk.Treeview(sidebar, show="tree")
        self.tree.pack(fill=BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_channel_selected)

        # --- RIGHT MAIN AREA ---
        main_content = ttk.Frame(self)
        main_content.pack(side=RIGHT, fill=BOTH, expand=True)

        # 1. Header Label
        self.library_label = ttk.Label(
            main_content,
            text="Select a channel to view library",
            font=("Segoe UI", 12)
        )
        self.library_label.pack(pady=(10, 5))

        # 2. Filter & Sort Controls
        controls_frame = ttk.Frame(main_content)
        controls_frame.pack(fill=X, padx=10, pady=5)

        # Search Bar
        ttk.Label(controls_frame, text="Search:").pack(side=LEFT, padx=(0, 5))
        search_entry = ttk.Entry(controls_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=LEFT)
        search_entry.bind("<KeyRelease>", self.on_search_typing)  # CHANGED

        # Spacer
        ttk.Frame(controls_frame).pack(side=LEFT, fill=X, expand=True)

        # Sort Order (Asc/Desc)
        order_cb = ttk.Combobox(
            controls_frame,
            textvariable=self.sort_order_var,
            values=["Ascending", "Descending"],
            state="readonly",
            width=10
        )
        order_cb.pack(side=RIGHT, padx=5)
        order_cb.bind("<<ComboboxSelected>>", self.on_sort_changed)  # CHANGED

        # Sort By Type
        ttk.Label(controls_frame, text="Sort by:").pack(side=RIGHT, padx=(10, 5))
        sort_cb = ttk.Combobox(
            controls_frame,
            textvariable=self.sort_by_var,
            values=["Date", "Views", "Title"],
            state="readonly",
            width=10
        )
        sort_cb.pack(side=RIGHT)
        sort_cb.bind("<<ComboboxSelected>>", self.on_sort_changed)  # CHANGED

        # 3. Notebook with ScrolledFrames
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

    def on_channel_selected(self, event):
        selected = self.tree.selection()
        if not selected: return

        item = self.tree.item(selected[0])
        if "channel" not in item["tags"]: return

        channel_name = item["text"]
        self.library_label.config(text=f"Library: {channel_name}")

        # 1. Fetch from DB
        self.current_videos = self.services.add_channel.get_videos_by_channel(channel_name)

        # 2. Get Metadata Path (for thumbnails)
        channel_info = self.services.add_channel.get_channel_details(channel_name)
        cid = channel_info.get("channel_id")
        handle = channel_info.get("handle")
        folder_name = f"{cid} ({handle})" if handle and handle != cid else cid
        self.current_thumb_dir = self.services.metadata_folder / folder_name / "Videos"

        # 3. Apply Filters & Render
        self.apply_filters_and_render()

    def on_search_typing(self, event=None):
        """Debounces the search bar so it only renders AFTER the user stops typing."""
        # 1. Cancel the previous timer if the user is still typing
        if self._search_timer is not None:
            self.after_cancel(self._search_timer)

        # 2. Set a new timer to update the UI after 400 milliseconds
        self._search_timer = self.after(1000, self.apply_filters_and_render)

    def on_sort_changed(self, event=None):
        """Updates immediately when a combobox is clicked."""
        if self.current_videos:
            self.apply_filters_and_render()

    def apply_filters_and_render(self):
        # --- 1. Clear Tabs ---
        for sf in self.tab_frames.values():
            for child in sf.winfo_children():
                child.destroy()
            sf.update_idletasks()
            sf.container.event_generate("<Configure>")

        # --- 2. Filter (Search) ---
        query = self.search_var.get().lower()
        filtered_videos = [
            v for v in self.current_videos
            if query in v.get("title", "").lower()
        ]

        # --- 3. Sort ---
        sort_key = self.sort_by_var.get()
        reverse_order = (self.sort_order_var.get() == "Descending")

        if sort_key == "Views":
            filtered_videos.sort(key=lambda x: x.get("view_count") or 0, reverse=reverse_order)
        elif sort_key == "Title":
            filtered_videos.sort(key=lambda x: x.get("title", "").lower(), reverse=reverse_order)
        else:  # Date
            # Handle YYYYMMDD sorting string safely
            filtered_videos.sort(key=lambda x: x.get("upload_date") or "00000000", reverse=reverse_order)

        # --- 4. Render ---
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
        thumb_path = thumb_dir / f"{video['video_id']}.jpg"
        img_label = ttk.Label(card, text="[Loading...]", bootstyle="inverse-secondary", anchor=CENTER)
        img_label.pack(side=TOP, fill=X)

        if thumb_path.exists():
            # Em vez de carregar a imagem agora, joga para a fila!
            self.image_queue.append((img_label, thumb_path))
        img_label.pack(side=TOP, fill=X)

        # 2. Title
        title_text = video.get("title", "Unknown Title")
        ttk.Label(
            card,
            text=title_text,
            font=("Segoe UI", 9, "bold"),
            wraplength=280,
            justify=LEFT
        ).pack(side=TOP, anchor=NW, pady=(8, 5), fill=X)

        # 3. Info Row
        info_row = ttk.Frame(card, bootstyle="secondary")
        info_row.pack(side=TOP, fill=X, pady=(5, 0))

        # Views & Date
        views = video.get("view_count") or 0
        date_str = video.get("upload_date", "")

        # Format Date: 20231225 -> 2023-12-25
        if date_str and len(date_str) == 8:
            date_formatted = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        else:
            date_formatted = "Unknown Date"

        info_text = f"{views:,} views • {date_formatted}"

        ttk.Label(
            info_row,
            text=info_text,
            font=("Segoe UI", 8),
            bootstyle="light"
        ).pack(side=LEFT)

        # Status Icon
        status_sym = "✅" if video.get("is_downloaded") else "🌐"
        ttk.Label(
            info_row,
            text=status_sym,
            font=("Segoe UI", 10)
        ).pack(side=RIGHT)

    def process_image_queue(self):
        """Carrega uma imagem por vez para não travar a interface"""
        if not self.image_queue:
            self.is_loading_images = False
            return

        self.is_loading_images = True
        label, path = self.image_queue.pop(0)  # Pega a primeira imagem da fila

        try:
            # Só carrega se o usuário não tiver mudado de canal (label ainda existe)
            if label.winfo_exists():
                img = Image.open(path).resize((300, 169))
                photo = ImageTk.PhotoImage(img)
                label.config(image=photo, text="")
                label.image = photo
        except:
            pass

        # Chama a próxima imagem da fila em 5 milissegundos
        self.after(5, self.process_image_queue)
