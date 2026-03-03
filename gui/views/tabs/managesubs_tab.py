import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.widgets.scrolled import ScrolledFrame
import os
import sys
import subprocess
from gui.dialogs.add_group_dialog import AddGroupDialog
from gui.dialogs.add_channel_dialog import AddChannelDialog
from config import FONTS_DIR
from gui.components.channel_card import ChannelCard


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

        self.build_ui()
        self.load_data()
        self.winfo_toplevel().bind("<<DataUpdated>>", self.refresh_all, add="+")

    def refresh_all(self, _event=None):
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

                # Use the new external Component
                card = ChannelCard(group_lf, channel_info, self.add_channel_service, self.has_icon_font,
                                   self.open_local_path)
                card.grid(row=card_idx, column=0, padx=10, pady=(10, 10), sticky="nsew")
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