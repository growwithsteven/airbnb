"""
청결도-가격 미니멀 산점도 시각화 생성 스크립트
1. 그래프 제목 완전 삭제
2. 그래프 내부 범례 완전 삭제
3. 축 서식에서 괄호 내용 삭제 (청결도 평점, 1박 가격)
"""

import os
import sqlite3
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

# 스타일 및 한글 폰트 설정
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({
    "font.family": "Apple SD Gothic Neo",
    "font.size": 11,
    "axes.labelsize": 11,
    "axes.labelweight": "bold",
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.dpi": 300,
    "savefig.bbox": "tight",
    "axes.unicode_minus": False
})

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "raw_data/airbnb2.db"
DOCS_PUBLIC = ROOT / "docs/public"
DOCS_PUBLIC.mkdir(parents=True, exist_ok=True)


def load_data():
    query = """
    SELECT 
        l.id AS listing_id,
        l.room_type,
        r.cleanliness,
        p.nightly_price_usd,
        p.ln_nightly_price_usd
    FROM LISTING l
    JOIN LISTING_BATCH b ON l.id = b.listing_id
    LEFT JOIN LISTING_EXCLUSION e 
        ON l.id = e.listing_id AND e.exclusion_category = 'PRICE_UNIT_ERROR'
    JOIN LISTING_PRICE_DERIVED p ON l.id = p.listing_id
    JOIN LISTING_RATING r ON l.id = r.listing_id
    WHERE b.is_original = 1 
      AND e.listing_id IS NULL
      AND r.cleanliness IS NOT NULL;
    """
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql(query, conn)
    return df


def main():
    df = load_data()
    plot_types = ["Entire home/apt", "Private room", "Shared room"]
    df_sub = df[df["room_type"].isin(plot_types)].copy()

    # 모델 적합
    model1 = smf.ols("ln_nightly_price_usd ~ cleanliness", data=df_sub).fit()
    model2 = smf.ols('ln_nightly_price_usd ~ cleanliness + C(room_type, Treatment(reference="Entire home/apt"))', data=df_sub).fit()

    palette = {
        "Entire home/apt": "#2b5c8f",   # 깊은 네이비
        "Private room": "#2e8b57",      # 에메랄드 그린
        "Shared room": "#d9534f"        # 코랄 레드
    }

    # 고정 시드로 지터링 생성 (두 차트의 점 위치 완전 일치)
    np.random.seed(42)
    df_sub["jitter_x"] = df_sub["cleanliness"] + np.random.normal(0, 0.015, len(df_sub))

    x_range = np.linspace(3.0, 5.0, 100)
    y_simple = model1.params["Intercept"] + model1.params["cleanliness"] * x_range
    b_clean = model2.params["cleanliness"]

    # =========================================================================
    # 차트 1: 전체 단순회귀선만 강조된 미니멀 차트 (제목 X, 범례 X, 괄호 X)
    # =========================================================================
    fig1, ax1 = plt.subplots(figsize=(6.5, 4.8))

    for t in plot_types:
        t_data = df_sub[df_sub["room_type"] == t]
        ax1.scatter(t_data["jitter_x"], t_data["ln_nightly_price_usd"],
                    color=palette[t], alpha=0.30, s=24, edgecolors="none")

    # 전체 단순회귀선 (검은 굵은 대시선)
    ax1.plot(x_range, y_simple, color="#111827", linestyle="--", linewidth=2.8)

    ax1.set_xlim(2.85, 5.15)
    ax1.set_ylim(2.5, 8.2)
    ax1.set_xlabel("청결도 평점")
    ax1.set_ylabel("1박 가격")

    chart1_path = DOCS_PUBLIC / "cleanliness_scatter_step1.png"
    fig1.savefig(chart1_path, dpi=300)
    plt.close(fig1)
    print(f"Chart 1 saved to {chart1_path}")

    # =========================================================================
    # 차트 2: 전체 선 회색/투명 처리 + 방 타입별 선 3개 오버레이 (제목 X, 범례 X, 괄호 X)
    # =========================================================================
    fig2, ax2 = plt.subplots(figsize=(6.5, 4.8))

    for t in plot_types:
        t_data = df_sub[df_sub["room_type"] == t]
        ax2.scatter(t_data["jitter_x"], t_data["ln_nightly_price_usd"],
                    color=palette[t], alpha=0.30, s=24, edgecolors="none")

    # 전체 단순회귀선: 옅은 회색, 반투명 점선 배경화
    ax2.plot(x_range, y_simple, color="#9ca3af", linestyle=":", linewidth=2.0, alpha=0.6)

    # 방 타입별 회귀선 3개 (실선)
    # Entire home
    y_entire = model2.params["Intercept"] + b_clean * x_range
    ax2.plot(x_range, y_entire, color=palette["Entire home/apt"], linestyle="-", linewidth=2.5)

    # Private room
    y_private = model2.params["Intercept"] + model2.params['C(room_type, Treatment(reference="Entire home/apt"))[T.Private room]'] + b_clean * x_range
    ax2.plot(x_range, y_private, color=palette["Private room"], linestyle="-", linewidth=2.5)

    # Shared room
    y_shared = model2.params["Intercept"] + model2.params['C(room_type, Treatment(reference="Entire home/apt"))[T.Shared room]'] + b_clean * x_range
    ax2.plot(x_range, y_shared, color=palette["Shared room"], linestyle="-", linewidth=2.5)

    ax2.set_xlim(2.85, 5.15)
    ax2.set_ylim(2.5, 8.2)
    ax2.set_xlabel("청결도 평점")
    ax2.set_ylabel("1박 가격")

    chart2_path = DOCS_PUBLIC / "cleanliness_scatter_step2.png"
    fig2.savefig(chart2_path, dpi=300)
    plt.close(fig2)
    print(f"Chart 2 saved to {chart2_path}")


if __name__ == "__main__":
    main()
