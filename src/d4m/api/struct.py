import dataclasses


@dataclasses.dataclass
class ModAPIInfo:
    id: int
    hash: str
    image: str
    download: str
    download_count: str
    like_count: str

    def __getitem__(self, item):
        return getattr(self, item)


@dataclasses.dataclass
class APISearchResult:
    name: str
    id: int
    author: str
    category: str
    origin: str
