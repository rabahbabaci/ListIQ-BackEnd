# ListIQ — Cross-Platform Resale Intelligence Engine

**"Should I Sell This?"** — A seller intelligence module that tells resale sellers where to list, at what price, and how fast an item will sell, using real sold-listing data across platforms.

Built for [Phia](https://phia.com/) as a capstone project for Data 198: Fashion x Data Science, UC Berkeley Spring 2026.

## Team
- Rabah Babaci
- Lisa Hao
- Perla Perez
- Alex Thomas Suggs

## Project Structure

```
listiq-repo/
├── scrapers/          # Platform scraping scripts (eBay, Poshmark, Depop)
├── data/
│   ├── raw/           # Raw scraped data (not committed — see .gitignore)
│   └── cleaned/       # Normalized, cleaned datasets
├── models/            # Trained model artifacts and evaluation notebooks
├── notebooks/         # EDA, analysis, and experimentation notebooks
├── demo/              # Streamlit/Gradio demo application
├── requirements.txt   # Python dependencies
└── README.md
```

## Pipeline Overview

1. **Data Collection** — Scrape sold listings from eBay (API), Poshmark, and Depop
2. **EDA + Segmentation** — Platform-item fit analysis, price distributions, sell velocity patterns
3. **Predictive Modeling** — Price prediction (regression) + sell-through probability (classification)
4. **Platform Routing** — Composite scoring algorithm ranking platforms per item type
5. **Demo** — Upload a photo → get a seller intelligence report

## Setup

```bash
pip install -r requirements.txt
```

## Data Schema

All sold-listing data is normalized into:

| Field | Type | Description |
|-------|------|-------------|
| platform | str | eBay, Poshmark, or Depop |
| item_category | str | e.g., denim jacket, midi dress, sneakers |
| brand | str | Brand name |
| condition | str | New, Like New, Good, Fair |
| final_sale_price | float | Actual sold price (USD) |
| original_list_price | float | Original asking price (USD) |
| days_to_sale | int | Days from listing to sale |
| listing_day_of_week | str | Day item was listed |
| listing_time | str | Time of day listed |
| sold_date | date | Date the item sold |
