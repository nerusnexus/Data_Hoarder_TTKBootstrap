import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.widgets.scrolled import ScrolledFrame
from ttkbootstrap.dialogs.dialogs import Querybox
from gui.components.ig_account_card import IgAccountCard


class InstaloaderView(ttk.Frame):
    def __init__(self, parent, services):
        super().__init__(parent)
        self.insta_service = services.insta
        self.cards_frame = None
        self.log_text = None

        self.build_ui()
        self.load_data()
        self.winfo_toplevel().bind("<<IgDataUpdated>>", self.refresh_all, add="+")

    def build_ui(self):
        # Top Controls
        top_frame = ttk.Frame(self, padding=10)
        top_frame.pack(fill=X)

        ttk.Label(top_frame, text="Instagram Archiver", font=("Segoe UI", 16, "bold")).pack(side=LEFT)
        ttk.Button(top_frame, text="+ Add IG Account", bootstyle="primary", command=self.add_account).pack(side=RIGHT)

        # Content Area split into Cards (Left) and Logs (Right)
        content_paned = ttk.Panedwindow(self, orient=HORIZONTAL)
        content_paned.pack(fill=BOTH, expand=True, padx=10, pady=(0, 10))

        # Cards Section
        cards_container = ttk.Labelframe(content_paned, text="Tracked Accounts", padding=5)
        content_paned.add(cards_container, weight=3)

        self.cards_frame = ScrolledFrame(cards_container, autohide=True)
        self.cards_frame.pack(fill=BOTH, expand=True)

        # Logs Section
        log_container = ttk.Labelframe(content_paned, text="Sync Logs", padding=5)
        content_paned.add(log_container, weight=1)

        self.log_text = ttk.Text(log_container, font=("Consolas", 8), state=DISABLED)
        self.log_text.pack(fill=BOTH, expand=True)

    def write_log(self, message):
        self.log_text.config(state=NORMAL)
        self.log_text.insert(END, f"{message}\n")
        self.log_text.see(END)
        self.log_text.config(state=DISABLED)

    def add_account(self):
        username = Querybox.get_string("Enter Instagram Username (e.g. @zuck)", "Add Account")
        if not username: return

        success, msg = self.insta_service.add_account(username)
        if success:
            self.refresh_all()
        else:
            self.write_log(f"Failed to add account: {msg}")

    def refresh_all(self, _event=None):
        for child in self.cards_frame.winfo_children():
            child.destroy()
        self.load_data()

    def load_data(self):
        accounts = self.insta_service.get_all_accounts()
        for idx, acc in enumerate(accounts):
            card = IgAccountCard(self.cards_frame, acc, self.insta_service, self.write_log)
            card.pack(fill=X, padx=5, pady=5)