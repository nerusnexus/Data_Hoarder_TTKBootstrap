import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.widgets.scrolled import ScrolledFrame
import webbrowser
import os
import sys
import subprocess
import json
from pathlib import Path
from PIL import Image, ImageTk, ImageOps
from gui.dialogs.add_group_dialog import AddGroupDialog
from gui.dialogs.add_channel_dialog import AddChannelDialog
from config import FONTS_DIR, METADATA_DIR


def format_number(num):
    """Formats large numbers into readable K, M, B formats."""
    try:
        num = int(num)
    except (ValueError, TypeError):
        return "0"

    if num == 0: return "0"
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B".replace(".0B", "B")
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M".replace(".0M", "M")
    if num >= 1_000:
        return f"{num / 1_000:.1f}K".replace(".0K", "K")
    return str(num)


class ResponsiveImage(ttk.Canvas):
    def __init__(self, parent, original_img, aspect_ratio, bg_color="black", **kwargs):
        super().__init__(parent, highlightthickness=0, background=bg_color, **kwargs)
        self.original_img = original_img
        self.aspect_ratio = aspect_ratio
        self.photo = None
        self._timer = None
        self.bind("<Configure>", self.on_resize)

    def on_resize(self, event):
        if self._timer is not None:
            self.after_cancel(self._timer)
        self._timer = self.after(100, self.perform_resize)

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
        except Exception:
            pass


