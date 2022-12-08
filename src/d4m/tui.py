import os
import subprocess
import sys
import time

import colorama
import packaging
from simple_term_menu import TerminalMenu

import d4m.api as api
from d4m.common import (VERSION, get_modloader_info,
                        modloader_is_installed, fetch_latest_d4m_version)
from d4m.global_config import D4mConfig
from d4m.manage import ModManager, check_modloader_version, install_modloader

from traceback import print_exc


def generate_preview(mod_str: str, mod_manager: ModManager):
    content = []
    found = list(filter(lambda x: str(x) == mod_str, mod_manager.mods))
    if not found:
        return ""
    mod = found[0]
    content.append(f"Name: {mod.name}")
    content.append(f"Author: {mod.author}")
    content.append(f"Version: {mod.version}")
    enable_str = f"{colorama.Fore.GREEN}Enabled{colorama.Fore.RESET}" if mod_manager.is_enabled(
        mod) else f"{colorama.Fore.RED}Disabled{colorama.Fore.RESET}"
    content.append(f"Status: {enable_str}")
    content.append(f"Install Path: {mod.path}")
    if not mod.is_simple():
        content.append(f"Origin: {mod.origin}")
        content.append(f"Mod ID: {mod.id}")
        try:
            utd_str = f"{colorama.Fore.YELLOW}Out of date{colorama.Fore.RESET}" if mod.is_out_of_date() else f"{colorama.Fore.GREEN}Up to date{colorama.Fore.RESET}"
        except RuntimeError as e:
            utd_str = f"Failed to check update: {colorama.Fore.RED}{e}{colorama.Fore.RESET}"
        content.append(utd_str)

    return "\n".join(content)


def menu_install(mod_manager: ModManager):
    search_str = input("Search for a mod...:")
    gb_mods = api.search_mods(search_str, origin="gamebanana")
    dma_mods = api.search_mods(search_str, origin="divamodarchive")
    found_mods = gb_mods + dma_mods
    installed_ids = [mod.id for mod in mod_manager.mods if not mod.is_simple()]
    if not found_mods:
        print(f"No mods matching {colorama.Style.BRIGHT}{search_str}{colorama.Style.RESET_ALL} found.")
    else:
        options = ["Cancel"]

        def mod_str_gen(m_t):
            mod_name = m_t["name"].strip().replace("\n", "")
            mod_author = m_t["author"].strip().replace("\n", "")
            content = f"{mod_name} by {mod_author} [{m_t['origin']}]"
            if m_t['id'] in installed_ids:
                return f"(installed) {content}"
            return content

        options.extend(map(mod_str_gen, found_mods))
        mod_search_menu = TerminalMenu(options)
        choice = mod_search_menu.show()
        if 0 < choice < len(options):
            mod = found_mods[choice - 1]
            if mod["id"] in installed_ids:
                print(f"{mod['name']} is already installed.")
            else:
                try:
                    print(f"Installing {mod['name']} ({mod['id']})")
                    mod_manager.install_mod(mod['id'], mod["category"], origin=mod['origin'])
                    print(f"{colorama.Fore.GREEN}Installed {mod['name']}{colorama.Fore.RESET}")
                except Exception as e:
                    print(f"{colorama.Fore.RED}Failed to install {mod['name']}{colorama.Fore.RESET}({e})")
                    print_exc()


