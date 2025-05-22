from typing import Self

from anystore.util import join_uri
from pydantic import BaseModel, HttpUrl

from ftm_assets.settings import Settings
from ftm_assets.store import get_storage

settings = Settings()
storage = get_storage()

IMAGE_PREFIX = "img"


def exists(key: str) -> bool:
    storage = get_storage()
    return storage.exists(key) and storage.info(key).size > 0


class Attribution(BaseModel):
    license: str
    license_url: HttpUrl
    author: str | None = None


class AltText(BaseModel):
    text: str
    language: str


class Image(BaseModel):
    id: str
    name: str
    url: HttpUrl
    alt: list[AltText] = []
    attribution: Attribution

    @property
    def key(self) -> str:
        return f"{IMAGE_PREFIX}/{self.id}/{self.name}"

    @property
    def thumbnail_key(self) -> str:
        return f"{IMAGE_PREFIX}/{self.id}/thumbs/{settings.thumbnail_size}.jpg"

    def get_public_url(self) -> HttpUrl:
        if settings.public_cdn_prefix is not None and exists(self.key):
            return HttpUrl(join_uri(settings.public_cdn_prefix, self.key))
        return self.url

    def get_thumbnail_url(self) -> HttpUrl:
        if settings.public_cdn_prefix is not None and exists(self.thumbnail_key):
            return HttpUrl(join_uri(settings.public_cdn_prefix, self.thumbnail_key))
        return self.get_public_url()


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
