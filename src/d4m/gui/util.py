import functools

from PySide6.QtGui import QImage

import d4m.api
import PySide6.QtWidgets as qwidgets

FAVICONS = {
    "divamodarchive": d4m.api.download_favicon("divamodarchive"),
    "gamebanana": d4m.api.download_favicon("gamebanana")
}


@functools.lru_cache(maxsize=10)
def favicon_qimage(origin):
    img_bytes = FAVICONS.get(origin, None)
    if img_bytes:
        try:
            img = QImage()
            img.loadFromData(img_bytes)
            return img.scaled(16, 16)
        except:
            return None
    else:
        return None


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
