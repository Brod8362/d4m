#!/usr/bin/env python
import os
import subprocess
import sys
import time
from sys import platform
from time import strftime
from traceback import format_exc, print_exc

import PySide6.QtConcurrent
import PySide6.QtCore
import PySide6.QtWidgets as qwidgets
import d4m.api
import d4m.common
import d4m.manage
import packaging.version
from PySide6.QtGui import QAction, QColor, QDesktopServices, QImage
from d4m.manage import ModManager

from d4m.global_config import D4mConfig

LOG_HISTORY = []


def log_msg(content: str):
    timestamp = strftime("%H:%M:%S")
    LOG_HISTORY.append(f"[{timestamp}] {content}")
    statusbar.showMessage(content)


def show_d4m_infobox(content: str, level: str = "info", buttons=qwidgets.QMessageBox.Ok):
    d = {
        "info": qwidgets.QMessageBox.Icon.Information,
        "warn": qwidgets.QMessageBox.Icon.Warning,
        "question": qwidgets.QMessageBox.Icon.Question,
        "error": qwidgets.QMessageBox.Icon.Critical
    }
    icon = d.get(level, qwidgets.QMessageBox.Icon.NoIcon)
    msgbox = qwidgets.QMessageBox()
    msgbox.setText(content)
    msgbox.setWindowTitle("d4m")
    msgbox.setIcon(icon)
    msgbox.setStandardButtons(buttons)
    return msgbox.exec()


def on_dml_toggle_click(status_label, mod_manager: ModManager):
    if mod_manager.enabled:
        mod_manager.disable_dml()
        status_label.setText("DISABLED")
    else:
        mod_manager.enable_dml()
        status_label.setText("ENABLED")


def on_install_mod(_, mod_manager: ModManager, callback):
    dialog = ModInstallDialog(mod_manager=mod_manager, callback=callback)
    dialog.exec()


def on_toggle_mod(selections, mod_manager: ModManager):
    for mod in selections:
        if mod_manager.is_enabled(mod):
            mod_manager.disable(mod)
            log_msg(f"Disabled {mod}")
        else:
            mod_manager.enable(mod)
            log_msg(f"Enabled {mod}")


def on_update_mod(selections, mod_manager: ModManager):
    # TODO: progress bar dialog
    log_msg(f"Attempting to update {len(selections)} mods")
    updated = 0
    for mod in selections:
        if mod.is_simple():
            log_msg(f"{str(mod)} has an unknown origin and cannot be updated.")
        else:
            if mod.is_out_of_date():
                log_msg(f"Updating {mod}...")
                mod_manager.update(mod)
                log_msg(f"{mod} updated successfully.")
                updated += 1
            else:
                log_msg(f"{mod} is already up to date.")
    log_msg(f"Updated {updated} mods")


def on_delete_mod(selections, mod_manager: ModManager):
    content = f"Are you sure you want to delete <strong>{len(selections)}</strong> mod(s)?\n" + ", ".join(
        map(lambda x: x.name, selections))
    msgbox = qwidgets.QMessageBox()
    msgbox.setText(content)
    msgbox.setStandardButtons(qwidgets.QMessageBox.Yes | qwidgets.QMessageBox.No)
    msgbox.setIcon(qwidgets.QMessageBox.Icon.Question)
    res = msgbox.exec()
    if res == qwidgets.QMessageBox.StandardButton.Yes:
        success = 0
        for mod in selections:
            try:
                mod_manager.delete_mod(mod)
                log_msg(f"Deleted {mod}")
                success += 1
            except Exception as e:
                log_msg(f"Failed to delete {mod.name}: {e}")
        log_msg(f"Deleted {success} mods")


def on_edit_mod(selections, mod_manager: ModManager):
    if len(selections) == 0:
        show_d4m_infobox("Select a mod to edit.", level="warn")
    elif len(selections) > 1:
        show_d4m_infobox("You can only edit one mod's config at a time.", level="warn")
    else:
        mod = selections[0]
        config_file_path = os.path.join(mod.path, "config.toml")
        if platform == "win32":
            os.startfile(config_file_path)
        elif platform == "linux":
            try:
                subprocess.Popen(["xdg-open", config_file_path])
            except IOError:
                show_d4m_infobox(f"Failed to open mod config:\n{format_exc()}", level="error")
        else:
            show_d4m_infobox(f"Unable to do that on your platform ({platform})", level="error")


