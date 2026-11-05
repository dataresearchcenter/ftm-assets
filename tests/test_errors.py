import httpx
import pytest
from anystore import decorators
from typer.testing import CliRunner

from ftm_assets import logic
from ftm_assets.cli import cli
from ftm_assets.model import Image
from ftm_assets.resolvers import (
    MAX_DELAY,
    MAX_RETRIES,
    RetryError,
    openverse,
    request,
    wikidata,
)
from ftm_assets.tasks import resolve_image

URL = "https://example.org/"


@pytest.fixture
def sleeps(monkeypatch):
    res = []
    monkeypatch.setattr("time.sleep", res.append)
    return res


@pytest.fixture
def no_debug(monkeypatch):
    """Tests run with `DEBUG=1`, `error_handler` only swallows errors without"""
    handler = decorators._error_handler

    def _handler(func, logger, retries, factor, jitter, do_raise, *args, **kwargs):
        return handler(func, logger, retries, factor, jitter, False, *args, **kwargs)

    monkeypatch.setattr(decorators, "_error_handler", _handler)


@pytest.fixture
def fallbacks(monkeypatch):
    res = []
    monkeypatch.setattr(openverse, "resolve", lambda *args: res.append(args))
    return res


def mock_responses(monkeypatch, *responses):
    """Answer requests with `responses` in order, repeating the last one"""
    calls = []

    def _request(method, url, **kwargs):
        calls.append(url)
        res = responses[min(len(calls), len(responses)) - 1]
        if isinstance(res, Exception):
            raise res
        res.request = httpx.Request(method, url)
        return res

    monkeypatch.setattr("httpx.request", _request)
    return calls


def run_task(id):
    entity = {"id": id, "schema": "Person", "properties": {"name": ["Jane Doe"]}}
    resolve_image(
        queue="ftm-assets",
        task="ftm_assets.tasks.resolve_image",
        dataset="test",
        payload={"entities": [entity]},
    )


@pytest.mark.parametrize("status", [200, 404, 500])
def test_request_no_retry(monkeypatch, sleeps, status):
    calls = mock_responses(monkeypatch, httpx.Response(status))
    assert request("GET", URL).status_code == status
    assert len(calls) == 1
    assert sleeps == []


def test_request_retry_after(monkeypatch, sleeps):
    responses = httpx.Response(429, headers={"Retry-After": "7"}), httpx.Response(200)
    calls = mock_responses(monkeypatch, *responses)
    assert request("GET", URL).status_code == 200
    assert len(calls) == 2
    assert sleeps == [7]


def test_request_backoff(monkeypatch, sleeps):
    # http dates are not parsed, they get the regular backoff
    date = {"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"}
    responses = (
        httpx.Response(503),
        httpx.Response(429, headers=date),
        httpx.Response(200),
    )
    calls = mock_responses(monkeypatch, *responses)
    assert request("GET", URL).status_code == 200
    assert len(calls) == 3
    assert 1 <= sleeps[0] < 2
    assert 2 <= sleeps[1] < 3


def test_request_gives_up(monkeypatch, sleeps):
    calls = mock_responses(monkeypatch, httpx.Response(429))
    with pytest.raises(RetryError) as e:
        request("GET", URL)
    assert e.value.response.status_code == 429
    assert len(calls) == MAX_RETRIES + 1
    assert len(sleeps) == MAX_RETRIES


def test_request_gives_up_on_long_retry_after(monkeypatch, sleeps):
    headers = {"Retry-After": str(MAX_DELAY + 1)}
    calls = mock_responses(monkeypatch, httpx.Response(429, headers=headers))
    with pytest.raises(RetryError):
        request("GET", URL)
    assert len(calls) == 1
    assert sleeps == []


def test_download_image_retries(monkeypatch, sleeps):
    responses = httpx.Response(429), httpx.Response(200, content=b"image")
    mock_responses(monkeypatch, *responses)
    assert logic.download_image(URL) == b"image"
    assert len(sleeps) == 1


