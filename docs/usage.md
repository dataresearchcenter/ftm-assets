# Usage

## Resolve images from Wikidata

Given a stream of FollowTheMoney entities or Wikidata QIDs, resolve their images:

```bash
cat entities.ftm.json | ftm-assets load-entities
```

```bash
echo "Q567" | ftm-assets load-ids
```

## Register images manually

Place an image (local or remote) for any entity ID:

```bash
ftm-assets register --id ENTITY1 --uri ./photo.jpg
ftm-assets register --id ENTITY1 --uri https://example.org/photo.jpg
ftm-assets register --id ENTITY1 --uri s3://bucket/photo.jpg --name custom.jpg
```

With metadata:

```bash
ftm-assets register --id ENTITY1 --uri ./photo.jpg --meta ./meta.json
```

## Mirror and thumbnails

Mirror resolved images to configured storage and generate thumbnails:

```bash
ftm-assets load-ids -i ids.txt -o results.json
ftm-assets mirror -i results.json
ftm-assets make-thumbnails -i results.json
```

## Run API server

```bash
uvicorn --port 8000 ftm_assets.api:app --workers 4
```

Get asset metadata:

```bash
curl http://localhost:8000/img/<entity_id>
```

With authentication (triggers mirroring/thumbnailing):

```bash
curl http://localhost:8000/img/<entity_id>?api_key=<your-key>
```
