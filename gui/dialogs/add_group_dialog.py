import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox

class AddGroupDialog(ttk.Toplevel):
    def __init__(self, parent, service):
        super().__init__(parent)

        self.service = service
        self.result = None

        self.title("Add Group")
        self.geometry("350x180")
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()

        self.center_window()

        container = ttk.Frame(self, padding=25)
        container.pack(fill=BOTH, expand=True)

        ttk.Label(
            container,
            text="Group Name",
            font=("Segoe UI", 12, "bold")
        ).pack(pady=(0, 10))

        self.entry = ttk.Entry(container)
        self.entry.pack(fill=X, pady=(0, 20))
        self.entry.focus()

        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=X)

        ttk.Button(
            btn_frame,
            text="Cancel",
            bootstyle="danger-outline",
            command=self.destroy
        ).pack(side=RIGHT, padx=5)

        ttk.Button(
            btn_frame,
            text="Add",
            bootstyle="success-outline",
            command=self.submit
        ).pack(side=RIGHT)

    def submit(self):
        name = self.entry.get().strip()

        try:
            result = self.service.add_group(name)
            self.result = result
            self.destroy()
        except Exception as e:
            Messagebox.show_error("Error", str(e))

    def center_window(self):
        self.update_idletasks()

        width = 350
        height = 180

        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)

        self.geometry(f"{width}x{height}+{x}+{y}")