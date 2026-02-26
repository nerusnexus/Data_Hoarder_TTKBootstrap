import pystray
from pystray import MenuItem as Item
from pystray import Menu
from PIL import Image
import threading

class TrayManager:
    def __init__(self, root):
        self.root = root
        self.icon = None

    def _create_icon(self):
        # Create a blank image placeholder for the icon
        image = Image.new("RGB", (64, 64), color="black")

        # Properly wrap the items inside a pystray Menu instance
        menu = Menu(
            Item("Open", self.show_window),
            Item("Quit", self.quit_app)
        )

        self.icon = pystray.Icon("DataHoarder", image, "Data Hoarder", menu)
        self.icon.run()

    def show(self):
        # Run the system tray icon on a background thread
        threading.Thread(target=self._create_icon, daemon=True).start()

    def show_window(self):
        # Bring the main window back up and destroy the tray icon
        self.root.after(0, self.root.deiconify)
        if self.icon:
            self.icon.stop()
            self.icon = None

    def quit_app(self):
        # Close the tray and shut down the main loop completely
        if self.icon:
            self.icon.stop()
        self.root.after(0, self.root.destroy)