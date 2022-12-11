from d4m.global_config import D4mConfig
from d4m.gui.d4m_logging import D4mLogger
from d4m.manage import ModManager
from d4m.steam import SteamUserInfo


class D4mGlobalContext:
    def __init__(self, config: D4mConfig, logger: D4mLogger, mod_manager: ModManager, steam_info: SteamUserInfo):
        self.config = config
        self.logger = logger
        self.mod_manager = mod_manager
        self.steam_info = steam_info