def menu_manage(mod_manager: ModManager):
    KEY_MOVE_UP = "w"
    KEY_MOVE_DOWN = "s"
    SHIFT_LUT = {
        KEY_MOVE_UP: -1,
        KEY_MOVE_DOWN: 1
    }
    idx = 0
    while True:
        options = [str(mod) for mod in mod_manager.mods]
        menu = TerminalMenu(options, preview_command=lambda x: generate_preview(x, mod_manager),
                            preview_title="Mod Info", preview_size=0.5,
                            status_bar=f"q to exit, / to search, {KEY_MOVE_UP}/{KEY_MOVE_DOWN} to adjust priority",
                            cursor_index=idx, accept_keys=["enter", KEY_MOVE_UP, KEY_MOVE_DOWN]
                            )
        idx = menu.show()
        selected_key = menu.chosen_accept_key
        if idx is None:
            return
        if selected_key in SHIFT_LUT.keys():
            new_index = idx + SHIFT_LUT[selected_key]
            if 0 <= new_index < len(mod_manager.mods):
                t = mod_manager.mods[idx]
                mod_manager.mods[idx] = mod_manager.mods[new_index]
                mod_manager.mods[new_index] = t
                mod_manager.save_priority()
                idx = new_index
            else:
                print(f"{colorama.Fore.RED}Cannot shift out of bounds{colorama.Fore.RESET}")
        elif 0 < idx < len(options):
            selected_mod = mod_manager.mods[idx]
            mod_is_enabled = mod_manager.is_enabled(selected_mod)
            editor = os.environ.get("EDITOR", "nano")
            inner_options = [
                "Cancel",
                "[d] Disable" if mod_is_enabled else "[e] Enable",
                "(update unavailable)" if selected_mod.is_simple() else "[u] Update",
                "[x] Delete",
                f"[e] Edit mod config... ({editor})"
            ]
            inner_menu = TerminalMenu(inner_options, title=str(selected_mod))
            inner_choice = inner_menu.show()
            if inner_choice == 1:
                if mod_is_enabled:
                    mod_manager.disable(selected_mod)
                    print(f"{selected_mod} {colorama.Fore.RED}disabled.{colorama.Fore.RESET}")
                else:
                    mod_manager.enable(selected_mod)
                    print(f"{selected_mod} {colorama.Fore.GREEN}enabled.{colorama.Fore.RESET}")
            elif inner_choice == 2:
                if selected_mod.is_simple():
                    print(
                        "This mod has an unknown origin and thus cannot be auto-updated. Try deleting it and reinstalling it using d4m.")
                else:
                    if selected_mod.is_out_of_date():
                        mod_manager.update(selected_mod)
                    else:
                        print(f"{selected_mod.name} is up-to-date.")
            elif inner_choice == 3:
                check_opt = TerminalMenu(["Cancel", f"Yes, delete {selected_mod.name}"],
                                         title=f"Are you sure you want to delete {selected_mod}?").show()
                if check_opt == 1:
                    mod_manager.delete_mod(selected_mod)
                    print(f"{colorama.Fore.RED}{selected_mod} deleted.{colorama.Fore.RESET}")
            elif inner_choice == 4:
                subprocess.run([editor, os.path.join(selected_mod.path, "config.toml")])


def do_update_all(mod_manager: ModManager):
    for mod in mod_manager.mods:
        if not mod.is_simple() and mod.is_out_of_date():
            print(f"Updating {mod}...")
            try:
                mod_manager.update(mod)
                print(f"{colorama.Fore.GREEN}Successfully updated {mod.name}{colorama.Fore.RESET}")
            except Exception as e:
                print(f"{colorama.Fore.RED}Failed to update {mod.name}: {e}{colorama.Fore.RESET}")


def edit_d4m_config(*args):
    editor = os.environ.get("EDITOR", "nano")
    subprocess.run([editor, os.path.expanduser("~/.config/d4m.toml")])


def migrate_from_dmm(mod_manager: ModManager):
    attempted = 0
    successful = 0
    for mod in mod_manager.mods:
        if mod.is_simple() and mod.can_attempt_dmm_migration():
            print(f"Attempting to migrate {mod.name}...")
            attempted += 1
            res = mod.attempt_migrate_from_dmm()
            if res:
                print(f"{colorama.Fore.GREEN}Successfully migrated {mod.name}.{colorama.Fore.RESET}")
                successful += 1
            else:
                print(f"{colorama.Fore.RED}Couldn't migrate {mod.name}{colorama.Fore.RESET}")
    if attempted > 0:
        print(f"Attempted to migrate {attempted} mods, {successful} successful.")
    else:
        print(f"No mods eligible for migration.")
    mod_manager.reload()


