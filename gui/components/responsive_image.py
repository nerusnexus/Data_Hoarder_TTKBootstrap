import ttkbootstrap as ttk
from PIL import Image, ImageTk, ImageOps

class ResponsiveImage(ttk.Canvas):
    def __init__(self, parent, original_img, aspect_ratio, bg_color="black", **kwargs):
        super().__init__(parent, highlightthickness=0, background=bg_color, **kwargs)
        self.original_img = original_img
        self.aspect_ratio = aspect_ratio
        self.photo = None
        self._timer = None
        self.bind("<Configure>", self.on_resize)

    def on_resize(self, _event):  # Fixed unused event warning
        if self._timer is not None:
            self.after_cancel(self._timer)
        self._timer = self.after(100, self.perform_resize)  # type: ignore

    def perform_resize(self):
        self._timer = None
        width = self.winfo_width()
        if width <= 10:
            return

        height = int(width / self.aspect_ratio)
        self.config(height=height)

        try:
            resized = ImageOps.fit(self.original_img, (width, height), method=Image.Resampling.LANCZOS,
                                   centering=(0.5, 0.5))
            self.photo = ImageTk.PhotoImage(resized)
            self.delete("all")
            self.create_image(0, 0, image=self.photo, anchor="nw")
        except OSError:  # Fixed broad exception
            pass