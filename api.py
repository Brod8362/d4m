import requests
from datetime import datetime

BASE_DOMAIN = "https://api.gamebanana.com"
GET_DATA_ENDPOINT = "/Core/Item/Data"

def fetch_mod_data(mod_id: int) -> datetime:
    resp = requests.get(BASE_DOMAIN+GET_DATA_ENDPOINT,
        params = {
            "itemid": mod_id,
            "fields": "mdate,Files().aFiles()",
            "itemtype": "Mod"
        }
    )

    if resp.status_code != 200:
        return None #TODO: exception?

    j = resp.json()
    files = sorted(j[1].values(), key = lambda x : x["_tsDateAdded"], reverse=True)
    return {
        "modified_date": j[0],
        "download": files[0]["_sDownloadUrl"]
    }