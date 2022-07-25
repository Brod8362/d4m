#!/usr/bin/env python
import tkinter
from tkinter import ttk

import d4m.common
import d4m.manage
from d4m.manage import ModManager
import d4m.api
from d4m.divamod import DivaSimpleMod

def create_mod_elem(mod: DivaSimpleMod, root: ttk.Treeview):
    root.insert('', 'end', iid=mod.name, text=str(mod))

class D4mGUI(tkinter.Frame):
    def __init__(self, master, mod_manager: ModManager):
        super().__init__(master)
        self.pack(fill=tkinter.BOTH, expand=True, padx=10)

        top_row_frame = tkinter.Frame(self)

        tkinter.Label(top_row_frame, text="<dml status>").pack(side=tkinter.LEFT)
        tkinter.Button(top_row_frame, text="Toggle DML", command=lambda x: None).pack(side=tkinter.LEFT)
        tkinter.Label(top_row_frame, text=f"{len(mod_manager.mods)} mods").pack(side=tkinter.RIGHT)

        mod_list_tree = ttk.Treeview(self)

        for (index, mod) in enumerate(mod_manager.mods):
            create_mod_elem(mod, mod_list_tree)

        mod_actions_frame = tkinter.Frame(self)
        tkinter.Button(mod_actions_frame, text="Toggle Mod", command = lambda x: None).pack(side=tkinter.LEFT)
        tkinter.Button(mod_actions_frame, text="Update Mod", command = lambda x: None).pack(side=tkinter.LEFT)
        tkinter.Button(mod_actions_frame, text="Delete Mod", command = lambda x: None).pack(side=tkinter.LEFT)

        statusbar = tkinter.Label(self, text=f"d4m v{d4m.common.VERSION}", bd=1, relief=tkinter.SUNKEN, anchor=tkinter.W)

        #TODO: fill all widgets here

        top_row_frame.pack(side=tkinter.TOP, fill=tkinter.X)
        mod_list_tree.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=True)
        mod_actions_frame.pack(side=tkinter.TOP, fill=tkinter.BOTH)
        statusbar.pack(side=tkinter.TOP, fill=tkinter.X)

def main():
    root = tkinter.Tk()
    megamix_path = d4m.common.get_megamix_path()
    if not d4m.common.modloader_is_installed(megamix_path):
        #TODO: show annoying popup box :)
        pass
    
    dml_version, dml_enabled, dml_mods_dir = d4m.common.get_modloader_info(megamix_path)
    dml_latest, dml_download = d4m.manage.check_modloader_version()
    if dml_version < dml_latest:
        #TODO: prompt for DML update
        pass

    mod_manager = ModManager(megamix_path, mods_path=dml_mods_dir)
    app = D4mGUI(root, mod_manager)
    app.master.title(f"d4m v{d4m.common.VERSION}")
    app.mainloop()

if __name__ == "__main__":
    main()