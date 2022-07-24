
MAGIC_PAIRS = [
    (b"\x37\x7A\xBC\xAF\x27\x1C", "application/x-7z-compressed"),
    (b"\x52\x61\x72\x21\x1A\x07\x01\x00", "application/x-rar"),
    (b"\x52\x61\x72\x21\x1A\x07\x00", "application/x-rar"),
    (b"\x50\x4B\x03\x04", "application/zip"),
    (b"\x50\x4B\x05\x06", "application/zip"),
    (b"\x50\x4B\x07\x08", "application/zip"),
]

def jank_magic(buf):
    for (data, mime) in MAGIC_PAIRS:
        if buf.startswith(data):
            return mime
    return None