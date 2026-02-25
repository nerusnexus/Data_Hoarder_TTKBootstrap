from pathlib import Path
from services.settings_service import SettingsService
from services.ytdlp_service import YtDlpService
from services.account_service import AccountService
from services.subservices.addgroup_service import AddGroupService
from services.subservices.addchannel_service import AddChannelService
from services.db.database_initializer import initialize_database

class AppServices:
    def __init__(self, style, data_folder: Path):
        self.style = style
        self.data_folder = data_folder
        self.db_path = self.data_folder / "database.db"

        # 🔥 Initialize DB once
        initialize_database(self.db_path)

        self.settings = SettingsService(data_folder)
        self.ytdlp = YtDlpService(data_folder)
        self.account = AccountService(data_folder)

        self.add_group = AddGroupService(self.db_path)
        self.add_channel = AddChannelService(self.db_path)

    def get_available_themes(self):
        return self.style.theme_names()

    def get_current_theme(self):
        return self.style.theme.name

    def change_theme(self, theme_name: str):
        self.settings.set_theme(theme_name)
        self.style.theme_use(theme_name)