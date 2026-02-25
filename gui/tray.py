import pystray
from pystray import MenuItem as item
from PIL import Image
import threading

class TrayManager:
    def __init__(self, root):
        self.root = root
        self.icon = None

    def _create_icon(self):
        image = Image.new("RGB", (64, 64), color="black")

        menu = (
            item("Open", self.show_window),
            item("Quit", self.quit_app),
        )

        self.icon = pystray.Icon("DataHoarder", image, "Data Hoarder", menu)
        self.icon.run()

    def show(self):
        threading.Thread(target=self._create_icon, daemon=True).start()

    def show_window(self):
        self.root.after(0, self.root.deiconify)
        if self.icon:
            self.icon.stop()
            self.icon = None

    def quit_app(self):
        if self.icon:
            self.icon.stop()
        self.root.after(0, self.root.destroy)
