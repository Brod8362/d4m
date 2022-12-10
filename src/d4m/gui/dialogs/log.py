import PySide6.QtCore
import PySide6.QtWidgets as qwidgets


class LogDialog(qwidgets.QDialog):
    def __init__(self, log_history, statusbar, parent=None):
        super(LogDialog, self).__init__(parent)
        self.log_history = log_history
        self.count_widget = qwidgets.QLabel()
        self.log_widget = qwidgets.QTextEdit()
        self.layout = qwidgets.QVBoxLayout()
        self.layout.addWidget(self.count_widget)
        self.layout.addWidget(self.log_widget)
        self.log_widget.setReadOnly(True)
        self.setLayout(self.layout)
        self.setWindowFlag(PySide6.QtCore.Qt.Tool)
        statusbar.messageChanged.connect(self.render_log)
        self.setWindowTitle("d4m log")
        self.setMinimumSize(350, 200)
        self.render_log()

    def render_log(self):
        self.count_widget.setText(f"{len(self.log_history)} log messages")
        self.log_widget.setText("\n".join(self.log_history))