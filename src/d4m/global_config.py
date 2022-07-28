import appdirs
import os
import toml
import d4m.common

CONFIG_PATH = os.path.join(appdirs.user_config_dir(), "d4m.toml")

CONFIG_OPTIONS = [
    ("last_d4m_update_check", 0),
    ("last_dmm_update_check", 0),
]


class D4mConfig:
    def __init__(self):
        self.data = dict(CONFIG_OPTIONS)
        try:
            with open(CONFIG_PATH, "r") as conf_fd:
                loaded_conf = toml.load(conf_fd)
                for k in loaded_conf:
                    self.data[k] = loaded_conf[k]
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
        if "D4M_INSTALL_DIR" in os.environ:
            return os.environ["D4M_INSTALL_DIR"]

        return self.data.get("diva_path", d4m.common.get_megamix_path())
        
