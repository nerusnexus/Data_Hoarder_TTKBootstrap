import ttkbootstrap as ttk


class SettingsView(ttk.Notebook):
    def __init__(self, parent, settings_service, theme_changer):
        super().__init__(parent)

        # Save the injected services
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

        # Now we just call self.settings directly
        self.close_to_tray_var = ttk.BooleanVar(
            value=self.settings.get_close_to_tray()
        )

        self.build_general_tab()

    def build_general_tab(self):
        # --- Theme ---
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

        # --- Start with system ---
        self.start_var = ttk.BooleanVar(
            value=self.settings.get_start_with_system()
        )

        ttk.Checkbutton(
            self.general,
            text="Start with system",
            variable=self.start_var,
            command=self.on_start_with_system_change,
        ).pack(anchor="w", padx=20, pady=(15, 0))

        ttk.Button(
            self.general,
            text="Open data folder",
            command=self.settings.open_data_folder
        ).pack(anchor="w", padx=20, pady=5)

        ttk.Checkbutton(
            self.general,
            text="Close to tray instead of exiting",
            variable=self.close_to_tray_var,
            command=lambda: self.settings.set_close_to_tray(
                self.close_to_tray_var.get()
            )
        ).pack(anchor="w", padx=20, pady=5)

    def on_theme_change(self, _event):
        # Call the injected theme changer function
        self.change_theme_func(self.theme_var.get())

    def on_start_with_system_change(self):
        self.settings.set_start_with_system(
            self.start_var.get()
        )

    def build_ytdlp_tab(self):
        pass

    def build_database_tab(self):
        pass