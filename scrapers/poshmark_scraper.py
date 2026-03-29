"""
ListIQ — Poshmark Sold Listings Scraper
========================================
Scrapes completed/sold listings from Poshmark's public pages.

Usage:
    python scrapers/poshmark_scraper.py
    python scrapers/poshmark_scraper.py --categories "denim jacket,sneakers" --limit 500

Note: Poshmark does not have an official API. This scraper uses public web pages.
Be respectful of rate limits and terms of service.
"""

import time
import argparse
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm

BASE_URL = "https://poshmark.com"

DEFAULT_CATEGORIES = [
    "denim jacket",
    "midi dress",
    "sneakers",
    "handbag",
    "blazer",
    "vintage t-shirt",
    "leather jacket",
    "crossbody bag",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def scrape_sold_listings(category, limit=500):
    """
    Scrape sold listings from Poshmark for a given category.
    
    Poshmark's sold listings can be accessed via:
    https://poshmark.com/search?query={category}&availability=sold_out
    
    TODO: Implement full scraping logic. This is a skeleton that your team 
    will need to complete and test. Key considerations:
    - Poshmark uses dynamic rendering (may need Selenium or similar)
    - Respect rate limits (add delays between requests)
    - Handle pagination
    - Extract: title, brand, price, condition, sold date
    """
    items = []
    
    search_url = f"{BASE_URL}/search"
    params = {
        "query": category,
        "availability": "sold_out",
        "type": "listings",
    }
    
    try:
        response = requests.get(search_url, headers=HEADERS, params=params, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "lxml")
            
            # Poshmark renders listings dynamically — this basic approach may 
            # only get partial results. If so, consider using:
            # 1. Selenium/Playwright for full JS rendering
            # 2. Poshmark's internal API endpoints (inspect network tab)
            
            listing_cards = soup.select("[data-et-name='listing']")
            
            for card in listing_cards[:limit]:
                try:
                    title = card.select_one(".title__condition__container .title")
                    price = card.select_one(".price")
                    brand = card.select_one(".brand")
                    
                    item = {
                        "platform": "Poshmark",
                        "item_category": category,
                        "brand": brand.text.strip() if brand else "Unknown",
                        "condition": "Unknown",  # Poshmark doesn't always show condition in search
                        "final_sale_price": parse_price(price.text) if price else None,
                        "original_list_price": None,
                        "days_to_sale": None,
                        "listing_day_of_week": None,
                        "listing_time": None,
                        "sold_date": None,
                        "title": title.text.strip() if title else "",
                    }
                    items.append(item)
                except Exception as e:
                    continue
            
        elif response.status_code == 403:
            print(f"  WARNING: Access blocked for '{category}'. May need Selenium.")
        else:
            print(f"  WARNING: Got status {response.status_code} for '{category}'")
            
    except Exception as e:
        print(f"  ERROR: Failed to scrape '{category}': {e}")
    
    return items


def parse_price(price_str):
    """Extract numeric price from string like '$45.00' or '$45'."""
    try:
        return float(price_str.replace("$", "").replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


def main():
    parser = argparse.ArgumentParser(description="Scrape Poshmark sold listings for ListIQ")
    parser.add_argument("--categories", type=str, default=",".join(DEFAULT_CATEGORIES))
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--output", type=str, default="data/raw/poshmark_sold_listings.csv")
    args = parser.parse_args()

    categories = [c.strip() for c in args.categories.split(",")]

    print("=" * 60)
    print("ListIQ — Poshmark Sold Listings Scraper")
    print("=" * 60)
    print(f"Categories: {categories}")
    print(f"Limit per category: {args.limit}")
    print()

    all_data = []
    for category in categories:
        print(f"Scraping: {category}")
        items = scrape_sold_listings(category, args.limit)
        all_data.extend(items)
        print(f"  Got {len(items)} items")
        time.sleep(2)  # Be respectful

    df = pd.DataFrame(all_data)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    print(f"\nDone! Saved {len(df)} listings to {args.output}")


if __name__ == "__main__":
    main()
