from anystore.util import join_uri
from pydantic import BaseModel, HttpUrl
from pydantic_extra_types.language_code import LanguageAlpha2

from ftm_assets.settings import Settings

settings = Settings()

IMAGE_PREFIX = "img"


class Attribution(BaseModel):
    license: str
    license_url: HttpUrl
    author: str | None = None


class AltText(BaseModel):
    text: str
    language: LanguageAlpha2


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
    def thumbnail(self) -> str:
        return f"{IMAGE_PREFIX}/{self.id}/thumbs/{settings.thumbnail_size}.jpg"

    @property
    def public_url(self) -> str:
        if settings.public_cdn_prefix is not None:
            return join_uri(settings.public_cdn_prefix, self.key)
        return str(self.url)

    @property
    def thumbnail_url(self) -> str:
        if settings.public_cdn_prefix is not None:
            return join_uri(settings.public_cdn_prefix, self.thumbnail)
        return self.thumbnail