class ManageSubsTab(ttk.Frame):
    def __init__(self, parent, add_group_service, add_channel_service):
        super().__init__(parent)
        self.add_group_service = add_group_service
        self.add_channel_service = add_channel_service

        self.has_icon_font = (FONTS_DIR / "MaterialSymbolsRounded.ttf").exists()
        if self.has_icon_font:
            style = ttk.Style()
            style.configure("Icon.TButton", font=("Material Symbols Rounded", 12))

        self.tree = None
        self.cards_frame = None
        self.card_images = []

        self.build_ui()
        self.load_data()

        self.winfo_toplevel().bind("<<DataUpdated>>", self.refresh_all, add="+")

    def refresh_all(self, _event=None):
        self.card_images.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        for child in self.cards_frame.winfo_children():
            child.destroy()
        self.load_data()

    def load_data(self):
        groups = self.add_group_service.get_all_groups()
        for group in groups:
            group_id = self.tree.insert("", "end", text=group, tags=("group",))
            channels = self.add_channel_service.get_channels_by_group(group)

            group_lf = ttk.Labelframe(self.cards_frame, text=group, padding=1)
            group_lf.pack(fill="x", expand=True, padx=1, pady=1)
            group_lf.columnconfigure(0, weight=1)

            card_idx = 0
            for channel_name in channels:
                self.tree.insert(group_id, "end", text=channel_name, tags=("channel",))
                channel_info = self.add_channel_service.get_channel_details(channel_name)
                self.create_channel_card(group_lf, channel_info, card_idx, 0)
                card_idx += 1

    def build_ui(self):
        top_frame = ttk.Frame(self, height=250)
        top_frame.pack(fill="x", padx=10, pady=10)
        top_frame.pack_propagate(False)

        self.tree = ttk.Treeview(top_frame, show="tree")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", self.on_double_click)

        buttons = ttk.Frame(top_frame)
        buttons.pack(side="right", fill="y", padx=(10, 0))

        ttk.Button(buttons, text="+ Group", command=self.add_group).pack(fill="x", pady=5)
        ttk.Button(buttons, text="+ Channel", command=self.add_channel).pack(fill="x", pady=5)
        ttk.Button(buttons, text="Delete", bootstyle="danger", command=self.delete_selected).pack(fill="x", pady=5)

        self.cards_frame = ScrolledFrame(self, autohide=True)
        self.cards_frame.pack(fill="both", expand=True, padx=5, pady=(0, 10))

    def create_channel_card(self, parent, channel_info, row, col):
        border_frame = ttk.Frame(parent, bootstyle="light")
        border_frame.grid(row=row, column=col, padx=10, pady=(10, 10), sticky="nsew")

        card = ttk.Frame(border_frame, bootstyle="dark", padding=10)
        card.pack(fill="both", expand=True, padx=1, pady=1)

        card.columnconfigure(0, weight=2, uniform="card_cols")
        card.columnconfigure(1, weight=12, uniform="card_cols")

        cid = channel_info.get("channel_id")
        handle = channel_info.get("handle", "")
        safe_handle = handle if handle.startswith('@') else f"@{handle}"
        folder_name = f"{cid} ({handle})" if handle and handle != cid else cid
        local_path = METADATA_DIR / folder_name

        profile_img_path = local_path / "profile.jpg"
        banner_img_path = local_path / "banner.jpg"

        # --- LEFT SIDE: Profile Picture ---
        left_container = ttk.Frame(card, bootstyle="dark")
        left_container.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        pfp_border = ttk.Frame(left_container, bootstyle="light")
        pfp_border.pack(fill="x", anchor="n")

        if profile_img_path.exists():
            try:
                img = Image.open(profile_img_path).convert("RGBA")
                pfp_canvas = ResponsiveImage(pfp_border, img, aspect_ratio=1.0, bg_color="#222")
                pfp_canvas.pack(fill="both", expand=True, padx=1, pady=1)
            except Exception:
                pass
        else:
            pfp_label = ttk.Label(pfp_border, text="account_circle" if self.has_icon_font else "👤",
                                  font=("Material Symbols Rounded", 48) if self.has_icon_font else ("Segoe UI", 36),
                                  bootstyle="inverse-dark", anchor="center")
            pfp_label.pack(fill="both", expand=True, padx=1, pady=1, ipady=30)

        # --- RIGHT SIDE: Container for Banner and Content ---
        right_container = ttk.Frame(card, bootstyle="dark")
        right_container.grid(row=0, column=1, sticky="nsew")

        banner_border = ttk.Frame(right_container, bootstyle="light")
        banner_border.pack(side="top", fill="x", anchor="nw")

        if banner_img_path.exists():
            try:
                img = Image.open(banner_img_path).convert("RGBA")
                banner_ratio = 1100 / 150.0
                banner_canvas = ResponsiveImage(banner_border, img, aspect_ratio=banner_ratio, bg_color="#222")
                banner_canvas.pack(fill="both", expand=True, padx=1, pady=1)
            except Exception:
                pass
        else:
            banner_label = ttk.Label(banner_border, text="[No Banner Found]", font=("Segoe UI", 8), anchor="center",
                                     bootstyle="inverse-dark")
            banner_label.pack(fill="both", expand=True, padx=1, pady=1, ipady=40)

        content_frame = ttk.Frame(right_container, bootstyle="dark")
        content_frame.pack(side="top", fill="both", expand=True, pady=(10, 0))

        content_frame.columnconfigure(0, weight=5, uniform="content_cols")
        content_frame.columnconfigure(1, weight=5, uniform="content_cols")
        content_frame.columnconfigure(2, weight=2, uniform="content_cols")

        name = channel_info.get("name", "Unknown")
        url = channel_info.get("url", "")
        subs_formatted = format_number(channel_info.get("follower_count", 0))

        videos = self.add_channel_service.get_videos_by_channel(name)
        v_count = sum(1 for v in videos if v.get("video_type") == "Videos")
        s_count = sum(1 for v in videos if v.get("video_type") == "Shorts")
        l_count = sum(1 for v in videos if v.get("video_type") == "Lives")

        creation_date = channel_info.get("creation_date") or ""
        date_str = "Unknown"
        if creation_date and len(str(creation_date)) == 8:
            date_str = f"{str(creation_date)[6:8]}/{str(creation_date)[4:6]}/{str(creation_date)[0:4]}"

        country = channel_info.get("country") or "Unknown"
        views_formatted = format_number(channel_info.get("view_count") or 0)

        # ====== COLUMN 1: STATS ======
        stats_frame = ttk.Frame(content_frame, bootstyle="dark")
        stats_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ttk.Label(stats_frame, text=f"{name} ({safe_handle})", font=("Segoe UI", 12, "bold"), bootstyle="light").pack(
            anchor="w")
        ttk.Label(stats_frame, text=f"{subs_formatted} subs • {v_count} Videos • {s_count} Shorts • {l_count} Lives",
                  font=("Segoe UI", 9), bootstyle="light").pack(anchor="w", pady=(2, 0))
        ttk.Label(stats_frame, text=f"Since {date_str} • {country} • {views_formatted} views",
                  font=("Segoe UI", 8), bootstyle="secondary").pack(anchor="w", pady=(0, 10))

        btn_frame = ttk.Frame(stats_frame, bootstyle="dark")
        btn_frame.pack(anchor="w")

        if self.has_icon_font:
            ttk.Button(btn_frame, text="public", style="Icon.TButton", bootstyle="outline-light",
                       command=lambda u=url: webbrowser.open(u)).pack(side="left", padx=(0, 5))
            ttk.Button(btn_frame, text="folder", style="Icon.TButton", bootstyle="outline-light",
                       command=lambda p=local_path: self.open_local_path(p)).pack(side="left")
        else:
            ttk.Button(btn_frame, text="Web", bootstyle="outline-light", command=lambda u=url: webbrowser.open(u)).pack(
                side="left", padx=(0, 5))
            ttk.Button(btn_frame, text="Dir", bootstyle="outline-light",
                       command=lambda p=local_path: self.open_local_path(p)).pack(side="left")

        # ====== COLUMN 2: DESCRIPTION ======
        desc_frame = ttk.Frame(content_frame, bootstyle="dark")
        desc_frame.grid(row=0, column=1, sticky="nsew", padx=10)

        ttk.Label(desc_frame, text="Description:", font=("Segoe UI", 9, "bold"), bootstyle="light").pack(anchor="w",
                                                                                                         pady=(0, 2))

        desc_str = channel_info.get("description") or "No description available."

        # Locked description height
        desc_text = ttk.Text(desc_frame, height=4, wrap="word", font=("Segoe UI", 8), background="#222",
                             foreground="#eee", borderwidth=0, highlightthickness=0)
        desc_text.pack(fill="x", pady=2)
        desc_text.insert("1.0", desc_str)
        desc_text.configure(state="disabled")

        # ====== COLUMN 3: LINKS ======
        links_frame = ttk.Frame(content_frame, bootstyle="dark")
        links_frame.grid(row=0, column=2, sticky="nsew", padx=(10, 0))

        ttk.Label(links_frame, text="Links:", font=("Segoe UI", 9, "bold"), bootstyle="light").pack(anchor="w",
                                                                                                    pady=(0, 2))

        links_scroll = ScrolledFrame(links_frame, autohide=True)
        links_scroll.pack(fill="both", expand=True)

        links_json_str = channel_info.get("links", "[]")
        try:
            links = json.loads(links_json_str) if links_json_str else []
        except:
            links = []

        if links:
            for link in links:
                if isinstance(link, str):
                    l_title = link.split("://")[-1].split("/")[0]
                    l_url = link
                else:
                    l_title = link.get("title") or link.get("url", "Link")
                    l_url = link.get("url") or ""

                if len(l_title) > 20:
                    l_title = l_title[:17] + "..."

                if l_url:
                    lbl = ttk.Label(links_scroll, text=f"🔗 {l_title}", font=("Segoe UI", 8, "underline"),
                                    bootstyle="info", cursor="hand2")
                    lbl.pack(anchor="w", pady=1)
                    lbl.bind("<Button-1>", lambda e, u=l_url: webbrowser.open(u))
        else:
            ttk.Label(links_scroll, text="No external links.", font=("Segoe UI", 8, "italic"),
                      bootstyle="secondary").pack(anchor="w")

    @staticmethod
    def open_local_path(path):
        if not path or not path.exists():
            Messagebox.show_warning("Not Found", "Folder does not exist yet. Run metadata fetch first.")
            return
        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.run(["open", path])
        else:
            subprocess.run(["xdg-open", path])

    def on_double_click(self, event):
        selected = self.tree.selection()
        if not selected: return
        if "group" in self.tree.item(selected[0], "tags"):
            self.add_channel()

    def add_group(self):
        dialog = AddGroupDialog(self.winfo_toplevel(), self.add_group_service)
        self.wait_window(dialog)
        if dialog.result:
            self.winfo_toplevel().event_generate("<<DataUpdated>>")

    def add_channel(self):
        selected = self.tree.selection()
        if not selected:
            Messagebox.show_error("Error", "Select a group first")
            return
        parent_iid = selected[0]
        if "group" not in self.tree.item(parent_iid, "tags"):
            Messagebox.show_error("Error", "Select a group, not a channel")
            return
        group_name = self.tree.item(parent_iid, "text")

        dialog = AddChannelDialog(self.winfo_toplevel())
        self.wait_window(dialog)
        if not dialog.result:
            return

        try:
            self.add_channel_service.add_channel(group_name, dialog.result)
            self.winfo_toplevel().event_generate("<<DataUpdated>>")
        except Exception as e:
            Messagebox.show_error("Error", str(e))

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected: return
        if not Messagebox.okcancel("Confirm delete", "Delete selected item(s)?"): return

        for iid in selected:
            if not self.tree.exists(iid): continue
            text = self.tree.item(iid, "text")
            tags = self.tree.item(iid, "tags")
            try:
                if "group" in tags:
                    self.add_group_service.delete_group(text)
                else:
                    self.add_channel_service.delete_channel(text)
            except Exception as e:
                Messagebox.show_error("Error", str(e))

        self.winfo_toplevel().event_generate("<<DataUpdated>>")