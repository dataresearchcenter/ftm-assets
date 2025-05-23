from anystore.model import StoreModel
from pydantic import BaseModel, Field  # , ImportString
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich import print


class ApiContact(BaseModel):
    name: str = "Data and Research Center – DARC"
    url: str = "https://dataresearchcenter.org"
    email: str = "hi@dataresearchcenter.org"


class ApiSettings(BaseModel):
    path_prefix: str = "/api"
    """Deploy the fastapi under this prefix. This allows to have e.g. a domain
    "https://assets.example.org/api" for the app and
    "https://assets.example.org/*" deployed for static serving."""

    title: str = "FollowTheMoney Asset resolver"
    contact: ApiContact = ApiContact()
    description_uri: str = "README.md"
    allowed_origins: list[str] = []

    build_key: str = "secret-key-for-build"
    """Backend api key to use for build processes to allow mirror & thumbnail
    generation"""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ftm_assets_",
        env_nested_delimiter="_",
        nested_model_default_partial_update=True,
    )

    debug: bool = Field(default=False, alias="debug")
    """Debug mode"""

    dev_static: bool = False
    """Serve static files for development mode"""

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


settings = Settings()

if settings.debug:
    print(settings)
