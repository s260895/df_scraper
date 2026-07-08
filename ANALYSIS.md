# Vendor / Market Forensic Analysis

Defensive, academic analysis layer built on top of the **already-collected**
dataset in `data/`. Nothing in this layer crawls, scrapes, or contacts any live
site — it only reads the committed CSVs. All functionality lives in new files;
the original notebooks, `README.md`, `requirements.txt`, scraped HTML folders and
`data/` CSVs are untouched.

## New modules

| File | Purpose |
|------|---------|
| `analysis/__init__.py` | Package entry point. |
| `analysis/load.py` | Robust loader for `data/all_users.csv`. Safely parses the stringified list columns (`markets`, `ships_from`, `products`) with `ast.literal_eval` plus a comma-split fallback, normalizes market / country / product labels, recomputes an authoritative `n_markets`, and adds `is_multi_market` / `primary_country`. Helpers: `explode_column`, `market_counts`, `country_counts`, `product_counts`. |
| `analysis/network.py` | Vendor-market network analysis with `networkx`: `build_bipartite` (vendor<->market graph), `overlap_matrix` / `overlap_pairs` (cross-market shared-vendor counts + Jaccard), `top_multi_market_vendors`, `market_projection` (markets linked by shared vendors, edge weight = overlap) and `projection_summary`. |
| `market_dashboard.py` | Streamlit dashboard (KPIs, bar charts, overlap heatmap, top-vendor table, scatter). |
| `tests/test_load.py` | Loader / network assertions (pytest-compatible, also runs standalone). |

## Running

Loader / network (headless):

```bash
python -c "from analysis.load import load_users; from analysis import network as nw; df = load_users(); print(nw.overlap_pairs(df).head())"
```

Dashboard:

```bash
streamlit run market_dashboard.py
# then open http://localhost:8501
```

Tests:

```bash
python -m pytest tests/ -q      # if pytest is installed
python tests/test_load.py       # otherwise runs the asserts directly (exit 0 = pass)
```

## Dashboard contents

- **(a)** KPI row: vendors, markets, total reported sales, multi-market share.
- **(b)** Plotly bar charts: vendors per market, top-15 ship-from countries, top-15 product categories, and a log-scale sales histogram.
- **(c)** Cross-market vendor-overlap heatmap (`plotly.imshow`, sequential blue).
- **(d)** Top-20 multi-market vendor table. **Handles are pseudonymized by default** (first 2 chars + `***`); a *"Show raw handles"* checkbox (off by default) reveals them for authorised review.
- **(e)** Scatter of reported sales vs. number of markets.

## Findings (computed from `data/all_users.csv`, N = 1,178 vendors)

1. **Scale.** 1,178 vendor handles span **24 distinct markets** with **769,051** total reported sales. `darkfox` is the dominant/anchor market (775 vendors), followed by `silkroad` (303), `vice city` (190) and `asap` (184).

2. **Most cross-posted market pair.** **`asap` <-> `empire`** share the most vendors — **83 shared vendors** — and also have by far the highest overlap *ratio* (Jaccard ~ **0.43**), indicating a strongly connected vendor base between those two markets. The next pairs (`darkfox`<->`vice city`: 80, `asap`<->`darkfox`: 77, `darkfox`<->`silkroad`: 71) are large only because `darkfox` is the biggest market (low Jaccard ~ 0.07-0.09).

3. **Multi-market vendors are a meaningful minority.** **261 of 1,178 vendors (22.2%)** operate on more than one market; the most prolific span up to **13 markets**. In the projection graph `asap` has the highest weighted degree (544), making it the most bridging market despite being only the 4th largest by vendor count.

4. **Top product & origin.** The most common product category is **Cocaine** (178 vendors), ahead of **Weed** (162), Ketamine (99) and Benzos (97) — a drugs-dominated catalogue. The leading declared ship-from country is the **United States** (223 vendors), then the United Kingdom (120), Germany (109) and the Netherlands (83). Only 646 of 1,178 vendors declare any origin.

5. **Multi-market presence tracks higher reported sales.** Multi-market vendors average **1,670** reported sales vs **363** for single-market vendors — a ~4.6x gap — though the correlation between market count and sales is only moderate (Pearson r ~ **0.24**), so breadth is associated with, but far from determinative of, volume.

6. **Reported-sales data is heavily zero-inflated.** **630 of 1,178 vendors (53%)** report 0 sales, so the sales histogram is shown on a log scale over the positive-sales subset only.

## Caveats

- `sales` are **self-/site-reported** counts from the original scrape, not verified transactions; the large zero-inflation and heavy right tail (max = 57,013) mean aggregate figures are indicative, not authoritative.
- Vendors are matched **by handle string** across markets. Identical handles are treated as the same actor and different handles as different actors — both assumptions can be wrong (handle reuse / impersonation / rebranding), so overlap counts are an upper-ish bound on confirmed cross-market identity.
- Only ~55% of vendors declare a ship-from country, so country rankings describe the *declaring* subset, not the whole population.
- Market and product label spaces differ across the per-market source files; the loader normalizes casing/whitespace but does not reconcile market-specific category taxonomies (e.g. `Ecstasy` vs `XTC Pills`).
- This is a static snapshot analysis for academic/defensive study only.
