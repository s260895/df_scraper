"""Robust loader for ``data/all_users.csv``.

The raw CSV stores ``markets``, ``ships_from`` and ``products`` as *stringified*
Python lists (e.g. ``"['darkfox', 'asap']"``).  This module parses those safely,
normalizes the market / product / country names, and returns a tidy dataframe
plus a couple of convenience helpers used by the network module and dashboard.

Defensive/academic use only: reads committed data, no network access.
"""

from __future__ import annotations

import ast
import os
from functools import lru_cache

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_THIS_DIR)
DATA_DIR = os.path.join(_REPO_ROOT, "data")
ALL_USERS_CSV = os.path.join(DATA_DIR, "all_users.csv")

LIST_COLUMNS = ("markets", "ships_from", "products")


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def parse_list(value) -> list:
    """Parse a stringified python list into an actual list of strings.

    Falls back gracefully for malformed / missing values:
      * real lists pass through (elements stringified & stripped)
      * ``ast.literal_eval`` is tried first (safe: no code execution)
      * on failure, a naive comma-split of the de-bracketed string is used
      * NaN / None / empty -> ``[]``
    """
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v).strip() for v in value if str(v).strip()]
    # pandas NaN is a float
    if isinstance(value, float):
        return []
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "[]"}:
        return []
    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, (list, tuple, set)):
            return [str(v).strip() for v in parsed if str(v).strip()]
        # a bare scalar such as "darkfox"
        return [str(parsed).strip()]
    except (ValueError, SyntaxError):
        # fallback: strip brackets/quotes and split on commas
        cleaned = text.strip("[](){}")
        parts = [p.strip().strip("'\"") for p in cleaned.split(",")]
        return [p for p in parts if p]


def normalize_market(name: str) -> str:
    """Canonicalize a market name (lower-case, collapsed whitespace)."""
    return " ".join(str(name).strip().lower().split())


def normalize_country(name: str) -> str:
    """Canonicalize a ship-from country label (title-cased, trimmed)."""
    text = " ".join(str(name).strip().split())
    if not text:
        return ""
    lowered = text.lower()
    _aliases = {
        "usa": "United States",
        "us": "United States",
        "u.s.a.": "United States",
        "uk": "United Kingdom",
        "u.k.": "United Kingdom",
        "not specified": "Not Specified",
        "worldwide": "Worldwide",
    }
    if lowered in _aliases:
        return _aliases[lowered]
    return text.title() if text.islower() or text.isupper() else text


def normalize_product(name: str) -> str:
    """Canonicalize a product-category label (trimmed, title-cased words)."""
    return " ".join(str(name).strip().split())


# ---------------------------------------------------------------------------
# Main loader
# ---------------------------------------------------------------------------

def load_users(path: str | None = None) -> pd.DataFrame:
    """Load and tidy ``all_users.csv``.

    Returns a dataframe with one row per vendor and the following columns:

      * ``name``          : vendor handle (str)
      * ``markets``       : list[str] normalized market names
      * ``ships_from``    : list[str] normalized country names
      * ``products``      : list[str] normalized product categories
      * ``sales``         : int reported sales
      * ``n_markets``     : int, recomputed from parsed markets (authoritative)
      * ``n_markets_raw`` : int, the value from the source CSV (for auditing)
      * ``is_multi_market``: bool
      * ``primary_country``: str, first ship-from country or ""
    """
    csv_path = path or ALL_USERS_CSV
    df = pd.read_csv(csv_path)

    # drop the unnamed integer index column if present
    unnamed = [c for c in df.columns if str(c).startswith("Unnamed")]
    if unnamed:
        df = df.drop(columns=unnamed)

    expected = {"name", "markets", "ships_from", "products", "sales", "n_markets"}
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"{csv_path} is missing expected columns: {sorted(missing)}")

    df = df.copy()
    df["name"] = df["name"].astype(str).str.strip()

    df["markets"] = df["markets"].apply(parse_list).apply(
        lambda lst: sorted({normalize_market(m) for m in lst})
    )
    df["ships_from"] = df["ships_from"].apply(parse_list).apply(
        lambda lst: [normalize_country(c) for c in lst if normalize_country(c)]
    )
    df["products"] = df["products"].apply(parse_list).apply(
        lambda lst: [normalize_product(p) for p in lst if normalize_product(p)]
    )

    df["sales"] = pd.to_numeric(df["sales"], errors="coerce").fillna(0).astype(int)

    # keep the raw count for auditing, but recompute an authoritative one
    df["n_markets_raw"] = pd.to_numeric(
        df["n_markets"], errors="coerce"
    ).fillna(0).astype(int)
    df["n_markets"] = df["markets"].apply(len)
    df["is_multi_market"] = df["n_markets"] > 1
    df["primary_country"] = df["ships_from"].apply(lambda lst: lst[0] if lst else "")

    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Tidy / exploded views
# ---------------------------------------------------------------------------

def explode_column(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Return a long dataframe with one row per (vendor, `column`-element)."""
    if column not in LIST_COLUMNS:
        raise ValueError(f"{column!r} is not a list column {LIST_COLUMNS}")
    keep = ["name", "sales", "n_markets"]
    out = df[keep + [column]].explode(column)
    out = out[out[column].notna() & (out[column] != "")]
    return out.reset_index(drop=True)


def market_counts(df: pd.DataFrame) -> pd.Series:
    """Vendors per market (descending)."""
    return explode_column(df, "markets")["markets"].value_counts()


def country_counts(df: pd.DataFrame) -> pd.Series:
    """Vendors per ship-from country (descending)."""
    return explode_column(df, "ships_from")["ships_from"].value_counts()


def product_counts(df: pd.DataFrame) -> pd.Series:
    """Vendors per product category (descending)."""
    return explode_column(df, "products")["products"].value_counts()


@lru_cache(maxsize=1)
def load_users_cached() -> pd.DataFrame:
    """Cached convenience loader (used by the Streamlit dashboard)."""
    return load_users()


if __name__ == "__main__":  # pragma: no cover - manual smoke check
    _df = load_users()
    print("rows:", len(_df))
    print("columns:", list(_df.columns))
    print("markets:", market_counts(_df).head().to_dict())
    print("multi-market vendors:", int(_df["is_multi_market"].sum()))
