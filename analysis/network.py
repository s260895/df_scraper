"""Vendor-market network analysis (defensive/academic).

Builds a bipartite vendor<->market graph from the tidy dataframe produced by
:mod:`analysis.load` and derives:

  * a cross-market vendor-overlap matrix (shared-vendor counts per market pair)
  * the top multi-market vendors ranked by reported sales
  * a market-projection graph where markets are linked by shared vendors
    (edge weight = number of shared vendors)

All computation is on the already-collected dataset; nothing here touches the
network or any live site.
"""

from __future__ import annotations

from itertools import combinations

import networkx as nx
import pandas as pd


# ---------------------------------------------------------------------------
# Bipartite graph
# ---------------------------------------------------------------------------

def build_bipartite(df: pd.DataFrame) -> nx.Graph:
    """Build a bipartite vendor<->market graph.

    Vendor nodes carry ``bipartite=0`` and ``sales``; market nodes carry
    ``bipartite=1``.  An edge connects a vendor to every market they appear on.
    """
    g = nx.Graph()
    for _, row in df.iterrows():
        vendor = f"v::{row['name']}"
        g.add_node(vendor, bipartite=0, kind="vendor",
                   label=row["name"], sales=int(row["sales"]))
        for market in row["markets"]:
            mnode = f"m::{market}"
            g.add_node(mnode, bipartite=1, kind="market", label=market)
            g.add_edge(vendor, mnode)
    return g


def _vendor_sets(df: pd.DataFrame) -> dict[str, set[str]]:
    """Map each market -> set of vendor names present on it."""
    sets: dict[str, set[str]] = {}
    for _, row in df.iterrows():
        for market in row["markets"]:
            sets.setdefault(market, set()).add(row["name"])
    return sets


# ---------------------------------------------------------------------------
# Cross-market overlap
# ---------------------------------------------------------------------------

def overlap_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Symmetric market x market matrix of shared-vendor counts.

    The diagonal holds each market's total vendor count.
    """
    sets = _vendor_sets(df)
    markets = sorted(sets, key=lambda m: (-len(sets[m]), m))
    mat = pd.DataFrame(0, index=markets, columns=markets, dtype=int)
    for m in markets:
        mat.loc[m, m] = len(sets[m])
    for a, b in combinations(markets, 2):
        shared = len(sets[a] & sets[b])
        mat.loc[a, b] = shared
        mat.loc[b, a] = shared
    return mat


def overlap_pairs(df: pd.DataFrame) -> pd.DataFrame:
    """Long-form table of market pairs ranked by shared-vendor count.

    Columns: ``market_a``, ``market_b``, ``shared_vendors``,
    ``jaccard`` (|A n B| / |A u B|).
    """
    sets = _vendor_sets(df)
    rows = []
    for a, b in combinations(sorted(sets), 2):
        inter = sets[a] & sets[b]
        union = sets[a] | sets[b]
        if inter:
            rows.append({
                "market_a": a,
                "market_b": b,
                "shared_vendors": len(inter),
                "jaccard": len(inter) / len(union) if union else 0.0,
            })
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values("shared_vendors", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Top multi-market vendors
# ---------------------------------------------------------------------------

def top_multi_market_vendors(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """Top ``n`` multi-market vendors ranked by sales then market breadth.

    Columns: ``name``, ``n_markets``, ``sales``, ``markets`` (list),
    ``markets_str`` (comma-joined for display).
    """
    multi = df[df["is_multi_market"]].copy()
    multi = multi.sort_values(["sales", "n_markets"], ascending=False)
    out = multi.head(n)[["name", "n_markets", "sales", "markets"]].copy()
    out["markets_str"] = out["markets"].apply(lambda lst: ", ".join(lst))
    return out.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Market-projection graph
# ---------------------------------------------------------------------------

def market_projection(df: pd.DataFrame) -> nx.Graph:
    """Graph of markets linked by shared vendors (edge weight = overlap).

    Each market node stores ``vendors`` (its vendor count).  Edges are only
    created where at least one vendor is shared.  ``jaccard`` is stored on the
    edge alongside ``weight``.
    """
    sets = _vendor_sets(df)
    g = nx.Graph()
    for market, vendors in sets.items():
        g.add_node(market, vendors=len(vendors))
    for a, b in combinations(sorted(sets), 2):
        inter = sets[a] & sets[b]
        if inter:
            union = sets[a] | sets[b]
            g.add_edge(a, b, weight=len(inter),
                       jaccard=len(inter) / len(union) if union else 0.0)
    return g


def projection_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Per-market centrality summary derived from the projection graph.

    Columns: ``market``, ``vendors``, ``degree`` (# connected markets),
    ``weighted_degree`` (sum of shared-vendor edge weights).
    """
    g = market_projection(df)
    rows = []
    for node in g.nodes:
        weighted = sum(d["weight"] for _, _, d in g.edges(node, data=True))
        rows.append({
            "market": node,
            "vendors": g.nodes[node]["vendors"],
            "degree": g.degree(node),
            "weighted_degree": weighted,
        })
    out = pd.DataFrame(rows)
    return out.sort_values("weighted_degree", ascending=False).reset_index(drop=True)


if __name__ == "__main__":  # pragma: no cover - manual smoke check
    from analysis.load import load_users

    _df = load_users()
    _g = build_bipartite(_df)
    print("bipartite nodes/edges:", _g.number_of_nodes(), _g.number_of_edges())
    print("top overlap pair:\n", overlap_pairs(_df).head(1))
    print("top vendor:\n", top_multi_market_vendors(_df, 1))
