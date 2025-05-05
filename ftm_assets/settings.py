from anystore.model import StoreModel
from pydantic import BaseModel  # , ImportString
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiContact(BaseModel):
    name: str = "Data and Research Center – DARC"
    url: str = "https://dataresearchcenter.org"
    email: str = "hi@dataresearchcenter.org"


class ApiSettings(BaseModel):
    title: str = "FollowTheMoney Asset resolver"
    contact: ApiContact = ApiContact()
    description_uri: str = "README.md"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ftm_assets_",
        env_nested_delimiter="__",
        nested_model_default_partial_update=True,
    )

    debug: bool = False
    """Debug mode"""

    cache: StoreModel = StoreModel(uri=".cache")
    """Lookup cache"""

    store: StoreModel = StoreModel(uri="static")
    """Storage for mirrored assets"""

    mirror: bool = False
    """Mirror assets from remotes on demand"""

    thumbnails: bool = False
    """Generate thumbnails on demand"""

    thumbnail_size: int = 600
    """Size (square) for generated thumbnails"""

    public_cdn_prefix: str | None = None
    """E.g. https://cdn.example.org"""

    # image_resolvers: list[ImportString] = ["ftm_assets.resolvers.wikidata:resolve"]
    # """Activated image resolvers"""

    api: ApiSettings = ApiSettings()
