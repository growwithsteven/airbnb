"""Generate one first-crawl scatterplot and OLS line for each review metric."""

import os
import sqlite3
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "raw_data/airbnb2.db"
OUTPUT_DIR = ROOT / "docs/public"

METRICS = {
    "checking": "체크인 만족도",
    "communication": "의사소통 만족도",
    "accuracy": "정보 정확도",
    "location": "위치 만족도",
    "guest_satisfaction": "종합 평점",
    "reviews_count": "누적 리뷰 수",
    "value": "가격 대비 가치",
}

PALETTE = {
    "Entire home/apt": "#2b5c8f",
    "Private room": "#2e8b57",
    "Shared room": "#d9534f",
    "Hotel room": "#9ca3af",
}


def load_first_crawl() -> pd.DataFrame:
    """Load first-crawl listings after registered price-unit errors are excluded."""
    query = """
    SELECT l.id AS listing_id, l.room_type, p.ln_nightly_price_usd,
           r.guest_satisfaction, r.accuracy, r.checking, r.communication,
           r.location, r.value, r.reviews_count
    FROM LISTING l
    JOIN LISTING_BATCH b ON b.listing_id = l.id
    JOIN LISTING_PRICE_DERIVED p ON p.listing_id = l.id
    JOIN LISTING_RATING r ON r.listing_id = l.id
    LEFT JOIN LISTING_EXCLUSION e
      ON e.listing_id = l.id AND e.exclusion_category = 'PRICE_UNIT_ERROR'
    WHERE b.is_original = 1 AND e.listing_id IS NULL
    """
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn)


def draw_chart(data: pd.DataFrame, metric: str, label: str) -> None:
    """Draw all observed points and one OLS line; only display differs by metric."""
    subset = data.dropna(subset=[metric, "ln_nightly_price_usd"]).copy()
    model = smf.ols(f"ln_nightly_price_usd ~ {metric}", data=subset).fit()
    rng = np.random.default_rng(42)
    x = subset[metric].to_numpy(dtype=float)
    if metric != "reviews_count":
        x = x + rng.normal(0, 0.015, len(x))

    fig, ax = plt.subplots(figsize=(5.2, 3.8))
    for room_type, color in PALETTE.items():
        group = subset[subset["room_type"] == room_type]
        if not group.empty:
            mask = group.index
            ax.scatter(x[subset.index.get_indexer(mask)], group["ln_nightly_price_usd"],
                       color=color, alpha=0.30, s=24, edgecolors="none")

    x_min, x_max = subset[metric].min(), subset[metric].max()
    pad = max((x_max - x_min) * 0.06, 0.15 if metric != "reviews_count" else 1)
    line_x = np.linspace(x_min - pad, x_max + pad, 100)
    line_y = model.params["Intercept"] + model.params[metric] * line_x
    ax.plot(line_x, line_y, color="#111827", linestyle="--", linewidth=2.8)
    ax.set_xlim(x_min - pad, x_max + pad)
    ax.set_ylim(2.5, 8.2)
    ax.set_xlabel(label)
    ax.set_ylabel("1박 가격")
    fig.savefig(OUTPUT_DIR / f"rating_regression_{metric}.png", dpi=300)
    plt.close(fig)


def main() -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update({
        "font.family": "Apple SD Gothic Neo",
        "font.size": 11,
        "axes.labelsize": 11,
        "axes.labelweight": "bold",
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "figure.dpi": 300,
        "savefig.bbox": "tight",
        "axes.unicode_minus": False,
    })
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    data = load_first_crawl()
    for metric, label in METRICS.items():
        draw_chart(data, metric, label)
    print(f"Generated {len(METRICS)} charts from {len(data)} first-crawl listings.")


if __name__ == "__main__":
    main()
