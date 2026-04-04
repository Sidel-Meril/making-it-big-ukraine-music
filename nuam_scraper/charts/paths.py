"""Repository paths for chart outputs."""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    """Project root (directory containing pyproject.toml)."""
    return Path(__file__).resolve().parents[2]


def charts_root() -> Path:
    """Root directory for all exported chart assets (HTML + generated JS/JSON)."""
    return repo_root() / "data" / "charts"
