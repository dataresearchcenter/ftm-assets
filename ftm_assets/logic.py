from io import BytesIO

import httpx
from anystore.decorators import error_handler
from followthemoney.proxy import EntityProxy
from followthemoney.types import registry
from PIL import Image
from rigour.ids.wikidata import is_qid

from ftm_assets import repository
from ftm_assets.logging import get_logger
from ftm_assets.model import Image as ImageModel
from ftm_assets.resolvers import wikidata
from ftm_assets.resolvers.wikidata import HEADERS
from ftm_assets.settings import Settings

settings = Settings()
log = get_logger(__name__)


def download_image(url: str) -> bytes:
    """Download image data from a URL with proper User-Agent."""
    with httpx.stream("GET", url, headers=HEADERS, follow_redirects=True) as r:
        r.raise_for_status()
        return r.read()


@error_handler(logger=log)
def generate_thumbnail(img: "ImageModel", size: int | None = None) -> str:
    size = size or settings.thumbnail_size
    key = repository.make_thumbnail_key(img.id)
    if not repository.thumbnail_exists(img.id):
        data = download_image(str(img.url))
        image = Image.open(BytesIO(data))
        rgb_img = image.convert("RGB")
        rgb_img.thumbnail((size, size))
        buf = BytesIO()
        rgb_img.save(buf, format="JPEG")
        repository.save_data(key, buf.getvalue())
        log.info("Generated thumbnail.", image=img.id, size=size, uri=key)
    return key


@error_handler(logger=log)
def mirror(img: "ImageModel") -> str:
    key = repository.make_key(img.id, img.name)
    if not repository.image_exists(img.id, img.name):
        data = download_image(str(img.url))
        repository.save_data(key, data)
        log.info("Stored image.", image=img.id, uri=key)
    return key


@error_handler(logger=log)
def lookup(
    id: str, store: bool | None = False, thumbnail: bool | None = False
) -> ImageModel | None:
    res = repository.get_image(id)
    if res is not None:
        return res
    return resolve(id, store, thumbnail)


@error_handler(logger=log)
def resolve(
    id: str, store: bool | None = False, thumbnail: bool | None = False
) -> ImageModel | None:
    image = wikidata.resolve(id)
    if image is not None:
        repository.save_metadata(image)
        if store or settings.mirror:
            mirror(image)
        if thumbnail or settings.thumbnails:
            generate_thumbnail(image)
        return image


@error_handler(logger=log)
def lookup_proxy(proxy: EntityProxy) -> ImageModel | None:
    id = str(proxy.id)
    if is_qid(id):
        return lookup(id)
    for id in proxy.get_type_values(registry.identifier):
        if is_qid(id):
            return lookup(id)
