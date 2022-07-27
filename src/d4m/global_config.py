import appdirs
import os
import toml
import d4m.common

CONFIG_PATH = os.path.join(appdirs.user_data_dir(), "d4m.toml")

CONFIG_OPTIONS = [
    ("diva_path", d4m.common.get_megamix_path()),
    ("last_d4m_update_check", 0),
    ("last_dmm_update_check", 0),

]


class D4mConfig:
    def __init__(self):
        self.data = dict(CONFIG_OPTIONS)
        try:
            with open(CONFIG_PATH, "r") as conf_fd:
                data = toml.load(conf_fd)
                for (k, v) in CONFIG_OPTIONS:
                    data[k] = v
        except FileNotFoundError:
            self.write()

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __delitem__(self, key):
        self.data.pop(key)

    def write(self):
        with open(CONFIG_PATH, "w") as conf_fd:
            toml.dump(self.data, conf_fd)

    def get_diva_path(self):
        return self.data["diva_path"]
