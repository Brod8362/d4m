import functools
from io import BytesIO
import os

import requests
import packaging.version
from d4m.divamod import DivaMod, DivaSimpleMod, UnmanageableModError, diva_mod_create
import d4m.api as api
import tempfile
import shutil
import libarchive.public
import toml

from traceback import print_exc


class ModManager:
    def __init__(self, base_path, mods_path=None):
        self.base_path = base_path
        self.mods_path = mods_path
        with open(os.path.join(self.base_path, "config.toml"), "r") as conf_fd:
            data = toml.load(conf_fd)
            self.enabled = data["enabled"]
            if not mods_path:
                mods_path = data.get("mods", "mods")
        self.mods = self.load_mods(mods_path)

    def disable_dml(self):
        with open(os.path.join(self.base_path, "config.toml"), "r") as conf_fd:
            data = toml.load(conf_fd)
        data["enabled"] = False
        with open(os.path.join(self.base_path, "config.toml"), "w") as conf_fd:
            data = toml.dump(data, conf_fd)
        self.enabled = False

    def enable_dml(self):
        with open(os.path.join(self.base_path, "config.toml"), "r") as conf_fd:
            data = toml.load(conf_fd)
        data["enabled"] = True
        with open(os.path.join(self.base_path, "config.toml"), "w") as conf_fd:
            data = toml.dump(data, conf_fd)
        self.enabled = True

    def enable(self, mod: DivaMod):
        mod.enable()

    def disable(self, mod: DivaMod):
        mod.disable()

    def update(self, mod: DivaMod, fetch_thumbnail=False):
        if not mod.is_simple():
            self.delete_mod(mod)
            self.install_mod(mod.id, mod.category, fetch_thumbnail=fetch_thumbnail, origin=mod.origin)

    def is_enabled(self, mod: DivaMod):
        return mod.enabled

    def delete_mod(self, mod: DivaMod):
        shutil.rmtree(mod.path)
        self.mods.remove(mod)

    def fetch_thumbnail(self, mod: DivaMod, force=False):
        if force or not mod.has_thumbnail():
            data = api.fetch_mod_data(mod.id, mod.category, origin=mod.origin)
            img_url = data["image"]
            resp = requests.get(img_url)
            if resp.status_code == 200:
                with open(os.path.join(mod.path, "preview.png"), "wb") as preview_fd:
                    preview_fd.write(resp.content)

    def install_from_archive(self, archive_path: str):
        with open(archive_path, "rb") as arch_fd:
            with tempfile.TemporaryDirectory(suffix="d4m") as tempdir:
                extract_archive(arch_fd.read(), tempdir)
                extracted = os.listdir(tempdir)
                if "config.toml" in extracted:
                    mod_folder = os.path.basename(archive_path)
                    shutil.move(tempdir, os.path.join(self.mods_path, mod_folder))
                elif len(extracted) == 1:
                    mod_folder = os.path.join(self.mods_path, extracted[0])
                    shutil.move(os.path.join(tempdir, extracted[0]), mod_folder)
                else:
                    raise RuntimeError("failed to install mod from archive: archive format unusable")
                new_mod = diva_mod_create(mod_folder)
                self.mods.append(new_mod)

    def install_mod(self, mod_id: int, category: str, fetch_thumbnail=False,
                    origin="gamebanana"):  # mod_id and hash are used for modinfo.toml
        data = api.fetch_mod_data(mod_id, category, origin=origin)
        with tempfile.TemporaryDirectory(suffix="-d4m") as tempdir:
            api.download_and_extract_mod(data["download"], tempdir)
            extracted = os.listdir(tempdir)
            if "config.toml" in extracted:
                mod_folder_name = os.path.join(self.mods_path,
                                               str(mod_id))  # TODO: move it to a folder using the mod's name
                shutil.move(tempdir, mod_folder_name)
            elif len(extracted) == 1:
                mod_folder_name = os.path.join(self.mods_path, extracted[0])
                shutil.move(os.path.join(tempdir, extracted[0]), mod_folder_name)
            else:
                raise RuntimeError("Failed to install mod: archive directory unusable")
            with open(os.path.join(mod_folder_name, "modinfo.toml"), "w") as modinfo_fd:
                data = {
                    "id": mod_id,
                    "hash": data["hash"],
                    "origin": origin,
                    "category": category
                }
                toml.dump(data, modinfo_fd)
            new_mod = diva_mod_create(mod_folder_name)

            self.mods.append(new_mod)

            # download mod thumbnail
            if fetch_thumbnail:
                self.fetch_thumbnail(new_mod)

    def check_for_updates(self, get_thumbnails=False):
        for origin in api.SUPPORTED_APIS.keys():
            mods_from_origin = self.mods_from(origin)
            api.multi_fetch_mod_data(set(map(lambda x: (x.id, x.category), mods_from_origin)), origin=origin)
        if get_thumbnails:
            for mod in self.mods:
                if not mod.is_simple():
                    try:
                        self.fetch_thumbnail(mod)
                    except Exception as e:
                        print(f"failed to get thumbnail {e}")

    def mods_from(self, origin):
        """Return a list of mods from a specified origin."""
        return [m for m in self.mods if not m.is_simple() and m.origin == origin]

    def mod_is_installed(self, s_id, origin: str = "gamebanana") -> bool:
        for mod in self.mods:
            if not mod.is_simple() and mod.id == s_id and mod.origin == origin:
                return True
        return False

    def reload(self):
        self.mods = self.load_mods(self.mods_path)

    def load_mods(self, path: str) -> "list[DivaSimpleMod]":
        with open(os.path.join(self.base_path, "config.toml"), "r", encoding="utf-8") as fd:
            priority = toml.load(fd).get("priority", [])
        loaded = []
        for mod_path in os.listdir(path):
            full_mod_path = os.path.join(path, mod_path)
            if os.path.isdir(full_mod_path):
                try:
                    loaded.append(diva_mod_create(full_mod_path))
                except:
                    print_exc()
        final = []
        ##now, order by priority
        for l in priority:
            for index, mod in enumerate(loaded):
                if os.path.basename(mod.path) == l:
                    final.append(loaded.pop(index))
                    break

        final.extend(loaded)  # append whatever is left as bottom priority
        return final

    def save_priority(self):
        dml_conf_path = os.path.join(self.base_path, "config.toml")
        with open(dml_conf_path, "r", encoding="utf-8") as fd:
            d = toml.load(fd)
        d["priority"] = [os.path.basename(m.path) for m in self.mods]
        with open(dml_conf_path, "w", encoding="utf-8") as fd:
            toml.dump(d, fd)


