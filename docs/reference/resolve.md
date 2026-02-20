# Resolution flow

## Request flow

```mermaid
flowchart TD
    A["Client request\n(API / CLI / task queue)"] --> B["lookup(id)"]
    B --> C{"repository.get_image(id)\n— store-first —"}

    C -->|meta.json found| D["Deserialize full Image\n(attribution, alt text)"]
    C -->|image file found| E["Construct minimal Image\n(manually placed)"]
    C -->|nothing found| F["resolve(id)"]

    D --> DONE["Return Image"]
    E --> DONE

    F --> G["wikidata.resolve(id)\n— external HTTP call —"]
    G -->|"query P18 claims,\nsort by date,\nresolve Commons redirect"| H{Image found?}

    H -->|no| NONE["Return None\n(404)"]
    H -->|yes| I["repository.save_metadata()\n— persist for future lookups —"]

    I --> J{mirror configured?}
    J -->|yes| K["mirror(image)\ndownload & store binary"]
    J -->|no| L{thumbnails configured?}
    K --> L

    L -->|yes| M["generate_thumbnail(image)\ncreate JPEG thumbnail"]
    L -->|no| DONE
    M --> DONE
```

## Store as single source of truth

There is no separate cache layer. The store (`FTM_ASSETS_STORE_URI`) holds everything:

- `img/{id}/meta.json` — full `Image` model (attribution, alt text, URL)
- `img/{id}/{filename}` — mirrored image binary
- `img/{id}/thumbs/{size}.jpg` — generated thumbnail

On subsequent requests for the same ID, `lookup()` finds the metadata in the store
and returns immediately without calling Wikidata.

## Manual image placement

Images can be placed for any entity ID (not just Wikidata QIDs) via the `register` CLI command or by writing directly to the store. The `get_image()` function handles both cases:

1. **With metadata**: reads `meta.json` for full `Image` with attribution
2. **Without metadata**: scans for image files and constructs a minimal `Image`

## API reference

::: ftm_assets.logic
