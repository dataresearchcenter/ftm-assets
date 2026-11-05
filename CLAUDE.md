# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ftm-assets resolves and builds assets (images) for [FollowTheMoney](https://followthemoney.tech) entities. Given a Wikidata QID, it fetches image metadata from Wikidata/Wikimedia Commons (with an Openverse search by entity name as fallback), mirrors the image into a store and generates a thumbnail. It exposes a Typer CLI and can run as an OpenAleph worker via procrastinate task queue.

There is no API: the store is meant to be served statically (bucket, PutFS/nginx, ...). Clients fetch `{id}/meta.json` (relative to the url the store is served from) and resolve the relative urls in it.

## Design Constraints

- **Keep the package slim.** It only holds the logic to build assets — no server, no knowledge of where the store is served from (no CDN prefix or similar settings).
- **Store layout is stable**, a production bucket (~350k images) uses it: `{id}/meta.json`, `{id}/{sha256}{ext}` (mirrored original, by its checksum), `{id}/thumbs/{size}.jpg` (none for svg, they are their own thumbnail). Keys are relative to the store root, which can be any prefix (the production bucket lives under `img/`, so its `FTM_ASSETS_STORE_URI` ends in `/img`). Don't change these paths.
- **`meta.json` is written last** (`logic.build()`), so its presence means the image is complete. If mirroring or thumbnailing fails, no `meta.json` is written.
- **Urls in `meta.json`**: `url` and `thumbnail_url` are relative to `meta.json`, `original_url` is the absolute source url.

## Environment

Use the virtualenv at `.venv`. Run Python/poetry commands via `.venv/bin/python`, `.venv/bin/pytest`, etc. or activate with `source .venv/bin/activate`.

If the package itself isn't installed in `.venv` (`ModuleNotFoundError: No module named 'ftm_assets'`), run `make install` or use `.venv/bin/python -m pytest`, which puts the repo root on `sys.path`.

## Commands

```bash
# Install (poetry required)
make install

# Run tests
make test

# Run a single test
.venv/bin/pytest tests/test_resolve.py -v
.venv/bin/pytest tests/test_resolve.py::test_name -v

# Lint
make lint

# Type check
make typecheck

# Pre-commit hooks
make pre-commit

# Build package
make build

# Docs (zensical, reads mkdocs.yml)
make docs

# Type check the JS package
npx tsc --noEmit
```

## Architecture

**Core flow:** `lookup(id, name)` → store-first via `repository.get_image()` (`meta.json`) → else `resolvers/wikidata.py` (Wikidata P18 lookup) → fallback `resolvers/openverse.py` (CC-licensed image search by entity name, only if a name is known, i.e. via `lookup_proxy()`) → `Image` model → `build()` in `logic.py`: `mirror()` (download original, store by its sha256 checksum) → `generate_thumbnail()` (from the mirrored original) → set relative urls, write `meta.json` → stored via `anystore`

Key modules in `ftm_assets/`:

- **`settings.py`** — Pydantic settings configured via `FTM_ASSETS_*` env vars (`FTM_ASSETS_STORE_URI`, `FTM_ASSETS_THUMBNAIL_SIZE`, `FTM_ASSETS_OPENVERSE_API_KEY`)
- **`model.py`** — Pure Pydantic models: `Image` (= `meta.json`), `Attribution`, `AltText`. No storage or settings dependencies
- **`repository.py`** — Store layout and CRUD: key construction, `make_relative_url()`, `get_image()`, `save_metadata()`, `get_data()`, `save_data()`. Single source of truth (no separate cache layer)
- **`logic.py`** — Business orchestration: `lookup()`, `resolve()`, `build()`, `mirror()`, `generate_thumbnail()`, `lookup_proxy()`. Store-first resolution with resolver chain fallback. Everything raises on failure, `None` only means no image, so only a successful Wikidata answer without an image falls back to Openverse
- **`resolvers/__init__.py`** — Shared `USER_AGENT`, `HEADERS` and `request()` used by all resolvers and `logic.py`. `request()` retries 429/503 with backoff (honours `Retry-After`) and raises `RetryError` when it gives up
- **`resolvers/wikidata.py`** — Resolves a QID to an `Image` by querying Wikidata P18 claims and Wikimedia Commons redirects
- **`resolvers/openverse.py`** — Fallback resolver: searches Openverse API for CC-licensed images by entity name. Optional Bearer token auth via `FTM_ASSETS_OPENVERSE_API_KEY`
- **`cli.py`** — Typer CLI (`ftm-assets`): `load-entities`, `load-ids`. Streams JSON lines via stdin/stdout. Wraps lookups in anystore's `error_handler` (raises in `DEBUG` mode, otherwise logs and continues with the next image)
- **`tasks.py`** — OpenAleph/procrastinate task queue integration (optional `[openaleph]` extra). Errors are not handled here, they fail the job

**`js/`** — `getImage(root, id)` and React component (`EntityImage`) that fetch `meta.json` from the statically served store and resolve its relative urls against the `meta.json` url. Built with TypeScript.

**`contrib/`** — One-off maintenance scripts for the production bucket: `migrate_metadata.py` (legacy store of the api version → current layout, runs on the local disk of the store), `backfill_metadata.py` (`meta.json` for images without one).

## Key Dependencies

- **anystore** — Abstracted storage layer. Backends beyond the local filesystem need the matching anystore extra (e.g. `anystore[s3]`). Also use its logging (`anystore.logging`), io helpers and progress bars (`anystore.io.SyncProgressBar`) instead of own implementations
- **putfs[client]** — fsspec filesystem for `putfs://` stores
- **ftmq** — FollowTheMoney query/streaming utilities
- **Pillow** — Thumbnail generation
- **httpx** — HTTP client for Wikidata/Commons/Openverse
- **rigour** — QID validation (`is_qid`)

## Test Environment

The test store uses `.test-store` directory (cleaned up by `make test`). Test fixtures are in `tests/fixtures/`. No Redis required. Tests make live requests to Wikidata, Wikimedia Commons and Openverse, and run with `DEBUG=1` (errors raise instead of being swallowed by `@error_handler`).

## Documentation

`README.md` and `docs/index.md` are identical copies, keep them in sync. `docs/reference/` is partly generated by mkdocstrings from docstrings. Zensical doesn't run mkdocs-typer2, so `docs/reference/cli.md` is a static write-up of `typer ftm_assets.cli utils docs`, update it when the CLI changes.

## Code Style

- Formatter: black (max line length 88)
- Import sorting: isort
- Linting: flake8 (see `setup.cfg` for config, extends ignore E203/E501/W503)
- Type checking: mypy --strict
