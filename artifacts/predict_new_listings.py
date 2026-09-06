#!/usr/bin/env python3
"""Predict prices for new listings from dataset_airbnb-scraper_2026-09-05_14-15-07-333.json
after deduplicating against raw_data/airbnb2.db.
"""

import json
import pickle
import re
import sqlite3
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd
import pyproj

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "raw_data" / "airbnb2.db"
JSON_PATH = ROOT / "dataset_airbnb-scraper_2026-09-05_14-15-07-333.json"
OUTPUT_CSV = ROOT / "artifacts" / "new_listings_price_predictions.csv"

AMENITY_RULES = {
    "has_kitchen": ("title", r"^Kitchen$"),
    "has_washer": ("icon", r"^SYSTEM_WASHER$"),
    "has_dryer": ("icon", r"^SYSTEM_DRYER$"),
    "has_workspace": ("icon", r"^SYSTEM_WORKSPACE$"),
    "has_elevator": ("icon", r"^SYSTEM_ELEVATOR$"),
    "has_free_parking": ("title", r"^Free parking (?:on premises|on street)(?:\b|$)"),
    "has_hot_tub": ("icon", r"^SYSTEM_JACUZZI$"),
    "has_bathtub": ("icon", r"^SYSTEM_BATHTUB$"),
    "has_self_check_in": ("title", r"^Self check-in$"),
    "has_private_entrance": ("title", r"^Private entrance$"),
}

ROOM_PATTERNS = {
    "bedrooms": r"^(\d+(?:\.\d+)?) bedrooms?$",
    "beds": r"^(\d+(?:\.\d+)?) (?:(?:single|double|queen|king|small double|bunk|sofa) )?beds?$",
    "bathrooms": r"^(\d+(?:\.\d+)?) (?:(?:shared|private) )?bath(?:s|rooms?)?$",
}


