import requests
from traceback import format_exc

mod_info_cache = {}

GB_BASE_DOMAIN = "https://api.gamebanana.com"
GB_GET_DATA_ENDPOINT = "/Core/Item/Data"

GB_ALT_API_DOMAIN = "https://gamebanana.com"
GB_SEARCH_ENDPOINT = "/apiv9/Util/Game/Submissions"

GB_DIVA_GAME_ID = 16522


def multi_fetch_mod_data(mod_info: "list[tuple[int, str]]") -> "list[dict]":
    mod_data = []
    need_fetch = []
    for (mod_id, category) in mod_info:
        if mod_id in mod_info_cache:
            mod_data.append(mod_info_cache[mod_id])
        else:
            need_fetch.append((mod_id, category))

    if len(need_fetch) > 0:
        params = {}
        for index, (mod_id, category) in enumerate(need_fetch):
            params.update({
                f"itemid[{index}]": mod_id,
                f"fields[{index}]": "Files().aFiles(),Preview().sStructuredDataFullsizeUrl(),likes,downloads",
                f"itemtype[{index}]": category
            })

        resp = requests.get(GB_BASE_DOMAIN + GB_GET_DATA_ENDPOINT, params=params)

        if resp.status_code != 200:
            raise RuntimeError(f"Gamebanana API returned {resp.status_code}")

        for (index, elem) in enumerate(resp.json()):
            mod_id = need_fetch[index][0]
            try:
                files = sorted(elem[0].values(), key=lambda x: x["_tsDateAdded"], reverse=True)
                obj = {
                    "id": mod_id,
                    "hash": files[0]["_sMd5Checksum"],
                    "image": elem[1],
                    "download": files[0]["_sDownloadUrl"],
                    "download_count": elem[3],
                    "like_count": elem[2]
                }
                mod_info_cache[mod_id] = obj
                mod_data.append(obj)
            except:
                obj = {
                    "id": mod_id,
                    "hash": "err",
                    "image": "err",
                    "download": "err",
                    "download_count": "err",
                    "like_count": "err",
                    "error": format_exc()
                }
                mod_info_cache[mod_id] = obj
                mod_data.append(obj)
    return mod_data


def fetch_mod_data(mod_id: int, category: str) -> "dict":
    """
    dict w/ keys id, hash, download
    """
    if mod_id in mod_info_cache:
        return mod_info_cache[mod_id]
    return multi_fetch_mod_data([(mod_id, category)])[0]


def search_mods(query: str):
    resp = requests.get(
        GB_ALT_API_DOMAIN + GB_SEARCH_ENDPOINT,
        params={
            "_idGameRow": GB_DIVA_GAME_ID,
            "_sName": query,
            "_nPerpage": 50
        }
    )
    if resp.status_code == 404:
        return []
    if resp.status_code != 200:
        raise RuntimeError(f"Gamebanana search API returned {resp.status_code}")

    j = resp.json()

    def map_mod(ers):
        obj = {
            "name": ers['_sName'],
            "id": ers['_idRow'],
            "author": ers['_aSubmitter']['_sName'],
            "category": ers['_sModelName'],
            "origin": "gamebanana"
        }
        return obj

    return list(map(map_mod, j))


def download_favicon():
    r = requests.get("https://images.gamebanana.com/static/img/favicon/favicon.ico")
    if r.status_code != 200:
        return None
    return r.content
