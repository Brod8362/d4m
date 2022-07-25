#!/usr/bin/env python
import tkinter
from tkinter import ttk

import d4m.common
import d4m.manage
import d4m.api

class D4mGUI(tkinter.Frame):
    def __init__(self, master, mod_manager):
        super().__init__(master)
        self.pack()

        ttk.Label(self, text="test").pack()
        ttk.Label(self, text="\n".join(str(mod) for mod in mod_manager.mods)).pack()

def main():
    root = tkinter.Tk()
    megamix_path = d4m.common.get_megamix_path()
    if not d4m.common.modloader_is_installed(megamix_path):
        #TODO: show annoying popup box :)
        pass
    
    dml_installed, dml_enabled, dml_mods_dir = d4m.common.get_modloader_info(megamix_path)
    dml_latest, dml_download = d4m.manage.check_modloader_version()
    mod_manager = d4m.manage.ModManager(megamix_path, mods_path=dml_mods_dir)
    app = D4mGUI(root, mod_manager)
    app.master.title(f"d4m v{d4m.common.VERSION}")
    app.mainloop()

if __name__ == "__main__":
    main()