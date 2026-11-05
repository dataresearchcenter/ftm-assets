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
    """Image metadata, stored as `meta.json` next to the image files. `url` and
    `thumbnail_url` are relative to the `meta.json` location, so clients can
    resolve them against wherever the store is served from."""

    id: str
    name: str
    """Filename of the original image at its source"""
    sha256: str | None = None
    """Checksum of the original image, its key in the store"""
    url: str | None = None
    """Mirrored original image, relative to `meta.json`"""
    thumbnail_url: str | None = None
    """Thumbnail, relative to `meta.json`"""
    original_url: HttpUrl | None = None
    """Source of the original image, if known"""
    alt: list[AltText] = []
    attribution: Attribution | None = None
