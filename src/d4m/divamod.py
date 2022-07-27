import os
import toml
import packaging.version
import d4m.api as api
import functools


class UnmanageableModError(ValueError):
    pass


def diva_mod_create(path: str):
    try:
        return DivaMod(path)
    except:
        return DivaSimpleMod(path)


class DivaSimpleMod:
    def __init__(self, path: str):
        self.path = path
        with open(os.path.join(path, "config.toml")) as mod_conf_fd:
            data = toml.load(mod_conf_fd)
            self.version = None if "version" not in data else packaging.version.Version(data["version"])
            self.name = data.get("name", os.path.basename(path))
            self.author = data.get("author", "unknown author")
            self.enabled = data["enabled"]
        self.size_bytes = sum(
            os.path.getsize(os.path.join(dirpath, filename)) for dirpath, _, filenames in os.walk(path) for filename in
            filenames)

    def __str__(self):
        return f'{self.name} ({self.version}) by {self.author}'

    def enable(self):
        with open(os.path.join(self.path, "config.toml"), "r") as mod_conf_fd:
            data = toml.load(mod_conf_fd)
        data["enabled"] = True
        with open(os.path.join(self.path, "config.toml"), "w") as mod_conf_fd:
            toml.dump(data, mod_conf_fd)
            self.enabled = True

    def disable(self):
        with open(os.path.join(self.path, "config.toml"), "r") as mod_conf_fd:
            data = toml.load(mod_conf_fd)
        data["enabled"] = False
        with open(os.path.join(self.path, "config.toml"), "w") as mod_conf_fd:
            toml.dump(data, mod_conf_fd)
            self.enabled = False

    def has_thumbnail(self):
        return os.path.exists(os.path.join(self.path, "preview.png"))

    def get_thumbnail_bytes(self):
        if self.has_thumbnail():
            with open(os.path.join(self.path, "preview.png"), "rb") as fd:
                return fd.read()
        return None

    def get_thumbnail_path(self):
        if self.has_thumbnail():
            return os.path.join(self.path, "preview.png")
        else:
            None

    def is_simple(self):
        return True


class DivaMod(DivaSimpleMod):
    def __init__(self, path: str):
        super().__init__(path)
        try:
            mod_id_path = os.path.join(path, "modinfo.toml")
            with open(mod_id_path) as moddata_fd:
                mod_data = toml.load(moddata_fd)
                self.id = mod_data["id"]
                self.hash = mod_data["hash"]
        except (IOError, KeyError):
            raise UnmanageableModError

    def is_out_of_date(self):
        return self.modinfo != None and self.hash != self.modinfo["hash"]

    def __eq__(self, other):
        return type(self) == type(other) and self.id == other.id

    def is_simple(self):
        return False

    @functools.cached_property
    def modinfo(self):
        return api.fetch_mod_data(self.id)
