import requests

DMA_BASE_DOMAIN = "https://divamodarchive.com/api/v1"
DMA_SEARCH = "/posts/latest"
DMA_GET_BY_ID = "/posts/"
DMA_GET_BY_ID_BULK = "/posts/posts"

mod_info_cache = {}


def multi_fetch_mod_data(mod_info: "list[tuple[int, str]]") -> "list[dict]":
    mod_data = []
    need_fetch = []
    for (mod_id, _) in mod_info:
        if mod_id in mod_info_cache:
            mod_data.append(mod_info_cache[mod_id])
        else:
            need_fetch.append(mod_id)

    if len(need_fetch) > 0:
        resp = requests.get(
            DMA_BASE_DOMAIN + DMA_GET_BY_ID_BULK,
            params=[("post_id", i) for i in need_fetch]
        )
        if resp.status_code // 100 != 2:
            raise RuntimeError(f"DMA info returned {resp.status_code}")

        j = resp.json()
        for post in j:
            obj = {
                "id": post["id"],
                "hash": post["date"],
                "image": post["image"],
                "download": post["link"],
                "download_count": post["downloads"],
                "like_count": post["likes"]
            }
            mod_info_cache[post["id"]] = obj
            mod_data.append(obj)

    return mod_data


# category is not used for diva mod archive
def fetch_mod_data(mod_id: int, _category: str) -> "dict":
    if mod_id in mod_info_cache:
        return mod_info_cache[mod_id]

    resp = requests.get(
        DMA_BASE_DOMAIN + DMA_GET_BY_ID + str(mod_id)
    )
    if resp.status_code // 100 != 2:
        raise RuntimeError(f"DMA info returned {resp.status_code}")

    j = resp.json()

    obj = {
        "id": mod_id,
        "hash": j["date"],
        "image": j["image"],
        "download": j["link"],
        "download_count": j["downloads"],
        "like_count": j["likes"]
    }
    mod_info_cache[mod_id] = obj
    return obj


def search_mods(query: str):
    resp = requests.get(
        DMA_BASE_DOMAIN + DMA_SEARCH,
        params={
            "name": query,
            "game_tag": 0
        }
    )
    if resp.status_code == 404:
        return []
    if resp.status_code // 100 != 2:
        raise RuntimeError(f"DMA search API returned {resp.status_code}")

    j = resp.json()

    def map_mod(e):
        obj = {
            "name": e["name"],
            "id": e["id"],
            "author": e["user"]["name"],
            "category": e["type_tag"],
            "origin": "divamodarchive"
        }
        return obj

    return list(map(map_mod, j))


def download_favicon():
    r = requests.get("https://divamodarchive.xyz/favicon.ico")
    if r.status_code != 200:
        return None
    return r.content
