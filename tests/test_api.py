from fastapi.testclient import TestClient
from typer.testing import CliRunner

from ftm_assets.api import app
from ftm_assets.model import ApiImageResponse

runner = CliRunner()


def test_api():
    client = TestClient(app)

    res = client.get("/img/Q567")
    assert res.status_code == 200
    data = res.json()
    assert ApiImageResponse(**data)
    assert data == {
        "id": "Q567",
        "name": "Angela Merkel (51614156068).jpg",
        "url": "https://static.example.org/img/Q567/Angela%20Merkel%20(51614156068).jpg",
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
        "original_url": "https://upload.wikimedia.org/wikipedia/commons/0/01/Angela_Merkel_%2851614156068%29.jpg",
        "thumbnail_url": "https://static.example.org/img/Q567/thumbs/600.jpg",
    }

    res = client.get("/img/Q567?api_key=secret")
    assert res.status_code == 200


def test_api_manual_image():
    """Manually registered image should be returned by the API."""
    from ftm_assets import repository
    from ftm_assets.model import Image

    storage = repository.get_storage()
    key = repository.make_key("API_TEST1", "photo.jpg")
    with storage.open(key, "wb") as f:
        f.write(b"fake image data")
    image = Image(
        id="API_TEST1",
        name="photo.jpg",
        url="https://example.org/photo.jpg",
    )
    repository.save_metadata(image)

    client = TestClient(app)
    res = client.get("/img/API_TEST1")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "API_TEST1"
    assert data["name"] == "photo.jpg"
