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
    # windows: who knows!
    paths = {
        "linux": os.path.expanduser("~/.steam/steam/config/loginusers.vdf")
    }
    with open(paths[sys.platform], "r") as vdf_fd:
        vdf_data = vdf.parse(vdf_fd)

    for id64 in vdf_data["users"]:
        info = vdf_data["users"][id64]
        if info["MostRecent"] == "1":
            id3 = f"U:1:{int(id64)&0xFFFFFFFF}"
            return SteamUserInfo(id64, id3, info["PersonaName"])

    return None