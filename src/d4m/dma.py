import requests

DMA_BASE_DOMAIN = "https://divamodarchive.xyz/api/v1"
DMA_SEARCH = "/posts/latest"
DMA_GET_BY_ID = "/posts/"

mod_info_cache = {}

def multi_fetch_mod_data(mod_ids: "list[int]") -> "list[dict]":
    mod_data = []
    need_fetch = []
    for mod_id in mod_ids:
        if mod_id in mod_info_cache:
            mod_data.append(mod_info_cache[mod_id])
        else:
            need_fetch.append(mod_id)

    for mod_id in need_fetch:
        resp = requests.get(
            DMA_BASE_DOMAIN + DMA_GET_BY_ID + str(mod_id)
        )
        if resp.status_code != 200:
            #TODO: how handle this?
            pass

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
        mod_data.append(obj)

    return mod_data
        

def fetch_mod_data(mod_id: int) -> "dict":
    if mod_id in mod_info_cache:
        return mod_info_cache[mod_id]

    return multi_fetch_mod_data([mod_id])[0]

def search_mods(query: str):
    resp = requests.get(
        DMA_BASE_DOMAIN + DMA_SEARCH,
        params = {
            "name": query
        }
    )
    if resp.status_code == 404:
        return []
    if resp.status_code != 200:
        raise RuntimeError(f"DMA search API returned {resp.status_code}")

    j = resp.json()

    return list(map(lambda e: (e["id"], e["name"]), j))

def download_mod(mod_id: int = None, download_url: str = None) -> bytes:
    effective_download = download_url
    if mod_id is not None:
        modinfo = fetch_mod_data(mod_id)
        effective_download = modinfo["download"]
    if not effective_download:
        raise ValueError("(DMA) Failed to download mod: invalid args")
    