def extract_archive(archive: bytes, extract_to: str) -> None:
    try:
        with libarchive.public.memory_reader(archive) as la:
            for entry in la:
                if entry.filetype.IFDIR:
                    os.makedirs(os.path.join(extract_to, entry.pathname), exist_ok=True)
                else:
                    dest = os.path.join(extract_to, entry.pathname)
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    with open(os.path.join(extract_to, entry.pathname), "xb") as fd:
                        for block in entry.get_blocks():
                            fd.write(block)

    except Exception as e:
        if isinstance(e, RuntimeError):
            raise e
        else:
            print_exc()
            raise RuntimeError(f"libarchive error {e}")  # TODO: there's probably a better exception for this


def install_modloader(diva_path: str):
    version, download_url = check_modloader_version()
    resp = requests.get(download_url)
    if resp.status_code != 200:
        raise RuntimeError(f"Github API returned {resp.status_code}")
    with libarchive.public.memory_reader(resp.content) as la:
        for entry in la:
            if entry.filetype.IFDIR:
                print(f"dir: {entry.pathname}")
                os.makedirs(os.path.join(diva_path, entry.pathname), exist_ok=True)
            else:
                dest = os.path.join(diva_path, entry.pathname)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                print(f"file: {entry.pathname}")
                if entry.pathname == "config.toml":
                    with open(dest, "w") as fd:
                        toml_buf = BytesIO()
                        [toml_buf.write(block) for block in entry.get_blocks()]
                        toml_buf.seek(0)
                        data = toml.loads(toml_buf.read().decode("UTF-8"))
                        data["version"] = str(version)
                        toml.dump(data, fd)
                else:
                    with open(os.path.join(diva_path, entry.pathname), "wb") as fd:
                        for block in entry.get_blocks():
                            fd.write(block)


@functools.lru_cache(maxsize=None)
def check_modloader_version() -> "tuple[packaging.version.Version,str]":
    resp = requests.get(
        f"https://api.github.com/repos/blueskythlikesclouds/DivaModLoader/releases/latest"
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Github API returned {resp.status_code}")
    j = resp.json()
    return (packaging.version.Version(j["name"]),
            j["assets"][0]["browser_download_url"])  # TODO: don't make assumption about assets?
