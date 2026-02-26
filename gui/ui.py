import ttkbootstrap as ttk
from gui.views.dashboard_view import DashboardView
from gui.views.ytdlp_view import YtDlpView
from gui.views.settings_view import SettingsView
from gui.views.database_view import DatabaseView


class MainUI:
    def __init__(self, root, services):
        self.root = root
        self.services = services
        self.views = {}

        # Declare visual attributes (to be defined later)
        self.main_frame = None
        self.content = None
        self.sidebar = None

        self.build()

    def build(self):
        # main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        # sidebar
        self.sidebar = ttk.Frame(self.main_frame, width=100)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # content
        self.content = ttk.Frame(self.main_frame)
        self.content.pack(side="right", fill="both", expand=True)

        self.build_sidebar()
        self.build_views()

        self.show_view("dashboard")

    def build_sidebar(self):
        ttk.Label(self.sidebar, text="Data Hoarder").pack(pady=5)

        ttk.Button(
            self.sidebar,
            text="Dashboard",
            command=lambda: self.show_view("dashboard")
        ).pack(fill="x", padx=5, pady=5)

        ttk.Button(
            self.sidebar,
            text=">_dlp",
            command=lambda: self.show_view("ytdlp")
        ).pack(fill="x", padx=5, pady=5)

        ttk.Button(
            self.sidebar,
            text="Database",
            command=lambda: self.show_view("db")
        ).pack(fill="x", padx=5, pady=5)

        ttk.Button(
            self.sidebar,
            text="Settings",
            command=lambda: self.show_view("settings")
        ).pack(fill="x", padx=5, pady=5)

    def build_views(self):
        self.views["dashboard"] = DashboardView(self.content, self.services)
        self.views["ytdlp"] = YtDlpView(self.content, self.services)
        self.views["db"] = DatabaseView(self.content, self.services)

        # --- DECOUPLED SETTINGS VIEW ---
        # We only pass what it explicitly needs, not the whole AppServices object
        self.views["settings"] = SettingsView(
            self.content,
            settings_service=self.services.settings,
            theme_changer=self.services.change_theme
        )

        for view in self.views.values():
            view.pack_forget()

    def show_view(self, name):
        for view in self.views.values():
            view.pack_forget()

        self.views[name].pack(fill="both", expand=True)