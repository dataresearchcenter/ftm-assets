"""
Openverse resolver. Searches the Openverse API (WordPress/CC) for CC-licensed
images by entity name.

https://api.openverse.org/v1/images/
"""

import httpx
from anystore.logging import get_logger
from pydantic import HttpUrl

from ftm_assets.model import Attribution, Image
from ftm_assets.resolvers import HEADERS
from ftm_assets.settings import Settings

log = get_logger(__name__)
settings = Settings()

BASE_URL = "https://api.openverse.org/v1/images/"

LICENSE_FILTER = "by,by-sa,cc0"


def resolve(id: str, name: str) -> Image | None:
    try:
        headers = dict(HEADERS)
        if settings.openverse_api_key:
            headers["Authorization"] = f"Bearer {settings.openverse_api_key}"

        params: dict[str, str | int] = {
            "q": name,
            "license": LICENSE_FILTER,
            "page_size": 5,
        }
        res = httpx.get(BASE_URL, headers=headers, params=params)
        res.raise_for_status()
        data = res.json()

        results = data.get("results", [])
        if not results:
            log.info("No Openverse results.", id=id, name=name)
            return None

        hit = results[0]
        url = hit.get("url")
        if not url:
            return None

        # used as storage key and url path, so don't use the free-text title
        filename = f"{hit['id']}.{hit.get('filetype') or 'jpg'}"
        license_name = hit.get("license", "").upper()
        license_version = hit.get("license_version", "")
        if license_version:
            license_name = f"{license_name} {license_version}"

        license_url = hit.get("license_url") or (
            "https://creativecommons.org/licenses/"
            f"{hit.get('license', 'by')}/{hit.get('license_version', '4.0')}/"
        )

        return Image(
            id=id,
            name=filename,
            original_url=HttpUrl(url),
            attribution=Attribution(
                license=license_name,
                license_url=HttpUrl(license_url),
                author=hit.get("creator"),
                source=hit.get("source") or "Openverse",
                source_url=(
                    HttpUrl(hit["foreign_landing_url"])
                    if hit.get("foreign_landing_url")
                    else None
                ),
            ),
        )
    except Exception as e:
        log.error(f"{e.__class__.__name__}: {e}")
        if settings.debug:
            raise e
        return None
