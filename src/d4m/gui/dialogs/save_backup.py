import os

import PySide6.QtWidgets as qwidgets

import d4m.save_data
from d4m.gui.context import D4mGlobalContext
from d4m.gui.util import show_d4m_infobox


class QHLine(qwidgets.QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(qwidgets.QFrame.HLine)
        self.setFrameShadow(qwidgets.QFrame.Sunken)


class SaveDataBackupDialog(qwidgets.QDialog):

    def check_valid(self):
        if self.output_file and self.backup_type:
            self.ok_button.setEnabled(True)
        else:
            self.ok_button.setEnabled(False)

    def radio_clicked(self, s_type: str):
        self.backup_type = s_type
        self.context.logger.log_msg(f"Set backup type to {self.backup_type}")
        self.check_valid()

    def do_backup(self):
        if self.output_file and self.backup_type:
            save_data_repr = d4m.save_data.inst(self.backup_type, self.context.config)
            if not save_data_repr:
                show_d4m_infobox("Backup failed (invalid type ID)", level="error")
                self.context.logger.log_msg(f"Backup failed (invalid type ID {self.backup_type})")
                self.close()
            try:
                save_data_repr.backup(self.output_file)
                show_d4m_infobox("Backup completed successfully.")
                self.context.logger.log_msg(f"Backup OK ({self.output_file})")
            except Exception as e:
                show_d4m_infobox(f"Backup failed ({e})", level="error")
                self.context.logger.log_msg(f"Exception attempting backup: {e}")
        self.close()

    def open_file_dialog(self) -> None:
        f_dialog = qwidgets.QFileDialog()
        f_dialog.setAcceptMode(qwidgets.QFileDialog.AcceptSave)
        f_dialog.setFileMode(qwidgets.QFileDialog.AnyFile)
        file = f_dialog.getSaveFileName(self, "Backup", os.path.expanduser("~"), filter="d4m Backup (*.d4mb)")
        if file:
            self.output_file = file[0] if file[0].endswith(".d4mb") else file[0] + ".d4mb"
            self.context.logger.log_msg(f"Backup target set to {self.output_file}")
        self.check_valid()

    def __init__(self, d4m_context: D4mGlobalContext, parent=None):
        self.backup_type = None
        self.output_file = None
        super(SaveDataBackupDialog, self).__init__(parent)
        self.context = d4m_context

        # Layouts
        self.layout = qwidgets.QVBoxLayout()
        self.button_box = qwidgets.QVBoxLayout()

        # Labels
        step_1_label = qwidgets.QLabel("1. Select data to backup:")
        step_2_label = qwidgets.QLabel("2. Select destination file:")
        step_3_label = qwidgets.QLabel("3. Backup!")

        # Buttons
        self.file_picker_button = qwidgets.QPushButton(f"Choose File")
        self.file_picker_button.setIcon(self.style().standardIcon(qwidgets.QStyle.SP_FileDialogNewFolder))
        self.file_picker_button.clicked.connect(lambda *_: self.open_file_dialog())

        self.ok_button = qwidgets.QPushButton("Backup!")
        self.ok_button.setDisabled(True)
        self.ok_button.setIcon(self.style().standardIcon(qwidgets.QStyle.SP_DialogOkButton))
        self.ok_button.clicked.connect(lambda *_: self.do_backup())

        # Generate radio buttons
        for index, save_type in enumerate(d4m.save_data.SAVE_DATA_TYPES):
            sd = save_type(self.context.config)
            radio_button = qwidgets.QRadioButton(sd.display_name())
            if sd.exists():
                radio_button.setEnabled(True)
                radio_button.setToolTip(sd.path())

                def v():
                    # dumb python scope hack
                    lv = sd.type_name()[:]
                    radio_button.clicked.connect(lambda *_: self.radio_clicked(f"{lv}"))

                v()
            else:
                radio_button.setText(f"{sd.display_name()} (not detected)")
                radio_button.setEnabled(False)
                radio_button.setToolTip("Save data not found")
            self.button_box.addWidget(radio_button)

        # Populate layout
        self.layout.addWidget(step_1_label)
        self.layout.addLayout(self.button_box)
        self.layout.addWidget(QHLine())
        self.layout.addWidget(step_2_label)
        self.layout.addWidget(self.file_picker_button)
        self.layout.addWidget(QHLine())
        self.layout.addWidget(step_3_label)
        self.layout.addWidget(self.ok_button)

        self.setLayout(self.layout)
        self.setFixedSize(450, 300)
        self.setWindowTitle("d4m - Backup Save Data")


def save_data_restore(context: D4mGlobalContext, parent=None):
    f_dialog = qwidgets.QFileDialog()
    f_dialog.setAcceptMode(qwidgets.QFileDialog.AcceptOpen)
    f_dialog.setFileMode(qwidgets.QFileDialog.ExistingFile)
    file = f_dialog.getSaveFileName(parent, "Backup", os.path.expanduser("~"), filter="d4m Backup (*.d4mb)")
    if not file or not file[0]:
        return
    # TODO: auto-detect type of data
    show_d4m_infobox("unsupported")
