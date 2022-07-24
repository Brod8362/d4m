from io import BytesIO
import requests
from datetime import datetime
import magic
from zipfile import ZipFile
import py7zr
from rarfile import RarFile
import functools

BASE_DOMAIN = "https://api.gamebanana.com"
GET_DATA_ENDPOINT = "/Core/Item/Data"

ALT_API_DOMAIN = "https://gamebanana.com"
SEARCH_ENDPOINT = "/apiv9/Util/Game/Submissions"

DIVA_GAME_ID = 16522

@functools.cache
def fetch_mod_data(mod_id: int) -> datetime:
    """
    dict w/ keys id, hash, download
    """
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

def download_and_extract_mod(download_url: str, destination: str):
    resp = requests.get(download_url)
    if resp.status_code != 200:
        #TODO: exception?
        pass

    file_content = BytesIO(resp.content)
    mime_type = magic.from_buffer(file_content.read(1024), mime=True)
    file_content.seek(0)
    if mime_type == "application/x-7z-compressed":
        archive = py7zr.SevenZipFile(file_content)
        archive.extractall(destination)
        archive.close()
        #TODO: catch exception for invalid 7z file
    elif mime_type == "application/zip":
        archive = ZipFile(file_content)
        archive.extractall(destination)
        archive.close()
        #TODO: catch exception for invalid 7z file
    elif mime_type == "application/x-rar":
        archive = RarFile(file_content)
        archive.extractall(destination)
        archive.close()
        #TODO: catch exception for invalid 7z file
    else:
        pass #TODO: exception? unsupported file type