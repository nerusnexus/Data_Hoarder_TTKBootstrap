import ttkbootstrap as ttk
from gui.views.tabs.managesubs_tab import ManageSubsTab
from gui.views.tabs.myaccount_tab import MyAccountTab
from gui.views.tabs.library_tab import LibraryTab


class YtDlpView(ttk.Notebook):
    def __init__(self, parent, services):
        super().__init__(parent)

        # Inject only required subservices into each tab
        self.library_tab = LibraryTab(
            self,
            add_group_service=services.add_group,
            add_channel_service=services.add_channel
        )

        self.managesubs_tab = ManageSubsTab(
            self,
            add_group_service=services.add_group,
            add_channel_service=services.add_channel
        )

        self.myaccount_tab = MyAccountTab(
            self,
            account_service=services.account,
            ytdlp_service=services.ytdlp
        )

        self.add(self.library_tab, text="Library")
        self.add(self.managesubs_tab, text="Manage Subscriptions")
        self.add(self.myaccount_tab, text="My Account")