# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ListIQ is a cross-platform resale intelligence engine ("Should I Sell This?") that scrapes sold-listing data from eBay, Poshmark, and Depop, then predicts optimal platform, price, and sell-through speed. Built as a UC Berkeley capstone project for Phia.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env  # then fill in eBay API credentials
```

## Running Scrapers

```bash
# eBay (requires API credentials in .env)
python scrapers/ebay_scraper.py
python scrapers/ebay_scraper.py --categories "denim jacket,sneakers" --limit 500

# Poshmark (no API key needed, but scraper is a skeleton — may need Selenium)
python scrapers/poshmark_scraper.py
python scrapers/poshmark_scraper.py --categories "denim jacket,sneakers" --limit 500
```

Output goes to `data/raw/`. Raw data is gitignored; cleaned data lives in `data/cleaned/`.

## Architecture

**Pipeline stages:** Scrape -> Clean/Normalize -> EDA -> Model -> Demo

- `scrapers/` — One scraper per platform. Each is a standalone CLI script with `--categories`, `--limit`, and `--output` args. All output conforms to a shared schema (see README.md "Data Schema").
- `data/raw/` — Gitignored raw CSVs from scrapers.
- `data/cleaned/` — Normalized datasets used for EDA and modeling.
- `models/` — Trained model artifacts (gitignored `.pkl`/`.joblib`/`.h5`).
- `notebooks/` — Jupyter notebooks for EDA and experimentation.
- `demo/` — Streamlit app for the seller intelligence report.

## Key Details

- eBay scraper uses OAuth2 client credentials flow via the Browse API. Credentials loaded from `.env` via `python-dotenv`.
- Poshmark scraper is incomplete — it's a skeleton using BeautifulSoup on public pages. Poshmark renders dynamically, so it likely needs Selenium/Playwright or internal API endpoints.
- Depop scraper does not exist yet.
- Brand extraction from listing titles uses a hardcoded known-brands list in `ebay_scraper.py:extract_brand()`.
- All scraped data normalizes to a common schema with fields: platform, item_category, brand, condition, final_sale_price, original_list_price, days_to_sale, listing_day_of_week, listing_time, sold_date.
