"""Analysis package for darkweb-marketplace vendor data (defensive/academic).

Modules
-------
load    : robust loader / normalizer for data/all_users.csv
network : vendor-market bipartite graph, cross-market overlap, projections

This package performs *forensic analysis of an already-collected dataset only*.
It contains no crawling/scraping functionality.
"""

from . import load  # noqa: F401
from . import network  # noqa: F401

__all__ = ["load", "network"]
