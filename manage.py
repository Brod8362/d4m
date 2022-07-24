import os
from divamod import DivaMod, DivaSimpleMod, UnmanageableModError, diva_mod_create
import api
import tempfile
import shutil
import toml

class ModManager():
    def __init__(self, enabled_path, disabled_path):
        self.enabled_path = enabled_path
        self.disabled_path = disabled_path
        self.enabled = load_mods(enabled_path)
        self.disabled = load_mods(disabled_path)

    def enable(self, mod: DivaMod):
        if mod in self.disabled:
            self.disabled.remove(mod)
            self.enabled.append(mod)
            pass

    def disable(self, mod: DivaMod):
        if mod in self.enabled:
            self.enabled.remove(mod)
            self.disabled.append(mod)
            pass

    def update(self, mod: DivaMod):
        if not mod.is_simple():
            self.delete_mod(mod)
            self.install_mod(mod.id)

    def is_enabled(self, mod: DivaMod):
        return mod in self.enabled

    def delete_mod(self, mod: DivaMod):
        cols = [self.enabled, self.disabled]
        for c in cols:
            if mod in c:
                c.remove(mod)
        shutil.rmtree(mod.path)
        
    def mods(self):
        return (self.enabled + self.disabled)

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
                self.enabled.append(new_mod)
            else:
                pass #TODO: idk lol

def load_mods(path: str) -> "list[DivaSimpleMod]":
    return [diva_mod_create(os.path.join(path, mod_path)) for mod_path in os.listdir(path)]