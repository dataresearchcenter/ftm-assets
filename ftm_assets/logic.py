from io import BytesIO

import httpx
from anystore.decorators import error_handler
from anystore.logging import get_logger
from anystore.util.checksum import make_data_checksum
from followthemoney.proxy import EntityProxy
from followthemoney.types import registry
from PIL import Image
from rigour.ids.wikidata import is_qid

from ftm_assets import repository
from ftm_assets.model import Image as ImageModel
from ftm_assets.resolvers import HEADERS, openverse, wikidata
from ftm_assets.settings import Settings

settings = Settings()
log = get_logger(__name__)


def download_image(url: str) -> bytes:
    """Download image data from a URL with proper User-Agent."""
    with httpx.stream("GET", url, headers=HEADERS, follow_redirects=True) as r:
        r.raise_for_status()
        return r.read()


@error_handler(logger=log)
def mirror(img: ImageModel) -> str:
    """Download the original image and store it by its sha256 checksum"""
    if img.original_url is None:
        raise ValueError(f"No source url for image `{img.id}`")
    data = download_image(str(img.original_url))
    img.sha256 = make_data_checksum(data)
    key = repository.make_key(img.id, img.sha256, img.name)
    if not repository.exists(key):
        repository.save_data(key, data)
        log.info("Stored image.", image=img.id, uri=key)
    return key


@error_handler(logger=log)
def generate_thumbnail(img: ImageModel, key: str) -> str:
    """Generate the thumbnail from the mirrored original image at `key`"""
    size = settings.thumbnail_size
    thumbnail_key = repository.make_thumbnail_key(img.id)
    if not repository.exists(thumbnail_key):
        data = repository.get_data(key)
        image = Image.open(BytesIO(data))
        rgb_img = image.convert("RGB")
        rgb_img.thumbnail((size, size))
        buf = BytesIO()
        rgb_img.save(buf, format="JPEG")
        repository.save_data(thumbnail_key, buf.getvalue())
        log.info("Generated thumbnail.", image=img.id, size=size, uri=thumbnail_key)
    return thumbnail_key


def build(img: ImageModel) -> ImageModel | None:
    """Mirror the original image and generate its thumbnail. The meta.json is
    written last, so its presence means the image is complete."""
    image_key = mirror(img)
    thumbnail_key = generate_thumbnail(img, image_key) if image_key else None
    if thumbnail_key:
        img.url = repository.make_relative_url(img.id, image_key)
        img.thumbnail_url = repository.make_relative_url(img.id, thumbnail_key)
        repository.save_metadata(img)
        return img
    return None


@error_handler(logger=log)
def lookup(id: str, name: str | None = None) -> ImageModel | None:
    """Get an image from the store, or resolve and build it"""
    res = repository.get_image(id)
    if res is not None:
        return res
    return resolve(id, name)


@error_handler(logger=log)
def resolve(id: str, name: str | None = None) -> ImageModel | None:
    """Resolve an image via Wikidata, falling back to an Openverse search by
    `name` if given, and build it"""
    image = wikidata.resolve(id)
    if image is None and name:
        image = openverse.resolve(id, name)
    if image is not None:
        return build(image)
    return None


@error_handler(logger=log)
def lookup_proxy(proxy: EntityProxy) -> ImageModel | None:
    name = proxy.first("name", quiet=True)
    id = str(proxy.id)
    if is_qid(id):
        return lookup(id, name)
    for id in proxy.get_type_values(registry.identifier):
        if is_qid(id):
            return lookup(id, name)
    return None
