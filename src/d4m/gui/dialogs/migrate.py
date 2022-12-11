import PySide6.QtWidgets as qwidgets

from d4m.gui.context import D4mGlobalContext


class DmmMigrateDialog(qwidgets.QDialog):
    def __init__(self, context: D4mGlobalContext = None, callback=None, parent=None):
        super(DmmMigrateDialog, self).__init__(parent)
        self.win_layout = qwidgets.QVBoxLayout()

        self.progress_log = qwidgets.QTextEdit()
        self.progress_bar = qwidgets.QProgressBar()
        self.start_button = qwidgets.QPushButton("Start")

        def migrate():
            eligible = [m for m in context.mod_manager.mods if m.can_attempt_dmm_migration()]
            successful_count = 0
            self.progress_bar.setRange(0, len(eligible))
            self.progress_log.append(f"{len(eligible)} mod(s) are eligible for migration\n")
            for (index, mod) in enumerate(eligible):
                if mod.can_attempt_dmm_migration():
                    self.progress_log.append(f"Attempting to migrate {mod.name}...\n")
                    success = mod.attempt_migrate_from_dmm()
                    if success:
                        self.progress_log.append(f"Migrated {mod.name} successfully.\n")
                        successful_count += 1
                    else:
                        self.progress_log.append(f"Failed to migrate {mod.name}.\n")
                    self.progress_bar.setValue(index + 1)

            self.progress_bar.setRange(0, 1)
            self.progress_bar.setValue(1)
            if successful_count > 0:
                self.progress_log.append(f"Migrated {successful_count}/{len(eligible)} successfully.\n")
                self.progress_log.append(
                    f"Please note that migrated mod(s) may need an update before the thumbnail appears.\n")
            if callback:
                callback()

        self.progress_log.setReadOnly(True)
        self.start_button.clicked.connect(migrate)
        self.progress_log.append("Click start to attempt migration from DivaModManager.")

        self.win_layout.addWidget(self.progress_log)
        self.win_layout.addWidget(self.progress_bar)
        self.win_layout.addWidget(self.start_button)
        self.setLayout(self.win_layout)
        self.setMinimumSize(350, 300)
        self.setWindowTitle("d4m - Migrate from DivaModManager")
