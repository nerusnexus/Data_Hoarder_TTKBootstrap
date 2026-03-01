import ctypes
import sys
from ttkbootstrap import Style
from gui.ui import MainUI
from services.services import AppServices
from gui.tray import TrayManager
from oled_theme import theme as oled_theme
from config import FONTS_DIR, DATABASE_ICON_PATH


def load_custom_fonts():
    if sys.platform.startswith("win"):
        font_path = FONTS_DIR / "MaterialSymbolsRounded.ttf"
        if font_path.exists():
            FR_PRIVATE = 0x10
            ctypes.windll.gdi32.AddFontResourceExW(str(font_path), FR_PRIVATE, 0)


def set_dark_titlebar(window):
    """Forces the Windows title bar to use dark mode."""
    if sys.platform.startswith("win"):
        try:
            window.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20  # Works on Windows 10 1903+
            value = ctypes.c_int(2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(value),
                                                       ctypes.sizeof(value))
        except Exception as e:
            print("Could not set dark title bar:", e)


def main():
    load_custom_fonts()

    style = Style()
    style.register_theme(oled_theme)

    services = AppServices(style)
    style.theme_use(services.settings.get_theme())

    root = style.master

    # --- NEW: Set window icon ---
    if DATABASE_ICON_PATH.exists():
        root.iconbitmap(DATABASE_ICON_PATH)

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

    # --- NEW: Force Dark Title Bar ---
    set_dark_titlebar(root)

    MainUI(root, services)
    root.mainloop()


if __name__ == "__main__":
    main()