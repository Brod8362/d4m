import functools
import packaging.version
import pkg_resources
import requests
import vdf
import os
import toml
from sys import exit, platform

MEGAMIX_APPID = 1761390

VERSION = pkg_resources.get_distribution("d4m").version


def get_vdf_path():
    if platform == "linux":
        return os.path.expanduser("~/.local/share/Steam/config/libraryfolders.vdf")
    elif platform == "win32":
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\WOW6432Node\Valve\Steam") as steam_key:
            return os.path.join(winreg.QueryValueEx(steam_key, "InstallPath")[0],
                                os.path.join("config", "libraryfolders.vdf"))
    elif platform == "darwin":  # TODO: macOS, where is the steam install directory?
        print("macOS is currently unsupported")
        exit(1)
    else:
        print(f"unsupported platform {platform}")
        exit(1)


def get_megamix_path(vdf_path=get_vdf_path()):
    if "D4M_INSTALL_DIR" in os.environ:
        return os.environ["D4M_INSTALL_DIR"]
    with open(vdf_path) as vdf_fd:
        data = vdf.parse(vdf_fd)
        for library_index in data["libraryfolders"]:
            library_folder = data["libraryfolders"][library_index]
            if str(MEGAMIX_APPID) in library_folder["apps"]:
                return os.path.join(library_folder['path'], "steamapps", "common",
                                    "Hatsune Miku Project DIVA Mega Mix Plus")


def modloader_is_installed(megamix_path: str):
    return os.path.isfile(os.path.join(megamix_path, "config.toml"))


def get_modloader_info(megamix_path: str):
    """Calling this function assumes that the modloader is known to be installed."""
    with open(os.path.join(megamix_path, "config.toml")) as conf_fd:
        config = toml.load(conf_fd)
        dml_version = packaging.version.Version(config.get("version", "v0.0.0"))
        enabled = config["enabled"]
        mods_folder = os.path.join(megamix_path, config.get("mods", "mods"))
        return dml_version, enabled, mods_folder


@functools.lru_cache(maxsize=None)
def fetch_latest_d4m_version():
    resp = requests.get(
        f"https://api.github.com/repos/Brod8362/d4m/releases/latest"
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Github API returned {resp.status_code}")
    j = resp.json()
    return (packaging.version.Version(j["name"]),
            j["assets"][0]["browser_download_url"])  # TODO: don't make assumption about assets?
