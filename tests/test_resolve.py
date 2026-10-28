import re
from contextlib import suppress

from followthemoney import model

from ftm_assets import logic, repository
from ftm_assets.model import Image


def test_logic_lookup():
    res = logic.resolve("Q567")
    assert isinstance(res, Image)
    data = res.model_dump(mode="json")
    # original is stored by its sha256 checksum
    sha256 = data.pop("sha256")
    assert re.fullmatch(r"[0-9a-f]{64}", sha256)
    assert data.pop("url") == f"{sha256}.jpg"
    assert data == {
        "id": "Q567",
        "name": "Angela Merkel (51614156068).jpg",
        "thumbnail_url": "thumbs/600.jpg",
        "original_url": "https://upload.wikimedia.org/wikipedia/commons/0/01/Angela_Merkel_%2851614156068%29.jpg",
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
    key = logic.mirror(res)
    storage = repository.get_storage()
    assert storage.exists(key)
    assert res.sha256 == storage.checksum(key)
    assert key == repository.make_key(res.id, res.sha256, res.name)
    assert res.url == repository.make_relative_url(res.id, key)


def test_logic_thumbnail():
    res = logic.lookup("Q567")
    key = logic.generate_thumbnail(res, logic.mirror(res))
    storage = repository.get_storage()
    assert key == repository.make_thumbnail_key(res.id)
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


def test_image_without_metadata():
    """Image files without meta.json are not visible to clients."""
    key = repository.make_key("MANUAL1", "abc", "photo.jpg")
    repository.save_data(key, b"fake image data")
    assert repository.get_image("MANUAL1") is None


def test_manual_image_with_metadata():
    """Manually placed image with meta.json should return full metadata."""
    key = repository.make_key("MANUAL2", "abc", "photo.jpg")
    repository.save_data(key, b"fake image data")
    image = Image(
        id="MANUAL2",
        name="photo.jpg",
        original_url="https://example.org/photo.jpg",
    )
    repository.save_metadata(image)
    res = repository.get_image("MANUAL2")
    assert res is not None
    assert res.id == "MANUAL2"
    assert res.name == "photo.jpg"
    assert str(res.original_url) == "https://example.org/photo.jpg"


def test_build_incomplete(monkeypatch):
    """meta.json is only written if mirroring and thumbnail generation succeed."""
    # no source url and nothing stored
    image = Image(id="INCOMPLETE1", name="photo.jpg")
    with suppress(Exception):  # raises in debug mode
        assert logic.build(image) is None
    assert repository.get_image("INCOMPLETE1") is None

    # original is not an image
    monkeypatch.setattr(logic, "download_image", lambda url: b"foo")
    image = Image(
        id="INCOMPLETE2", name="photo.jpg", original_url="https://example.org/a.jpg"
    )
    with suppress(Exception):
        assert logic.build(image) is None
    assert repository.get_image("INCOMPLETE2") is None


def test_lookup_proxy_openverse_fallback(monkeypatch):
    """Openverse is searched by entity name if Wikidata has no image."""
    calls = []
    monkeypatch.setattr(logic.wikidata, "resolve", lambda id: None)
    monkeypatch.setattr(
        logic.openverse, "resolve", lambda id, name: calls.append((id, name))
    )
    proxy = model.get_proxy(
        {"id": "Q99999999", "schema": "Person", "properties": {"name": ["Jane Doe"]}}
    )
    assert logic.lookup_proxy(proxy) is None
    assert calls == [("Q99999999", "Jane Doe")]

    # no name, no Openverse search
    calls.clear()
    assert logic.lookup("Q99999999") is None
    assert calls == []
