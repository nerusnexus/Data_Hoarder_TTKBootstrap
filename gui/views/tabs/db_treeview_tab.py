import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.widgets.scrolled import ScrolledFrame


class DbTreeviewTab(ttk.Frame):
    def __init__(self, parent, add_channel_service):
        super().__init__(parent)
        self.add_channel_service = add_channel_service

        # Define all columns based on your database schema
        self.columns = (
            "id", "channel_name", "video_id", "title", "url",
            "view_count", "is_downloaded", "video_type", "upload_date",
            "duration", "tags", "like_count",
            "comment_count", "filepath"
        )

        self.tree = None
        self.build_ui()
        self.load_data()

    def build_ui(self):
        # Container for the Treeview and scrollbars
        container = ttk.Frame(self, padding=10)
        container.pack(fill=BOTH, expand=True)

        # Create Treeview with horizontal and vertical scrollbars
        self.tree = ttk.Treeview(
            container,
            columns=self.columns,
            show="headings",
            bootstyle="primary"
        )

        # Scrollbars
        v_scroll = ttk.Scrollbar(container, orient=VERTICAL, command=self.tree.yview)
        h_scroll = ttk.Scrollbar(container, orient=HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        # Configure columns and headings
        for col in self.columns:
            # Set a default width, making 'title' and 'description' wider
            width = 150
            if col in ["title", "description", "url", "filepath"]:
                width = 300

            self.tree.heading(col, text=col.replace("_", " ").title(), anchor=W)
            self.tree.column(col, width=width, anchor=W)

        # Layout using grid to accommodate scrollbars
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Refresh Button
        ttk.Button(
            self,
            text="Refresh Data",
            bootstyle="secondary-outline",
            command=self.load_data
        ).pack(pady=10)

    def load_data(self):
        """Clears the tree and reloads all video data from all channels."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Get all channels to iterate through their videos
        groups = self.add_channel_service.get_all_groups()

        for group in groups:
            channels = self.add_channel_service.get_channels_by_group(group)
            for channel in channels:
                videos = self.add_channel_service.get_videos_by_channel(channel)
                for video in videos:
                    # Extract values in the correct order defined in self.columns
                    values = [video.get(col, "") for col in self.columns]
                    self.tree.insert("", "end", values=values)