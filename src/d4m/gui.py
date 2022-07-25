#!/usr/bin/env python
import tkinter
from tkinter import ttk
import tkinter.messagebox
import tkinter.scrolledtext
import traceback

import d4m.common
import d4m.manage
from d4m.manage import ModManager
import d4m.api
from d4m.divamod import DivaSimpleMod
import sys

def log_msg(content: str):
    statusbar.insert(tkinter.END, content+"\n")
    statusbar.update_idletasks()

def show_exc_dialog(what_failed: str, exception: Exception, fatal = True):
    f = tkinter.messagebox.showerror if fatal else tkinter.messagebox.showwarning
    f(what_failed, traceback.format_exc())
    if fatal:
        sys.exit(1)

def on_unhandled_exception(*args):
    tkinter.messagebox.showerror(title="Uncaught Exception", message=traceback.format_exc())
    sys.exit(1)

def create_mod_elem(mod: DivaSimpleMod, root: ttk.Treeview):
    root.insert('', 'end', iid=mod.name, text=str(mod))

def on_dml_toggle_click(root, status_label, mod_manager: ModManager):
    try:
        if mod_manager.enabled:
            mod_manager.disable_dml()
            status_label.set("DISABLED")
        else:
            mod_manager.enable_dml()
            status_label.set("ENABLED")
    except Exception as e:
        show_exc_dialog("Toggling DML", e, fatal = False)

def on_install_mod():
    pass #TODO: score lol

def on_toggle_mod(selections, mod_manager: ModManager, tree: ttk.Treeview):
    for selection in selections:
        mod = next(filter(lambda mod: mod.name == selection, mod_manager.mods))
        if mod_manager.is_enabled(mod):
            mod_manager.disable(mod)
            log_msg(f"Disabled {mod}")
        else:
            mod_manager.enable(mod)
            log_msg(f"Enabled {mod}")

def on_update_mod(selections, mod_manager: ModManager, tree: ttk.Treeview):
    log_msg(f"Attempting to update {len(selections)} mods")
    for selection in selections:
        mod = next(filter(lambda mod: mod.name == selection, mod_manager.mods))
        if mod.is_simple():
            log_msg(f"{str(mod)} has an unknown origin and cannot be updated.")
        else:
            if mod.is_out_of_date():
                log_msg(f"Updating {mod}...")
                mod_manager.update(mod)
                log_msg(f"{mod} updated successfully.")
            else:
                log_msg(f"{mod} is already up to date.")

def on_delete_mod(selections, mod_manager: ModManager, tree: ttk.Treeview):
    content = f"Are you sure you want to delete {len(selections)} mods?\n"+", ".join(selections)
    if tkinter.messagebox.askyesno(title = f"Delete {len(selections)} mods?", message=content):
        for selection in selections:
            mod = next(filter(lambda mod: mod.name == selection, mod_manager.mods))
            mod_manager.delete_mod(mod)
            log_msg(f"Deleted {mod}")

class D4mGUI(tkinter.Frame):
    def __init__(self, master, mod_manager: ModManager):
        super().__init__(master)

        top_row_frame = tkinter.Frame(self)
        mod_list_tree = ttk.Treeview(self)
        mod_actions_frame = tkinter.Frame(self)
        global statusbar
        statusbar = tkinter.scrolledtext.ScrolledText(self, relief=tkinter.SUNKEN, height=5)
        log_msg(f"d4m v{d4m.common.VERSION}")

        # Propogate top row
        tkinter.Label(top_row_frame, text=f"DivaModLoader").pack(side=tkinter.LEFT)
        dml_toggle_text = tkinter.StringVar(self, "ENABLED" if mod_manager.enabled else "DISABLED")
        tkinter.Label(top_row_frame, textvariable=dml_toggle_text).pack(side=tkinter.LEFT)
        tkinter.Button(top_row_frame, text="Toggle DML", command=lambda *args: on_dml_toggle_click(self, dml_toggle_text, mod_manager)).pack(side=tkinter.LEFT)
        mod_count_value = tkinter.StringVar(self, f"-- mods")
        tkinter.Label(top_row_frame, textvariable=mod_count_value).pack(side=tkinter.RIGHT)

        def populate_modlist():
            for a in mod_list_tree.get_children():
                mod_list_tree.delete(a)
            mod_list_tree.delete()
            for (index, mod) in enumerate(mod_manager.mods):
                create_mod_elem(mod, mod_list_tree)
            mod_count_value.set(f"{len(mod_manager.mods)} mods")

        # Propogate modlist
        populate_modlist()

        def autoupdate_button(func, *args):
            func(*args)
            populate_modlist()

        # Propogate action buttons
        tkinter.Button(mod_actions_frame,
            text="Install Mods...",
            command = lambda *_: autoupdate_button(on_install_mod)
        )

        tkinter.Button(mod_actions_frame, 
            text="Toggle Mod", 
            command = lambda *_: autoupdate_button(on_toggle_mod, mod_list_tree.selection(), mod_manager, mod_list_tree)
        ).pack(side=tkinter.LEFT)

        tkinter.Button(mod_actions_frame, 
            text="Update Mod", 
            command = lambda *_: autoupdate_button(on_update_mod, mod_list_tree.selection(), mod_manager, mod_list_tree)
        ).pack(side=tkinter.LEFT)

        tkinter.Button(mod_actions_frame, 
            text="Delete Mod", 
            command = lambda *_: autoupdate_button(on_delete_mod, mod_list_tree.selection(), mod_manager, mod_list_tree)
        ).pack(side=tkinter.LEFT)

        tkinter.Button(mod_actions_frame,
            text="Refresh",
            command = lambda *_: autoupdate_button(mod_manager.reload)
        ).pack(side=tkinter.RIGHT)

        # Populate main GUI
        top_row_frame.pack(side=tkinter.TOP, fill=tkinter.X)
        mod_list_tree.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=True)
        mod_actions_frame.pack(side=tkinter.TOP, fill=tkinter.BOTH)
        statusbar.pack(fill=tkinter.X)
        self.pack(fill=tkinter.BOTH, expand=True, padx=10)

def main():
    root = tkinter.Tk()
    megamix_path = d4m.common.get_megamix_path()
    if not d4m.common.modloader_is_installed(megamix_path):
        #TODO: show annoying popup box :)
        pass
    
    dml_version, dml_enabled, dml_mods_dir = d4m.common.get_modloader_info(megamix_path)
    try:
        dml_latest, dml_download = d4m.manage.check_modloader_version()
        if dml_version < dml_latest:
            if d4m.common.can_autoupdate_dml():
                content = f"A new version of DivaModLoader is available.\nCurrent: {dml_version}\nLatest:{dml_latest}\nDo you want to update?"
                tkinter.messagebox.askyesno(title="DivaModLoader Update Available", message=content)
            else:
                pass
                #dml autoupdate not supported
    except Exception as e:
        show_exc_dialog("Fetching latest DML version", e, fatal=False)

    mod_manager = ModManager(megamix_path, mods_path=dml_mods_dir)
    app = D4mGUI(root, mod_manager)
    app.master.title(f"d4m v{d4m.common.VERSION}")
    tkinter.Tk.report_callback_exception = on_unhandled_exception
    app.mainloop()

if __name__ == "__main__":
    main()