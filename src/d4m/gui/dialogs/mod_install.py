from traceback import print_exc

import PySide6.QtCore
import PySide6.QtWidgets as qwidgets

import d4m.api.api
from d4m.gui.context import D4mGlobalContext
# from d4m.gui.main import log_msg
from d4m.gui.util import favicon_qimage


class ModInstallDialog(qwidgets.QDialog):
    def __init__(self, context: D4mGlobalContext = None, parent=None):
        super(ModInstallDialog, self).__init__(parent)

        self.context = context

        self.win_layout = qwidgets.QVBoxLayout()
        self.search_layout = qwidgets.QHBoxLayout()

        self.mod_name_input = qwidgets.QLineEdit("")
        self.mod_name_input.setPlaceholderText("Search...")
        self.status_label = qwidgets.QLabel("")
        self.install_button = qwidgets.QPushButton("Install Selected")
        self.install_button.setEnabled(False)
        self.progress_bar = qwidgets.QProgressBar()

        self.checkbox_layout = qwidgets.QHBoxLayout()
        self.checkbox_search_dma = qwidgets.QCheckBox("Search Diva Mod Archive")
        self.checkbox_search_dma.setChecked(True)
        self.checkbox_search_gb = qwidgets.QCheckBox("Search GameBanana")

        self.checkbox_search_gb.setChecked(True)
        self.checkbox_layout.addWidget(self.checkbox_search_dma)
        self.checkbox_layout.addWidget(self.checkbox_search_gb)

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
            for index, mod_info in enumerate(selected_ids):
                text = f"<strong>{index + 1}/{len(selected_ids)}... Installing mod {mod_info.name} "
                self.status_label.setText(text)
                if not context.mod_manager.mod_is_installed(mod_info.id, origin=mod_info.origin):
                    try:
                        context.mod_manager.install_mod(mod_info.id, mod_info.category, fetch_thumbnail=True,
                                                        origin=mod_info.origin)
                        success += 1
                    except Exception as e:
                        print_exc()
                        r = f"Failed to install {mod_info.origin}: {e}"
                        self.status_label.setText(text)
                        context.logger.log_msg(r)
                    self.progress_bar.setValue(index + 1)
            # when all is done
            if success == len(selected_ids):
                self.status_label.setText(f"Installed {success} mod(s) successfully.")
            else:
                self.status_label.setText(f"Installed {success} mod(s) ({len(selected_ids) - success} errors)")
            self.search_button.setEnabled(True)
            self.install_button.setEnabled(True)

        def populate_search_results():
            try:
                results = []
                self.progress_bar.setRange(0, 5)
                self.progress_bar.setValue(1)

                if self.checkbox_search_gb.isChecked():
                    gb_results = d4m.api.api.search_mods(self.mod_name_input.text(), origin="gamebanana")
                    results.extend(gb_results)
                    self.progress_bar.setValue(2)
                    d4m.api.api.multi_fetch_mod_data([(x.id, x.category) for x in gb_results], origin="gamebanana")

                if self.checkbox_search_dma.isChecked():
                    self.progress_bar.setValue(3)
                    dma_results = d4m.api.api.search_mods(self.mod_name_input.text(), origin="divamodarchive")
                    results.extend(dma_results)
                    self.progress_bar.setValue(4)
                    d4m.api.api.multi_fetch_mod_data([(x.id, x.category) for x in dma_results],
                                                     origin="divamodarchive")

            except RuntimeError as e:
                self.status_label.setText(f"Err: <strong color=red>{e}</strong>")
                return
            finally:
                self.progress_bar.setValue(5)

            self.status_label.setText(
                f"Found <strong>{len(results)}</strong> mod(s) matching <em>{self.mod_name_input.text()}</em>")
            self.found_mod_list.clear()
            self.found_mod_list.setColumnCount(5)
            self.found_mod_list.setHorizontalHeaderLabels(["Mod", "Author", "Mod ID", "Info", "Status"])
            self.found_mod_list.horizontalHeader().setSectionResizeMode(0,
                                                                        qwidgets.QHeaderView.ResizeMode.ResizeToContents)
            self.found_mod_list.setEditTriggers(qwidgets.QAbstractItemView.NoEditTriggers)
            self.found_mod_list.setSelectionBehavior(qwidgets.QAbstractItemView.SelectionBehavior.SelectRows)
            self.found_mod_list.horizontalHeader().setStretchLastSection(True)
            self.found_mod_list.setRowCount(len(results))
            for index, mod_info in enumerate(results):
                # should already be fetched and cached, no performance concerns here
                detailed_mod_info = d4m.api.api.fetch_mod_data(mod_info.id, mod_info.category, origin=mod_info.origin)
                mod_label = qwidgets.QTableWidgetItem(mod_info.name)
                mod_label.setToolTip(mod_info.name)
                mod_author_label = qwidgets.QTableWidgetItem(mod_info.author)
                mod_author_label.setToolTip(mod_info.author)
                mod_id_label = qwidgets.QTableWidgetItem(str(mod_info.id))

                fav = favicon_qimage(mod_info.origin)
                if fav:
                    mod_id_label.setData(PySide6.QtCore.Qt.DecorationRole, fav)

                status = "Available"
                if context.mod_manager.mod_is_installed(mod_info.id, origin=mod_info.origin):
                    status = "Installed"
                if detailed_mod_info["hash"] == "err":
                    status = "Unavailable (Error)"
                mod_installed_label = qwidgets.QTableWidgetItem(status)
                mod_info_label = qwidgets.QTableWidgetItem(
                    f"❤️{detailed_mod_info['like_count']} ⬇️{detailed_mod_info['download_count']}")
                self.found_mod_list.setItem(index, 0, mod_label)
                self.found_mod_list.setItem(index, 1, mod_author_label)
                self.found_mod_list.setItem(index, 2, mod_id_label)
                self.found_mod_list.setItem(index, 3, mod_info_label)
                self.found_mod_list.setItem(index, 4, mod_installed_label)
            if len(results) > 0:
                self.install_button.setEnabled(True)
                self.install_button.clicked.connect(lambda *_: on_install_click(results))

        # Populate user intractable fields
        self.search_layout.addWidget(self.mod_name_input)
        self.search_layout.addWidget(self.search_button)
        self.search_button.clicked.connect(populate_search_results)

        # Populate main layout
        self.win_layout.addLayout(self.search_layout)
        self.win_layout.addLayout(self.checkbox_layout)
        self.win_layout.addWidget(self.found_mod_list)
        self.win_layout.addWidget(self.status_label)
        self.win_layout.addWidget(self.progress_bar)
        self.win_layout.addWidget(self.install_button)

        self.setLayout(self.win_layout)
        self.setMinimumSize(650, 350)
        self.setWindowTitle("d4m - Install new mods")
