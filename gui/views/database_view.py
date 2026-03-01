import ttkbootstrap as ttk
from gui.views.tabs.db_treeview_tab import DbTreeviewTab

class DatabaseView(ttk.Notebook):
    def __init__(self, parent, services):
        super().__init__(parent)
        self.services = services

        self.tree_tab = None
        self.manage_tab = None

        self.build()

    def build(self):
        # FIXED: Changed self.services.add_channel to self.services.add_channel_service
        self.tree_tab = DbTreeviewTab(self, self.services.add_channel_service)
        self.manage_tab = ttk.Frame(self)

        # Add tabs to the notebook
        self.add(self.tree_tab, text="Full Video List")
        self.add(self.manage_tab, text="Manage")