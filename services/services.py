from services.settings_service import SettingsService
from services.ytdlp_service import YtDlpService
from services.account_service import AccountService
from services.subservices.addgroup_service import AddGroupService
from services.subservices.addchannel_service import AddChannelService
from services.subservices.fetchmetadata_service import FetchMetadataService # NEW
from services.db.database_initializer import initialize_database


class AppServices:
    def __init__(self, style):
        self.style = style

        # Initialize the database
        initialize_database()

        # Initialize all services
        self.settings = SettingsService()
        self.ytdlp = YtDlpService()
        self.account = AccountService()
        self.add_group = AddGroupService()
        self.add_channel = AddChannelService(self.ytdlp)
        self.fetch_metadata = FetchMetadataService() # NEW

    def get_available_themes(self):
        return self.style.theme_names()

    def get_current_theme(self):
        return self.style.theme.name

    def change_theme(self, theme_name: str):
        self.settings.set_theme(theme_name)
        self.style.theme_use(theme_name)