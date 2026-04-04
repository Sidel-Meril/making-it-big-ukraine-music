"""Build long tables and artist frame from NUAM parquet (same logic as notebooks/eda.ipynb)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple

import numpy as np
import pandas as pd

ARTIST_BASE_COLUMNS = [
    "artist_name",
    "genre",
    "date_added",
    "instagram",
    "is_empty_flag",
    "ru_lang_flag",
    "last_year_release_flag",
    "more_than_one_release_flag",
    "invalid_description_flag",
    "is_description_present_flag",
    "city",
]

COLUMN_RENAME = {
    "Артист": "artist_name",
    "Жанр": "genre",
    "Дата додавання": "date_added",
    "Instagram": "instagram",
    "Empty": "is_empty_flag",
    "RuLang": "ru_lang_flag",
    "YearRel": "last_year_release_flag",
    "MultiRel": "more_than_one_release_flag",
    "ОписCheck": "invalid_description_flag",
    "Опис": "is_description_present_flag",
    "City": "city",
}


def _process_flag(series: pd.Series, *, default: bool = True) -> pd.Series:
    return series.replace({"+": 1, "-": 0, "": np.nan}).fillna(default).astype(bool)


def debut_year_from_column(col: str) -> int:
    m = re.search(r"(\d{2})$", str(col))
    if m:
        return 2000 + int(m.group(1))
    return int(str(col)[-2]) + 2000


class NuamFrames(NamedTuple):
    raw_df: pd.DataFrame
    artists_df: pd.DataFrame
    listeners_df: pd.DataFrame
    debut_df: pd.DataFrame
    labels_df: pd.DataFrame


def load_nuam_parquet(path: str | Path) -> NuamFrames:
    path = Path(path)
    df = pd.read_parquet(path)
    df.replace("", np.nan, inplace=True)

    df.rename(columns=COLUMN_RENAME | {"Debut": "Debut26"}, inplace=True)

    for col, default in [
        ("is_empty_flag", False),
        ("ru_lang_flag", False),
        ("last_year_release_flag", False),
        ("more_than_one_release_flag", False),
        ("invalid_description_flag", True),
        ("is_description_present_flag", False),
    ]:
        df[col] = _process_flag(df[col], default=default)

    df["artist_id"] = df.index

    url_cols = [c for c in df.columns if str(c).startswith("URL")]
    df["url"] = df[url_cols].bfill(axis=1).iloc[:, 0]
    df["spotify"] = df[url_cols].apply(
        lambda row: next((v for v in row if isinstance(v, str) and "spotify" in v.lower()), np.nan),
        axis=1,
    )

    cyrylic_listeners_wide_cols = [c for c in df.columns if str(c).startswith("Слухачів")]
    listeners_long_fmt: list[pd.DataFrame] = []
    for col in cyrylic_listeners_wide_cols:
        mask = df[col].notna()
        month_datetime = pd.to_datetime(str(col).split(" ")[-1], format="%m.%y")
        listeners_long_fmt.append(
            pd.DataFrame(
                {
                    "artist_id": df.loc[mask, "artist_id"],
                    "artist_name": df.loc[mask, "artist_name"],
                    "listeners": pd.to_numeric(df.loc[mask, col], errors="coerce"),
                    "month": month_datetime,
                }
            )
        )
    listeners_df = pd.concat(listeners_long_fmt, ignore_index=True).sort_values(["artist_id", "month"])

    debut_wide_cols = [c for c in df.columns if str(c).startswith("Debut")]
    debut_long_fmt: list[pd.DataFrame] = []
    for col in debut_wide_cols:
        mask = df[col].notna()
        year = debut_year_from_column(col)
        flagged = _process_flag(df.loc[mask, col], default=False)
        debut_long_fmt.append(
            pd.DataFrame(
                {
                    "artist_id": df.loc[mask, "artist_id"],
                    "artist_name": df.loc[mask, "artist_name"],
                    "is_debuted": flagged,
                    "year": year,
                }
            )
        )
    debut_df = pd.concat(debut_long_fmt, ignore_index=True).sort_values(["artist_id", "year"])

    label_wide_cols = [c for c in df.columns if str(c).startswith("Label")]
    labels_long_fmt: list[pd.DataFrame] = []
    for col in label_wide_cols:
        mask = df[col].notna()
        labels_long_fmt.append(
            pd.DataFrame(
                {
                    "artist_id": df.loc[mask, "artist_id"],
                    "artist_name": df.loc[mask, "artist_name"],
                    "label": df.loc[mask, col],
                }
            )
        )
    labels_df = pd.concat(labels_long_fmt, ignore_index=True).sort_values(["artist_id"])

    df["has_label_flag"] = df[label_wide_cols].notna().any(axis=1)
    df["has_debut_in_last_three_years_flag"] = df[debut_wide_cols].iloc[:, -3:].any(axis=1)

    artists_df = df[ARTIST_BASE_COLUMNS + ["url", "spotify", "artist_id"]].copy()

    return NuamFrames(
        raw_df=df,
        artists_df=artists_df,
        listeners_df=listeners_df,
        debut_df=debut_df,
        labels_df=labels_df,
    )
