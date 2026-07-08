"""Streamlit dashboard for darkweb-marketplace vendor forensics (academic).

Run with::

    streamlit run market_dashboard.py

This is read-only analysis of an already-collected dataset. Vendor handles are
pseudonymized by default; a checkbox reveals raw handles for authorised review.
No crawling / scraping happens here.
"""

from __future__ import annotations

import os
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# make the analysis package importable when run via `streamlit run`
_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from analysis import load, network  # noqa: E402

# --- palette (validated categorical/sequential defaults) -------------------
PRIMARY = "#2a78d6"          # categorical slot 1 (blue)
INK = "#0b0b0b"
MUTED = "#898781"
# sequential blue ramp, light -> dark (used for the overlap heatmap)
BLUE_SCALE = [
    "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5",
    "#256abf", "#184f95", "#0d366b",
]

st.set_page_config(page_title="Market Vendor Forensics", layout="wide")


@st.cache_data
def get_data() -> pd.DataFrame:
    return load.load_users()


def pseudonymize(name: str) -> str:
    """Show first two chars then '***' (privacy default)."""
    s = str(name)
    if len(s) <= 2:
        return s[:1] + "***"
    return s[:2] + "***"


def _style(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=40, b=10),
        font=dict(color=INK),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    fig.update_xaxes(showgrid=False, color=MUTED)
    fig.update_yaxes(gridcolor="rgba(137,135,129,0.2)", color=MUTED)
    return fig


df = get_data()

st.title("Marketplace Vendor Forensics")
st.caption(
    "Read-only academic analysis of an already-collected vendor dataset "
    "(data/all_users.csv). No live collection is performed."
)

# --- (a) overview KPIs ------------------------------------------------------
n_vendors = len(df)
n_markets = df["markets"].explode().nunique()
total_sales = int(df["sales"].sum())
multi = int(df["is_multi_market"].sum())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Vendors", f"{n_vendors:,}")
c2.metric("Markets", f"{n_markets:,}")
c3.metric("Total reported sales", f"{total_sales:,}")
c4.metric("Multi-market vendors", f"{multi:,}", f"{multi / n_vendors:.1%}")

st.divider()

# --- (b) bar charts ---------------------------------------------------------
mc = load.market_counts(df)
cc = load.country_counts(df).head(15)
pc = load.product_counts(df).head(15)

r1c1, r1c2 = st.columns(2)
with r1c1:
    st.subheader("Vendors per market")
    fig = px.bar(x=mc.values, y=mc.index, orientation="h",
                 labels={"x": "vendors", "y": ""})
    fig.update_traces(marker_color=PRIMARY, marker_line_width=0)
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(_style(fig, 460), use_container_width=True)
with r1c2:
    st.subheader("Top 15 ship-from countries")
    fig = px.bar(x=cc.values, y=cc.index, orientation="h",
                 labels={"x": "vendors", "y": ""})
    fig.update_traces(marker_color=PRIMARY, marker_line_width=0)
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(_style(fig, 460), use_container_width=True)

r2c1, r2c2 = st.columns(2)
with r2c1:
    st.subheader("Top 15 product categories")
    fig = px.bar(x=pc.values, y=pc.index, orientation="h",
                 labels={"x": "vendors", "y": ""})
    fig.update_traces(marker_color=PRIMARY, marker_line_width=0)
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(_style(fig, 460), use_container_width=True)
with r2c2:
    st.subheader("Sales distribution (log scale)")
    pos = df[df["sales"] > 0]
    fig = px.histogram(pos, x="sales", nbins=40, log_x=True,
                       labels={"sales": "reported sales (log)"})
    fig.update_traces(marker_color=PRIMARY, marker_line_width=0)
    st.plotly_chart(_style(fig, 460), use_container_width=True)
    st.caption(f"{(df['sales'] == 0).sum()} vendors report 0 sales (excluded from log view).")

st.divider()

# --- (c) cross-market overlap heatmap --------------------------------------
st.subheader("Cross-market vendor overlap")
st.caption("Shared-vendor count for each market pair (diagonal = market's own vendor count).")
mat = network.overlap_matrix(df)
top_markets = mat.index[:12]
sub = mat.loc[top_markets, top_markets]
fig = px.imshow(sub, text_auto=True, color_continuous_scale=BLUE_SCALE,
                labels=dict(color="shared vendors"), aspect="auto")
fig.update_layout(height=560, margin=dict(l=10, r=10, t=30, b=10),
                  font=dict(color=INK), paper_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- (d) top multi-market vendors table ------------------------------------
st.subheader("Top 20 multi-market vendors")
show_raw = st.checkbox("Show raw handles", value=False)
top = network.top_multi_market_vendors(df, n=20)
display = top[["name", "n_markets", "sales", "markets_str"]].copy()
if not show_raw:
    display["name"] = display["name"].apply(pseudonymize)
display = display.rename(columns={
    "name": "vendor", "n_markets": "# markets",
    "sales": "reported sales", "markets_str": "markets",
})
st.dataframe(display, use_container_width=True, hide_index=True)
if not show_raw:
    st.caption("Handles pseudonymized by default (first 2 chars + '***').")

st.divider()

# --- (e) scatter sales vs n_markets ----------------------------------------
st.subheader("Reported sales vs. number of markets")
fig = px.scatter(df, x="n_markets", y="sales", opacity=0.55,
                 hover_data={"n_markets": True, "sales": True},
                 labels={"n_markets": "# markets", "sales": "reported sales"})
fig.update_traces(marker=dict(color=PRIMARY, size=8,
                              line=dict(width=1, color="#fcfcfb")))
st.plotly_chart(_style(fig, 420), use_container_width=True)
st.caption(
    "Each point is one vendor. Multi-market presence and reported sales are "
    "positively but loosely associated."
)