def on_refresh_click(selections, mod_manager: ModManager):
    mod_manager.reload()


class LogDialog(qwidgets.QDialog):
    def __init__(self, parent=None):
        super(LogDialog, self).__init__(parent)
        self.count_widget = qwidgets.QLabel()
        self.log_widget = qwidgets.QTextEdit()
        self.layout = qwidgets.QVBoxLayout()
        self.layout.addWidget(self.count_widget)
        self.layout.addWidget(self.log_widget)
        self.log_widget.setReadOnly(True)
        self.setLayout(self.layout)
        self.setWindowFlag(PySide6.QtCore.Qt.Tool)
        statusbar.messageChanged.connect(self.render)
        self.setWindowTitle("d4m log")
        self.setMinimumSize(350, 200)
        self.render()

    def render(self):
        self.count_widget.setText(f"{len(LOG_HISTORY)} log messages")
        self.log_widget.setText("\n".join(LOG_HISTORY))


class ModInstallDialog(qwidgets.QDialog):
    def __init__(self, mod_manager=None, callback=None, parent=None):
        super(ModInstallDialog, self).__init__(parent)

        self.win_layout = qwidgets.QVBoxLayout()
        self.search_layout = qwidgets.QHBoxLayout()

        self.mod_name_input = qwidgets.QLineEdit("")
        self.mod_name_input.setPlaceholderText("Search...")
        self.status_label = qwidgets.QLabel("")
        self.install_button = qwidgets.QPushButton("Install Selected")
        self.install_button.setEnabled(False)
        self.progress_bar = qwidgets.QProgressBar()

        self.search_button = qwidgets.QPushButton("Search")
        self.found_mod_list = qwidgets.QTableWidget()

        def on_install_click(results):
            self.install_button.setEnabled(False)
            self.search_button.setEnabled(False)
            selected_rows = set(map(lambda x: x.row(), self.found_mod_list.selectedIndexes()))
            selected_ids = list(map(lambda i: results[i], selected_rows))
            self.progress_bar.setRange(0, len(selected_ids))
            self.progress_bar.setValue(0)
            self.status_label.setText(f"Preparing to install {len(selected_ids)} mod(s)")
            success = 0
            for index, (mod_id, mod_name) in enumerate(selected_ids):
                text = f"<strong>{index + 1}/{len(selected_ids)}... Installing mod {mod_name} "
                self.status_label.setText(text)
                if not mod_manager.mod_is_installed(mod_id):
                    try:
                        mod_manager.install_mod(mod_id, fetch_thumbnail=True)
                        success += 1
                    except Exception as e:
                        print_exc()
                        r = f"Failed to install {mod_name}: {e}"
                        self.status_label.setText(text)
                        log_msg(r)
                    self.progress_bar.setValue(index + 1)
            # when all is done
            if success == len(selected_ids):
                self.status_label.setText(f"Installed {success} mods successfully.")
            else:
                self.status_label.setText(f"Installed {success} mods ({len(selected_ids) - success} errors)")
            self.search_button.setEnabled(True)
            self.install_button.setEnabled(True)

        def populate_search_results():
            try:
                self.progress_bar.setRange(0, 3)
                self.progress_bar.setValue(1)
                results = d4m.api.search_mods(self.mod_name_input.text())
                self.progress_bar.setValue(2)
                d4m.api.multi_fetch_mod_data(t[0] for t in results)  # fetch detailed info
            except RuntimeError as e:
                self.status_label.setText(f"Err: <strong color=red>{e}</strong>")
                return
            finally:
                self.progress_bar.setValue(3)
            self.status_label.setText(
                f"Found <strong>{len(results)}</strong> mods matching <em>{self.mod_name_input.text()}</em>")
            self.found_mod_list.clear()
            self.found_mod_list.setColumnCount(5)
            self.found_mod_list.setHorizontalHeaderLabels(["Mod", "Mod ID", "Likes", "Downloads", "Status", ])
            self.found_mod_list.horizontalHeader().setSectionResizeMode(0,
                                                                        qwidgets.QHeaderView.ResizeMode.ResizeToContents)
            self.found_mod_list.setEditTriggers(qwidgets.QAbstractItemView.NoEditTriggers)
            self.found_mod_list.setSelectionBehavior(qwidgets.QAbstractItemView.SelectionBehavior.SelectRows)
            self.found_mod_list.horizontalHeader().setStretchLastSection(True)
            self.found_mod_list.setRowCount(len(results))
            for index, (m_id, m_name) in enumerate(results):
                detailed_mod_info = d4m.api.fetch_mod_data(
                    m_id)  # should already be fetched and cached, no performance concerns here
                mod_label = qwidgets.QTableWidgetItem(m_name)
                mod_label.setToolTip(m_name)
                mod_id_label = qwidgets.QTableWidgetItem(str(m_id))
                status = "Available"
                if mod_manager.mod_is_installed(m_id):
                    status = "Installed"
                if detailed_mod_info["hash"] == "err":
                    status = "Unavailable (Error)"
                mod_installed_label = qwidgets.QTableWidgetItem(status)
                mod_downloads_label = qwidgets.QTableWidgetItem(str(detailed_mod_info["download_count"]))
                mod_likes_label = qwidgets.QTableWidgetItem(str(detailed_mod_info["like_count"]))
                self.found_mod_list.setItem(index, 0, mod_label)
                self.found_mod_list.setItem(index, 1, mod_id_label)
                self.found_mod_list.setItem(index, 2, mod_downloads_label)
                self.found_mod_list.setItem(index, 3, mod_likes_label)
                self.found_mod_list.setItem(index, 4, mod_installed_label)
            if len(results) > 0:
                self.install_button.setEnabled(True)
                self.install_button.clicked.connect(lambda *_: on_install_click(results))

        # Populate user interactable fields
        self.search_layout.addWidget(self.mod_name_input)
        self.search_layout.addWidget(self.search_button)
        self.search_button.clicked.connect(populate_search_results)

        # Populate main layout
        self.win_layout.addLayout(self.search_layout)
        self.win_layout.addWidget(self.found_mod_list)
        self.win_layout.addWidget(self.status_label)
        self.win_layout.addWidget(self.progress_bar)
        self.win_layout.addWidget(self.install_button)

        self.setLayout(self.win_layout)
        self.setMinimumWidth(550)
        self.setMinimumHeight(350)
        self.setWindowTitle("d4m - Install new mods")


