from functools import cache

from anystore.store import Store, get_store
from anystore.util import join_uri
from pydantic import HttpUrl

from ftm_assets.model import Image
from ftm_assets.settings import Settings

settings = Settings()

IMAGE_PREFIX = "img"
META_FILENAME = "meta.json"


@cache
def get_storage() -> Store:
    return get_store(**{**settings.store.model_dump(), "store_none_values": False})


def make_key(id: str, name: str) -> str:
    return f"{IMAGE_PREFIX}/{id}/{name}"


def make_thumbnail_key(id: str) -> str:
    return f"{IMAGE_PREFIX}/{id}/thumbs/{settings.thumbnail_size}.jpg"


def make_meta_key(id: str) -> str:
    return f"{IMAGE_PREFIX}/{id}/{META_FILENAME}"


def get_image(id: str) -> Image | None:
    """Load image from store.

    1. If public_cdn_prefix is None, return None (clean fallback to resolver)
    2. Check for meta.json — if found, deserialize full Image
    3. If no meta.json, iterate keys filtering out thumbs/ and meta.json
    4. Return None if nothing found
    """
    if settings.public_cdn_prefix is None:
        return None
    storage = get_storage()
    meta_key = make_meta_key(id)
    if storage.exists(meta_key):
        data = storage.get(meta_key, model=Image)
        if data is not None:
            return data
    prefix = f"{IMAGE_PREFIX}/{id}"
    for key in storage.iterate_keys(prefix):
        name = key.split("/")[-1]
        if name == META_FILENAME or "/thumbs/" in key:
            continue
        url = HttpUrl(join_uri(settings.public_cdn_prefix, key))
        return Image(id=id, name=name, url=url)
    return None


def save_metadata(image: Image) -> None:
    """Persist Image model as img/{id}/meta.json."""
    storage = get_storage()
    meta_key = make_meta_key(image.id)
    storage.put(meta_key, image, model=Image)


def image_exists(id: str, name: str) -> bool:
    storage = get_storage()
    key = make_key(id, name)
    return storage.exists(key) and storage.info(key).size > 0


def thumbnail_exists(id: str) -> bool:
    storage = get_storage()
    key = make_thumbnail_key(id)
    return storage.exists(key) and storage.info(key).size > 0


def save_data(key: str, data: bytes) -> None:
    storage = get_storage()
    with storage.open(key, "wb") as out:
        out.write(data)


def get_public_url(image: Image) -> HttpUrl:
    """CDN URL if cdn prefix configured and file exists in store, else original URL."""
    if settings.public_cdn_prefix is not None:
        key = make_key(image.id, image.name)
        if image_exists(image.id, image.name):
            return HttpUrl(join_uri(settings.public_cdn_prefix, key))
    return image.url


def get_thumbnail_url(image: Image) -> HttpUrl:
    """CDN thumbnail URL if exists, else falls back to get_public_url."""
    if settings.public_cdn_prefix is not None and thumbnail_exists(image.id):
        key = make_thumbnail_key(image.id)
        return HttpUrl(join_uri(settings.public_cdn_prefix, key))
    return get_public_url(image)
