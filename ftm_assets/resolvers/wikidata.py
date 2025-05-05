"""
Wikidata resolver. Takes a wikidata id (QID) and finds the most recent image

https://www.wikidata.org/w/api.php?action=wbgetclaims&property=P18&entity=Q7747
"""

import httpx
from anystore.types import SDict
from banal import ensure_list
from rigour.ids.wikidata import is_qid

from ftm_assets.model import Image

BASE_URL = (
    "https://www.wikidata.org/w/api.php?action=wbgetclaims"
    "&property=P18&entity={qid}&format=json"
)

IMAGE_URL = (
    "https://commons.wikimedia.org/w/index.php?title=Special:Redirect/file/{name}"
)


def resolve_image_url(name: str) -> str:
    res = httpx.head(IMAGE_URL.format(name=name), follow_redirects=True)
    res.raise_for_status()
    return str(res.url)


def resolve(id: str) -> Image | None:
    # FIXME use `nomenklatura.wikidata` client?
    if is_qid(id):
        url = BASE_URL.format(qid=id)
        res = httpx.get(url)
        res.raise_for_status()
        data = res.json()
        candidates: list[SDict] = []
        for claim in ensure_list(data["claims"].get("P18")):
            candidates.append(
                {
                    "name": claim["mainsnak"]["datavalue"]["value"],
                    "date": sorted(
                        [
                            p["datavalue"]["value"]["time"]
                            for p in claim["qualifiers"]["P585"]
                        ],
                        reverse=True,
                    )[0],
                    "alt": [
                        p["datavalue"]["value"]
                        for p in ensure_list(claim["qualifiers"].get("P2096"))
                    ],
                }
            )
        for candidate in sorted(candidates, key=lambda x: x["date"], reverse=True):
            url = resolve_image_url(candidate["name"])
            return Image(
                id=id,
                name=candidate["name"],
                url=url,
                alt=candidate["alt"],
                attribution={
                    "license": "CC BY 4.0",
                    "license_url": "https://creativecommons.org/licenses/by/4.0/",
                },
            )
