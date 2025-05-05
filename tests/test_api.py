from fastapi.testclient import TestClient
from typer.testing import CliRunner

from ftm_assets.api import app
from ftm_assets.model import Image

runner = CliRunner()


def test_api():
    client = TestClient(app)

    res = client.get("/img/Q567")
    assert res.status_code == 200
    assert Image(**res.json())

    res = client.get("/r/img/Q567", follow_redirects=False)
    assert res.status_code == 307
    assert (
        res.headers["location"]
        == "https://static.example.org/img/Q567/Angela%20Merkel%20(51614156068).jpg"
    )

    res = client.get("/r/img/Q567/thumb", follow_redirects=False)
    assert res.status_code == 307
    assert (
        res.headers["location"] == "https://static.example.org/img/Q567/thumbs/600.jpg"
    )
