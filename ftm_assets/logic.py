from anystore.decorators import anycache
from anystore.io import smart_open
from followthemoney.proxy import EntityProxy
from followthemoney.types import registry
from PIL import Image
from rigour.ids.wikidata import is_qid

from ftm_assets.logging import get_logger
from ftm_assets.model import Image as ImageModel
from ftm_assets.resolvers import wikidata
from ftm_assets.settings import Settings
from ftm_assets.store import get_cache, get_storage

settings = Settings()
log = get_logger(__name__)


@anycache(
    store=get_cache(),
    key_func=lambda i, s=None: f"thumbnails/{i.id}/{s or settings.thumbnail_size}",
)
def generate_thumbnail(img: "ImageModel", size: int | None = None) -> str:
    storage = get_storage()
    size = size or settings.thumbnail_size
    if not storage.exists(img.thumbnail_key):
        with smart_open(str(img.url)) as io:
            image = Image.open(io)
            image.convert("RGB")
            image.thumbnail((size, size))
            with storage.open(img.thumbnail_key, "wb") as out:
                image.save(out)
        log.info("Generated thumbnail.", image=img.id, size=size, uri=img.thumbnail_key)
    return img.thumbnail_key


@anycache(
    store=get_cache(),
    key_func=lambda i: f"mirrored/{i.id}",
)
def mirror(img: "ImageModel") -> str:
    storage = get_storage()
    if not storage.exists(img.key):
        with smart_open(str(img.url)) as io:
            with storage.open(img.key, "wb") as out:
                out.write(io.read())
        log.info("Stored image.", image=img.id, uri=img.key)
    return img.key


@anycache(store=get_cache(), key_func=lambda x: x, model=ImageModel)
def lookup(id: str) -> ImageModel | None:
    image = wikidata.resolve(id)
    if image is not None:
        if settings.thumbnails:
            generate_thumbnail(image)
        if settings.mirror:
            mirror(image)
        return image


def lookup_proxy(proxy: EntityProxy) -> ImageModel | None:
    id = str(proxy.id)
    if is_qid(id):
        return lookup(id)
    for id in proxy.get_type_values(registry.identifier):
        if is_qid(id):
            return lookup(id)
