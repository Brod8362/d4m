from d4m.common import VERSION, get_megamix_path, modloader_is_installed, get_modloader_info, can_autoupdate_dml, get_vdf_path
from d4m.manage import ModManager, check_modloader_version
import time
import colorama
from simple_term_menu import TerminalMenu
import d4m.api as api
from d4m.manage import install_modloader
import os

def generate_preview(mod_str: str, mod_manager: ModManager):
    content = []
    found = list(filter(lambda x: str(x) == mod_str, mod_manager.mods))
    if not found:
        return ""
    mod = found[0]
    content.append(f"Name: {mod.name}")
    content.append(f"Author: {mod.author}")
    content.append(f"Version: {mod.version}")
    enable_str = f"{colorama.Fore.GREEN}Enabled{colorama.Fore.RESET}" if mod_manager.is_enabled(mod) else f"{colorama.Fore.RED}Disabled{colorama.Fore.RESET}"
    content.append(f"Status: {enable_str}")
    content.append(f"Install Path: {mod.path}")
    if mod.is_simple() == False:
        content.append(f"Mod ID: {mod.id}")
        utd_str = f"{colorama.Fore.YELLOW}Out of date{colorama.Fore.RESET}" if mod.is_out_of_date() else f"{colorama.Fore.GREEN}Up to date{colorama.Fore.RESET}"
        content.append(f"Update Status: {utd_str}")
    return "\n".join(content)

def menu_install(mod_manager: ModManager):
    search_str = input("Search for a mod...:")
    found_mods = api.search_mods(search_str)
    installed_ids = [mod.id for mod in mod_manager.mods if not mod.is_simple()]
    if not found_mods:
        print(f"No mods matching {colorama.Style.BRIGHT}{search_str}{colorama.Style.RESET_ALL} found.")
    else:
        options = ["Cancel"]
        def mod_str_gen(m_t):
            content = m_t[1].strip().replace("\n", "")
            if m_t[0] in installed_ids:
                return f"(installed) {content}"
            return content

        options.extend(map(mod_str_gen, found_mods))
        mod_search_menu = TerminalMenu(options)
        choice = mod_search_menu.show()
        if 0 < choice < len(options):
            mod = found_mods[choice-1]
            if mod[0] in installed_ids:
                print(f"{mod[1]} is already installed.")
            else:
                try:
                    print(f"Installing {mod[1]} ({mod[0]})")
                    mod_manager.install_mod(mod[0])
                    print(f"{colorama.Fore.GREEN}Installed {mod[1]}{colorama.Fore.RESET}")
                except Exception as e:
                    print(f"{colorama.Fore.RED}Failed to stalled {mod[1]} {colorama.Fore.RESET}({e})")

def menu_manage(mod_manager: ModManager):
    options = ["Cancel"]
    options.extend(str(mod) for mod in mod_manager.mods)
    menu = TerminalMenu(options, preview_command=lambda x: generate_preview(x, mod_manager), preview_title="Mod Info", preview_size=0.5, status_bar="Press / to search")
    choice = menu.show()
    if not choice:
        return
    if 0 < choice < len(options):
        selected_mod = mod_manager.mods[choice-1]
        mod_is_enabled = mod_manager.is_enabled(selected_mod)
        inner_options = [
            "Cancel",
            "[d] Disable" if mod_is_enabled else "[e] Enable",
            "(update unavailable)" if selected_mod.is_simple() else "[u] Update",
            "[x] Delete",
        ]
        inner_menu = TerminalMenu(inner_options, title=str(selected_mod))
        inner_choice = inner_menu.show()
        match inner_choice:
            case 0:
                pass
            case 1:
                if mod_is_enabled:
                    mod_manager.disable(selected_mod)
                    print(f"{selected_mod} {colorama.Fore.RED}disabled.{colorama.Fore.RESET}")
                else:
                    mod_manager.enable(selected_mod)
                    print(f"{selected_mod} {colorama.Fore.GREEN}enabled.{colorama.Fore.RESET}")
            case 2:
                if selected_mod.is_simple():
                    print("This mod has an unknown origin and thus cannot be auto-updated. Try deleting it and reinstalling it using d4m.")
                else:
                    if selected_mod.is_out_of_date():
                        mod_manager.delete_mod(selected_mod)
                        mod_manager.install_mod(selected_mod.id)
                    else:
                        print(f"{selected_mod.name} is up-to-date.")
            case 3:
                check_opt = TerminalMenu(["Cancel", f"Yes, delete {selected_mod.name}"], title=f"Are you sure you want to delete {selected_mod}?").show()
                if check_opt == 1:
                    mod_manager.delete_mod(selected_mod)
                    print(f"{colorama.Fore.RED}{selected_mod} deleted.{colorama.Fore.RESET}")

def menu_exit(mod_manager: ModManager):
    quit()

def main():
    print(f"d4m v{VERSION}")

    megamix_path = get_megamix_path()

    if not modloader_is_installed(megamix_path):
        menu = TerminalMenu(["Yes", "No"], title="It doesn't seem like DivaModLoader is installed. Would you like to install the latest version?")
        choice = menu.show()
        if choice == 0:
            install_modloader(megamix_path)
        else:
            quit()

    dml_version, dml_enabled, MODS_PATH = get_modloader_info(megamix_path)

    dml_latest, dml_url = check_modloader_version()
    if dml_latest > dml_version:
        if can_autoupdate_dml():
            print(f"DivaModLoader update available. Latest version is {dml_latest}, you're running {dml_version}. Would you like to update?")
            menu = TerminalMenu(["Yes", "No"])
            choice = menu.show()
            if choice == 0:
                print("Updating DivaModLoader...")
                try:
                    install_modloader(megamix_path)
                    print(f"Updated to DivaModLoader {dml_latest}")
                except Exception as e:
                    print(f'Failed to update DivaModLoader. ({e})')
                    quit()
        else:
            print(f"DivaModLoader update available, but auto-updating is not supported on this platform. Download it here: {dml_url}")

    os.makedirs(MODS_PATH, exist_ok=True)
    mod_manager = ModManager(MODS_PATH)

    print(f"{len(mod_manager.mods)} mods installed")
    print(f"{colorama.Fore.YELLOW}Checking for mod updates...{colorama.Fore.RESET}")
    begin = time.time()
    mod_manager.check_for_updates()
    print(f"Update check completed in {time.time()-begin:.1f}s")
    available_updates = sum(1 for x in filter(lambda x: not  x.is_simple() and x.is_out_of_date(), mod_manager.mods))
    if available_updates == 0:
        print(f"{colorama.Fore.GREEN}All mods up-to-date.{colorama.Fore.RESET}")
    else:
        print(f"{colorama.Fore.YELLOW}{available_updates} mods have updates available.{colorama.Fore.RESET}")

    options = [
        ("Install new mods", menu_install),
        ("Manage existing mods", menu_manage),
        ("Exit", menu_exit)
    ]

    while True:
        root_menu = TerminalMenu(x[0] for x in options)
        sel = root_menu.show()
        if sel is None:
            break
        if 0 <= sel < len(options):
            options[sel][1](mod_manager)