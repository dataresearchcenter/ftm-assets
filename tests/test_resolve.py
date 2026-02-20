from ftm_assets import logic, repository
from ftm_assets.model import Image


def test_logic_lookup():
    res = logic.resolve("Q567")
    assert isinstance(res, Image)
    assert res.model_dump(mode="json") == {
        "id": "Q567",
        "name": "Angela Merkel (51614156068).jpg",
        "url": "https://upload.wikimedia.org/wikipedia/commons/0/01/Angela_Merkel_%2851614156068%29.jpg",
        "alt": [
            {
                "text": "Angela Merkel im Jahr 2021 bei der EPP Summit in Brüssel",
                "language": "de",
            },
            {
                "text": "Angela Merkel in 2021 at the EPP Summit in Brussels",
                "language": "en",
            },
        ],
        "attribution": {
            "license": "CC BY 4.0",
            "license_url": "https://creativecommons.org/licenses/by/4.0/",
            "author": None,
            "source": "Wikimedia Commons",
            "source_url": "https://commons.wikimedia.org/wiki/File:Angela%20Merkel%20(51614156068).jpg",
        },
    }


def test_logic_mirror():
    res = logic.lookup("Q567")
    logic.mirror(res)
    storage = repository.get_storage()
    key = repository.make_key(res.id, res.name)
    assert storage.exists(key)


def test_logic_thumbnail():
    res = logic.lookup("Q567")
    logic.generate_thumbnail(res)
    storage = repository.get_storage()
    key = repository.make_thumbnail_key(res.id)
    assert storage.exists(key)


def test_metadata_persisted():
    """After resolve() (called by earlier tests), meta.json exists in storage."""
    storage = repository.get_storage()
    meta_key = repository.make_meta_key("Q567")
    assert storage.exists(meta_key)
    loaded = repository.get_image("Q567")
    assert loaded is not None
    assert loaded.attribution is not None
    assert loaded.attribution.source == "Wikimedia Commons"


def test_store_first_lookup():
    """If image is in store, lookup should return it without Wikidata.

    Previous tests already resolved Q567 and saved metadata to store,
    so lookup should find it via repository.get_image() without Wikidata.
    """
    res = repository.get_image("Q567")
    assert res is not None
    assert res.id == "Q567"
    # Also verify lookup() returns it (store-first path)
    res2 = logic.lookup("Q567")
    assert res2 is not None
    assert res2.id == "Q567"


def test_manual_image():
    """Manually placed image (no meta.json) should be found by get_image."""
    storage = repository.get_storage()
    key = repository.make_key("MANUAL1", "photo.jpg")
    with storage.open(key, "wb") as f:
        f.write(b"fake image data")
    res = repository.get_image("MANUAL1")
    assert res is not None
    assert res.id == "MANUAL1"
    assert res.name == "photo.jpg"


def test_manual_image_with_metadata():
    """Manually placed image with meta.json should return full metadata."""
    storage = repository.get_storage()
    key = repository.make_key("MANUAL2", "photo.jpg")
    with storage.open(key, "wb") as f:
        f.write(b"fake image data")
    image = Image(
        id="MANUAL2",
        name="photo.jpg",
        url="https://example.org/photo.jpg",
    )
    repository.save_metadata(image)
    res = repository.get_image("MANUAL2")
    assert res is not None
    assert res.id == "MANUAL2"
    assert res.name == "photo.jpg"
    assert str(res.url) == "https://example.org/photo.jpg"