@pytest.mark.parametrize(
    "response,error",
    [
        (httpx.Response(429), RetryError),
        (httpx.Response(503), RetryError),
        (httpx.Response(500), httpx.HTTPStatusError),
        (httpx.Response(502), httpx.HTTPStatusError),
        (httpx.Response(403), httpx.HTTPStatusError),
        (httpx.Response(200, text="<html>"), ValueError),
        (httpx.ConnectError("down"), httpx.ConnectError),
        (httpx.ReadTimeout("slow"), httpx.ReadTimeout),
    ],
)
def test_wikidata_failure_skips_openverse(
    monkeypatch, sleeps, no_debug, fallbacks, response, error
):
    mock_responses(monkeypatch, response)
    with pytest.raises(error):
        logic.resolve("Q567", "Angela Merkel")
    assert fallbacks == []


def test_commons_failure_skips_openverse(monkeypatch, sleeps, no_debug, fallbacks):
    claim = {"mainsnak": {"datavalue": {"value": "Image.jpg"}}}
    claims = httpx.Response(200, json={"claims": {"P18": [claim]}})
    mock_responses(monkeypatch, claims, httpx.Response(500))
    with pytest.raises(httpx.HTTPStatusError):
        logic.resolve("Q567", "Angela Merkel")
    assert fallbacks == []


@pytest.mark.parametrize(
    "data", [{}, {"claims": {}}, {"error": {"code": "param-invalid"}}]
)
def test_wikidata_no_image_falls_back_to_openverse(monkeypatch, fallbacks, data):
    mock_responses(monkeypatch, httpx.Response(200, json=data))
    assert logic.resolve("Q567", "Angela Merkel") is None
    assert fallbacks == [("Q567", "Angela Merkel")]


def test_wikidata_unknown_qualifiers(monkeypatch):
    unknown = {"snaktype": "somevalue"}
    claim = {
        "mainsnak": {"datavalue": {"value": "Image.jpg"}},
        "qualifiers": {"P585": [unknown], "P2096": [unknown]},
    }
    claims = httpx.Response(200, json={"claims": {"P18": [claim]}})
    mock_responses(monkeypatch, claims, httpx.Response(200))
    image = wikidata.resolve("Q567")
    assert image is not None
    assert image.name == "Image.jpg"
    assert image.alt == []


def test_task_raises_on_wikidata_failure(monkeypatch, sleeps, no_debug, fallbacks):
    mock_responses(monkeypatch, httpx.Response(500))
    with pytest.raises(httpx.HTTPStatusError):
        run_task("Q99999991")
    assert fallbacks == []


def test_task_raises_on_openverse_failure(monkeypatch, sleeps, no_debug):
    monkeypatch.setattr(wikidata, "resolve", lambda id: None)
    mock_responses(monkeypatch, httpx.Response(429))
    with pytest.raises(RetryError):
        run_task("Q99999992")


def test_task_raises_on_failed_download(monkeypatch, sleeps, no_debug):
    image = Image(id="Q99999993", name="a.jpg", original_url=URL)
    monkeypatch.setattr(wikidata, "resolve", lambda id: image)
    mock_responses(monkeypatch, httpx.ConnectError("down"))
    with pytest.raises(httpx.ConnectError):
        run_task("Q99999993")


def test_cli_continues_on_error(monkeypatch, sleeps, no_debug, tmp_path):
    def _resolve(id, name=None):
        calls.append(id)
        raise httpx.ConnectError("down")

    calls = []
    monkeypatch.setattr(logic, "resolve", _resolve)
    ids = tmp_path / "ids.txt"
    ids.write_text("Q99999994\nQ99999995\n")
    res = CliRunner().invoke(cli, ["load-ids", "-i", str(ids)])
    assert res.exit_code == 0
    assert calls == ["Q99999994", "Q99999995"]
