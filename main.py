from pathlib import Path
from ttkbootstrap import Style
from gui.ui import MainUI
from services.services import AppServices
from gui.tray import TrayManager


def get_app_dir() -> Path:
    return Path(__file__).resolve().parent


def ensure_data_folder() -> Path:
    data_dir = get_app_dir() / "Data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def main():
    data_folder = ensure_data_folder()

    style = Style()
    services = AppServices(style, data_folder)

    style.theme_use(services.settings.get_theme())

    root = style.master
    tray = TrayManager(root)

    def on_close():
        if services.settings.get_close_to_tray():
            root.withdraw()
            tray.show()
        else:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    root.title("Data Hoarder")
    root.state("zoomed")

    MainUI(root, services)
    root.mainloop()


if __name__ == "__main__":
    main()
