"""
Storage layout. The store is meant to be served statically, clients find an
image via its `meta.json` and resolve the relative urls in it:

    img/{id}/meta.json          # Image model, written last (image is complete)
    img/{id}/{sha256}{ext}      # mirrored original, by its checksum
    img/{id}/thumbs/{size}.jpg  # thumbnail
"""

from functools import cache
from pathlib import PurePosixPath
from urllib.parse import quote

from anystore.store import Store, get_store

from ftm_assets.model import Image
from ftm_assets.settings import Settings

settings = Settings()

IMAGE_PREFIX = "img"
META_FILENAME = "meta.json"


@cache
def get_storage() -> Store:
    return get_store(**{**settings.store.model_dump(), "store_none_values": False})


def make_key(id: str, checksum: str, name: str) -> str:
    """Key of the original image: its sha256 checksum with the file extension
    of its `name`"""
    suffix = PurePosixPath(name).suffix.lower()
    return f"{IMAGE_PREFIX}/{id}/{checksum}{suffix}"


def make_thumbnail_key(id: str) -> str:
    return f"{IMAGE_PREFIX}/{id}/thumbs/{settings.thumbnail_size}.jpg"


def make_meta_key(id: str) -> str:
    return f"{IMAGE_PREFIX}/{id}/{META_FILENAME}"


def make_relative_url(id: str, key: str) -> str:
    """Url of the given key relative to the image's meta.json"""
    return quote(key.removeprefix(f"{IMAGE_PREFIX}/{id}/"))


def get_image(id: str) -> Image | None:
    """Load the Image model from img/{id}/meta.json, if it exists."""
    storage = get_storage()
    meta_key = make_meta_key(id)
    if storage.exists(meta_key):
        return storage.get(meta_key, model=Image)
    return None


def save_metadata(image: Image) -> None:
    """Persist Image model as img/{id}/meta.json."""
    storage = get_storage()
    meta_key = make_meta_key(image.id)
    storage.put(meta_key, image, model=Image)


def exists(key: str) -> bool:
    storage = get_storage()
    return storage.exists(key) and storage.info(key).size > 0


def get_data(key: str) -> bytes:
    storage = get_storage()
    with storage.open(key, "rb") as fh:
        data: bytes = fh.read()
        return data


def save_data(key: str, data: bytes) -> None:
    storage = get_storage()
    with storage.open(key, "wb") as out:
        out.write(data)
