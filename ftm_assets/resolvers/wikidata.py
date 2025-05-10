"""
Wikidata resolver. Takes a wikidata id (QID) and finds the most recent image

https://www.wikidata.org/w/api.php?action=wbgetclaims&property=P18&entity=Q7747
"""

from datetime import datetime

import httpx
from anystore.decorators import anycache
from anystore.types import SDict
from banal import ensure_list
from pydantic import HttpUrl
from rigour.ids.wikidata import is_qid

from ftm_assets.logging import get_logger
from ftm_assets.model import Attribution, Image
from ftm_assets.settings import Settings
from ftm_assets.store import get_cache

log = get_logger(__name__)
settings = Settings()

BASE_URL = (
    "https://www.wikidata.org/w/api.php?action=wbgetclaims"
    "&property=P18&entity={qid}&format=json"
)

IMAGE_URL = (
    "https://commons.wikimedia.org/w/index.php?title=Special:Redirect/file/{name}"
)


def resolve_image_url(name: str) -> str | None:
    res = httpx.head(IMAGE_URL.format(name=name), follow_redirects=True)
    if res.status_code == 404:
        log.error("Image redirect not found", name=name)
        return
    res.raise_for_status()
    return str(res.url)


def extract_date(claim: SDict) -> str:
    for date in sorted(
        [
            p["datavalue"]["value"]["time"]
            for p in ensure_list(claim.get("qualifiers", {}).get("P585"))
        ],
        reverse=True,
    ):
        return date
    return datetime(1970, 1, 1).isoformat()


@anycache(
    store=get_cache(), key_func=lambda x: f"resolve/wikidata/{x}", ttl=3600, model=Image
)
def resolve(id: str) -> Image | None:
    # FIXME use `nomenklatura.wikidata` client?
    if is_qid(id):
        url = BASE_URL.format(qid=id)
        res = httpx.get(url)
        res.raise_for_status()
        data = res.json()
        candidates: list[SDict] = []
        for claim in ensure_list(data.get("claims", {}).get("P18")):
            candidates.append(
                {
                    "name": claim["mainsnak"]["datavalue"]["value"],
                    "date": extract_date(claim),
                    "alt": [
                        p["datavalue"]["value"]
                        for p in ensure_list(claim.get("qualifiers", {}).get("P2096"))
                    ],
                }
            )
        for candidate in sorted(candidates, key=lambda x: x["date"], reverse=True):
            url = resolve_image_url(candidate["name"])
            if url is not None:
                return Image(
                    id=id,
                    name=candidate["name"],
                    url=HttpUrl(url),
                    alt=candidate["alt"],
                    attribution=Attribution(
                        license="CC BY 4.0",
                        license_url=HttpUrl(
                            "https://creativecommons.org/licenses/by/4.0/"
                        ),
                    ),
                )
