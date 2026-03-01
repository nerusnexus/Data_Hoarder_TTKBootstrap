import ctypes
import sys
from ttkbootstrap import Style
from gui.ui import MainUI
from services.services import AppServices
from gui.tray import TrayManager
from oled_theme import theme as oled_theme
from config import FONTS_DIR


def load_custom_fonts():
    """Temporarily installs the TTF font into Windows for this app session."""
    if sys.platform.startswith("win"):
        font_path = FONTS_DIR / "MaterialSymbolsRounded.ttf"
        if font_path.exists():
            FR_PRIVATE = 0x10
            ctypes.windll.gdi32.AddFontResourceExW(str(font_path), FR_PRIVATE, 0)
        else:
            print(f"Font not found at {font_path}. Skipping custom icons.")


def main():
    load_custom_fonts()

    style = Style()
    style.register_theme(oled_theme)

    services = AppServices(style)
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