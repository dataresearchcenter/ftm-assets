from typing import Self

from anystore.util import join_uri
from pydantic import BaseModel, HttpUrl

from ftm_assets.settings import Settings
from ftm_assets.store import get_storage

settings = Settings()
storage = get_storage()

IMAGE_PREFIX = "img"


def key_exists(key: str) -> bool:
    storage = get_storage()
    return storage.exists(key) and storage.info(key).size > 0


def make_key(id: str, name: str) -> str:
    return f"{IMAGE_PREFIX}/{id}/{name}"


def make_thumbnail_key(id: str) -> str:
    return f"{IMAGE_PREFIX}/{id}/thumbs/{settings.thumbnail_size}.jpg"


class Attribution(BaseModel):
    license: str
    license_url: HttpUrl
    author: str | None = None
    source: str | None = None
    source_url: HttpUrl | None = None


class AltText(BaseModel):
    text: str
    language: str


class Image(BaseModel):
    id: str
    name: str
    url: HttpUrl
    alt: list[AltText] = []
    attribution: Attribution | None = None

    @property
    def key(self) -> str:
        return make_key(self.id, self.name)

    @property
    def thumbnail_key(self) -> str:
        return make_thumbnail_key(self.id)

    def get_public_url(self) -> HttpUrl:
        if settings.public_cdn_prefix is not None and key_exists(self.key):
            return HttpUrl(join_uri(settings.public_cdn_prefix, self.key))
        return self.url

    def get_thumbnail_url(self) -> HttpUrl:
        if settings.public_cdn_prefix is not None and key_exists(self.thumbnail_key):
            return HttpUrl(join_uri(settings.public_cdn_prefix, self.thumbnail_key))
        return self.get_public_url()

    @classmethod
    def from_id(cls, id: str) -> Self | None:
        if settings.public_cdn_prefix is None:
            raise NotImplementedError("Missing setting for public url")
        storage = get_storage()
        prefix = f"{IMAGE_PREFIX}/{id}"
        for key in storage.iterate_keys(prefix):
            name = key.split("/")[-1]
            url = HttpUrl(join_uri(settings.public_cdn_prefix, key))
            return cls(id=id, name=name, url=url)


class ApiImageResponse(Image):
    original_url: HttpUrl
    thumbnail_url: HttpUrl

    @classmethod
    def from_image(cls, image: Image) -> Self:
        return cls(
            id=image.id,
            name=image.name,
            alt=image.alt,
            attribution=image.attribution,
            url=image.get_public_url(),
            original_url=image.url,
            thumbnail_url=image.get_thumbnail_url(),
        )
