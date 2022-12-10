import functools

import feedparser

NEWS_URL = "https://hijiri.byakuren.pw/files/d4m.rss"


@functools.lru_cache(maxsize=1)
def retrieve_news() -> list:
    try:
        return feedparser.parse(NEWS_URL).entries
    except:
        return None


def latest_news() -> list:
    news_list = retrieve_news()
    if not news_list:
        return None
    return retrieve_news()[0]
