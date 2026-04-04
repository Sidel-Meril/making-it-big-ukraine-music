from __future__ import annotations

import time
from collections.abc import Callable

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from .config import ScraperSettings


def build_client(settings: ScraperSettings) -> httpx.Client:
    return httpx.Client(
        headers={
            "User-Agent": settings.user_agent,
            "Accept": "text/csv,text/plain,text/html,*/*;q=0.8",
            "Accept-Language": "uk-UA,uk;q=0.9,en;q=0.8",
        },
        timeout=settings.httpx_timeout(),
        follow_redirects=True,
    )


def _retryable(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        c = exc.response.status_code
        return c == 429 or c >= 500
    return False


def fetch_text(client: httpx.Client, url: str, settings: ScraperSettings) -> str:
    @retry(
        stop=stop_after_attempt(settings.retry_attempts),
        wait=wait_exponential(
            multiplier=1,
            min=settings.retry_min_wait,
            max=settings.retry_max_wait,
        ),
        retry=retry_if_exception(_retryable),
        reraise=True,
    )
    def _get() -> str:
        r = client.get(url)
        r.raise_for_status()
        return r.text

    text = _get()
    if settings.request_delay_seconds:
        time.sleep(settings.request_delay_seconds)
    return text


def make_fetcher(client: httpx.Client, settings: ScraperSettings) -> Callable[[str], str]:
    return lambda url: fetch_text(client, url, settings)
