import random
import time
from typing import Any

import httpx
from anystore.logging import get_logger

log = get_logger(__name__)

USER_AGENT = "ftm-assets/0.0.4 (https://github.com/dataresearchcenter/ftm-assets)"

HEADERS = {"User-Agent": USER_AGENT}

RETRY_STATUS = (429, 503)
MAX_RETRIES = 5
MAX_DELAY = 60


class RetryError(httpx.HTTPStatusError):
    """The server still rate limits or is unavailable after all retries"""


def get_delay(res: httpx.Response, attempt: int) -> float:
    """Seconds to wait before the next attempt: `Retry-After` if the server sent
    it as seconds, otherwise an exponential backoff with jitter"""
    retry_after = res.headers.get("Retry-After", "")
    if retry_after.isdecimal():
        return float(retry_after)
    return 2.0**attempt + random.random()


def request(method: str, url: str, **kwargs: Any) -> httpx.Response:
    """Like `httpx.request`, but waits and retries if the server rate limits or
    is unavailable. Raises a `RetryError` after `MAX_RETRIES`, or if the server
    asks to wait longer than `MAX_DELAY` seconds."""
    for attempt in range(MAX_RETRIES + 1):
        res = httpx.request(method, url, **kwargs)
        if res.status_code not in RETRY_STATUS:
            return res
        delay = get_delay(res, attempt)
        if attempt == MAX_RETRIES or delay > MAX_DELAY:
            break
        log.warning("Retrying request.", url=url, status=res.status_code, delay=delay)
        time.sleep(delay)
    raise RetryError(
        f"Giving up on `{url}` after status {res.status_code}",
        request=res.request,
        response=res,
    )
