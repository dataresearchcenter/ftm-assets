from functools import cache

from anystore.store import BaseStore, get_store

from ftm_assets.settings import Settings

settings = Settings()


@cache
def get_storage() -> BaseStore:
    return get_store(**{**settings.store.model_dump(), "store_none_values": False})


@cache
def get_cache() -> BaseStore:
    return get_store(**{**settings.cache.model_dump(), "store_none_values": False})
