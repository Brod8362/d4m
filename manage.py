import os
from divamod import DivaMod, UnmanageableModError
import api
import tempfile
import shutil
import toml

class ModManager():
    def __init__(self, base, enabled_valid, disabled_valid, enabled_invalid, disabled_invalid):
        self.base = base

    def enable(self, mod: DivaMod):
        pass

    def disable(self, mod: DivaMod):
        pass 

    def update(self, mod: DivaMod):
        pass

    def is_enabled(self, mod: DivaMod):
        pass

    def install_mod(self, mod_id: int): #mod_id and hash are used for modinfo.toml
        data = api.fetch_mod_data(mod_id)
        with tempfile.TemporaryDirectory(suffix = "d4m") as tempdir:
            api.download_and_extract_mod(data["download"], tempdir)
            extracted = os.listdir(tempdir)
            if "config.toml" in extracted:
                shutil.move(tempdir, os.path.join(self.base, mod_id))
            elif len(extracted) == 1:
                mod_folder_name = os.path.join(self.base, extracted[0])
                shutil.move(os.path.join(tempdir, extracted[0]), mod_folder_name)
                with open(os.path.join(mod_folder_name, "modinfo.toml"), "w") as modinfo_fd:
                    data = {
                        "id": mod_id,
                        "hash": data["hash"]
                    }
                    toml.dump(data, modinfo_fd)
            else:
                pass #TODO: idk lol




def load_mods(path: str) -> "tuple[list[DivaMod], list[str]]":
    ok = []
    bad = []
    for mod_path in os.listdir(path):
        try:
            ok.append(DivaMod(os.path.join(path, mod_path)))
        except UnmanageableModError:
            bad.append(mod_path)
    return ok, bad
