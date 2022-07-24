import os
import toml
import packaging.version #TODO: is this in pip?

def get_or_else(indexable, index, default):
    return indexable[index] if 0 <= index < len(indexable) else default

class DivaMod():
    def __init__(self, path: str):
        with open(os.path.join(path, "config.toml")) as mod_conf_fd:
            data = toml.load(mod_conf_fd)
            self.version = None if "version" not in data else packaging.version.Version(data["version"])
            self.name = data["name"]
            self.author = data["author"]
            #TODO: look up the id in the lookup database

    def is_out_of_date(self, t: "tuple[int,int,int]"): #TODO: how to handle None versions?
        (major, minor, patch) = t
        return (major > self.version.major or minor > self.version.minor or patch > self.version.micro)
        
    def __str__(self):
        return f'{self.name} ({self.version}) by {self.author}'
