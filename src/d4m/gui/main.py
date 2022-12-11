#!/usr/bin/env python
import os
import subprocess
import sys
import time
from importlib.resources import files
from traceback import format_exc

import PySide6.QtConcurrent
import PySide6.QtCore
import PySide6.QtWidgets as qwidgets
import packaging.version
from PySide6.QtGui import QAction, QColor, QDesktopServices, QImage, QPixmap

import d4m.api
import d4m.common
# Import various d4m dialogs
import d4m.gui.dialogs
import d4m.manage
import d4m.rss
import d4m.save_data
from d4m.global_config import D4mConfig
from d4m.gui.context import D4mGlobalContext
from d4m.gui.d4m_logging import D4mLogger
from d4m.gui.dialogs.log import LogDialog
from d4m.gui.dialogs.migrate import DmmMigrateDialog
from d4m.gui.dialogs.mod_install import ModInstallDialog
from d4m.gui.dialogs.news import NewsHistoryDialog
from d4m.gui.dialogs.save_backup import SaveDataBackupDialog
from d4m.gui.util import favicon_qimage, show_d4m_infobox
from d4m.manage import ModManager

if sys.platform == "win32":  # windows hack for svg because pyinstaller isn't cooperating
    with open(os.path.join(os.path.expandvars("%ProgramFiles(x86)%"), "d4m", "logo.svg"), "rb") as fd:
        D4M_ICON_DATA = fd.read()
else:
    D4M_ICON_DATA = files("d4m.res").joinpath("logo.svg").read_bytes()

d4m_logger = D4mLogger(None)

##############################
### BUTTON CLICK FUNCTIONS ###
##############################

def on_dml_toggle_click(status_label, mod_manager: ModManager):
    if mod_manager.enabled:
        mod_manager.disable_dml()
        status_label.setText("DISABLED")
    else:
        mod_manager.enable_dml()
        status_label.setText("ENABLED")


def on_install_mod(_, context: D4mGlobalContext):
    dialog = ModInstallDialog(context=context)
    dialog.exec()


def on_toggle_mod(selections, mod_manager: ModManager):
    for mod in selections:
        if mod_manager.is_enabled(mod):
            mod_manager.disable(mod)
            d4m_logger.log_msg(f"Disabled {mod}")
        else:
            mod_manager.enable(mod)
            d4m_logger.log_msg(f"Enabled {mod}")


def on_update_mod(selections, mod_manager: ModManager):
    # TODO: progress bar dialog
    d4m_logger.log_msg(f"Attempting to update {len(selections)} mods")
    updated = 0
    for mod in selections:
        if mod.is_simple():
            d4m_logger.log_msg(f"{str(mod)} has an unknown origin and cannot be updated.")
        else:
            if mod.is_out_of_date():
                d4m_logger.log_msg(f"Updating {mod}...")
                mod_manager.update(mod, fetch_thumbnail=True)
                d4m_logger.log_msg(f"{mod} updated successfully.")
                updated += 1
            else:
                d4m_logger.log_msg(f"{mod} is already up to date.")
    d4m_logger.log_msg(f"Updated {updated} mods")


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
                d4m_logger.log_msg(f"Deleted {mod}")
                success += 1
            except Exception as e:
                d4m_logger.log_msg(f"Failed to delete {mod.name}: {e}")
        d4m_logger.log_msg(f"Deleted {success} mods")


def on_edit_mod(selections, mod_manager: ModManager):
    if len(selections) == 0:
        show_d4m_infobox("Select a mod to edit.", level="warn")
    elif len(selections) > 1:
        show_d4m_infobox("You can only edit one mod's config at a time.", level="warn")
    else:
        mod = selections[0]
        config_file_path = os.path.join(mod.path, "config.toml")
        if sys.platform == "win32":
            os.startfile(config_file_path)
        elif sys.platform == "linux":
            try:
                subprocess.Popen(["xdg-open", config_file_path])
            except IOError:
                show_d4m_infobox(f"Failed to open mod config:\n{format_exc()}", level="error")
        else:
            show_d4m_infobox(f"Unable to do that on your platform ({sys.platform})", level="error")


def on_refresh_click(_selections, mod_manager: ModManager):
    mod_manager.save_priority()
    mod_manager.reload()


def install_from_archive(_selected, mod_manager: ModManager):
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


def open_mod_folder(selected):
    QDesktopServices.openUrl("file://" + selected[0].path)
    pass


def show_about(parent):
    about_str = f"""
    d4m v{d4m.common.VERSION}

    Open-source, cross-platform, Project Diva MegaMix+ mod manager

    Written By Brod8362
    """
    qwidgets.QMessageBox.about(parent, "About d4m", about_str)


