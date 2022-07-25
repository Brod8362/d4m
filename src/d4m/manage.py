import functools
from io import BytesIO
import os

import requests
import packaging.version
from d4m.divamod import DivaMod, DivaSimpleMod, UnmanageableModError, diva_mod_create
import d4m.api as api
import tempfile
import shutil
import toml

class ModManager():
    def __init__(self, base_path, mods_path = None):
        self.base_path = base_path
        self.mods_path = mods_path
        with open(os.path.join(self.base_path, "config.toml"), "r") as conf_fd:
            data = toml.load(conf_fd)
            self.enabled = data["enabled"]
            if not mods_path:
                mods_path = data.get("mods", "mods")
        self.mods = load_mods(mods_path)

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
            
    def update(self, mod: DivaMod):
        if not mod.is_simple():
            self.delete_mod(mod)
            self.install_mod(mod.id)

    def is_enabled(self, mod: DivaMod):
        return mod.enabled

    def delete_mod(self, mod: DivaMod):
        shutil.rmtree(mod.path)
        self.mods.remove(mod)

    def fetch_thumbnail(self, mod: DivaMod, force=False):
        if force or not mod.has_thumbnail():
            data = api.fetch_mod_data(mod.id)
            img_url = data["image"]
            resp = requests.get(img_url)
            if resp.status_code == 200:
                with open(os.path.join(mod.path, "preview.png"), "wb") as preview_fd:
                    preview_fd.write(resp.content)
                    

    def install_mod(self, mod_id: int, fetch_thumbnail=False): #mod_id and hash are used for modinfo.toml
        data = api.fetch_mod_data(mod_id)
        with tempfile.TemporaryDirectory(suffix = "d4m") as tempdir:
            api.download_and_extract_mod(data["download"], tempdir)
            extracted = os.listdir(tempdir)
            if "config.toml" in extracted:
                shutil.move(tempdir, os.path.join(self.mods_path, mod_id))
            elif len(extracted) == 1:
                mod_folder_name = os.path.join(self.mods_path, extracted[0])
                shutil.move(os.path.join(tempdir, extracted[0]), mod_folder_name)
                with open(os.path.join(mod_folder_name, "modinfo.toml"), "w") as modinfo_fd:
                    data = {
                        "id": mod_id,
                        "hash": data["hash"]
                    }
                    toml.dump(data, modinfo_fd)
                new_mod = diva_mod_create(mod_folder_name)

                self.mods.append(new_mod)

                #download mod thumbnail
                if fetch_thumbnail:
                   self.fetch_thumbnail(new_mod)
            else:
                raise RuntimeError("Failed to install mod: archive directory unusable")

    def check_for_updates(self, get_thumbnails=False):
        ids = [x.id for x in self.mods if not x.is_simple()]
        api.multi_fetch_mod_data(ids)
        if get_thumbnails:
            for mod in self.mods:
                if not mod.is_simple():
                    try:
                        self.fetch_thumbnail(mod)
                    except Exception as e:
                        print(f"failed to get thumbnail {e}")

    def mod_is_installed(self, s_id) -> bool:
        for mod in self.mods:
            if not mod.is_simple() and mod.id == s_id:
                return True
        return False

    def reload(self):
        self.mods = load_mods(self.mods_path)

def load_mods(path: str) -> "list[DivaSimpleMod]":
    return [diva_mod_create(os.path.join(path, mod_path)) for mod_path in os.listdir(path)]

def install_modloader(diva_path: str):
    try:
        import libarchive.public
    except:
        raise RuntimeError("Modloader installation not supported on this platform")
    #TODO: add check here to see if platform supports this
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
                print(f"file: {entry.pathname}")
                if entry.pathname == "config.toml":
                    with open(os.path.join(diva_path, entry.pathname), "w") as fd:
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
    

@functools.cache
def check_modloader_version() -> "tuple[packaging.version.Version,str]": 
    resp = requests.get(
        f"https://api.github.com/repos/blueskythlikesclouds/DivaModLoader/releases/latest"
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Github API returned {resp.status_code}")
    j = resp.json()
    return (packaging.version.Version(j["name"]), j["assets"][0]["browser_download_url"]) #TODO: don't make assumption about assets?