import io
import os
import sys
import time

import libarchive.constants
import libarchive.public
import toml

import d4m.common
from d4m.gui.context import D4mGlobalContext


def platform_expand(game_type: str, context: D4mGlobalContext) -> str:
    if sys.platform == "win32":
        return os.path.expandvars(f"%APPDATA%\\{game_type}\\Project DIVA MEGA39's\\Steam\\{context.steam_info.id64}\\")
    elif sys.platform == "linux":
        diva_install_dir = context.config.get_diva_path()
        save_file_loc = os.path.join(diva_install_dir, "..", "..", "compatdata", "1761390", "pfx", "drive_c",
                                     "users", "steamuser", "AppData", "Roaming", game_type, "Project DIVA MEGA39's",
                                     "Steam", context.steam_info.id64
                                     )
        return os.path.realpath(save_file_loc)
    else:
        raise RuntimeError(f"Cannot determine save data install location on your platform ({sys.platform})")


def detect_backup_info(file_path: str) -> dict:
    with libarchive.public.file_reader(file_path) as la:
        for entry in la:
            if entry.filetype.IFDIR:
                pass
            else:
                if entry.pathname == "d4m_meta.toml":
                    buffer = io.BytesIO()
                    for block in entry.get_blocks():
                        buffer.write(block)
                    buffer.seek(0)
                    return toml.loads(buffer.read().decode("UTF-8"))


class MMSaveDataType:

    def __init__(self, context: D4mGlobalContext):
        self.context = context

    def type_name(self) -> str:
        raise NotImplementedError()

    def display_name(self) -> str:
        raise NotImplementedError

    def exists(self) -> bool:
        return os.path.exists(self.path())

    def path(self) -> str:
        raise NotImplementedError()

    def backup(self, output_file_path: str) -> None:
        prev_wd = os.getcwd()
        # TODO yeah, this is jank as shit, but it's temporary
        # changing working directory to avoid reading libarchive documentation
        # i'm sure this will never go wrong
        input_path = self.path()
        os.chdir(input_path)
        metadata = {
            "type": self.type_name(),
            "steam_id": self.context.steam_info.id64,
            "timestamp": int(time.time()),
            "d4m_version": d4m.common.VERSION
        }
        with open("d4m_meta.toml", "w") as fd:
            toml.dump(metadata, fd)
        libarchive.public.create_file(
            output_file_path,
            libarchive.constants.ARCHIVE_FORMAT_ZIP,
            os.listdir(input_path)
        )
        os.remove("d4m_meta.toml")
        os.chdir(prev_wd)

    def restore(self, input_file_path: str) -> None:
        extract_to = self.path()
        os.makedirs(self.path(), exist_ok=True)
        with libarchive.public.file_reader(input_file_path) as la:
            for entry in la:
                if entry.filetype.IFDIR:
                    continue
                else:
                    if entry.pathname == "d4m_meta.toml":
                        continue
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
        return platform_expand("SEGA", self.context)


class SongLimitPatchSaveData(MMSaveDataType):

    def type_name(self) -> str:
        return "songlimitpatch"

    def display_name(self) -> str:
        return "Song Limit Patch"

    def path(self) -> str:
        return platform_expand("DIVA", self.context)


SAVE_DATA_TYPES = [
    VanillaSaveData,
    SongLimitPatchSaveData
]


def inst(type_search: str, context: D4mGlobalContext):
    for x in SAVE_DATA_TYPES:
        sd = x(context)
        if sd.type_name() == type_search:
            return sd
    return None