def install_from_archive(selected, mod_manager: ModManager):
    dialog = qwidgets.QFileDialog()
    if dialog.exec():
        file_names = dialog.selectedFiles()
        if len(file_names) > 1:
            show_d4m_infobox("Only one mod can be installed at a time.")
        else:
            file = file_names[0]
            try:
                mod_manager.install_from_archive(file)
                show_d4m_infobox("Mod installed successfully.")
            except:
                show_d4m_infobox(f"Failed to install from archive:\n{format_exc()}", level="error")


def show_log(parent):
    dialog = LogDialog(parent=parent)
    dialog.show()


def show_about(parent):
    about_str = f"""
    d4m v{d4m.common.VERSION}

    Open-source, cross-platform, Project Diva MegaMix+ mod manager

    Written By Brod8362
    """
    qwidgets.QMessageBox.about(parent, "About d4m", about_str)


class BackgroundUpdateWorker(PySide6.QtCore.QRunnable):
    def __init__(self, mod_manager, populate_func, parent=None, on_complete=None):
        super(BackgroundUpdateWorker, self).__init__(parent)
        self.updates_ready = False
        self.mod_manager = mod_manager
        self.populate = populate_func
        self.on_complete = on_complete

    def run(self):
        log_msg("Checking for updates...")
        try:
            self.mod_manager.check_for_updates(get_thumbnails=True)
            self.populate(update_check=True)
            log_msg("Update check complete.")
        except Exception as e:
            log_msg(f"Update check failed: {e}")
        self.updates_ready = True
        if self.on_complete:
            self.on_complete()


class VoidFuncBackgroundWorker(PySide6.QtCore.QRunnable):
    def __init__(self, func, on_complete=None, parent=None):
        super(VoidFuncBackgroundWorker, self).__init__(parent)
        self.func = func
        self.on_complete = on_complete

    def run(self):
        self.func()
        if self.on_complete:
            self.on_complete()


