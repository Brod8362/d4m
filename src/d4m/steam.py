import dataclasses
import os
import sys
import vdf


@dataclasses.dataclass
class SteamUserInfo:
    id64: str
    id3: str
    persona_name: str


def determine_steam_user_info() -> SteamUserInfo:
    """
    Return id64, username
    """
    # linux: ~/.steam/steam/config/loginusers.vdf
    # windows: %ProgramFiles(x86)%\Steam\config\loginusers.vdf
    if sys.platform == "linux":
        path = os.path.expanduser("~/.steam/steam/config/loginusers.vdf")
    elif sys.platform == "win32":
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\WOW6432Node\Valve\Steam") as steam_key:
            path = os.path.join(winreg.QueryValueEx(steam_key, "InstallPath")[0],
                                os.path.join("config", "loginusers.vdf"))
    else:
        # unsupported platform
        return None

    try:
        with open(path, "r") as vdf_fd:
            vdf_data = vdf.parse(vdf_fd)

        for id64 in vdf_data["users"]:
            info = vdf_data["users"][id64]
            if info["MostRecent"] == "1":
                id3 = f"U:1:{int(id64) & 0xFFFFFFFF}"
                return SteamUserInfo(id64, id3, info["PersonaName"])
    except:
        pass

    return None
