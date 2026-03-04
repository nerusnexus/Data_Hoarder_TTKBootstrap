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
        self.instaloader = ttk.Frame(self)  # NEW
        self.database = ttk.Frame(self)

        self.add(self.general, text="General")
        self.add(self.ytdlp, text="Yt Dlp")
        self.add(self.instaloader, text="Instaloader")  # NEW
        self.add(self.database, text="Database")

        self.start_var = None
        self.theme_var = None
        self.api_var = None
        self.quota_label = None

        self.ig_user_var = None  # NEW
        self.ig_pass_var = None  # NEW

        self.close_to_tray_var = ttk.BooleanVar(
            value=self.settings.get_close_to_tray()
        )

        self.build_general_tab()
        self.build_ytdlp_tab()
        self.build_instaloader_tab()  # NEW
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

        remaining = self.settings.get_remaining_quota()
        self.quota_label = ttk.Label(
            self.ytdlp,
            text=f"Estimated quota remaining today: {remaining:,} / 10,000 requests",
            font=("Segoe UI", 8, "italic"),
            bootstyle="secondary"
        )
        self.quota_label.pack(anchor="w", padx=22, pady=(0, 5))

    def on_api_key_saved(self):
        self.settings.set_youtube_api_key(self.api_var.get())
        Messagebox.show_info("Settings Saved", "YouTube API Key saved successfully.")

    # --- NEW: Instaloader Tab ---
    def build_instaloader_tab(self):
        ttk.Label(self.instaloader, text="Instagram Credentials (Burner Account Recommended):",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=20, pady=(15, 10))

        user_frame = ttk.Frame(self.instaloader)
        user_frame.pack(fill="x", padx=20, pady=5)
        ttk.Label(user_frame, text="Username:", width=12).pack(side="left")
        self.ig_user_var = ttk.StringVar(value=self.settings.get_ig_username())
        ttk.Entry(user_frame, textvariable=self.ig_user_var, width=40).pack(side="left")

        pass_frame = ttk.Frame(self.instaloader)
        pass_frame.pack(fill="x", padx=20, pady=5)
        ttk.Label(pass_frame, text="Password:", width=12).pack(side="left")
        self.ig_pass_var = ttk.StringVar(value=self.settings.get_ig_password())
        ttk.Entry(pass_frame, textvariable=self.ig_pass_var, width=40, show="*").pack(side="left")

        ttk.Button(self.instaloader, text="Save Credentials", bootstyle="success", command=self.on_ig_creds_saved).pack(
            anchor="w", padx=20, pady=15)

        warning_text = "⚠️ WARNING: Instaloader behaves like a bot and may cause Instagram to temporarily block or ban the account.\nNever use your personal account. Always use a burner account."
        ttk.Label(self.instaloader, text=warning_text, bootstyle="danger", font=("Segoe UI", 9, "italic")).pack(
            anchor="w", padx=20, pady=5)

    def on_ig_creds_saved(self):
        self.settings.set_ig_username(self.ig_user_var.get())
        self.settings.set_ig_password(self.ig_pass_var.get())
        Messagebox.show_info("Settings Saved", "Instagram credentials saved successfully.")

    def build_database_tab(self):
        pass