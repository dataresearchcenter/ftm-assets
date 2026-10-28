# Usage

## Configuration

Settings are read from environment variables (see [settings reference](reference/settings.md)):

| Variable | Default | Description |
| --- | --- | --- |
| `FTM_ASSETS_STORE_URI` | `static` | Store for the built images (local path or remote uri) |
| `FTM_ASSETS_THUMBNAIL_SIZE` | `600` | Thumbnail size in pixels (square bounding box) |
| `FTM_ASSETS_OPENVERSE_API_KEY` | | Optional Openverse api key for higher rate limits |
| `DEBUG` | `0` | Raise errors instead of logging them |

The store can be any [anystore](https://github.com/dataresearchcenter/anystore) uri. Backends beyond the local filesystem need the matching anystore extra, e.g. `pip install "anystore[s3]"`:

```bash
# local directory
export FTM_ASSETS_STORE_URI=./static

# S3 (or S3 compatible via FSSPEC_S3_ENDPOINT_URL), credentials via AWS_* env vars
export FTM_ASSETS_STORE_URI=s3://my-bucket

# PutFS server
export FTM_ASSETS_STORE_URI=putfs://assets.example.org
```

## Resolve and build images

Given a stream of FollowTheMoney entities or Wikidata QIDs, resolve and build their images:

```bash
cat entities.ftm.json | ftm-assets load-entities
```

```bash
echo "Q567" | ftm-assets load-ids
```

For each entity or id:

1. If its `meta.json` is already in the store, it is returned as is. Nothing is resolved or downloaded again.
2. Otherwise, the most recent image (P18) is looked up on Wikidata. For entities (`load-entities`) without a Wikidata image, Openverse is searched for CC-licensed images by the entity name.
3. The original image is mirrored into the store and the thumbnail is generated from it.
4. `meta.json` is written.

`load-entities` uses the entity id if it is a Wikidata QID, otherwise the first QID among the entity's identifier properties (e.g. `wikidataId`). Entities without a QID are skipped.

Both commands write the image metadata as JSON lines to stdout (or `-o`). If any step fails, no `meta.json` is written and the image is resolved again on the next run.

Changing `FTM_ASSETS_THUMBNAIL_SIZE` only affects images built afterwards. The actual path is recorded as `thumbnail_url` in `meta.json`, so clients don't need to know the size.

## Serve statically

The store can be served as is. Layout:

```
img/<entity_id>/meta.json          # metadata, written last
img/<entity_id>/<sha256>.<ext>     # mirrored original image, by its checksum
img/<entity_id>/thumbs/600.jpg     # thumbnail
```

Clients fetch `img/<entity_id>/meta.json`. A 404 means there is no image for this entity.

### `meta.json`

| Field | Description |
| --- | --- |
| `id` | Entity id |
| `name` | Filename of the original image at its source |
| `sha256` | Checksum of the original image, its key in the store |
| `url` | Mirrored original image, relative to `meta.json` |
| `thumbnail_url` | Thumbnail, relative to `meta.json`. Vector images (svg) are their own thumbnail |
| `original_url` | Source of the original image, if known |
| `alt` | List of alt texts (`text`, `language`) |
| `attribution` | `license`, `license_url`, `author`, `source`, `source_url` |

Resolve the relative urls against the url `meta.json` was fetched from:

```js
const res = await fetch(`${root}/img/${id}/meta.json`);
if (res.ok) {
  const image = await res.json();
  const src = new URL(image.thumbnail_url, res.url).toString();
}
```

### Notes

- Try it locally with `python -m http.server --directory ./static`.
- When `meta.json` is fetched by a browser from another origin, the server needs to send CORS headers (`Access-Control-Allow-Origin`) for `GET` requests.
- On S3, files are uploaded without an explicit `Content-Type`. Browsers still display raster images and `fetch().json()` doesn't care, but svg images are only displayed with `Content-Type: image/svg+xml`, so configure the bucket or CDN for proper content types.

## JavaScript

The npm package `@dataresearchcenter/ftm-assets` fetches `meta.json` and resolves its urls:

```tsx
import { EntityImage, getImage } from "@dataresearchcenter/ftm-assets";

// react component for an entity with a `wikidataId` property, renders nothing
// if there is no image
<EntityImage entity={entity} root="https://assets.example.org" thumbnail />;

// metadata only, with absolute `url` and `thumbnail_url`
const image = await getImage("https://assets.example.org", "Q567");
```

## Python

```python
from ftm_assets.logic import lookup

image = lookup("Q567")  # from the store, or resolved and built
```