def show_generic_dialog(parent, dialog_class, *args, **kwargs):
    dialog = dialog_class(*args, **kwargs, parent=parent)
    dialog.show()


def on_increase_priority(selected, mod_manager: ModManager) -> int:
    return generic_priority_shift(selected[0], mod_manager, -1)


def on_decrease_priority(selected, mod_manager: ModManager) -> int:
    return generic_priority_shift(selected[0], mod_manager, +1)


def generic_priority_shift(mod, mod_manager, shift):
    if (mod_idx := mod_manager.mods.index(mod)) != -1:
        if 0 <= mod_idx + shift <= len(mod_manager.mods):
            t = mod_manager.mods[mod_idx]
            mod_manager.mods[mod_idx] = mod_manager.mods[mod_idx + shift]
            mod_manager.mods[mod_idx + shift] = t
            mod_manager.save_priority()
            return mod_idx + shift


##########################
### BACKGROUND WORKERS ###
##########################

class BackgroundUpdateWorker(PySide6.QtCore.QRunnable):
    def __init__(self, mod_manager, populate_func, parent=None, on_complete=None):
        super(BackgroundUpdateWorker, self).__init__(parent)
        self.updates_ready = False
        self.mod_manager = mod_manager
        self.populate = populate_func
        self.on_complete = on_complete

    def run(self):
        d4m_logger.log_msg("Checking for updates...")
        try:
            self.mod_manager.check_for_updates(get_thumbnails=True)
            self.populate(update_check=True)
            d4m_logger.log_msg("Update check complete.")
        except Exception as e:
            d4m_logger.log_msg(f"Update check failed: {e}")
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
        global_context = D4mGlobalContext(d4m_config, d4m_logger, mod_manager)

        D4M_LOGO_PIXMAP = QPixmap()
        D4M_LOGO_PIXMAP.loadFromData(D4M_ICON_DATA)
        D4M_LOGO_PIXMAP = D4M_LOGO_PIXMAP.scaled(48, 48)
        qapp.setWindowIcon(D4M_LOGO_PIXMAP)

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

        # build main elements
        menu_bar = qwidgets.QMenuBar()

        # news button
        latest_news = d4m.rss.latest_news()
        if latest_news:
            news_layout = qwidgets.QHBoxLayout()

            news_banner = qwidgets.QPushButton(f"News: {latest_news.title}  -  {latest_news.description}")
            news_banner.clicked.connect(lambda *_: QDesktopServices.openUrl(latest_news.link))
            news_banner.setIcon(main_window.style().standardIcon(qwidgets.QStyle.SP_MessageBoxInformation))
            news_banner.setToolTip("Open this news entry in your browser")

            old_news_button = qwidgets.QPushButton()
            old_news_button.setIcon(main_window.style().standardIcon(qwidgets.QStyle.SP_FileDialogListView))
            old_news_button.setToolTip("See old news")
            old_news_button.clicked.connect(lambda *_: show_generic_dialog(main_window, NewsHistoryDialog))

            news_layout.addWidget(news_banner, 1)
            news_layout.addWidget(old_news_button)

        top_row = qwidgets.QHBoxLayout()

        mod_table_and_buttons_layout = qwidgets.QHBoxLayout()
        mod_table = qwidgets.QTableWidget()
        mod_table_and_buttons_layout.addWidget(mod_table, 1)
        mod_buttons = qwidgets.QHBoxLayout()

        statusbar = qwidgets.QStatusBar()
        d4m_logger.attach_statusbar(statusbar)

        ver_str = f"d4m v{d4m.common.VERSION}"
        d4m_label = qwidgets.QLabel(ver_str)
        d4m_label.setPixmap(D4M_LOGO_PIXMAP)
        d4m_label.setContentsMargins(0, 0, 0, 0)
        d4m_logger.log_msg(ver_str)
        window.setWindowTitle(ver_str)

        # Priority buttons
        # Signals are all connected later, so they can access the autoupdate func
        mod_context_button_box = qwidgets.QVBoxLayout()
        mod_context_button_box.insertStretch(-1, 1)

        open_mod_folder_button = qwidgets.QPushButton()
        open_mod_folder_button.setIcon(main_window.style().standardIcon(qwidgets.QStyle.SP_DirIcon))
        open_mod_folder_button.setEnabled(False)
        open_mod_folder_button.setToolTip("Open the mod folder in the system file browser")

        edit_mod_config_button = qwidgets.QPushButton()
        edit_mod_config_button.setIcon(main_window.style().standardIcon(qwidgets.QStyle.SP_FileDialogContentsView))
        edit_mod_config_button.setEnabled(False)
        edit_mod_config_button.setToolTip("Open mod config file in a text editor")

        priority_increase_button = qwidgets.QPushButton()
        priority_increase_button.setIcon(main_window.style().standardIcon(qwidgets.QStyle.SP_ArrowUp))
        priority_increase_button.setEnabled(False)
        priority_increase_button.setToolTip("Increase selected mod priority")

        priority_decrease_button = qwidgets.QPushButton()
        priority_decrease_button.setIcon(main_window.style().standardIcon(qwidgets.QStyle.SP_ArrowDown))
        priority_decrease_button.setEnabled(False)
        priority_decrease_button.setToolTip("Decrease selected mod priority")

        mod_context_button_box.addWidget(open_mod_folder_button)
        mod_context_button_box.addWidget(edit_mod_config_button)
        mod_context_button_box.addWidget(priority_increase_button)
        mod_context_button_box.addWidget(priority_decrease_button)
        mod_table_and_buttons_layout.addLayout(mod_context_button_box)

        ### Populate Menu Bar

        # create menus
        file_menu = menu_bar.addMenu("&File")
        save_data_menu = menu_bar.addMenu("&Save Data")
        help_menu = menu_bar.addMenu("&Help")

        # fill save data menu
        action_backup_save = QAction("Backup Save Data...", window)
        action_backup_save.triggered.connect(
            lambda *_: show_generic_dialog(main_window, SaveDataBackupDialog, d4m_config, d4m_logger)
        )
        action_restore_save = QAction("Restore Save Data...", window)
        action_restore_save.triggered.connect(
            lambda *_: d4m.gui.dialogs.save_backup.save_data_restore(d4m_config, d4m_logger, parent=main_window)
        )

        # Temporarily disable save data management while it's broken
        action_restore_save.setEnabled(False)
        action_backup_save.setEnabled(False)

        save_data_menu.addAction(action_backup_save)
        save_data_menu.addAction(action_restore_save)

        # fill help menu
        action_github = QAction("GitHub", window)
        action_github.triggered.connect(lambda *_: QDesktopServices.openUrl("https://github.com/Brod8362/d4m"))

        action_bug_report = QAction("File a Bug/Suggest Feature", window)
        action_bug_report.triggered.connect(
            lambda *_: QDesktopServices.openUrl("https://github.com/Brod8362/d4m/issues/new/choose"))

        action_about = QAction("About d4m", window)
        action_about.triggered.connect(lambda *_: show_about(main_window))

        help_menu.addAction(action_github)
        help_menu.addAction(action_bug_report)
        help_menu.addAction(action_about)


        ### Propagate top row
        dml_status_label = qwidgets.QLabel(f"DivaModLoader {dml_version}")
        dml_enable_label = qwidgets.QLabel("ENABLED" if mod_manager.enabled else "DISABLED")
        dml_toggle_button = qwidgets.QPushButton("Toggle DivaModLoader")
        dml_toggle_button.clicked.connect(lambda *_: on_dml_toggle_click(dml_enable_label, mod_manager))
        run_diva_button = qwidgets.QPushButton("Run Project Diva")
        run_diva_button.clicked.connect(lambda *_: QDesktopServices.openUrl(f"steam://run/{d4m.common.MEGAMIX_APPID}"))
        open_diva_folder = qwidgets.QPushButton("Open Diva Install Folder")
        open_diva_folder.clicked.connect(lambda *_: QDesktopServices.openUrl(f"file://{mod_manager.base_path}"))
        mod_count_label = qwidgets.QLabel("-- mod(s) / -- enabled")

        top_row.addWidget(d4m_label)
        top_row.addWidget(dml_status_label)
        top_row.addWidget(dml_enable_label, alignment=PySide6.QtCore.Qt.AlignLeft)
        top_row.addWidget(dml_toggle_button)
        top_row.addWidget(run_diva_button)
        top_row.addWidget(open_diva_folder)
        top_row.addWidget(mod_count_label)

        image_thumbnail_cache = {}

        ### Propagate mod list
        mod_table.setColumnCount(7)  # thumbnail, image, name, creator, version, id, size

        def populate_modlist(update_check=True):
            mod_table.clear()
            mod_table.setSelectionBehavior(qwidgets.QAbstractItemView.SelectionBehavior.SelectRows)
            mod_table.setEditTriggers(qwidgets.QAbstractItemView.NoEditTriggers)
            mod_table.setHorizontalHeaderLabels(
                ["Thumbnail", "Mod Name", "Enabled",
                 "Mod Author(s)", "Mod Version", "Mod ID",
                 "Size"]
            )
            mod_table.horizontalHeader().setSectionResizeMode(0, qwidgets.QHeaderView.ResizeMode.ResizeToContents)
            mod_table.horizontalHeader().setSectionResizeMode(1, qwidgets.QHeaderView.ResizeMode.ResizeToContents)
            mod_table.setAlternatingRowColors(True)
            mod_table.horizontalHeader().setStretchLastSection(True)
            mod_table.verticalHeader().setSectionResizeMode(qwidgets.QHeaderView.ResizeMode.Fixed)
            mod_table.setRowCount(len(mod_manager.mods))
            for (index, mod) in enumerate(mod_manager.mods):
                mod_image = qwidgets.QTableWidgetItem("No Preview")
                if mod.has_thumbnail():
                    if not mod.is_simple() and mod.id in image_thumbnail_cache:
                        image = image_thumbnail_cache[mod.id]
                    else:
                        base = QImage()
                        base.load(mod.get_thumbnail_path())
                        image = base.scaled(128, 128, aspectMode=PySide6.QtCore.Qt.AspectRatioMode.KeepAspectRatio)
                        if not mod.is_simple():
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
                    if mod.can_attempt_dmm_migration():
                        mod_version.setToolTip("This mod may be able to be migrated from DivaModManager.")
                        mod_version.setBackground(QColor.fromRgb(0, 255, 255))
                    else:
                        mod_version.setToolTip(
                            "This mod is missing metadata information and the latest version cannot be determined.")
                else:
                    mod_version = qwidgets.QTableWidgetItem(str(mod.version))
                    try:
                        if update_check and mod.is_out_of_date():
                            mod_version.setBackground(QColor.fromRgb(255, 255, 0))
                            mod_version.setToolTip("A new version is available.")
                    except RuntimeError as e:
                        mod_version.setBackground(QColor.fromRgb(255, 0, 0))
                        mod_version.setToolTip(f"An error occurred while checking for updates:\n{e}")

                    mod_id = qwidgets.QTableWidgetItem(str(mod.id))

                    fav = favicon_qimage(mod.origin)  # apply favicon if available
                    if fav is not None:
                        mod_id.setData(PySide6.QtCore.Qt.DecorationRole, fav)

                    mod_table.setItem(index, 5, mod_id)
                mod_table.setItem(index, 0, mod_image)
                mod_table.setItem(index, 1, mod_name)
                mod_table.setItem(index, 2, mod_enabled)
                mod_table.setItem(index, 3, mod_author)
                mod_table.setItem(index, 4, mod_version)
                mod_table.setItem(index, 6, mod_size)
                enabled_mod_count = sum(1 for m in mod_manager.mods if m.enabled)
                mod_count_label.setText(f"{len(mod_manager.mods)} mod(s) / {enabled_mod_count} enabled")

        populate_modlist(update_check=False)

        def autoupdate(func, *args):
            """Call function func, passing in the currently selected mods as the first argument to the function.
            *args will be passed in as the remainder of the arguments.
            After func() returns, the mod list will be re-populated."""
            selected_rows = set(map(lambda x: x.row(), mod_table.selectedIndexes()))
            selected_mods = list(map(lambda i: mod_manager.mods[i], selected_rows))
            r = func(selected_mods, *args)
            populate_modlist(update_check=buw.updates_ready)
            if r is not None:
                mod_table.selectRow(r)

        # fill file menu (needs access to autoupdate)
        action_load_from = QAction("Load from archive...", window)
        action_load_from.triggered.connect(lambda *_: autoupdate(install_from_archive, mod_manager))

        action_open_log = QAction("Open Log...", window)
        action_open_log.triggered.connect(
            lambda *_: show_generic_dialog(main_window, LogDialog, d4m_logger))

        action_migrate_dmm = QAction("Migrate from DivaModManager...", window)
        action_migrate_dmm.triggered.connect(
            lambda *_: show_generic_dialog(None, DmmMigrateDialog, context=global_context,
                                           callback=populate_modlist(update_check=buw.updates_ready))
        )

        # connect mod context buttons (needs access to autoupdate)
        edit_mod_config_button.clicked.connect(lambda *_: autoupdate(on_edit_mod, mod_manager))
        open_mod_folder_button.clicked.connect(lambda *_: autoupdate(open_mod_folder))
        priority_increase_button.clicked.connect(lambda *_: autoupdate(on_increase_priority, mod_manager))
        priority_decrease_button.clicked.connect(lambda *_: autoupdate(on_decrease_priority, mod_manager))

        action_quit = QAction("Exit", window)
        action_quit.triggered.connect(lambda *_: sys.exit(0))

        file_menu.addAction(action_load_from)
        file_menu.addAction(action_open_log)
        file_menu.addAction(action_migrate_dmm)
        file_menu.addAction(action_quit)

        ### Propagate action buttons
        install_mod_button = qwidgets.QPushButton("Install Mods...")
        install_mod_button.clicked.connect(lambda *_: autoupdate(on_install_mod, global_context))

        toggle_mod_button = qwidgets.QPushButton("Toggle Selected")
        toggle_mod_button.clicked.connect(lambda *_: autoupdate(on_toggle_mod, mod_manager))

        update_mod_button = qwidgets.QPushButton("Update Selected")
        update_mod_button.clicked.connect(lambda *_: autoupdate(on_update_mod, mod_manager))
        update_mod_button.setEnabled(False)

        delete_mod_button = qwidgets.QPushButton("Delete Selected")
        delete_mod_button.clicked.connect(lambda *_: autoupdate(on_delete_mod, mod_manager))

        def mod_contexts_available():
            context_enabled = len(set(map(lambda x: x.row(), mod_table.selectedIndexes()))) == 1
            edit_mod_config_button.setEnabled(context_enabled)
            priority_increase_button.setEnabled(context_enabled)
            priority_decrease_button.setEnabled(context_enabled)
            open_mod_folder_button.setEnabled(context_enabled)

        mod_table.itemSelectionChanged.connect(mod_contexts_available)

        refresh_mod_button = qwidgets.QPushButton("Refresh")
        refresh_mod_button.clicked.connect(lambda *_: autoupdate(on_refresh_click, mod_manager))

        mod_buttons.addWidget(install_mod_button)
        mod_buttons.addWidget(toggle_mod_button)
        mod_buttons.addWidget(update_mod_button)
        mod_buttons.addWidget(delete_mod_button)
        mod_buttons.addWidget(refresh_mod_button)

        buw = BackgroundUpdateWorker(mod_manager, populate_modlist,
                                     on_complete=lambda *_: update_mod_button.setEnabled(True),
                                     parent=main_window)
        threadpool.start(buw)

        ## Populate main GUI

        main_window.setMenuBar(menu_bar)
        # main_window.setWindowIcon(D4M_LOGO_PIXMAP)
        main_window.setStatusBar(statusbar)

        if latest_news:  # only if news exists
            main_widget.addLayout(news_layout)

        main_widget.addLayout(top_row)
        main_widget.addLayout(mod_table_and_buttons_layout)
        main_widget.addLayout(mod_buttons)

        d4m_logger.log_msg(f"Megamix @ {d4m.common.get_megamix_path()}")

        for sd_r in d4m.save_data.SAVE_DATA_TYPES:
            sd: d4m.save_data.MMSaveDataType = sd_r(d4m_config)
            if sd.exists():
                d4m_logger.log_msg(f"Found {sd.display_name()} save data at {sd.path()}")
                sd.backup(f"/tmp/save_data_{sd.type_name()}.zip")

        main_window.setMinimumSize(950, 500)
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

    # determine megamix install path
    try:
        megamix_path = d4m_config.get_diva_path()
        if not megamix_path:
            raise RuntimeError("megamix path is None")
    except:
        content = f"Failed to determine where MegaMix is installed.\nWould you like to specify the install directory manually?"
        res = show_d4m_infobox(content, level="error", buttons=qwidgets.QMessageBox.Yes | qwidgets.QMessageBox.No)
        if res == qwidgets.QMessageBox.StandardButton.Yes:
            file_dialog = qwidgets.QFileDialog()
            file_dialog.setFileMode(qwidgets.QFileDialog.Directory)
            if file_dialog.exec():
                folders = file_dialog.selectedFiles()
                if len(folders) != 1:
                    show_d4m_infobox("uh oh", level="error")
                    sys.exit(1)
                d4m_config["diva_path"] = folders[0]
                d4m_config.write()
                megamix_path = folders[0]
        else:
            sys.exit(1)

    # offer to install DML
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

    # check DML for updates
    dml_version, dml_enabled, dml_mods_dir = d4m.common.get_modloader_info(megamix_path)
    if time.time() - d4m_config["last_dml_update_check"] > 60 * 60:
        try:
            d4m_config["last_dml_update_check"] = time.time()
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