class D4mGUI:
    def __init__(self, qapp: qwidgets.QApplication, mod_manager: ModManager, dml_version, d4m_config: D4mConfig):
        threadpool = PySide6.QtCore.QThreadPool()
        main_window = qwidgets.QMainWindow()
        window = qwidgets.QWidget()
        main_window.setCentralWidget(window)

        ## Start d4m update check
        def d4m_update_check():
            last_checked = d4m_config["last_d4m_update_check"]
            if time.time() - last_checked > 60 * 60:
                latest, download = d4m.common.fetch_latest_d4m_version()
                d4m_config["last_d4m_update_check"] = time.time()
                d4m_config.write()
                if latest > packaging.version.Version(d4m.common.VERSION):
                    res = show_d4m_infobox(
                        f"A new version of d4m is available ({latest})\nWould you like to open the releases page?",
                        level="question",
                        buttons=qwidgets.QMessageBox.Yes | qwidgets.QMessageBox.No
                    )
                    if res == qwidgets.QMessageBox.StandardButton.Yes:
                        QDesktopServices.openUrl("https://github.com/Brod8362/d4m/releases")

        d4m_update_worker = VoidFuncBackgroundWorker(d4m_update_check)
        threadpool.start(d4m_update_worker)

        main_widget = qwidgets.QVBoxLayout(window)

        menu_bar = qwidgets.QMenuBar()
        top_row = qwidgets.QHBoxLayout()
        mod_table = qwidgets.QTableWidget()
        mod_buttons = qwidgets.QHBoxLayout()
        global statusbar
        statusbar = qwidgets.QStatusBar()
        ver_str = f"d4m v{d4m.common.VERSION}"
        log_msg(ver_str)
        window.setWindowTitle(ver_str)

        ### Populate Menu Bar

        # create menus
        file_menu = menu_bar.addMenu("&File")
        help_menu = menu_bar.addMenu("&Help")

        # fill help menu
        action_github = QAction("GitHub", window)
        action_github.triggered.connect(lambda *_: QDesktopServices.openUrl("https://github.com/Brod8362/d4m"))

        action_bug_report = QAction("File a Bug/Suggest Feature", window)
        action_bug_report.triggered.connect(
            lambda *_: QDesktopServices.openUrl("https://github.com/Brod8362/d4m/issues/new/choose"))

        action_about = QAction("About d4m", window)
        action_about.triggered.connect(lambda *_: show_about(window))

        help_menu.addAction(action_github)
        help_menu.addAction(action_bug_report)
        help_menu.addAction(action_about)

        ### Propogate top row
        dml_status_label = qwidgets.QLabel(f"DivaModLoader {dml_version}")
        dml_enable_label = qwidgets.QLabel("ENABLED" if mod_manager.enabled else "DISABLED")
        dml_toggle_button = qwidgets.QPushButton("Toggle DivaModLoader")
        dml_toggle_button.clicked.connect(lambda *_: on_dml_toggle_click(dml_enable_label, mod_manager))
        run_diva_button = qwidgets.QPushButton("Run Project Diva")
        run_diva_button.clicked.connect(lambda *_: QDesktopServices.openUrl(f"steam://run/{d4m.common.MEGAMIX_APPID}"))
        open_diva_folder = qwidgets.QPushButton("Open Diva Install Folder")
        open_diva_folder.clicked.connect(lambda *_: QDesktopServices.openUrl(f"file://{mod_manager.base_path}"))
        mod_count_label = qwidgets.QLabel("-- mods / -- enabled")

        top_row.addWidget(dml_status_label)
        top_row.addWidget(dml_enable_label, alignment=PySide6.QtCore.Qt.AlignLeft)
        top_row.addWidget(dml_toggle_button)
        top_row.addWidget(run_diva_button)
        top_row.addWidget(open_diva_folder)
        top_row.addWidget(mod_count_label)

        image_thumbnail_cache = {}

        ### Propogate mod list
        mod_table.setColumnCount(7)  # thumbnail, image, name, creator, version, id, size

        def populate_modlist(update_check=True):
            mod_table.clear()
            mod_table.setSelectionBehavior(qwidgets.QAbstractItemView.SelectionBehavior.SelectRows)
            mod_table.setEditTriggers(qwidgets.QAbstractItemView.NoEditTriggers)
            mod_table.setHorizontalHeaderLabels(
                ["Thumbnail", "Mod Name", "Enabled",
                 "Mod Author(s)", "Mod Version", "Gamebanana ID",
                 "Size"]
            )
            mod_table.horizontalHeader().setSectionResizeMode(0, qwidgets.QHeaderView.ResizeMode.ResizeToContents)
            mod_table.horizontalHeader().setSectionResizeMode(1, qwidgets.QHeaderView.ResizeMode.ResizeToContents)
            mod_table.horizontalHeader().setStretchLastSection(True)
            mod_table.verticalHeader().setSectionResizeMode(qwidgets.QHeaderView.ResizeMode.Fixed)
            mod_table.setRowCount(len(mod_manager.mods))
            for (index, mod) in enumerate(mod_manager.mods):
                mod_image = qwidgets.QTableWidgetItem("No Preview")
                if mod.has_thumbnail():
                    if mod.id in image_thumbnail_cache:
                        image = image_thumbnail_cache[mod.id]
                    else:
                        base = QImage()
                        base.load(mod.get_thumbnail_path())
                        image = base.scaled(128, 128, aspectMode=PySide6.QtCore.Qt.AspectRatioMode.KeepAspectRatio)
                        image_thumbnail_cache[mod.id] = image
                    mod_image.setData(PySide6.QtCore.Qt.DecorationRole, image)
                    mod_image.setText("")
                mod_name = qwidgets.QTableWidgetItem(mod.name)
                mod_name.setToolTip(mod.name)
                mod_enabled = qwidgets.QTableWidgetItem("Enabled" if mod.enabled else "Disabled")
                mod_author = qwidgets.QTableWidgetItem(mod.author)
                mod_author.setToolTip(mod.author)
                mod_size = qwidgets.QTableWidgetItem(f"{mod.size_bytes / (1024 * 1024):.1f}Mb")
                if mod.is_simple():
                    mod_version = qwidgets.QTableWidgetItem(str(mod.version) + "*")
                    mod_version.setToolTip(
                        "This mod is missing metadata information and the latest version cannot be determined.")
                else:
                    mod_version = qwidgets.QTableWidgetItem(str(mod.version))
                    if update_check and mod.is_out_of_date():
                        mod_version.setBackground(QColor.fromRgb(255, 255, 0))
                        mod_version.setToolTip("A new version is available.")
                    url = f"https://gamebanana.com/mods/{mod.id}"
                    # mod_id = qwidgets.QTableWidgetItem(f"<a href=\"{url}\">{mod.id}</a>")
                    # TODO: how to embed URL in table?
                    mod_id = qwidgets.QTableWidgetItem(str(mod.id))
                    mod_table.setItem(index, 5, mod_id)
                mod_table.setItem(index, 0, mod_image)
                mod_table.setItem(index, 1, mod_name)
                mod_table.setItem(index, 2, mod_enabled)
                mod_table.setItem(index, 3, mod_author)
                mod_table.setItem(index, 4, mod_version)
                mod_table.setItem(index, 6, mod_size)
                enabled_mod_count = sum(1 for m in mod_manager.mods if m.enabled)
                mod_count_label.setText(f"{len(mod_manager.mods)} mods / {enabled_mod_count} enabled")

        populate_modlist(update_check=False)

        def autoupdate(func, *args):
            """Selected mods will automatically be passed in as first argument."""
            selected_rows = set(map(lambda x: x.row(), mod_table.selectedIndexes()))
            selected_mods = list(map(lambda i: mod_manager.mods[i], selected_rows))
            func(selected_mods, *args)
            populate_modlist(update_check=buw.updates_ready)

        # fill file menu (needs access to autoupdate)
        action_load_from = QAction("Load from archive...", window)
        action_load_from.triggered.connect(lambda *_: autoupdate(install_from_archive, mod_manager))

        action_open_log = QAction("Open Log...", window)
        action_open_log.triggered.connect(lambda *_: show_log(main_window))

        action_quit = QAction("Exit", window)
        action_quit.triggered.connect(lambda *_: sys.exit(0))

        file_menu.addAction(action_load_from)
        file_menu.addAction(action_open_log)
        file_menu.addAction(action_quit)

        ### Propogate action buttons
        install_mod_button = qwidgets.QPushButton("Install Mods...")
        install_mod_button.clicked.connect(lambda *_: autoupdate(on_install_mod, mod_manager, populate_modlist))

        toggle_mod_button = qwidgets.QPushButton("Toggle Selected")
        toggle_mod_button.clicked.connect(lambda *_: autoupdate(on_toggle_mod, mod_manager))

        update_mod_button = qwidgets.QPushButton("Update Selected")
        update_mod_button.clicked.connect(lambda *_: autoupdate(on_update_mod, mod_manager))
        update_mod_button.setEnabled(False)

        delete_mod_button = qwidgets.QPushButton("Delete Selected")
        delete_mod_button.clicked.connect(lambda *_: autoupdate(on_delete_mod, mod_manager))

        edit_mod_config_button = qwidgets.QPushButton("Edit Config...")
        edit_mod_config_button.setEnabled(False)
        edit_mod_config_button.clicked.connect(lambda *_: autoupdate(on_edit_mod, mod_manager))

        def mod_edit_available():
            selected_row_count = len(set(map(lambda x: x.row(), mod_table.selectedIndexes())))
            if selected_row_count == 1:
                edit_mod_config_button.setEnabled(True)
            else:
                edit_mod_config_button.setEnabled(False)

        mod_table.itemSelectionChanged.connect(mod_edit_available)

        refresh_mod_button = qwidgets.QPushButton("Refresh")
        refresh_mod_button.clicked.connect(lambda *_: autoupdate(on_refresh_click, mod_manager))

        mod_buttons.addWidget(install_mod_button)
        mod_buttons.addWidget(toggle_mod_button)
        mod_buttons.addWidget(update_mod_button)
        mod_buttons.addWidget(delete_mod_button)
        mod_buttons.addWidget(edit_mod_config_button)
        mod_buttons.addWidget(refresh_mod_button)

        buw = BackgroundUpdateWorker(mod_manager, populate_modlist,
                                     on_complete=lambda *_: update_mod_button.setEnabled(True))
        threadpool.start(buw)

        # # Populate main GUI
        main_window.setMenuBar(menu_bar)
        main_window.setStatusBar(statusbar)

        main_widget.addLayout(top_row)
        main_widget.addWidget(mod_table)
        main_widget.addLayout(mod_buttons)

        main_window.setMinimumSize(850, 500)
        main_window.setMaximumSize(900, 1500)
        main_window.show()
        sys.exit(qapp.exec())


