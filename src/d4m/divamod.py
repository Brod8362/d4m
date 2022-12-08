import os
import toml
import packaging.version
import d4m.api as api
import functools
import json


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
        with open(os.path.join(path, "config.toml"), "r", encoding="UTF-8") as mod_conf_fd:
            data = toml.load(mod_conf_fd)
            self.version = None
            try:
                self.version = packaging.version.Version(data["version"])
            except packaging.version.InvalidVersion:
                #mod version is unparseable
                pass
            except KeyError:
                # mod does not have a version specified in the config
                pass
            self.name = data.get("name", os.path.basename(path))
            self.author = data.get("author", "unknown author")
            self.enabled = data["enabled"]
        self.size_bytes = sum(
            os.path.getsize(os.path.join(dirpath, filename)) for dirpath, _, filenames in os.walk(path) for filename in
            filenames)

    def __str__(self):
        return f'{self.name} ({self.version}) by {self.author}'

    def enable(self):
        with open(os.path.join(self.path, "config.toml"), "r", encoding="UTF-8") as mod_conf_fd:
            data = toml.load(mod_conf_fd)
        data["enabled"] = True
        with open(os.path.join(self.path, "config.toml"), "w", encoding="UTF-8") as mod_conf_fd:
            toml.dump(data, mod_conf_fd)
            self.enabled = True

    def disable(self):
        with open(os.path.join(self.path, "config.toml"), "r", encoding="UTF-8") as mod_conf_fd:
            data = toml.load(mod_conf_fd)
        data["enabled"] = False
        with open(os.path.join(self.path, "config.toml"), "w", encoding="UTF-8") as mod_conf_fd:
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

    def can_attempt_dmm_migration(self) -> bool:
        return os.path.exists(os.path.join(self.path, "mod.json"))

    def attempt_migrate_from_dmm(self) -> bool:
        """Attempt to use dmm's mod.json file to get metadata."""
        try:
            with open(os.path.join(self.path, "mod.json"), "r", encoding="UTF-8") as dmm_fd:
                dmm_data = json.load(dmm_fd)
                if "homepage" in dmm_data:
                    homepage = dmm_data["homepage"]
                    if "gamebanana" in homepage:
                        potential_id = homepage.split("/")[-1]
                        try:
                            api.fetch_mod_data(potential_id, "Mod", origin="gamebanana") #TODO: maybe don't assume mod here?
                            with open(os.path.join(self.path, "modinfo.toml"), "w", encoding="UTF-8") as d4m_fd:
                                d4m_mod_data = {
                                    "id": potential_id,
                                    "hash": "no-hash",
                                    "origin": "gamebanana",
                                    "category": "Mod"
                                }
                                toml.dump(d4m_mod_data, d4m_fd)
                                return True
                        except:
                            return False
        except:
            return False
        return False

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
                self.origin = mod_data.get("origin", "gamebanana") #gamebanana compat
                self.category = mod_data.get("category", "Mod") #gamebanana compat
        except (IOError, KeyError):
            raise UnmanageableModError

    def is_out_of_date(self):
        return self.modinfo != None and self.hash != self.modinfo["hash"]

    def __eq__(self, other):
        return type(self) == type(other) and self.id == other.id

    def is_simple(self):
        return False

    def can_attempt_dmm_migration(self) -> bool:
        return False

    @functools.cached_property
    def modinfo(self):
        return api.fetch_mod_data(self.id, self.category, origin=self.origin)
