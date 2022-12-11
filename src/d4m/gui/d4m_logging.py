from time import strftime


class D4mLogger:
    def __init__(self, statusbar):
        self.statusbar = statusbar
        self.log_history = []

    def attach_statusbar(self, statusbar):
        self.statusbar = statusbar

    def detach_statusbar(self):
        self.statusbar = None

    def log_msg(self, content):
        timestamp = strftime("%H:%M:%S")
        self.log_history.append(f"[{timestamp}] {content}")
        if self.statusbar:
            self.statusbar.showMessage(content)

    def history(self) -> list[str]:
        return self.log_history