def main():
    app = qwidgets.QApplication([])

    try:  # libarchive check
        import libarchive.public
    except:
        show_d4m_infobox(f"libarchive is not installed/cannot import.\n{format_exc()}", level="question")
        sys.exit(0)

    d4m_config = D4mConfig()

    try:
        megamix_path = os.environ.get("D4M_INSTALL_DIR", d4m_config.get_diva_path())
    except:
        content = f"Failed to determine where MegaMix is installed.\n{format_exc()}"
        show_d4m_infobox(content, level="error")
        sys.exit(1)
    if not d4m.common.modloader_is_installed(megamix_path):
        content = f"DivaModLoader is not installed. Would you like d4m to install the latest version of DivaModLoader?"
        res = show_d4m_infobox(content, buttons=qwidgets.QMessageBox.Yes | qwidgets.QMessageBox.No, level="question")
        if res == qwidgets.QMessageBox.StandardButton.Yes:
            try:
                d4m.manage.install_modloader(megamix_path)
                show_d4m_infobox("DivaModLoader installed successfully.")
            except:
                show_d4m_infobox(f"Failed to install DivaModLoader:\n {format_exc()}", level="error")
                sys.exit(0)
    dml_version, dml_enabled, dml_mods_dir = d4m.common.get_modloader_info(megamix_path)
    if time.time() - d4m_config["last_dmm_update_check"] > 60 * 60:
        try:
            d4m_config["last_dmm_update_check"] = time.time()
            d4m_config.write()
            dml_latest, dml_download = d4m.manage.check_modloader_version()
            if dml_version < dml_latest:
                content = f"A new version of DivaModLoader is available.\nCurrent: {dml_version}\nLatest: {dml_latest}\nDo you want to update?"
                res = show_d4m_infobox(content, level="question",
                                       buttons=qwidgets.QMessageBox.Yes | qwidgets.QMessageBox.No)
                if res == qwidgets.QMessageBox.StandardButton.Yes:
                    try:
                        d4m.manage.install_modloader(megamix_path)
                        show_d4m_infobox(f'DivaModLoader updated successfully.')
                        dml_version = dml_latest
                    except:
                        show_d4m_infobox(f"Failed to update DivaModLoader:\n{format_exc()}", level="error")
                        sys.exit(0)
        except:
            content = f"Cannot fetch latest DivaModLoader version: {format_exc()}"
            show_d4m_infobox(content, level="warn")

    mod_manager = ModManager(megamix_path, mods_path=dml_mods_dir)

    D4mGUI(app, mod_manager, dml_version, d4m_config)


if __name__ == "__main__":
    main()
