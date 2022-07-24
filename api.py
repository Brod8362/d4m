import requests
from datetime import datetime

BASE_DOMAIN = "https://api.gamebanana.com"
GET_DATA_ENDPOINT = "/Core/Item/Data"

ALT_API_DOMAIN = "https://gamebanana.com"
SEARCH_ENDPOINT = "/apiv9/Util/Game/Submissions"

DIVA_GAME_ID = 16522

def fetch_mod_data(mod_id: int) -> datetime:
    resp = requests.get(BASE_DOMAIN+GET_DATA_ENDPOINT,
        params = {
            "itemid": mod_id,
            "fields": "Files().aFiles()",
            "itemtype": "Mod"
        }
    )

    if resp.status_code != 200:
        return None #TODO: exception?

    j = resp.json()
    files = sorted(j[0].values(), key = lambda x : x["_tsDateAdded"], reverse=True)
    return {
        "id": mod_id,
        "hash": files[0]["_sMd5Checksum"],
        "download": files[0]["_sDownloadUrl"],
    }

def search_mods(query: str) -> "list[dict]":
    resp = requests.get(ALT_API_DOMAIN+SEARCH_ENDPOINT,
        params = {
            "_idGameRow": DIVA_GAME_ID,
            "_sName": query,
            "_nPerpage": 50
        }
    )
    if resp.status_code != 200:
        return None #TODO: exception?
    j = resp.json()
    def map_name(ers):
        mod_id = ers["_idRow"]
        return (mod_id, f"{ers['_sName']} by {ers['_aSubmitter']['_sName']}")
    return list(map(map_name, j))