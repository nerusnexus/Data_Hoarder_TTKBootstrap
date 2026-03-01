from ttkbootstrap import Style
from gui.ui import MainUI
from services.services import AppServices
from gui.tray import TrayManager
from oled_theme import theme as oled_theme


def main():
    style = Style()

    # Register your custom OLED theme into ttkbootstrap's system
    style.register_theme(oled_theme)

    # We no longer need to pass 'data_folder' here!
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