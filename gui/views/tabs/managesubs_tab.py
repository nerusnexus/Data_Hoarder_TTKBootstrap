import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from gui.dialogs.add_group_dialog import AddGroupDialog
from gui.dialogs.add_channel_dialog import AddChannelDialog


class ManageSubsTab(ttk.Frame):
    def __init__(self, parent, add_group_service, add_channel_service):
        super().__init__(parent)
        self.add_group_service = add_group_service
        self.add_channel_service = add_channel_service
        self.tree = None

        self.build_ui()
        self.load_data()

        self.winfo_toplevel().bind("<<DataUpdated>>", self.refresh_tree, add="+")

    def refresh_tree(self, _event=None):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.load_data()

    def load_data(self):
        groups = self.add_group_service.get_all_groups()
        for group in groups:
            group_id = self.tree.insert("", "end", text=group, tags=("group",))
            channels = self.add_channel_service.get_channels_by_group(group)

            for channel in channels:
                self.tree.insert(
                    group_id,
                    "end",
                    text=channel,
                    tags=("channel",)
                )

    def build_ui(self):
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(container, show="tree")
        self.tree.pack(side="left", fill="both", expand=True)

        # BIND DOUBLE CLICK
        self.tree.bind("<Double-1>", self.on_double_click)

        buttons = ttk.Frame(container)
        buttons.pack(side="right", fill="y", padx=(10, 0))

        ttk.Button(buttons, text="+ Group", command=self.add_group).pack(fill="x", pady=5)
        ttk.Button(buttons, text="+ Channel", command=self.add_channel).pack(fill="x", pady=5)
        ttk.Button(buttons, text="Delete", command=self.delete_selected).pack(fill="x", pady=5)

    def on_double_click(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        if "group" in self.tree.item(selected[0], "tags"):
            self.add_channel()

    def add_group(self):
        dialog = AddGroupDialog(
            self.winfo_toplevel(),
            self.add_group_service
        )

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
            self.add_channel_service.add_channel(
                group_name,
                dialog.result
            )
            self.winfo_toplevel().event_generate("<<DataUpdated>>")

        except Exception as e:
            Messagebox.show_error("Error", str(e))

    def delete_selected(self):
        selected = self.tree.selection()

        if not selected:
            return

        if not Messagebox.okcancel(
                "Confirm delete",
                "Delete selected item(s)?"
        ):
            return

        for iid in selected:
            # Prevents crashing if a parent group was deleted, which already auto-deleted the child row
            if not self.tree.exists(iid):
                continue

            text = self.tree.item(iid, "text")
            tags = self.tree.item(iid, "tags")

            try:
                if "group" in tags:
                    self.add_group_service.delete_group(text)
                else:
                    self.add_channel_service.delete_channel(text)

            except Exception as e:
                Messagebox.show_error("Error", str(e))

        # Force the entire tree to reload to perfectly reflect DB state
        self.winfo_toplevel().event_generate("<<DataUpdated>>")