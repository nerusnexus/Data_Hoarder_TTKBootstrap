import ttkbootstrap as ttk
from gui.views.tabs.managesubs_tab import ManageSubsTab
from gui.views.tabs.myaccount_tab import MyAccountTab
from gui.views.tabs.library_tab import LibraryTab # New import

class YtDlpView(ttk.Notebook):
    def __init__(self, parent, services):
        super().__init__(parent)
        self.services = services

        # --- Tabs ---
        self.library_tab = LibraryTab(self, services) # New Tab
        self.managesubs_tab = ManageSubsTab(self, services)
        self.myaccount_tab = MyAccountTab(self, services)

        # --- Add to Notebook ---
        self.add(self.library_tab, text="Library") # Library first
        self.add(self.managesubs_tab, text="Manage Subscriptions")
        self.add(self.myaccount_tab, text="My Account")