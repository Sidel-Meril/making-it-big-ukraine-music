#!/usr/bin/env python3
"""Export milestone flower chart data (wrapper around nuam-chart milestones)."""

from __future__ import annotations

import sys

from nuam_scraper.charts.cli import main

if __name__ == "__main__":
    main(["milestones", *sys.argv[1:]])
