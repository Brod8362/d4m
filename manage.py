from dis import dis
import os
from divamod import DivaMod, UnmanageableModError

class ModManager():
    def __init__(self, enabled_mods, disabled_mods):
        self.enabled = enabled_mods
        self.disabled = disabled_mods

    def enable(self, mod: DivaMod):
        pass

    def disable(self, mod: DivaMod):
        pass 

    def update(self, mod: DivaMod):
        pass

    def is_enabled(self, mod: DivaMod):
        pass


def load_mods(path: str) -> "tuple[list[DivaMod], list[str]]":
    ok = []
    bad = []
    for mod_path in os.listdir(path):
        try:
            ok.append(DivaMod(os.path.join(path, mod_path)))
        except UnmanageableModError:
            bad.append(mod_path)
    return ok, bad