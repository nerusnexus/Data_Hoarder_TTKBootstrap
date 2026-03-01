import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class AddChannelDialog(ttk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.result = None

        self.title("Add Channel")
        self.geometry("400x180")
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()

        self.center_window()

        container = ttk.Frame(self, padding=25)
        container.pack(fill=BOTH, expand=True)

        ttk.Label(
            container,
            text="Channel URL or @Handle",
            font=("Segoe UI", 12, "bold")
        ).pack(pady=(0, 10))

        self.entry = ttk.Entry(container)
        self.entry.pack(fill=X, pady=(0, 20))
        self.entry.focus()

        # BIND ENTER KEY
        self.entry.bind("<Return>", lambda e: self.submit())

        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=X)

        ttk.Button(
            btn_frame,
            text="Cancel",
            bootstyle="danger-outline",
            command=self.destroy
        ).pack(side="right", padx=5)

        ttk.Button(
            btn_frame,
            text="Add",
            bootstyle="success-outline",
            command=self.submit
        ).pack(side="right")

    def submit(self):
        self.result = self.entry.get().strip()
        self.destroy()

    def center_window(self):
        self.update_idletasks()

        width = 400
        height = 180

        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)

        self.geometry(f"{width}x{height}+{x}+{y}")