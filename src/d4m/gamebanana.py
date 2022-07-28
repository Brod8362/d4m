import requests
from traceback import format_exc

mod_info_cache = {}

GB_BASE_DOMAIN = "https://api.gamebanana.com"
GB_GET_DATA_ENDPOINT = "/Core/Item/Data"

GB_ALT_API_DOMAIN = "https://gamebanana.com"
GB_SEARCH_ENDPOINT = "/apiv9/Util/Game/Submissions"

GB_DIVA_GAME_ID = 16522

def multi_fetch_mod_data(mod_ids: "list[int]") -> "list[dict]":
    mod_data = []
    need_fetch = []
    for mod_id in mod_ids:
        if mod_id in mod_info_cache:
            mod_data.append(mod_info_cache[mod_id])
        else:
            need_fetch.append(mod_id)

    if len(need_fetch) > 0:
        params = {}
        for (index, mod_id) in enumerate(need_fetch):
            params.update({
                f"itemid[{index}]": mod_id,
                f"fields[{index}]": "Files().aFiles(),Preview().sStructuredDataFullsizeUrl(),likes,downloads",
                f"itemtype[{index}]": "Mod"
            })
        resp = requests.get(GB_BASE_DOMAIN + GB_GET_DATA_ENDPOINT,
                            params=params
                            )

        if resp.status_code != 200:
            raise RuntimeError(f"Gamebanana API returned {resp.status_code}")

        for (index, elem) in enumerate(resp.json()):
            mod_id = need_fetch[index]
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


def fetch_mod_data(mod_id: int) -> "dict":
    """
    dict w/ keys id, hash, download
    """
    if mod_id in mod_info_cache:
        return mod_info_cache[mod_id]

    return multi_fetch_mod_data([mod_id])[0]

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

    def map_name(ers):
        mod_id = ers["_idRow"]
        return mod_id, f"{ers['_sName']} by {ers['_aSubmitter']['_sName']}"

    return list(map(map_name, j))

def download_mod(mod_id: int = None, download_path: str = None) -> bytes:
    effective_download = download_path
    if mod_id is not None:
        modinfo = fetch_mod_data(mod_id)
        effective_download = modinfo["download"]
    if not effective_download:
        raise ValueError("Failed to download mod: invalid args")
    resp = requests.get(effective_download)
    if resp.status_code != 200:
        raise RuntimeError(f"File download returned {resp.status_code}")
    return resp.content