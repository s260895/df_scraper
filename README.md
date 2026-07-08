# Dark-Web Marketplace Vendor Analysis

A three-stage scraping and analysis pipeline studying **drug-vendor activity across four Tor dark-web marketplaces** (DarkFox, ASAP, Silk Road 3, Vice City), built for the Data Forensics course at JADS (2021).

## Pipeline

1. **Crawl** (`Crawlers/*.ipynb`) — Selenium drives a Tor Browser instance (`tbselenium`) through each market's vendor listings, saving every vendor profile page as HTML. Crawls are resumable: already-downloaded profiles are skipped on restart.
2. **Parse** (`scraper.ipynb`) — BeautifulSoup extracts per vendor: product categories, ship-from country, completed-order counts, and cross-market presence (which of ~24 known marketplaces the vendor is also active on). Results land in per-market CSVs and a joined `data/all_users.csv` (~1,200 vendors).
3. **Analyze** (`notebook.ipynb`) — exploratory analysis of the joined dataset: most-active markets, multi-market vendor distribution, top origin countries, product-category popularity, and sales volume vs cross-market reach.

## Setup

This code runs on Linux (developed on Ubuntu 20.04) and requires a working Tor Browser installation.

### Geckodriver
Install [geckodriver](https://github.com/mozilla/geckodriver/releases/) and place the binary in `/usr/bin`.

### Tor Browser
Download the Tor Browser bundle from [torproject.org](https://www.torproject.org/) (or `sudo apt install tor`). Verify the setup:

```python
from tbselenium.tbdriver import TorBrowserDriver
with TorBrowserDriver("/path/to/tor-browser_en-US/") as driver:
    driver.get('https://check.torproject.org')
```

### Python dependencies

```bash
pip install -r requirements.txt
```

Update the hardcoded data/browser paths in the notebooks to match your machine before running.

## Note

Collected for academic research in a data-forensics context. Marketplace onion addresses rotate frequently; the hardcoded URLs are historical and long dead.

## Docker

```bash
docker compose up --build -d      # dashboard at http://localhost:8504
docker compose --profile tools run --rm tests        # run loader tests
docker compose down --rmi local -v                   # full teardown
```
