import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
import threading


class MyAccountTab(ttk.Frame):
    def __init__(self, parent, services):
        super().__init__(parent)

        self.services = services
        self.account = services.account
        self.ytdlp = services.ytdlp

        self.build_ui()

    # ---------------- UI ----------------

    def build_ui(self):
        # ---------- Account Info ----------
        info_frame = ttk.LabelFrame(self, text="Account Info")
        info_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(info_frame, text="Channel Handle:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.handle_entry = ttk.Entry(info_frame)
        self.handle_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(info_frame, text="Channel URL:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.url_entry = ttk.Entry(info_frame)
        self.url_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        info_frame.columnconfigure(1, weight=1)

        ttk.Button(
            info_frame,
            text="Save",
            command=self.save_account
        ).grid(row=2, column=0, columnspan=2, pady=5)

        ttk.Button(
            info_frame,
            text="Fetch Channel Info",
            command=self.fetch_channel_info
        ).grid(row=3, column=0, columnspan=2, pady=5)

        # ---------- Stats ----------
        stats_frame = ttk.LabelFrame(self, text="Channel Stats")
        stats_frame.pack(fill="x", padx=10, pady=10)

        self.subs_label = ttk.Label(stats_frame, text="")
        self.subs_label.pack(anchor="w", padx=5, pady=2)

        self.videos_label = ttk.Label(stats_frame, text="")
        self.videos_label.pack(anchor="w", padx=5, pady=2)

        # ---------- Subscriptions (future use) ----------
        subs_frame = ttk.LabelFrame(self, text="Subscriptions")
        subs_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.sub_tree = ttk.Treeview(subs_frame)
        self.sub_tree.pack(fill="both", expand=True)

        self.load_data()

    # ---------------- Data ----------------

    def load_data(self):
        handle = self.account.get("channel_handle") or ""
        url = self.account.get("channel_url") or ""

        self.handle_entry.insert(0, handle)
        self.url_entry.insert(0, url)

        self.update_stats_labels()

    def update_stats_labels(self):
        subs = self.account.get("subscribers") or "Unknown"
        videos = self.account.get("video_count") or "Unknown"

        self.subs_label.config(text=f"Subscribers: {subs}")
        self.videos_label.config(text=f"Videos: {videos}")

    # ---------------- Save ----------------

    def save_account(self):
        handle = self.handle_entry.get().strip()
        url = self.url_entry.get().strip()

        # normalize handle (remove @)
        if handle.startswith("@"):
            handle = handle[1:]

        self.account.update_field("channel_handle", handle)
        self.account.update_field("channel_url", url)

        Messagebox.show_info("Saved", "Account information saved.")

    # ---------------- Fetch ----------------

    def fetch_channel_info(self):
        handle = self.handle_entry.get().strip()
        url = self.url_entry.get().strip()

        if not handle and not url:
            Messagebox.show_warning("Missing Info", "Enter handle or URL first.")
            return

        channel_input = url if url else f"https://youtube.com/@{handle.lstrip('@')}"

        threading.Thread(
            target=self._fetch_worker,
            args=(channel_input,),
            daemon=True
        ).start()

    def _fetch_worker(self, channel_input):
        try:
            meta = self.ytdlp.fetch_channel_public_info(channel_input)
        except Exception as e:
            self.after(0, lambda: Messagebox.show_error("Error", str(e)))
            return

        def update_ui():
            self.account.update_field("channel_id", meta.get("channel_id"))
            self.account.update_field("subscribers", meta.get("subscriber_count"))
            self.account.update_field("video_count", meta.get("video_count"))

            self.update_stats_labels()
            Messagebox.show_info("Success", "Channel info fetched.")

        self.after(0, update_ui)