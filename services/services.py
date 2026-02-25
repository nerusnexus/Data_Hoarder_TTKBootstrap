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
        # Define the metadata folder path
        self.metadata_folder = self.data_folder / "Metadata"

        # Ensure necessary folders exist
        self.metadata_folder.mkdir(parents=True, exist_ok=True)
        initialize_database(self.db_path)

        self.settings = SettingsService(data_folder)
        self.ytdlp = YtDlpService(self.db_path)
        self.account = AccountService(data_folder)

        self.add_group = AddGroupService(self.db_path)
        # Inject the metadata folder and ytdlp service
        self.add_channel = AddChannelService(self.db_path, self.metadata_folder, self.ytdlp)

    def get_available_themes(self):
        return self.style.theme_names()

    def get_current_theme(self):
        return self.style.theme.name

    def change_theme(self, theme_name: str):
        self.settings.set_theme(theme_name)
        self.style.theme_use(theme_name)