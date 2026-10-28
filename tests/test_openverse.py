from ftm_assets.model import Image
from ftm_assets.resolvers import openverse


def test_openverse_resolve():
    res = openverse.resolve("Q567", "Angela Merkel")
    assert isinstance(res, Image)
    assert res.id == "Q567"
    assert "/" not in res.name
    assert res.original_url is not None
    assert res.attribution is not None
    assert res.attribution.license is not None


def test_openverse_resolve_no_results():
    res = openverse.resolve("Q0", "xyzzy_nonexistent_entity_12345")
    assert res is None
