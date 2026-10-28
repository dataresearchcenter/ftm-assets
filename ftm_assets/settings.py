from anystore.model import StoreModel
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich import print


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ftm_assets_",
        env_nested_delimiter="_",
        nested_model_default_partial_update=True,
    )

    debug: bool = Field(default=False, alias="debug")
    """Debug mode"""

    store: StoreModel = StoreModel(uri="static")
    """Storage for built assets (mirrored images, thumbnails, metadata). Its
    contents are meant to be served statically, e.g. from a bucket."""

    thumbnail_size: int = 600
    """Size (square) for generated thumbnails"""

    # image_resolvers: list[ImportString] = ["ftm_assets.resolvers.wikidata:resolve"]
    # """Activated image resolvers"""

    openverse_api_key: str | None = None
    """Optional Openverse API key for higher rate limits"""


settings = Settings()

if settings.debug:
    print(settings)
