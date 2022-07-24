import os
from divamod import DivaMod, DivaSimpleMod, UnmanageableModError, diva_mod_create
import api
import tempfile
import shutil
import toml

class ModManager():
    def __init__(self, mods_path):
        self.mods_path = mods_path
        self.mods = load_mods(mods_path)

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

    def install_mod(self, mod_id: int): #mod_id and hash are used for modinfo.toml
        data = api.fetch_mod_data(mod_id)
        with tempfile.TemporaryDirectory(suffix = "d4m") as tempdir:
            api.download_and_extract_mod(data["download"], tempdir)
            extracted = os.listdir(tempdir)
            if "config.toml" in extracted:
                shutil.move(tempdir, os.path.join(self.enabled_path, mod_id))
            elif len(extracted) == 1:
                mod_folder_name = os.path.join(self.enabled_path, extracted[0])
                shutil.move(os.path.join(tempdir, extracted[0]), mod_folder_name)
                with open(os.path.join(mod_folder_name, "modinfo.toml"), "w") as modinfo_fd:
                    data = {
                        "id": mod_id,
                        "hash": data["hash"]
                    }
                    toml.dump(data, modinfo_fd)
                new_mod = diva_mod_create(mod_folder_name)
                self.mods.append(new_mod)
            else:
                pass #TODO: idk lol

    def check_for_updates(self):
        ids = [x.id for x in self.mods if not x.is_simple()]
        api.multi_fetch_mod_data(ids)

def load_mods(path: str) -> "list[DivaSimpleMod]":
    return [diva_mod_create(os.path.join(path, mod_path)) for mod_path in os.listdir(path)]