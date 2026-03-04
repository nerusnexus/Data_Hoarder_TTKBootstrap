import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
import threading
import webbrowser
from PIL import Image
from pathlib import Path
from gui.components.responsive_image import ResponsiveImage


def format_number(num):
    try:
        num = int(num)
    except (ValueError, TypeError):
        return "0"
    if num >= 1_000_000_000: return f"{num / 1_000_000_000:.1f}B".replace(".0B", "B")
    if num >= 1_000_000: return f"{num / 1_000_000:.1f}M".replace(".0M", "M")
    if num >= 1_000: return f"{num / 1_000:.1f}K".replace(".0K", "K")
    return str(num)


class IgAccountCard(ttk.Frame):
    def __init__(self, parent, account_info, insta_service, log_callback, **kwargs):
        super().__init__(parent, bootstyle="light", **kwargs)
        self.insta_service = insta_service
        self.username = account_info.get("username")
        self.log_callback = log_callback
        self.sync_btn = None

        card = ttk.Frame(self, bootstyle="dark", padding=10)
        card.pack(fill=BOTH, expand=True, padx=1, pady=1)

        card.columnconfigure(0, weight=2, uniform="ig_cols")
        card.columnconfigure(1, weight=10, uniform="ig_cols")

        # --- LEFT SIDE: Profile Picture ---
        left_container = ttk.Frame(card, bootstyle="dark")
        left_container.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        pfp_border = ttk.Frame(left_container, bootstyle="light")
        pfp_border.pack(fill=X, anchor=N)

        pfp_path = Path(account_info.get("profile_pic_path", ""))

        if pfp_path.exists():
            try:
                img = Image.open(pfp_path).convert("RGBA")
                pfp_canvas = ResponsiveImage(pfp_border, img, aspect_ratio=1.0, bg_color="#222")
                pfp_canvas.pack(fill=BOTH, expand=True, padx=1, pady=1)
            except OSError:
                pass
        else:
            ttk.Label(pfp_border, text="📷", font=("Segoe UI", 36), bootstyle="inverse-dark", anchor=CENTER).pack(
                fill=BOTH, expand=True, padx=1, pady=1, ipady=30)

        # --- RIGHT SIDE: Stats & Controls ---
        right_container = ttk.Frame(card, bootstyle="dark")
        right_container.grid(row=0, column=1, sticky="nsew")

        full_name = account_info.get("full_name") or self.username
        ttk.Label(right_container, text=f"{full_name} (@{self.username})", font=("Segoe UI", 12, "bold"),
                  bootstyle="light").pack(anchor=W)

        followers = format_number(account_info.get("followers", 0))
        following = format_number(account_info.get("following", 0))
        privacy = "🔒 Private" if account_info.get("is_private") else "🌍 Public"

        ttk.Label(right_container, text=f"{followers} Followers • {following} Following • {privacy}",
                  font=("Segoe UI", 9), bootstyle="secondary").pack(anchor=W, pady=(2, 10))

        bio_str = account_info.get("biography") or "No biography."
        bio_text = ttk.Text(right_container, height=3, wrap="word", font=("Segoe UI", 8), background="#222",
                            foreground="#eee", borderwidth=0, highlightthickness=0)
        bio_text.pack(fill=X, pady=(0, 10))
        bio_text.insert("1.0", bio_str)
        bio_text.configure(state="disabled")

        btn_frame = ttk.Frame(right_container, bootstyle="dark")
        btn_frame.pack(anchor=W)

        ttk.Button(btn_frame, text="Open in Browser", bootstyle="outline-light",
                   command=lambda u=f"https://instagram.com/{self.username}": webbrowser.open(u)).pack(side=LEFT,
                                                                                                       padx=(0, 5))

        self.sync_btn = ttk.Button(btn_frame, text="Start Safe Sync", bootstyle="outline-success",
                                   command=self.start_sync)
        self.sync_btn.pack(side=LEFT, padx=(0, 5))

        ttk.Button(btn_frame, text="Delete", bootstyle="danger-link", command=self.delete_account).pack(side=RIGHT)

    def delete_account(self):
        if Messagebox.okcancel(f"Delete @{self.username} from database?", "Confirm Delete"):
            self.insta_service.delete_account(self.username)
            self.winfo_toplevel().event_generate("<<IgDataUpdated>>")

    def start_sync(self):
        self.sync_btn.config(state="disabled", text="Syncing...")
        threading.Thread(target=self._run_sync, daemon=True).start()

    def _run_sync(self):
        success, message = self.insta_service.sync_account(self.username, self.log_callback)
        self.after(0, self._finish_sync, success, message)  # type: ignore

    def _finish_sync(self, success, message):
        if self.sync_btn and self.sync_btn.winfo_exists():
            self.sync_btn.config(state="normal", text="Start Safe Sync")
        if success:
            Messagebox.show_info(message, "Sync Complete")
            self.winfo_toplevel().event_generate("<<IgDataUpdated>>")
        else:
            Messagebox.show_error(message, "Sync Failed")