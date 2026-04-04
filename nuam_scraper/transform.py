from __future__ import annotations

import io
import re
from pathlib import Path

import pandas as pd


def is_artist_data_row(artist_cell: object) -> bool:
    """Drop empty rows and the aggregate/summary row (numeric-only first column)."""
    s = str(artist_cell).strip()
    if not s:
        return False
    # NBSP used as thousands separator in published CSV
    if re.fullmatch(r"[\d\s\u00a0]+", s):
        return False
    return True


def artists_csv_to_dataframe(csv_text: str) -> pd.DataFrame:
    """Parse NUAM artist export: all columns as strings; drop summary rows."""
    df = pd.read_csv(io.StringIO(csv_text), dtype=str, keep_default_na=False)
    if df.empty:
        return df
    name_col = df.columns[0]
    mask = df[name_col].map(is_artist_data_row)
    return df.loc[mask].reset_index(drop=True)


def dataframe_to_parquet(df: pd.DataFrame, path: str | Path) -> None:
    df.to_parquet(path, index=False)
