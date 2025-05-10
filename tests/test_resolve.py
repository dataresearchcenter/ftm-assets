from ftm_assets import logic
from ftm_assets.model import Image
from ftm_assets.store import get_storage


def test_logic_lookup():
    res = logic.lookup("Q567")
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
        },
    }


def test_logic_mirror():
    res = logic.lookup("Q567")
    logic.mirror(res)
    storage = get_storage()
    assert storage.exists(res.key)


def test_logic_thumbnail():
    res = logic.lookup("Q567")
    logic.generate_thumbnail(res)
    storage = get_storage()
    assert storage.exists(res.thumbnail_key)
