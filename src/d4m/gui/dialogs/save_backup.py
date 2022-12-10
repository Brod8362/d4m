import PySide6.QtCore
import PySide6.QtWidgets as qwidgets

from d4m.global_config import D4mConfig
import d4m.save_data
from d4m.gui.util import show_d4m_infobox
import os


class SaveDataBackupDialog(qwidgets.QDialog):

    def check_valid(self):
        if self.output_file and self.backup_type:
            self.ok_button.setEnabled(True)
        else:
            self.ok_button.setEnabled(False)

    def radio_clicked(self, s_type: str):
        self.backup_type = s_type
        self.check_valid()

    def do_backup(self):
        if self.output_file and self.backup_type:
            save_data_repr = d4m.save_data.inst(self.backup_type, self.d4m_config)
            if not save_data_repr:
                show_d4m_infobox("Backup failed (invalid type ID)", level="error")
                self.close()
            try:
                save_data_repr.backup(self.output_file)
                show_d4m_infobox("Backup completed successfully.")
            except Exception as e:
                show_d4m_infobox(f"Backup failed ({e})", level="error")
        self.close()

    def open_file_dialog(self) -> None:
        f_dialog = qwidgets.QFileDialog()
        f_dialog.setAcceptMode(qwidgets.QFileDialog.AcceptSave)
        f_dialog.setFileMode(qwidgets.QFileDialog.AnyFile)
        file = f_dialog.getSaveFileName(self, "Backup", os.path.expanduser("~"), filter="Zip Archive (*.zip)")
        if file:
            self.output_file = file[0]
        self.check_valid()

    def __init__(self, d4m_config: D4mConfig, parent=None):
        self.backup_type = None
        self.output_file = None
        super(SaveDataBackupDialog, self).__init__(parent)
        self.d4m_config = d4m_config

        # Layouts
        self.layout = qwidgets.QVBoxLayout()
        self.button_box = qwidgets.QVBoxLayout()

        # Labels
        self.step_1_label = qwidgets.QLabel("1. Select data to backup:")
        self.step_2_label = qwidgets.QLabel("2. Select destination file (zip):")
        self.step_3_label = qwidgets.QLabel("3. Backup!")

        # Buttons
        self.file_picker_button = qwidgets.QPushButton(f"Choose File")
        self.file_picker_button.setIcon(self.style().standardIcon(qwidgets.QStyle.SP_FileDialogNewFolder))
        self.file_picker_button.clicked.connect(lambda *_: self.open_file_dialog())

        self.ok_button = qwidgets.QPushButton("Backup!")
        self.ok_button.setDisabled(True)
        self.ok_button.setIcon(self.style().standardIcon(qwidgets.QStyle.SP_DialogOkButton))
        self.ok_button.clicked.connect(lambda *_: self.do_backup())

        # Generate radio buttons
        for save_type in d4m.save_data.SAVE_DATA_TYPES:
            sd = save_type(self.d4m_config)
            radio_button = qwidgets.QRadioButton(sd.display_name())
            if sd.exists():
                radio_button.setEnabled(True)
                radio_button.setToolTip(sd.path())
                radio_button.clicked.connect(lambda *_: self.radio_clicked(sd.type_name()))
            else:
                radio_button.setText(f"{sd.display_name()} (not detected)")
                radio_button.setEnabled(False)
                radio_button.setToolTip("Save data not found")
            self.button_box.addWidget(radio_button)

        # Populate layout
        self.layout.addWidget(self.step_1_label)
        self.layout.addLayout(self.button_box)
        self.layout.addWidget(self.step_2_label)
        self.layout.addWidget(self.file_picker_button)
        self.layout.addWidget(self.step_3_label)
        self.layout.addWidget(self.ok_button)

        self.setLayout(self.layout)
        self.setMinimumSize(450, 300)
        self.setWindowTitle("d4m - Backup Save Data")
