"""Tests for the analysis loader and network helpers.

Run either with pytest::

    python -m pytest tests/ -q

or directly (no pytest required)::

    python tests/test_load.py
"""

from __future__ import annotations

import os
import sys

# make the repo root importable when run directly as a script
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from analysis import load, network  # noqa: E402


def test_parse_list_handles_variants():
    assert load.parse_list("['darkfox', 'asap']") == ["darkfox", "asap"]
    assert load.parse_list("[]") == []
    assert load.parse_list(None) == []
    assert load.parse_list(float("nan")) == []
    assert load.parse_list(["a", " b ", ""]) == ["a", "b"]
    # malformed string still degrades gracefully
    assert load.parse_list("['a', 'b'") == ["a", "b"]


def test_normalizers():
    assert load.normalize_market("  DarkFox ") == "darkfox"
    assert load.normalize_country("usa") == "United States"
    assert load.normalize_country("uk") == "United Kingdom"


def test_load_users_shape_and_columns():
    df = load.load_users()
    assert len(df) > 1000, f"expected >1000 rows, got {len(df)}"
    for col in ("name", "markets", "ships_from", "products",
                "sales", "n_markets", "is_multi_market"):
        assert col in df.columns, f"missing column {col}"


def test_list_columns_are_lists():
    df = load.load_users()
    assert df["markets"].apply(lambda v: isinstance(v, list)).all()
    assert df["products"].apply(lambda v: isinstance(v, list)).all()
    assert df["ships_from"].apply(lambda v: isinstance(v, list)).all()
    # every vendor is on at least one market
    assert (df["n_markets"] >= 1).all()


def test_sales_numeric_nonnegative():
    df = load.load_users()
    assert df["sales"].dtype.kind in "iu"
    assert (df["sales"] >= 0).all()


def test_overlap_matrix_symmetric_and_diagonal():
    df = load.load_users()
    mat = network.overlap_matrix(df)
    assert (mat.values == mat.values.T).all(), "overlap matrix must be symmetric"
    counts = load.market_counts(df)
    for market in mat.index:
        assert mat.loc[market, market] == counts[market]


def test_top_multi_market_vendors():
    df = load.load_users()
    top = network.top_multi_market_vendors(df, n=20)
    assert len(top) <= 20
    assert (top["n_markets"] > 1).all(), "multi-market vendors must span >1 market"


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failures = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as exc:
            failures += 1
            print(f"FAIL {fn.__name__}: {exc}")
    print(f"\n{len(fns) - failures}/{len(fns)} tests passed")
    return failures


if __name__ == "__main__":
    sys.exit(1 if _run_all() else 0)
