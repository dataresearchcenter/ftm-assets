[![ftm-assets on pypi](https://img.shields.io/pypi/v/ftm-assets)](https://pypi.org/project/ftm-assets/)
[![Python test and package](https://github.com/dataresearchcenter/ftm-assets/actions/workflows/python.yml/badge.svg)](https://github.com/dataresearchcenter/ftm-assets/actions/workflows/python.yml)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Coverage Status](https://coveralls.io/repos/github/dataresearchcenter/ftm-assets/badge.svg?branch=main)](https://coveralls.io/github/dataresearchcenter/ftm-assets?branch=main)
[![AGPLv3+ License](https://img.shields.io/pypi/l/ftm-assets)](./LICENSE)

# ftm-assets

Resolve and build assets (currently images) for [FollowTheMoney](https://followthemoney.tech) entities.

`ftm-assets` finds an image for an entity via its [Wikidata](https://www.wikidata.org) id (with an [Openverse](https://openverse.org) search by entity name as fallback), mirrors it and generates a thumbnail into a store: a local directory, a S3 bucket, a [PutFS](https://putf.sh) server, ...

There is no api server. The store is meant to be served statically, clients find images by a simple path convention.

## Installation

```bash
pip install ftm-assets
```

Storage backends beyond the local filesystem need the matching [anystore](https://github.com/dataresearchcenter/anystore) extra, e.g. `pip install "anystore[s3]"`. The PutFS client (`putfs://`) is included.

## Build images

```bash
export FTM_ASSETS_STORE_URI=s3://my-bucket/img  # default: ./static

cat entities.ftm.json | ftm-assets load-entities
echo "Q567" | ftm-assets load-ids
```

Images that are already in the store are not resolved again.

## Serve statically

Layout of the store:

```
<entity_id>/meta.json          # metadata, written last
<entity_id>/<sha256>.<ext>     # mirrored original image, by its checksum
<entity_id>/thumbs/600.jpg     # thumbnail
```

Paths are relative to the store root (`FTM_ASSETS_STORE_URI`), which can be any prefix, e.g. `s3://my-bucket/img`.

`meta.json` is only written after the image and its thumbnail are stored, so its presence means the image is complete. A missing `meta.json` (404) means there is no image for this entity.

`url` and `thumbnail_url` are relative to the `meta.json`, so clients resolve them against wherever the store is served from:

```json
{
    "id": "Q567",
    "name": "Angela Merkel (51614156068).jpg",
    "sha256": "96c8c810c4dfc230f9606f6e585ad0149716ac9850bacbee603011515f5d9755",
    "url": "96c8c810c4dfc230f9606f6e585ad0149716ac9850bacbee603011515f5d9755.jpg",
    "thumbnail_url": "thumbs/600.jpg",
    "original_url": "https://upload.wikimedia.org/wikipedia/commons/0/01/Angela_Merkel_%2851614156068%29.jpg",
    "alt": [
        {
            "text": "Angela Merkel in 2021 at the EPP Summit in Brussels",
            "language": "en"
        }
    ],
    "attribution": {
        "license": "CC BY 4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "author": null,
        "source": "Wikimedia Commons",
        "source_url": "https://commons.wikimedia.org/wiki/File:Angela%20Merkel%20(51614156068).jpg"
    }
}
```

```js
const res = await fetch(`https://assets.example.org/img/${id}/meta.json`);
const image = await res.json();
const thumbnail = new URL(image.thumbnail_url, res.url);
```

## JavaScript

The npm package `@dataresearchcenter/ftm-assets` implements this lookup and provides a react component:

```tsx
import { EntityImage, getImage } from "@dataresearchcenter/ftm-assets";

<EntityImage entity={entity} root="https://assets.example.org/img" thumbnail />;

const image = await getImage("https://assets.example.org/img", "Q567");
```

## Run as an OpenAleph worker service

    pip install ftm-assets[openaleph]

To integrate `ftm-assets` into the [OpenAleph](https://openaleph.org) ecosystem as a worker that processes entities, start the worker queue like this:

    PROCRASTINATE_APP=ftm_assets.tasks.app procrastinate worker -q ftm-assets

To defer tasks from other places, use `ftm-assets` as queue name and `ftm_assets.tasks.resolve_image` as the task identifier.

## License and Copyright

`ftm-assets`, (C) 2025 [Data and Research Center – DARC](https://dataresearchcenter.org)

`ftm-assets` is licensed under the AGPLv3 or later license.

see [NOTICE](./NOTICE) and [LICENSE](./LICENSE)
