import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from pathlib import Path
from PIL import Image, ImageTk


class LibraryTab(ttk.Frame):
    def __init__(self, parent, services):
        super().__init__(parent)
        self.services = services
        self.cards_frame = None
        self.tree = None

        self.build_ui()
        self.load_tree_data()

    def build_ui(self):
        # Left sidebar for selection
        sidebar = ttk.Frame(self, width=250)
        sidebar.pack(side=LEFT, fill=Y, padx=5, pady=5)
        sidebar.pack_propagate(False)

        ttk.Label(sidebar, text="Channels", font=("Segoe UI", 10, "bold")).pack(pady=5)
        self.tree = ttk.Treeview(sidebar, show="tree")
        self.tree.pack(fill=BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_channel_selected)

        # Right area for the video library
        main_content = ttk.Frame(self)
        main_content.pack(side=RIGHT, fill=BOTH, expand=True)

        self.library_label = ttk.Label(
            main_content,
            text="Select a channel to view library",
            font=("Segoe UI", 12)
        )
        self.library_label.pack(pady=10)

        self.cards_frame = ScrolledFrame(main_content, autohide=True)
        self.cards_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

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
        # Clear existing cards
        for child in self.cards_frame.winfo_children():
            child.destroy()

        channel_info = self.services.add_channel.get_channel_details(channel_name)
        videos = self.services.add_channel.get_videos_by_channel(channel_name)

        if not channel_info or not videos: return

        # Construct path: Data/Metadata/channel_id (@handle)/Videos/
        cid = channel_info.get("channel_id")
        handle = channel_info.get("handle")
        folder_name = f"{cid} ({handle})" if handle and handle != cid else cid
        thumb_dir = self.services.metadata_folder / folder_name / "Videos"

        # Grid settings
        cols = 3
        for i, video in enumerate(videos):
            row, col = divmod(i, cols)
            self.create_video_card(self.cards_frame, video, thumb_dir, row, col)

    def create_video_card(self, parent, video, thumb_dir, row, col):
        card = ttk.Frame(parent, padding=5, bootstyle="secondary")
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        # Thumbnail logic
        thumb_path = thumb_dir / f"{video['video_id']}.jpg"  # Assumes .jpg extension

        img_label = ttk.Label(card, text="[No Thumbnail]", bootstyle="inverse-secondary")
        if thumb_path.exists():
            try:
                img = Image.open(thumb_path).resize((240, 135))
                photo = ImageTk.PhotoImage(img)
                img_label.config(image=photo, text="")
                img_label.image = photo  # Keep reference
            except:
                pass
        img_label.pack(fill=X)

        # Title and Status
        status_sym = "✅" if video.get("is_downloaded") else "🌐"
        title_text = video.get("title", "Unknown Title")
        if len(title_text) > 40: title_text = title_text[:37] + "..."

        ttk.Label(
            card,
            text=f"{status_sym} {title_text}",
            font=("Segoe UI", 9, "bold"),
            wraplength=230
        ).pack(anchor=W, pady=(5, 0))

        # Views
        views = video.get("view_count") or 0
        ttk.Label(
            card,
            text=f"{views:,} views",
            font=("Segoe UI", 8),
            bootstyle="light"
        ).pack(anchor=W)