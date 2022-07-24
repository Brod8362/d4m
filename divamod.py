import os
import toml
import packaging.version #TODO: is this in pip?
import api
import functools

class DivaMod():
    def __init__(self, path: str):
        with open(os.path.join(path, "config.toml")) as mod_conf_fd:
            data = toml.load(mod_conf_fd)
            self.version = None if "version" not in data else packaging.version.Version(data["version"])
            self.name = data["name"]
            self.author = data["author"]
            self.id = None
            self.hash = None

        mod_id_path = os.path.join(path, "modinfo.toml")
        if os.path.exists(mod_id_path):
            with open(mod_id_path) as moddata_fd:
                mod_data = toml.load(moddata_fd)
                self.id = mod_data["id"]
                self.hash = mod_data["hash"]

    def is_out_of_date(self): #TODO: how to handle None versions?
        return self.modinfo != None and self.hash != self.modinfo["hash"]
        
    def __str__(self):
        return f'{self.name} ({self.version}) by {self.author}'

    @functools.cached_property
    def modinfo(self):
        return api.fetch_mod_data(self.id) if self.id else None
        