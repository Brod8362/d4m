import functools

from PySide6.QtGui import QImage

import d4m.api

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
