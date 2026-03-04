import ttkbootstrap as ttk
from PIL import Image, ImageTk
from pathlib import Path

from gui.views.dashboard_view import DashboardView
from gui.views.ytdlp_view import YtDlpView
from gui.views.settings_view import SettingsView
from gui.views.database_view import DatabaseView
from gui.views.instaloader_view import InstaloaderView

class MainUI:
    def __init__(self, root, services):
        self.root = root
        self.services = services
        self.views = {}

        # Dictionary to keep image references alive (prevents garbage collection)
        self.icons = {}

        # Declare visual attributes
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
            self.sidebar, text="Dashboard", bootstyle="outline", command=lambda: self.show_view("dashboard")
        ).pack(fill="x", padx=5, pady=5)

        try:
            img_path = Path("assets/_dlp.png")
            img = Image.open(img_path)
            img.thumbnail((70, 70), Image.Resampling.LANCZOS)
            self.icons["dlp"] = ImageTk.PhotoImage(img)
            ttk.Button(
                self.sidebar,
                image=self.icons["dlp"],
                bootstyle="outline",
                padding=(0, 2),  # <--- Shrinks the internal vertical padding to maximize the image
                command=lambda: self.show_view("ytdlp")
            ).pack(fill="x", padx=5, pady=5)
        except Exception as e:
            print(f"Could not load _dlp.png: {e}")
            # Fallback to standard text button if image is missing
            ttk.Button(
                self.sidebar,
                text=">_dlp",
                bootstyle="outline",  # Keep the outline style on the fallback too!
                command=lambda: self.show_view("ytdlp")
            ).pack(fill="x", padx=5, pady=5)

        try:
            ig_img = Image.open(Path("assets/instaloader.png"))
            ig_img.thumbnail((30, 30), Image.Resampling.LANCZOS)
            self.icons["insta"] = ImageTk.PhotoImage(ig_img)
            ttk.Button(self.sidebar, image=self.icons["insta"], bootstyle="outline", padding=(0, 2),
                       command=lambda: self.show_view("insta")).pack(fill="x", padx=5, pady=5)
        except Exception:
            ttk.Button(self.sidebar, text="Insta", bootstyle="warning-outline",
                       command=lambda: self.show_view("insta")).pack(fill="x", padx=5, pady=5)
        # ----------------------------------------------

        ttk.Button(
            self.sidebar,
            text="Database",
            bootstyle="outline",
            command=lambda: self.show_view("db")
        ).pack(fill="x", padx=5, pady=5)

        ttk.Button(
            self.sidebar,
            text="Settings",
            bootstyle="outline",
            command=lambda: self.show_view("settings")
        ).pack(fill="x", padx=5, pady=5)

    def build_views(self):
        self.views["dashboard"] = DashboardView(self.content, self.services)
        self.views["ytdlp"] = YtDlpView(self.content, self.services)
        self.views["db"] = DatabaseView(self.content, self.services)
        self.views["insta"] = InstaloaderView(self.content, self.services)

        # --- DECOUPLED SETTINGS VIEW ---
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