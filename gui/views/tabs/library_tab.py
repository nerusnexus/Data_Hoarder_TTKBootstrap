import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from pathlib import Path
from PIL import Image, ImageTk


class LibraryTab(ttk.Frame):
    def __init__(self, parent, services):
        super().__init__(parent)
        self.services = services
        self.tree = None
        self.library_label = None
        self.notebook = None
        self.tab_frames = {}

        self.build_ui()
        self.load_tree_data()

    def build_ui(self):
        # Left sidebar for selection
        sidebar = ttk.Frame(self, width=290)
        sidebar.pack(side=LEFT, fill=Y, padx=5, pady=5)
        sidebar.pack_propagate(False)

        ttk.Label(sidebar, text="Channels", font=("Segoe UI", 10, "bold")).pack(pady=5)
        self.tree = ttk.Treeview(sidebar, show="tree")
        self.tree.pack(fill=BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_channel_selected)

        # Right area for the main content
        main_content = ttk.Frame(self)
        main_content.pack(side=RIGHT, fill=BOTH, expand=True)

        # Keep the label above the notebook to indicate the selected channel
        self.library_label = ttk.Label(
            main_content,
            text="Select a channel to view library",
            font=("Segoe UI", 12)
        )
        self.library_label.pack(pady=10)

        # Create the Notebook
        self.notebook = ttk.Notebook(main_content)
        self.notebook.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Create tabs
        for tab_name in ["Videos", "Shorts", "Lives"]:
            # 1. Create a standard frame as the direct notebook child
            tab_frame = ttk.Frame(self.notebook)
            self.notebook.add(tab_frame, text=tab_name)

            # 2. Put the ScrolledFrame inside the standard tab frame
            sf = ScrolledFrame(tab_frame, autohide=True)
            sf.pack(fill=BOTH, expand=True)

            # 3. Configure columns directly on the ScrolledFrame
            for i in range(3):
                sf.columnconfigure(i, weight=1)

            # 4. Store the ScrolledFrame for later use
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
        self.display_videos(channel_name)

    def display_videos(self, channel_name):
        # Clear all tabs safely
        for sf in self.tab_frames.values():
            for child in sf.winfo_children():
                child.destroy()
            # Force scrollbar reset
            sf.update_idletasks()
            sf.container.event_generate("<Configure>")

        channel_info = self.services.add_channel.get_channel_details(channel_name)
        videos = self.services.add_channel.get_videos_by_channel(channel_name)

        if not channel_info or not videos: return

        cid = channel_info.get("channel_id")
        handle = channel_info.get("handle")
        folder_name = f"{cid} ({handle})" if handle and handle != cid else cid
        thumb_dir = self.services.metadata_folder / folder_name / "Videos"

        # Track positions for each tab independently
        counters = {"Videos": 0, "Shorts": 0, "Lives": 0}

        for video in videos:
            v_type = "Videos" # Default

            # Categorize based on metadata
            live_status = video.get("live_status")
            if live_status in ["is_live", "was_live", "is_upcoming"]:
                v_type = "Lives"
            else:
                url = video.get("original_url", "") or video.get("webpage_url", "")
                if "/shorts/" in url:
                    v_type = "Shorts"

            # Fallback to Videos tab if somehow missing
            if v_type not in self.tab_frames:
                v_type = "Videos"

            # Get row and col for this tab
            row, col = divmod(counters[v_type], 3)

            # Build the card
            self.create_video_card(self.tab_frames[v_type], video, thumb_dir, row, col)
            counters[v_type] += 1

    def create_video_card(self, parent, video, thumb_dir, row, col):
        card = ttk.Frame(parent, padding=10, bootstyle="secondary")
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        # 1. Thumbnail
        thumb_path = thumb_dir / f"{video['video_id']}.jpg"
        img_label = ttk.Label(card, text="[No Thumbnail]", bootstyle="inverse-secondary", anchor=CENTER)

        if thumb_path.exists():
            try:
                img = Image.open(thumb_path).resize((300, 169))
                photo = ImageTk.PhotoImage(img)
                img_label.config(image=photo, text="")
                img_label.image = photo
            except:
                pass
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

        views = video.get("view_count") or 0
        ttk.Label(
            info_row,
            text=f"{views:,} views",
            font=("Segoe UI", 8),
            bootstyle="light"
        ).pack(side=LEFT)

        status_sym = "✅" if video.get("is_downloaded") else "🌐"
        ttk.Label(
            info_row,
            text=status_sym,
            font=("Segoe UI", 10)
        ).pack(side=RIGHT)

        # Prevent UI tearing while processing images synchronously
        card.update_idletasks()