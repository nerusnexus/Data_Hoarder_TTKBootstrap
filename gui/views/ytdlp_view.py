import ttkbootstrap as ttk
from gui.views.tabs.managesubs_tab import ManageSubsTab
from gui.views.tabs.myaccount_tab import MyAccountTab


class YtDlpView(ttk.Notebook):
    def __init__(self, parent, services):
        super().__init__(parent)

        self.services = services

        # --- Tabs ---
        self.managesubs_tab = ManageSubsTab(self, services)
        self.myaccount_tab = MyAccountTab(self, services)

        # --- Add to Notebook ---
        self.add(self.managesubs_tab, text="Manage Subscriptions")
        self.add(self.myaccount_tab, text="My Account")