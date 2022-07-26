from io import BytesIO
from traceback import format_exc
import requests
from zipfile import ZipFile
import py7zr
from rarfile import RarFile
from d4m.util import jank_magic

BASE_DOMAIN = "https://api.gamebanana.com"
GET_DATA_ENDPOINT = "/Core/Item/Data"

ALT_API_DOMAIN = "https://gamebanana.com"
SEARCH_ENDPOINT = "/apiv9/Util/Game/Submissions"

DIVA_GAME_ID = 16522

mod_info_cache = {}

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
        resp = requests.get(BASE_DOMAIN+GET_DATA_ENDPOINT,
            params = params
        )

        if resp.status_code != 200:
            raise RuntimeError(f"Gamebanana API returned {resp.status_code}")

        for (index, elem) in enumerate(resp.json()):
            try:
                mod_id = need_fetch[index]
                files = sorted(elem[0].values(), key = lambda x: x["_tsDateAdded"], reverse=True)
                obj = {
                    "id": mod_id,
                    "hash": files[0]["_sMd5Checksum"],
                    "image": elem[1],
                    "download": files[0]["_sDownloadUrl"],
                    "download_count": elem[2],
                    "like_count": elem[3]
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

def search_mods(query: str) -> "list[dict]":
    resp = requests.get(ALT_API_DOMAIN+SEARCH_ENDPOINT,
        params = {
            "_idGameRow": DIVA_GAME_ID,
            "_sName": query,
            "_nPerpage": 50
        }
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Gamebanana search API returned {resp.status_code}")

    j = resp.json()
    def map_name(ers):
        mod_id = ers["_idRow"]
        return (mod_id, f"{ers['_sName']} by {ers['_aSubmitter']['_sName']}")
    return list(map(map_name, j))

def download_mod(mod_id: int = None, download_path: str = None) -> bytes:
    effective_download = download_path
    if mod_id != None:
        modinfo = fetch_mod_data(mod_id)
        effective_download = modinfo["download"]
    if not effective_download:
        raise ValueError("Failed to download mod: invalid args")
    resp = requests.get(effective_download)
    if resp.status_code != 200:
        raise RuntimeError(f"File download returned {resp.status_code}")
    return resp.content

def extract_archive(archive: bytes, extract_to: str) -> None:
    file_content = BytesIO(archive)
    mime_type = jank_magic(file_content.read(64))
    file_content.seek(0)
    try:
        if mime_type == "application/x-7z-compressed":
            archive = py7zr.SevenZipFile(file_content)
            archive.extractall(extract_to)
            archive.close()
        elif mime_type == "application/zip":
            archive = ZipFile(file_content)
            archive.extractall(extract_to)
            archive.close()
        elif mime_type == "application/x-rar":
            archive = RarFile(file_content)
            archive.extractall(extract_to)
            archive.close()
        else:
            raise RuntimeError("Unsupported mod archive format (must be 7z, zip, or rar)")
    except Exception as e:
        if isinstance(e, RuntimeError):
            raise(e)
        else:
            raise RuntimeError("Archive corrupted or otherwise unreadable") #TODO: there's probably a better exception for this


def download_and_extract_mod(download_url: str, destination: str):
    content = download_mod(download_path = download_url)
    extract_archive(content, destination)