import PySide6.QtWidgets as qwidgets
from PySide6.QtGui import QDesktopServices
import d4m.rss


class NewsHistoryDialog(qwidgets.QDialog):
    def __init__(self, parent=None):
        super(NewsHistoryDialog, self).__init__(parent)
        self.news = d4m.rss.retrieve_news()

        self.window_layout = qwidgets.QVBoxLayout()

        self.news_list_layout = qwidgets.QListWidget()

        self.header_label = qwidgets.QLabel("Older News")
        self.header_label.setToolTip("Double-click any entry to open")

        self.close_button = qwidgets.QPushButton("Close")
        self.close_button.setIcon(self.style().standardIcon(qwidgets.QStyle.SP_DialogCloseButton))
        self.close_button.clicked.connect(lambda *_: self.close())

        for entry in self.news:
            # populate news entries
            if hasattr(entry, "published"):
                news_list_item = qwidgets.QListWidgetItem(f"{entry.title} ({entry.published})\n{entry.description}",
                                                          listview=self.news_list_layout)
            else:
                news_list_item = qwidgets.QListWidgetItem(f"{entry.title}\n{entry.description}",
                                                          listview=self.news_list_layout)
            news_list_item.setIcon(self.style().standardIcon(qwidgets.QStyle.SP_MessageBoxInformation))
            news_list_item.setToolTip(entry.link)

        self.window_layout.addWidget(self.header_label)
        self.window_layout.addWidget(self.news_list_layout)
        self.window_layout.addWidget(self.close_button)

        # Slot 3 is the tooltip, which is the url
        # see: https://doc.qt.io/qt-6/qt.html#ItemDataRole-enum
        self.news_list_layout.itemDoubleClicked.connect(lambda item: QDesktopServices.openUrl(item.data(3)))
        self.setLayout(self.window_layout)
        self.setMinimumSize(450, 300)
        self.setWindowTitle("d4m - News")
