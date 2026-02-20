from typing import Self

from pydantic import BaseModel, HttpUrl


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


class ApiImageResponse(Image):
    original_url: HttpUrl
    thumbnail_url: HttpUrl

    @classmethod
    def from_image(
        cls, image: Image, public_url: HttpUrl, thumbnail_url: HttpUrl
    ) -> Self:
        return cls(
            id=image.id,
            name=image.name,
            alt=image.alt,
            attribution=image.attribution,
            url=public_url,
            original_url=image.url,
            thumbnail_url=thumbnail_url,
        )
