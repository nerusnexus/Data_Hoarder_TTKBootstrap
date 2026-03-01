import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox


class SettingsView(ttk.Notebook):
    def __init__(self, parent, settings_service, theme_changer):
        super().__init__(parent)

        self.settings = settings_service
        self.change_theme_func = theme_changer
        self.style = ttk.Style.get_instance()

        self.general = ttk.Frame(self)
        self.ytdlp = ttk.Frame(self)
        self.database = ttk.Frame(self)

        self.add(self.general, text="General")
        self.add(self.ytdlp, text="Yt Dlp")
        self.add(self.database, text="Database")

        self.start_var = None
        self.theme_var = None

        self.close_to_tray_var = ttk.BooleanVar(
            value=self.settings.get_close_to_tray()
        )

        self.build_general_tab()
        self.build_ytdlp_tab()
        self.build_database_tab()

    def build_general_tab(self):
        ttk.Label(
            self.general, text="Theme"
        ).pack(anchor="w", padx=20, pady=(10, 0))

        self.theme_var = ttk.StringVar(value=self.style.theme.name)

        theme_combo = ttk.Combobox(
            self.general,
            textvariable=self.theme_var,
            values=self.style.theme_names(),
            state="readonly",
            width=20,
        )
        theme_combo.pack(anchor="w", padx=20, pady=5)
        theme_combo.bind("<<ComboboxSelected>>", self.on_theme_change)

        self.start_var = ttk.BooleanVar(
            value=self.settings.get_start_with_system()
        )

        ttk.Checkbutton(
            self.general,
            text="Start with system",
            variable=self.start_var,
            command=self.on_start_with_system_change,
        ).pack(anchor="w", padx=20, pady=(15, 0))

        ttk.Checkbutton(
            self.general,
            text="Close to tray instead of exiting",
            variable=self.close_to_tray_var,
            command=lambda: self.settings.set_close_to_tray(
                self.close_to_tray_var.get()
            )
        ).pack(anchor="w", padx=20, pady=5)

        ttk.Button(
            self.general,
            text="Open data folder",
            bootstyle="outline",
            command=self.settings.open_data_folder
        ).pack(anchor="w", padx=20, pady=5)

    def on_theme_change(self, _event):
        self.change_theme_func(self.theme_var.get())

    def on_start_with_system_change(self):
        self.settings.set_start_with_system(
            self.start_var.get()
        )

    def build_ytdlp_tab(self):
        ttk.Label(self.ytdlp, text="YouTube Data API v3 Key:").pack(anchor="w", padx=20, pady=(10, 0))

        api_frame = ttk.Frame(self.ytdlp)
        api_frame.pack(fill="x", padx=20, pady=5)

        self.api_var = ttk.StringVar(value=self.settings.get_youtube_api_key())
        api_entry = ttk.Entry(api_frame, textvariable=self.api_var, width=50, show="*")
        api_entry.pack(side="left", padx=(0, 10))

        ttk.Button(api_frame, text="Save Key", bootstyle="success", command=self.on_api_key_saved).pack(side="left")

        # --- NEW: Quota Tracker Label ---
        remaining = self.settings.get_remaining_quota()
        self.quota_label = ttk.Label(
            self.ytdlp,
            text=f"Estimated quota remaining today: {remaining:,} / 10,000 requests",
            font=("Segoe UI", 8, "italic"),
            bootstyle="secondary"
        )
        self.quota_label.pack(anchor="w", padx=22, pady=(0, 5))

    def build_database_tab(self):
        pass

    def on_api_key_saved(self):
        self.settings.set_youtube_api_key(self.api_var.get())
        Messagebox.show_info("Settings Saved", "YouTube API Key saved successfully.")