def main():
    print(f"d4m v{VERSION}")

    d4m_config = D4mConfig()

    if time.time() - d4m_config["last_d4m_update_check"] > 60 * 60:
        d4m_config["last_d4m_update_check"] = time.time()
        d4m_config.write()
        d4m_latest, _ = fetch_latest_d4m_version()
        if d4m_latest > packaging.version.Version(VERSION):
            print(
                f"{colorama.Fore.YELLOW}A new version of d4m is available. Please update via\n\tpip install d4m=={d4m_latest}{colorama.Fore.RESET}")

    try:
        megamix_path = d4m_config.get_diva_path()
    except:
        menu = TerminalMenu(["Yes", "No"],
                            title=f"Couldn't determine diva install dir. Would you like to edit the d4m config file?")
        r = menu.show()
        if r == 0:
            edit_d4m_config()
            sys.exit(0)
        else:
            sys.exit(1)

    print(f"Using the diva directory located at {megamix_path}")

    if not modloader_is_installed(megamix_path):
        menu = TerminalMenu(["Yes", "No"],
                            title="It doesn't seem like DivaModLoader is installed. Would you like to install the latest version?")
        choice = menu.show()
        if choice == 0:
            install_modloader(megamix_path)
        else:
            sys.exit()

    dml_version, _, mods_path = get_modloader_info(megamix_path)

    if time.time() - d4m_config["last_dmm_update_check"] > 60 * 60:
        d4m_config["last_dmm_update_check"] = time.time()
        d4m_config.write()
        dml_latest, dml_url = check_modloader_version()

        if dml_latest > dml_version:
            print(
                f"DivaModLoader update available. Latest version is {dml_latest}, you're running {dml_version}. Would you like to update?")
            menu = TerminalMenu(["Yes", "No"])
            choice = menu.show()
            if choice == 0:
                print("Updating DivaModLoader...")
                try:
                    install_modloader(megamix_path)
                    print(f"Updated to DivaModLoader {dml_latest}")
                except Exception as e:
                    print(f'Failed to update DivaModLoader. ({e})')
                    sys.exit(2)

    os.makedirs(mods_path, exist_ok=True)
    mod_manager = ModManager(megamix_path, mods_path)

    print(f"{len(mod_manager.mods)} mods installed")
    print(f"{colorama.Fore.YELLOW}Checking for mod updates...{colorama.Fore.RESET}")
    begin = time.time()
    available_updates = -1
    try:
        mod_manager.check_for_updates()
        print(f"Update check completed in {time.time() - begin:.1f}s")
        available_updates = sum(1 for _ in filter(lambda x: not x.is_simple() and x.is_out_of_date(), mod_manager.mods))
        if available_updates == 0:
            print(f"{colorama.Fore.GREEN}All mods up-to-date.{colorama.Fore.RESET}")
        else:
            print(f"{colorama.Fore.YELLOW}{available_updates} mods have updates available.{colorama.Fore.RESET}")
    except RuntimeError as e:
        print(f"{colorama.Fore.RED}Failed to check for mod updates:{colorama.Fore.RESET} {e}")

    base_options = [
        ("Install new mods", menu_install),
        ("Manage existing mods", menu_manage),
        ("Edit d4m config", edit_d4m_config),
        ("Migrate from DivaModManager", migrate_from_dmm),
        ("Run Project Diva", lambda *_: subprocess.run([f"xdg-open", "steam://run/{MEGAMIX_APPID}"]))
    ]

    while True:
        options = base_options.copy()
        if available_updates > 0:
            options.append(
                (f"Update all", do_update_all)
            )
        if mod_manager.enabled:
            options.append(
                (f"Disable DivaModLoader", lambda x: x.disable_dml())
            )
        else:
            options.append(
                (f"Enable DivaModLoader", lambda x: x.enable_dml())
            )
        status_strings = [
            "q to quit",
            f"d4m v{VERSION}",
            f"{len(mod_manager.mods)} mods",
            f"DivaModLoader {dml_version} {'ENABLED' if mod_manager.enabled else 'DISABLED'}"
        ]
        root_menu = TerminalMenu([x[0] for x in options], status_bar="; ".join(status_strings),
                                 status_bar_style=("fg_cyan", "bg_black"))
        sel = root_menu.show()
        if sel is None:
            break
        if 0 <= sel < len(options):
            options[sel][1](mod_manager)
