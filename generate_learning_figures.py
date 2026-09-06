#!/usr/bin/env python3
"""Generate publication-quality educational figures for Seoul Airbnb Price Model Learning Report."""

import os
import json
import sqlite3
from pathlib import Path
os.environ.setdefault("MPLBACKEND", "Agg")  # File-only rendering; avoid macOS GUI backend crashes.
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D
from pyproj import Transformer

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "raw_data/airbnb2.db"
FIG_DIR = ROOT / "artifacts/figures"
SEOUL_BOUNDARY = ROOT / "artifacts/reference-data/seoul_municipalities_geo_simple.json"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Set clean aesthetic style
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.labelsize": 11,
    "axes.labelweight": "bold",
    "figure.titlesize": 14,
    "figure.titleweight": "bold",
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.dpi": 300,
    "savefig.bbox": "tight"
})

def fig1_validation_architecture():
    """Figure 1: Traditional 80:20 Holdout vs External OOD Validation Architecture."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    
    # Left: Traditional 80:20 Holdout
    ax1 = axes[0]
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 10)
    ax1.axis("off")
    ax1.set_title("A. Alternative: Internal Random Holdout", pad=15, color="#7f8c8d")
    
    # Draw boxes
    rect1 = plt.Rectangle((1, 6.5), 8, 2.2, facecolor="#ebf5fb", edgecolor="#2980b9", lw=2, zorder=2)
    ax1.add_patch(rect1)
    ax1.text(5, 7.8, "Historical Crawl Dataset (1,909 listings)", ha="center", va="center", weight="bold", fontsize=11, color="#1b4f72")
    
    # 80% / 20% split
    split_train = plt.Rectangle((1.2, 6.7), 6.1, 0.8, facecolor="#aed6f1", edgecolor="#2471a3", lw=1.5, zorder=3)
    split_test = plt.Rectangle((7.5, 6.7), 1.3, 0.8, facecolor="#f5b7b1", edgecolor="#c0392b", lw=1.5, zorder=3)
    ax1.add_patch(split_train)
    ax1.add_patch(split_test)
    ax1.text(4.25, 7.1, "80% Training (1,527)", ha="center", va="center", fontsize=9, weight="bold")
    ax1.text(8.15, 7.1, "20% Holdout", ha="center", va="center", fontsize=8, weight="bold", color="#922b21")
    
    # Problems callout
    prob_box = plt.Rectangle((1, 1.2), 8, 4.2, facecolor="#fdfefe", edgecolor="#e74c3c", lw=1.5, ls="--", zorder=2)
    ax1.add_patch(prob_box)
    ax1.text(5, 4.8, "[What this design does and does not measure]", ha="center", va="center", weight="bold", color="#7f8c8d", fontsize=10)
    reasons_left = (
        "• Reserves observations for a one-time internal evaluation.\n"
        "• Random records can share crawl-era conditions and related\n  listing characteristics with training records.\n"
        "• It evaluates within-sample interpolation, not necessarily\n  transfer to a later crawl."
    )
    ax1.text(1.5, 3.0, reasons_left, ha="left", va="center", fontsize=9.5, linespacing=1.6, color="#2c3e50")
    
    # Right: Our Design (100% 5-Fold CV + External OOD JSON)
    ax2 = axes[1]
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 10)
    ax2.axis("off")
    ax2.set_title("B. Adopted Design: Full-Population CV + Novel JSON Evaluation", pad=15, color="#27ae60")
    
    # Historical 100% Training Box
    rect2 = plt.Rectangle((1, 6.5), 8, 2.2, facecolor="#eafaf1", edgecolor="#27ae60", lw=2, zorder=2)
    ax2.add_patch(rect2)
    ax2.text(5, 8.0, "100% Historical Dataset (1,909 listings)", ha="center", va="center", weight="bold", fontsize=11, color="#145a32")
    
    # 5-fold blocks
    for i in range(5):
        fold = plt.Rectangle((1.2 + i * 1.52, 6.8), 1.45, 0.7, facecolor="#a9dfbf", edgecolor="#1e8449", lw=1.2, zorder=3)
        ax2.add_patch(fold)
        ax2.text(1.2 + i * 1.52 + 0.725, 7.15, f"Fold {i+1}", ha="center", va="center", fontsize=8, weight="bold")
    ax2.text(5, 6.2, "Model selection & hyperparameter tuning via 5-Fold CV (0 rows wasted)", ha="center", va="center", fontsize=8.5, color="#196f3d", style="italic")
    
    # External Test Box
    ext_box = plt.Rectangle((1, 1.2), 8, 4.2, facecolor="#fef9e7", edgecolor="#f39c12", lw=2, zorder=2)
    ax2.add_patch(ext_box)
    ax2.text(5, 4.8, "[Independent External Evaluation]", ha="center", va="center", weight="bold", color="#d35400", fontsize=10)
    reasons_right = (
        "• Novel listing IDs (N=392) from a separate crawler JSON.\n"
        "• Zero Overlap: All 857 previously seen listings strictly filtered out.\n"
        "• A time-heterogeneous comparison; crawl and reservation\n  conditions may differ from historical records."
    )
    ax2.text(1.5, 3.0, reasons_right, ha="left", va="center", fontsize=9.5, linespacing=1.6, color="#2c3e50")
    
    plt.tight_layout()
    fig.savefig(FIG_DIR / "fig1_validation_architecture.png")
    plt.close(fig)
    print("Saved fig1_validation_architecture.png")

def fig2_price_distribution_outliers():
    """Figure 2: Log Price Distribution, 3xIQR Fences, and PRICE_UNIT_ERROR Invisibility."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT listing_id, nightly_price_usd, ln_nightly_price_usd, is_price_outlier,
               prior_suspected_price_error, is_in_modeling_population
        FROM LISTING_MODEL_FEATURES
    """, conn)
    conn.close()
    
    df["nightly_price_usd"] = pd.to_numeric(df["nightly_price_usd"], errors="coerce")
    df["ln_nightly_price_usd"] = pd.to_numeric(df["ln_nightly_price_usd"], errors="coerce")
    valid = df.dropna(subset=["ln_nightly_price_usd"]).copy()
    
    q1 = valid["ln_nightly_price_usd"].quantile(0.25)
    q3 = valid["ln_nightly_price_usd"].quantile(0.75)
    iqr = q3 - q1
    lower_fence = q1 - 3 * iqr
    upper_fence = q3 + 3 * iqr
    lower_usd = np.exp(lower_fence)
    upper_usd = np.exp(upper_fence)
    
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    
    # Subplot A: Histogram of Log Price
    ax1 = axes[0]
    sns.histplot(valid["ln_nightly_price_usd"], kde=True, ax=ax1, color="#3498db", bins=35, alpha=0.6)
    ax1.axvline(lower_fence, color="#e74c3c", ls="--", lw=2, label=f"Lower 3×IQR Fence (ln={lower_fence:.2f}, ${lower_usd:.2f})")
    ax1.axvline(upper_fence, color="#e74c3c", ls="--", lw=2, label=f"Upper 3×IQR Fence (ln={upper_fence:.2f}, ${upper_usd:,.0f})")
    ax1.axvspan(lower_fence, upper_fence, color="#2ecc71", alpha=0.08, label="Accepted Range (99.95%)")
    
    # Highlight domain-registered errors separately from the statistical flag.
    pue = valid[valid["prior_suspected_price_error"] == 1]
    pue_inside = pue[(pue["ln_nightly_price_usd"] >= lower_fence) & (pue["ln_nightly_price_usd"] <= upper_fence)]
    ax1.scatter(pue["ln_nightly_price_usd"], [5] * len(pue), color="#e67e22", s=70, zorder=5,
                edgecolor="black", label=f"PRICE_UNIT_ERROR (N={len(pue)}; inside fence={len(pue_inside)})")
    
    ax1.set_title("A. Log Price Distribution & 3×IQR Fences", pad=12)
    ax1.set_xlabel("Natural Log Nightly Price (ln USD)")
    ax1.set_ylabel("Listing Count")
    ax1.legend(loc="upper left", frameon=True, fontsize=8.5)
    
    # Subplot B: Scatter/Strip plot of Nightly Price (USD) showing the paradox
    ax2 = axes[1]
    
    # Normal listings, PUE listings, and 3xIQR outlier
    normal = valid[(valid["prior_suspected_price_error"] == 0) & (valid["is_price_outlier"] == 0)]
    stat_outliers = valid[valid["is_price_outlier"] == 1]
    
    np.random.seed(42)
    jitter_normal = np.random.normal(1, 0.08, size=len(normal))
    jitter_pue = np.random.normal(2, 0.08, size=len(pue))
    jitter_out = np.random.normal(3, 0.08, size=len(stat_outliers))
    
    ax2.scatter(jitter_normal, normal["nightly_price_usd"], alpha=0.25, color="#95a5a6", s=15, label=f"Other records (N={len(normal)})")
    ax2.scatter(jitter_pue, pue["nightly_price_usd"], color="#e67e22", s=80, edgecolor="black", zorder=5, label=f"PRICE_UNIT_ERROR (N={len(pue)})")
    ax2.scatter(jitter_out, stat_outliers["nightly_price_usd"], color="#c0392b", marker="X", s=120, zorder=6, label=f"3×IQR statistical flag (N={len(stat_outliers)})")
    
    ax2.axhline(lower_usd, color="#e74c3c", ls="--", lw=1.5, alpha=0.8)
    ax2.axhline(upper_usd, color="#e74c3c", ls="--", lw=1.5, alpha=0.8)
    ax2.set_yscale("log")
    ax2.set_xticks([1, 2, 3])
    ax2.set_xticklabels(["Valid Records", "Unit Error Records\n(Domain Error)", "3×IQR Outliers\n(Statistical Error)"])
    ax2.set_title("B. Domain Error Register and Statistical Flag", pad=12)
    ax2.set_ylabel("Nightly Price (USD, Log Scale)")
    ax2.legend(loc="upper right", frameon=True, fontsize=8.5)
    
    ax2.annotate(f"{len(pue_inside)} registered errors are inside\nthe 3×IQR fence; the rules are complementary.",
                 xy=(2, np.median(pue["nightly_price_usd"])), xytext=(2.15, lower_usd * 8),
                 arrowprops=dict(facecolor="#d35400", shrink=0.08, width=1.5, headwidth=6),
                 fontsize=8.5, weight="bold", color="#d35400")
    
    plt.tight_layout()
    fig.savefig(FIG_DIR / "fig2_price_distribution_outliers.png")
    plt.close(fig)
    print("Saved fig2_price_distribution_outliers.png")

def fig3_seoul_spatial_clusters():
    """Figure 3: Projected Coordinates (x_km, y_km) and K=5 Spatial Clusters."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT listing_id, x_km, y_km, cluster_id, district, nightly_price_usd
        FROM LISTING_MODEL_FEATURES
        WHERE is_in_modeling_population = 1
    """, conn)
    cluster_labels = pd.read_sql_query("""
        SELECT cluster_id, cluster_name_en
        FROM LOCATION_CLUSTER WHERE cluster_count=5 ORDER BY cluster_id
    """, conn)
    conn.close()
    cluster_names = dict(zip(cluster_labels.cluster_id.astype(str), cluster_labels.cluster_name_en))
    df["cluster_name"] = df["cluster_id"].astype(str).map(cluster_names)
    
    fig, ax = plt.subplots(figsize=(10, 7))
    palette = sns.color_palette("Set1", n_colors=5)
    
    sns.scatterplot(
        data=df, x="x_km", y="y_km", hue="cluster_name",
        palette=palette, s=35, alpha=0.75, ax=ax, edgecolor="w", linewidth=0.3
    )
    
    ax.set_title("Seoul Airbnb Spatial Distribution & Existing K=5 Clusters (EPSG:5179)", pad=15)
    ax.set_xlabel("Projected Easting (x_km)")
    ax.set_ylabel("Projected Northing (y_km)")
    ax.legend(title="Macro Spatial Cluster", frameon=True, loc="upper right", fontsize=9)
    
    # Add educational annotations
    ax.text(0.03, 0.05, 
            "How to read this representation\n"
            "• x_km and y_km are one projected location pair.\n"
            "• Cluster IDs are existing categorical spatial groups.\n"
            "• Their signals may overlap; this chart does not establish\n  either feature's independent contribution.",
            transform=ax.transAxes, fontsize=9, bbox=dict(boxstyle="round,pad=0.5", facecolor="#f8f9f9", edgecolor="#bdc3c7"))
    
    plt.tight_layout()
    fig.savefig(FIG_DIR / "fig3_seoul_spatial_clusters.png")
    plt.close(fig)
    print("Saved fig3_seoul_spatial_clusters.png")

def fig3b_seoul_cluster_map():
    """Draw existing K=5 assignments on public Seoul municipal boundaries."""
    assert SEOUL_BOUNDARY.exists(), f"Missing boundary source: {SEOUL_BOUNDARY}"
    conn = sqlite3.connect(DB_PATH)
    points = pd.read_sql_query("""
        SELECT x_km, y_km, cluster_id
        FROM LISTING_MODEL_FEATURES WHERE is_in_modeling_population=1
    """, conn)
    labels = pd.read_sql_query("""
        SELECT cluster_id, cluster_name_en FROM LOCATION_CLUSTER
        WHERE cluster_count=5 ORDER BY cluster_id
    """, conn)
    conn.close()
    points["cluster_id"] = points["cluster_id"].astype(int)
    with SEOUL_BOUNDARY.open(encoding="utf-8") as handle:
        boundary = json.load(handle)
    transformer = Transformer.from_crs("EPSG:5179", "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(points.x_km.to_numpy() * 1000, points.y_km.to_numpy() * 1000)
    points["longitude"], points["latitude"] = lon, lat
    palette = dict(zip(range(5), sns.color_palette("Set1", n_colors=5)))
    fig, ax = plt.subplots(figsize=(10, 10))
    for feature in boundary["features"]:
        geometry = feature["geometry"]
        polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
        for polygon in polygons:
            exterior = np.asarray(polygon[0])
            ax.fill(exterior[:, 0], exterior[:, 1], facecolor="#f4f5f6", edgecolor="#9aa0a6", linewidth=.55, zorder=1)
    for cluster_id, group in points.groupby("cluster_id"):
        ax.scatter(group.longitude, group.latitude, s=10, alpha=.45, color=palette[int(cluster_id)],
                   edgecolors="none", zorder=2)
    label_by_id = dict(zip(labels.cluster_id.astype(int), labels.cluster_name_en))
    handles=[Line2D([0],[0],marker="o",color="w",markerfacecolor=palette[i],markersize=8,
                    label=f"{i}: {label_by_id[i]} (n={(points.cluster_id == i).sum()})") for i in sorted(palette)]
    ax.legend(handles=handles, title="Existing K=5 cluster", loc="lower left", frameon=True, fontsize=9)
    ax.set_title("Seoul Airbnb Listings by Existing K=5 Spatial Cluster", pad=14)
    ax.set_xlabel("Longitude (WGS84)")
    ax.set_ylabel("Latitude (WGS84)")
    ax.set_aspect("equal", adjustable="box")
    ax.text(.99, .01, "Points: eligible historical listings; colors reproduce existing cluster_id.\nBoundaries: Seoul Maps / KOSTAT 2013 simplified GeoJSON.",
            transform=ax.transAxes, fontsize=8.2, va="bottom", ha="right", bbox=dict(boxstyle="round,pad=.4", facecolor="white", alpha=.9, edgecolor="#bdc3c7"))
    plt.tight_layout()
    fig.savefig(FIG_DIR / "fig3b_seoul_cluster_map.png")
    plt.close(fig)
    print("Saved fig3b_seoul_cluster_map.png")

def fig4_model_cv_performance():
    """Figure 4: 5-Fold Cross Validation Performance across Algorithms & Feature Sets."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT experiment_id, algorithm, feature_set_name, r2_mean, rmse_mean, mae_mean
        FROM PRICE_MODEL_EXPERIMENT
        WHERE experiment_id LIKE 'CORRECTED%' AND algorithm != 'MeanBaseline'
    """, conn)
    conn.close()
    
    best_df = df.groupby(["algorithm", "feature_set_name"]).agg({
        "r2_mean": "max",
        "rmse_mean": "min",
        "mae_mean": "min"
    }).reset_index()
    
    feature_order = ["core", "structure", "amenities", "coordinates"]
    best_df["feature_order"] = best_df["feature_set_name"].map(lambda x: feature_order.index(x) if x in feature_order else 99)
    best_df = best_df.sort_values("feature_order")
    
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    
    # Subplot A: R2 Score (%) Progression
    ax1 = axes[0]
    sns.barplot(
        data=best_df, x="feature_set_name", y="r2_mean", hue="algorithm",
        palette={"Ridge": "#95a5a6", "RandomForest": "#e67e22", "HistGradientBoosting": "#27ae60"},
        ax=ax1
    )
    ax1.set_ylim(0.5, 0.85)
    ax1.set_yticks([0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85])
    ax1.set_yticklabels([f"{int(y*100)}%" for y in [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85]])
    ax1.set_title("A. Cross-Validation Explanatory Power (CV R² in %)", pad=12)
    ax1.set_xlabel("Feature Set Progression")
    ax1.set_ylabel("CV R² Score (Higher is Better)")
    ax1.legend(title="Algorithm", frameon=True, fontsize=8.5)
    
    
    # Subplot B: RMSE (Log Error) Progression
    ax2 = axes[1]
    sns.barplot(
        data=best_df, x="feature_set_name", y="rmse_mean", hue="algorithm",
        palette={"Ridge": "#95a5a6", "RandomForest": "#e67e22", "HistGradientBoosting": "#27ae60"},
        ax=ax2
    )
    ax2.set_ylim(0.4, 0.7)
    ax2.set_title("B. Cross-Validation Error (CV RMSE in Log USD)", pad=12)
    ax2.set_xlabel("Feature Set Progression")
    ax2.set_ylabel("CV RMSE (Lower is Better)")
    ax2.legend(title="Algorithm", frameon=True, fontsize=8.5)
    
    
    plt.tight_layout()
    fig.savefig(FIG_DIR / "fig4_model_cv_performance.png")
    plt.close(fig)
    print("Saved fig4_model_cv_performance.png")

def fig5_external_residuals_and_gains():
    """Figure 5: External Test Residual Distribution & Relative Metric Gains."""
    conn = sqlite3.connect(DB_PATH)
    raw_audit = conn.execute("SELECT value_json FROM PRICE_MODEL_RUN_AUDIT WHERE audit_key='external_json_evaluation'").fetchone()[0]
    conn.close()
    audit_data = json.loads(raw_audit)
    
    base_preds = pd.DataFrame(audit_data["baseline_predictions"])
    corr_preds = pd.DataFrame(audit_data["corrected_predictions"])
    
    base_preds["residual_usd"] = base_preds["predicted_nightly_price_usd"] - base_preds["observed_nightly_price_usd"]
    corr_preds["residual_usd"] = corr_preds["predicted_nightly_price_usd"] - corr_preds["observed_nightly_price_usd"]
    
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    
    # Subplot A: Residual Distribution (KDE)
    ax1 = axes[0]
    sns.kdeplot(base_preds["residual_usd"], ax=ax1, color="#c0392b", lw=2, label="Baseline training population", fill=True, alpha=0.15)
    sns.kdeplot(corr_preds["residual_usd"], ax=ax1, color="#27ae60", lw=2.5, label="Corrected training population", fill=True, alpha=0.2)
    
    ax1.axvline(0, color="black", ls="--", lw=1.2, alpha=0.7)
    def signed_usd(value):
        return f"+${value:.2f}" if value >= 0 else f"−${abs(value):.2f}"
    ax1.axvline(base_preds["residual_usd"].mean(), color="#c0392b", ls=":", lw=1.5, label=f"Baseline Bias ({signed_usd(base_preds['residual_usd'].mean())})")
    ax1.axvline(corr_preds["residual_usd"].mean(), color="#27ae60", ls=":", lw=1.5, label=f"Corrected Bias ({signed_usd(corr_preds['residual_usd'].mean())})")
    
    ax1.set_xlim(-150, 150)
    ax1.set_title("A. Prediction Error Distribution on 392 Novel Listings", pad=12)
    ax1.set_xlabel("Prediction Error (Predicted − Actual Displayed USD)")
    ax1.set_ylabel("Density")
    ax1.legend(loc="upper right", frameon=True, fontsize=8.5)
    
    # Subplot B: observed metric differences; values are derived from current audit data.
    ax2 = axes[1]
    base_metrics = audit_data["baseline_metrics"]
    corrected_metrics = audit_data["corrected_metrics"]
    metrics = ["MAE (%)", "Median AE (%)", "RMSE (%)", "MAPE (pp)"]
    improvements = [
        100 * (corrected_metrics["mae_usd"] / base_metrics["mae_usd"] - 1),
        100 * (corrected_metrics["median_absolute_error_usd"] / base_metrics["median_absolute_error_usd"] - 1),
        100 * (corrected_metrics["rmse_usd"] / base_metrics["rmse_usd"] - 1),
        100 * (corrected_metrics["mape"] - base_metrics["mape"]),
    ]
    colors = ["#2ecc71", "#27ae60", "#1abc9c", "#16a085"]
    
    bars = ax2.barh(metrics, improvements, color=colors, edgecolor="black", height=0.55)
    ax2.set_xlim(-15, 2)
    ax2.axvline(0, color="black", lw=1)
    ax2.set_title("B. External-Test Metric Differences", pad=12)
    ax2.set_xlabel("Corrected minus baseline (negative means lower error)")
    
    for bar, label, val in zip(bars, metrics, improvements):
        unit = "pp" if "MAPE" in label else "%"
        ax2.text(val - 0.5, bar.get_y() + bar.get_height()/2, f"{val:.1f}{unit}",
                 ha="right", va="center", weight="bold", color="#145a32", fontsize=9.5)
        
    
    plt.tight_layout()
    fig.savefig(FIG_DIR / "fig5_external_residuals_and_gains.png")
    plt.close(fig)
    print("Saved fig5_external_residuals_and_gains.png")

if __name__ == "__main__":
    print("Generating educational figures in artifacts/figures/...")
    fig1_validation_architecture()
    fig2_price_distribution_outliers()
    fig3_seoul_spatial_clusters()
    fig3b_seoul_cluster_map()
    fig4_model_cv_performance()
    fig5_external_residuals_and_gains()
    print("All 5 figures generated successfully!")
