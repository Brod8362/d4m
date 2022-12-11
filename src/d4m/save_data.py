import os
import sys

import libarchive.constants
import libarchive.public
from d4m.global_config import D4mConfig


class MMSaveDataType:

    def __init__(self, config: D4mConfig):
        self.config = config

    def type_name(self) -> str:
        raise NotImplementedError()

    def display_name(self) -> str:
        raise NotImplementedError

    def exists(self) -> bool:
        return os.path.exists(self.path())

    def path(self) -> str:
        raise NotImplementedError()

    def backup(self, output_file_path: str) -> None:
        files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(self.path()) for f in filenames]
        libarchive.public.create_file(
            output_file_path,
            libarchive.constants.ARCHIVE_FORMAT_ZIP,
            files
        )

    def restore(self, input_file_path: str) -> None:
        extract_to = self.path()
        os.makedirs(self.path(), exist_ok=True)
        with libarchive.public.file_reader(input_file_path) as la:
            for entry in la:
                if entry.filetype.IFDIR:
                    os.makedirs(os.path.join(extract_to, entry.pathname), exist_ok=True)
                else:
                    dest = os.path.join(extract_to, entry.pathname)
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    with open(os.path.join(extract_to, entry.pathname), "xb") as fd:
                        for block in entry.get_blocks():
                            fd.write(block)


class VanillaSaveData(MMSaveDataType):

    def type_name(self) -> str:
        return "vanilla"

    def display_name(self) -> str:
        return "Vanilla"

    def path(self) -> str:
        if sys.platform == "win32":
            return os.path.expandvars("%APPDATA%\\SEGA\\Project Diva MEGA39's")
        elif sys.platform == "linux":
            diva_install_dir = self.config.get_diva_path()
            save_file_loc = os.path.join(diva_install_dir, "..", "..", "compatdata", "1761390", "pfx", "drive_c",
                                         "users", "steamuser", "AppData", "Roaming", "SEGA", "Project DIVA MEGA39's")
            return os.path.realpath(save_file_loc)
        else:
            raise RuntimeError(f"Cannot determine save data install location on your platform ({sys.platform})")


class SongLimitPatchSaveData(MMSaveDataType):

    def type_name(self) -> str:
        return "songlimitpatch"

    def display_name(self) -> str:
        return "Song Limit Patch"

    def path(self) -> str:
        if sys.platform == "win32":
            return os.path.expandvars("%APPDATA%\\DIVA\\Project Diva MEGA39's")
        elif sys.platform == "linux":
            # this is kind of hacky, but I can't think of a better way, if you know of one please let me know
            diva_install_dir = self.config.get_diva_path()
            save_file_loc = os.path.join(diva_install_dir, "..", "..", "compatdata", "1761390", "pfx", "drive_c",
                                         "users", "steamuser", "AppData", "Roaming", "DIVA", "Project DIVA MEGA39's")
            return os.path.realpath(save_file_loc)
        else:
            raise RuntimeError(f"Cannot determine save data install location on your platform ({sys.platform})")


SAVE_DATA_TYPES = [
    VanillaSaveData,
    SongLimitPatchSaveData
]

def inst(type_search: str, config: D4mConfig):
    for x in SAVE_DATA_TYPES:
        sd = x(config)
        if sd.type_name() == type_search:
            return sd
    return None
