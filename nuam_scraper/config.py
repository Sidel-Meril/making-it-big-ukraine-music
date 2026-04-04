from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Published sheet behind the GitHub-hosted iframe on https://www.nuam.club/base
DEFAULT_ARTISTS_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vQF8E3B7sRWEdfGxrRwQqtNvf4scBZexST0LGUbR7cXss53wcZw6UCZFHA9ChflUcDOJDTL1F1pJ3M8/"
    "pub?gid=0&single=true&output=csv"
)

DEFAULT_BASE_PAGE_URL = "https://www.nuam.club/base"
DEFAULT_GITHUB_APP_URL = "https://newuam.github.io/base/nuam-base.html"


class ScraperSettings(BaseSettings):
    """Polite defaults: identifiable UA, timeouts, small delay between I/O steps."""

    model_config = SettingsConfigDict(
        env_prefix="NUAM_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    user_agent: str = Field(
        default=(
            "NUAMScraper/1.0 (+https://www.nuam.club/base; research/archival; "
            "contact: local script)"
        ),
        description="Sent as User-Agent on every HTTP request.",
    )
    timeout_seconds: float = Field(default=120.0, ge=5.0)
    request_delay_seconds: float = Field(
        default=0.35,
        ge=0.0,
        description="Sleep after each successful HTTP response (reduces burst traffic).",
    )
    artists_csv_url: str | None = Field(
        default=None,
        description="Override CSV URL; when unset, discover or use built-in default.",
    )
    base_page_url: str = Field(default=DEFAULT_BASE_PAGE_URL)
    github_app_url: str = Field(default=DEFAULT_GITHUB_APP_URL)
    snapshot_html_path: str | None = Field(
        default=None,
        description="Optional saved Wix page HTML to extract CSV URLs from.",
    )
    retry_attempts: int = Field(default=5, ge=1, le=20)
    retry_min_wait: float = Field(default=1.0, ge=0.0)
    retry_max_wait: float = Field(default=30.0, ge=0.0)

    def httpx_timeout(self) -> float:
        return self.timeout_seconds
