import d4m.gamebanana as gamebanana
import d4m.dma as dma
import d4m.manage
import requests

SUPPORTED_APIS = {
    "divamodarchive": dma,
    "gamebanana": gamebanana
}

class UnsupportedAPIError(Exception):
    pass

def multi_fetch_mod_data(mod_ids: "list[int]", origin = "gamebanana") -> "list[dict]":
    """Fetch data for multiple mods from the requested origin.

    Params:
        mod_id - list of mod ids to request data for
        origin - origin API to use (default: gamebanana)

    Returns: a list of dicts with the keys id, hash, image, download, download_count, like_count
    """
    if origin not in SUPPORTED_APIS.keys():
        raise UnsupportedAPIError(origin)
    return SUPPORTED_APIS[origin].multi_fetch_mod_data(mod_ids)

def fetch_mod_data(mod_id: int, origin = "gamebanana") -> "dict":
    """Fetch data for a mod from the requested origin.

    Params:
        mod_id - mod id to request data for
        origin - origin API to use (default: gamebanana)

    Returns: a dict with the keys id, hash, image, download, download_count, like_count
    """
    if origin not in SUPPORTED_APIS.keys():
        raise UnsupportedAPIError(origin)
    return SUPPORTED_APIS[origin].fetch_mod_data(mod_id)

def search_mods(query: str, origin = "gamebanana") -> "list[tuple[any,any]]":
    """Search for mods matching `query` on the requested origin.
    
    Params:
        query: string to match against
        origin: origin API to use (defualt: gamebanana)
        
    Returns: a list of tuples in the format (id, mod_name)"""
    if origin not in SUPPORTED_APIS.keys():
        raise UnsupportedAPIError(origin)
    return SUPPORTED_APIS[origin].search_mods(query)


def download_and_extract_mod(download_url: str, destination: str):
    """Download a mod from download_url and extract it to destination.
    This function is only here for backwards compatibility.
    """
    resp = requests.get(download_url)
    if resp.status_code != 200:
        raise RuntimeError(f"Failed to download mod from {download_url}")
    d4m.manage.extract_archive(resp.content, destination)
