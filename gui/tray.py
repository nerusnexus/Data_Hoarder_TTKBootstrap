import pystray
from PIL import Image, ImageDraw
from config import DATABASE_ICON_PATH

class TrayManager:
    def __init__(self, root):
        self.root = root
        self.icon = None

    def create_image(self):
        # --- NEW: Use custom icon if available ---
        if DATABASE_ICON_PATH.exists():
            try:
                return Image.open(DATABASE_ICON_PATH)
            except Exception:
                pass

        # Fallback generated icon
        image = Image.new('RGB', (64, 64), color=(20, 20, 20))
        dc = ImageDraw.Draw(image)
        dc.rectangle([16, 16, 48, 48], fill=(200, 50, 50))
        return image

    def on_quit(self, icon, item):
        self.icon.stop()
        self.root.destroy()

    def on_show(self, icon, item):
        self.icon.stop()
        self.root.after(0, self.root.deiconify)

    def show(self):
        image = self.create_image()
        menu = pystray.Menu(
            pystray.MenuItem('Show App', self.on_show, default=True),
            pystray.MenuItem('Quit', self.on_quit)
        )
        self.icon = pystray.Icon("Data Hoarder", image, "Data Hoarder", menu)
        self.icon.run()