def main():
    # 1. Load existing listings from SQLite database
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id FROM LISTING")
    existing_ids = set(str(r[0]) for r in cur.fetchall())

    # Load primary price model artifact
    row = cur.execute(
        "SELECT pipeline_blob, feature_schema, model_id FROM PRICE_MODEL_ARTIFACT"
    ).fetchone()
    pipeline = pickle.loads(row[0])
    schema = json.loads(row[1])
    cols = schema["columns"]
    model_id = row[2]

    # Load cluster centroids
    centroids = cur.execute(
        "SELECT DISTINCT cluster_id, centroid_x_epsg5179_m, centroid_y_epsg5179_m "
        "FROM LISTING_LOCATION_CLUSTER ORDER BY cluster_id"
    ).fetchall()
    centers = np.array([[r[1], r[2]] for r in centroids])

    # Cluster name mapping
    cluster_names = dict(
        cur.execute(
            "SELECT cluster_id, cluster_name_ko FROM LOCATION_CLUSTER WHERE cluster_count=5"
        ).fetchall()
    )
    conn.close()

    print(f"[1] Loaded model '{model_id}'. Features: {cols}")
    print(f"[2] Found {len(existing_ids)} existing listing IDs in DB.")

    # 2. Read new scrape JSON
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"[3] Total records in JSON: {len(data)}")

    # 3. Filter out listings that match existing data
    unmatched = [item for item in data if str(item.get("id")) not in existing_ids]
    matched_count = len(data) - len(unmatched)
    print(f"[4] Deduplication result:")
    print(f"    - Matched (removed): {matched_count} listings")
    print(f"    - New unique listings: {len(unmatched)} listings")

    # 4. Feature engineering for new listings
    transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:5179", always_xy=True)

    records = []
    for item in unmatched:
        lid = str(item.get("id"))
        title = item.get("title", "")
        room_type = item.get("roomType")
        prop_type = item.get("propertyType")
        cap = float(item.get("personCapacity") or 1)
        ln_cap = np.log(cap) if cap > 0 else np.nan

        # Coordinates & cluster assignment
        lat = float(item.get("coordinates", {}).get("latitude") or 0)
        lon = float(item.get("coordinates", {}).get("longitude") or 0)
        x, y = transformer.transform(lon, lat)
        x_km = x / 1000.0
        y_km = y / 1000.0

        dists = np.sqrt(((np.array([x, y]) - centers) ** 2).sum(axis=1))
        cluster_id_num = dists.argmin()
        cluster_id = str(cluster_id_num)
        cluster_name = cluster_names.get(cluster_id_num, "")

        # Room characteristics from subDescription items
        sub_items = item.get("subDescription", {}).get("items", [])
        room_dict = {}
        for feature, pat in ROOM_PATTERNS.items():
            vals = []
            for text in sub_items:
                t = str(text).strip()
                m = re.fullmatch(pat, t, re.I)
                val = (
                    float(m.group(1))
                    if m
                    else 0.0
                    if (feature == "bedrooms" and t.lower() == "studio")
                    or (feature == "bathrooms" and t.lower() == "no bathroom")
                    else None
                )
                if val is not None:
                    vals.append(val)
            room_dict[feature] = vals[0] if len(set(vals)) == 1 else np.nan

        # Amenities
        avail_items = []
        for cat in item.get("amenities", []):
            for v in cat.get("values", []):
                if v.get("available") is True:
                    avail_items.append(v)
        amenity_count = float(len(avail_items))

        amenity_flags = {}
        titles = [v.get("title", "") for v in avail_items]
        icons = [v.get("icon", "") for v in avail_items]
        for name, (field, pat) in AMENITY_RULES.items():
            target_list = titles if field == "title" else icons
            has_flag = any(re.search(pat, t, re.I) for t in target_list)
            amenity_flags[name] = float(has_flag)

        rec = {
            "listing_id": lid,
            "title": title,
            "room_type": room_type,
            "property_type": prop_type,
            "person_capacity": cap,
            "ln_capacity": ln_cap,
            "cluster_id": cluster_id,
            "cluster_name_ko": cluster_name,
            "bedrooms": room_dict["bedrooms"],
            "beds": room_dict["beds"],
            "bathrooms": room_dict["bathrooms"],
            "amenity_count": amenity_count,
            "x_km": x_km,
            "y_km": y_km,
            "latitude": lat,
            "longitude": lon,
            **amenity_flags,
        }

        # Actual price from JSON if present
        price_obj = item.get("price")
        cin = item.get("checkIn")
        cout = item.get("checkOut")
        rec["actual_total_usd"] = np.nan
        rec["stay_nights"] = np.nan
        rec["actual_nightly_price_usd"] = np.nan
        rec["actual_ln_nightly_price"] = np.nan
        rec["actual_price_per_person_usd"] = np.nan

        raw_price = None
        if price_obj:
            raw_price = price_obj.get("price") or (
                price_obj.get("breakDown", {}).get("total", {}).get("price")
            ) or (
                price_obj.get("breakDown", {}).get("basePrice", {}).get("price")
            )

        if raw_price and cin and cout:
            try:
                total_str = (
                    str(raw_price)
                    .replace("$", "")
                    .replace(",", "")
                    .strip()
                )
                total_usd = float(total_str)
                d1 = date.fromisoformat(cin)
                d2 = date.fromisoformat(cout)
                nights = (d2 - d1).days
                if nights > 0:
                    nightly_usd = total_usd / nights
                    rec["actual_total_usd"] = total_usd
                    rec["stay_nights"] = nights
                    rec["actual_nightly_price_usd"] = nightly_usd
                    rec["actual_ln_nightly_price"] = np.log(nightly_usd)
                    rec["actual_price_per_person_usd"] = nightly_usd / cap
            except Exception:
                pass

        records.append(rec)

    df = pd.DataFrame(records)

    # 5. Predict using trained pipeline
    X = df[cols]
    preds = pipeline.predict(X)

    df["predicted_ln_nightly_price"] = preds
    df["predicted_nightly_price_usd"] = np.exp(preds)
    df["predicted_price_per_person_usd"] = (
        df["predicted_nightly_price_usd"] / df["person_capacity"]
    )

    # Calculate errors if actual price is available
    has_actual = df.dropna(subset=["actual_ln_nightly_price"]).copy()
    if len(has_actual) > 0:
        has_actual["log_residual"] = (
            has_actual["actual_ln_nightly_price"]
            - has_actual["predicted_ln_nightly_price"]
        )
        has_actual["dollar_error"] = (
            has_actual["predicted_nightly_price_usd"]
            - has_actual["actual_nightly_price_usd"]
        )
        has_actual["abs_dollar_error"] = has_actual["dollar_error"].abs()
        has_actual["pct_error"] = (
            has_actual["dollar_error"] / has_actual["actual_nightly_price_usd"] * 100
        )

        mae_log = np.mean(np.abs(has_actual["log_residual"]))
        rmse_log = np.sqrt(np.mean(has_actual["log_residual"] ** 2))
        ss_res = np.sum(has_actual["log_residual"] ** 2)
        ss_tot = np.sum(
            (
                has_actual["actual_ln_nightly_price"]
                - has_actual["actual_ln_nightly_price"].mean()
            )
            ** 2
        )
        r2 = 1.0 - (ss_res / ss_tot)

        med_abs_usd = has_actual["abs_dollar_error"].median()
        mean_abs_usd = has_actual["abs_dollar_error"].mean()
        med_pct = has_actual["pct_error"].median()

        print("\n" + "=" * 60)
        print(" [MODEL EVALUATION ON NEW REAL-WORLD UNSEEN DATA] ")
        print("=" * 60)
        print(f"Evaluated Listings Count: {len(has_actual)}")
        print(f"Log-scale MAE : {mae_log:.4f}")
        print(f"Log-scale RMSE: {rmse_log:.4f}")
        print(f"Log-scale R²  : {r2:.4f}")
        print("-" * 60)
        print(f"Dollar MAE (Mean)  : ${mean_abs_usd:.2f} / night")
        print(f"Dollar MAE (Median): ${med_abs_usd:.2f} / night")
        print(f"Median Percentage Error: {med_pct:+.1f}%")
        print("=" * 60)

    # 6. Save results
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out_cols = [
        "listing_id",
        "title",
        "cluster_name_ko",
        "room_type",
        "property_type",
        "person_capacity",
        "bedrooms",
        "beds",
        "bathrooms",
        "amenity_count",
        "predicted_nightly_price_usd",
        "predicted_price_per_person_usd",
        "actual_nightly_price_usd",
        "actual_price_per_person_usd",
        "predicted_ln_nightly_price",
        "actual_ln_nightly_price",
    ]
    df[out_cols].to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"\n[5] Saved prediction results to {OUTPUT_CSV}")

    # Summary by cluster
    print("\n--- Predicted Nightly Price Summary by Cluster (USD) ---")
    cluster_summary = df.groupby("cluster_name_ko").agg(
        count=("listing_id", "count"),
        pred_mean=("predicted_nightly_price_usd", "mean"),
        pred_median=("predicted_nightly_price_usd", "median"),
        pred_min=("predicted_nightly_price_usd", "min"),
        pred_max=("predicted_nightly_price_usd", "max"),
        act_median=("actual_nightly_price_usd", "median"),
    )
    print(cluster_summary.round(1))

    # Summary by room type
    print("\n--- Predicted Nightly Price Summary by Room Type (USD) ---")
    room_summary = df.groupby("room_type").agg(
        count=("listing_id", "count"),
        pred_mean=("predicted_nightly_price_usd", "mean"),
        pred_median=("predicted_nightly_price_usd", "median"),
        pred_min=("predicted_nightly_price_usd", "min"),
        pred_max=("predicted_nightly_price_usd", "max"),
        act_median=("actual_nightly_price_usd", "median"),
    )
    print(room_summary.round(1))

    # Top 5 most expensive predicted listings
    print("\n--- Top 5 Highest Predicted Nightly Price Listings ---")
    top5 = df.sort_values(
        by="predicted_nightly_price_usd", ascending=False
    ).head(5)
    for _, r in top5.iterrows():
        print(
            f"ID: {r['listing_id']} | Cap: {r['person_capacity']} | {r['cluster_name_ko']} | Pred: ${r['predicted_nightly_price_usd']:.1f} (Act: ${r['actual_nightly_price_usd']:.1f}) | {r['title'][:40]}"
        )

    # Top 5 lowest predicted listings
    print("\n--- Top 5 Lowest Predicted Nightly Price Listings ---")
    low5 = df.sort_values(
        by="predicted_nightly_price_usd", ascending=True
    ).head(5)
    for _, r in low5.iterrows():
        print(
            f"ID: {r['listing_id']} | Cap: {r['person_capacity']} | {r['cluster_name_ko']} | Pred: ${r['predicted_nightly_price_usd']:.1f} (Act: ${r['actual_nightly_price_usd']:.1f}) | {r['title'][:40]}"
        )


if __name__ == "__main__":
    main()
