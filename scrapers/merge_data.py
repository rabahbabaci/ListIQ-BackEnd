"""
ListIQ — Cross-Platform Data Merge
===================================
Combines all per-platform cleaned CSVs in `data/cleaned/` into a single
unified dataset for downstream EDA and modeling.

The script picks up any file matching `*_cleaned.csv` (except the merged
output itself), so new platforms (e.g. Depop) are included automatically
once their cleaning pipeline lands a file in `data/cleaned/`.

Usage:
    python scrapers/merge_data.py
    python scrapers/merge_data.py --output data/cleaned/all_platforms.csv
    python scrapers/merge_data.py --input-dir data/cleaned --output data/cleaned/all_platforms.csv
"""

import sys
import glob
import argparse
from pathlib import Path

import pandas as pd
import numpy as np


# Map raw condition strings (lowercased) → canonical 4-bucket schema.
# This is a safety net — clean_data.py already normalizes per-platform.
CONDITION_NORMALIZATION = {
    # New
    "new": "New",
    "nwt": "New",
    "brand new": "New",
    "new with tags": "New",
    # Like New
    "like new": "Like New",
    "nwot": "Like New",
    "euc": "Like New",
    "new without tags": "Like New",
    "excellent": "Like New",
    "mint": "Like New",
    # Good
    "good": "Good",
    "vguc": "Good",
    "guc": "Good",
    "very good": "Good",
    "pre-owned": "Good",
    "preowned": "Good",
    # Fair
    "fair": "Fair",
    "well worn": "Fair",
    "acceptable": "Fair",
}

CANONICAL_CONDITIONS = {"New", "Like New", "Good", "Fair", "Unknown"}


def normalize_condition(value):
    """Map any condition string to one of the 5 canonical buckets."""
    if not isinstance(value, str):
        return "Unknown"
    cleaned = value.strip()
    if cleaned in CANONICAL_CONDITIONS:
        return cleaned
    return CONDITION_NORMALIZATION.get(cleaned.lower(), "Unknown")


def assign_price_tier(price):
    """Bucket a final sale price into a tier."""
    if pd.isna(price):
        return None
    if price < 20:
        return "budget"
    if price < 75:
        return "mid"
    if price < 200:
        return "premium"
    return "luxury"


def load_platform_files(input_dir, output_filename):
    """Load every *_cleaned.csv in input_dir except the merged output itself."""
    pattern = str(Path(input_dir) / "*_cleaned.csv")
    paths = sorted(p for p in glob.glob(pattern) if Path(p).name != output_filename)
    if not paths:
        print(f"ERROR: no '*_cleaned.csv' files found in {input_dir}")
        sys.exit(1)

    frames = []
    for path in paths:
        df = pd.read_csv(path)
        print(f"  Loaded {Path(path).name}: {len(df)} rows")
        frames.append(df)
    return frames


def merge(frames):
    """Concatenate, normalize, drop bad prices, and add derived columns."""
    df = pd.concat(frames, ignore_index=True, sort=False)
    initial = len(df)

    # Drop rows with no usable price (or below the $1 sanity floor)
    df = df[df["final_sale_price"].notna() & (df["final_sale_price"] >= 1)].copy()
    dropped_low_price = initial - len(df)

    # Normalize condition labels (safety net over per-platform cleaning)
    df["condition"] = df["condition"].apply(normalize_condition)

    # Cap days_to_sale at 365 with a null-safe outlier flag
    df["days_to_sale_outlier"] = df["days_to_sale"].notna() & (df["days_to_sale"] > 365)
    df["days_to_sale"] = df["days_to_sale"].clip(upper=365)

    # price_discount_pct: null when original_list_price is null or <= 0
    orig = df["original_list_price"]
    valid_orig = orig.notna() & (orig > 0)
    df["price_discount_pct"] = np.where(
        valid_orig,
        ((orig - df["final_sale_price"]) / orig * 100).round(1),
        np.nan,
    )

    # price_tier
    df["price_tier"] = df["final_sale_price"].apply(assign_price_tier)

    return df, dropped_low_price


def print_summary(df, dropped_low_price):
    print("=" * 70)
    print("Merge Summary")
    print("=" * 70)
    print(f"Dropped {dropped_low_price} rows (price < $1 sanity floor)")
    print(f"Total merged rows: {len(df)}")
    print()

    print("--- Rows per platform ---")
    print(df["platform"].value_counts().to_string())
    print()

    print("--- Category × platform ---")
    print(pd.crosstab(df["item_category"], df["platform"]).to_string())
    print()

    print("--- Condition distribution (overall) ---")
    print(df["condition"].value_counts().to_string())
    print()

    print("--- Condition distribution (per platform) ---")
    print(pd.crosstab(df["condition"], df["platform"]).to_string())
    print()

    print("--- Price stats per platform ---")
    price_stats = df.groupby("platform")["final_sale_price"].agg(
        ["count", "mean", "median", "min", "max"]
    ).round(2)
    print(price_stats.to_string())
    print()

    print("--- Price tier distribution ---")
    print(df["price_tier"].value_counts().to_string())
    print()

    print("--- Derived column nulls ---")
    for col in ("price_discount_pct", "price_tier", "days_to_sale", "days_to_sale_outlier"):
        nulls = df[col].isna().sum()
        print(f"  {col}: {nulls} null ({nulls / len(df) * 100:.1f}%)")
    print()

    print("--- price_discount_pct coverage per platform ---")
    by_platform = df.groupby("platform")["price_discount_pct"].agg(
        non_null="count",
        median="median",
    ).round(1)
    by_platform["pct_with_discount"] = (
        df.groupby("platform")["price_discount_pct"].apply(lambda s: s.notna().mean() * 100).round(1)
    )
    print(by_platform.to_string())
    print()

    print("--- sold_date range per platform ---")
    for platform, sub in df.groupby("platform"):
        dates = pd.to_datetime(sub["sold_date"], errors="coerce").dropna()
        if dates.empty:
            print(f"  {platform}: no parseable dates")
        else:
            print(f"  {platform}: {dates.min().date()} → {dates.max().date()} "
                  f"({dates.dt.date.nunique()} distinct days)")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Merge per-platform cleaned CSVs into a unified ListIQ dataset"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/cleaned",
        help="Directory containing per-platform *_cleaned.csv files",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/cleaned/all_platforms.csv",
        help="Output CSV path",
    )
    args = parser.parse_args()

    print(f"Reading from: {args.input_dir}")
    output_filename = Path(args.output).name
    frames = load_platform_files(args.input_dir, output_filename)
    print()

    df, dropped_low_price = merge(frames)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Wrote {len(df)} rows to {args.output}")
    print()

    print_summary(df, dropped_low_price)


if __name__ == "__main__":
    main()
