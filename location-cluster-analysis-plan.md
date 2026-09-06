# Location Cluster Analysis Plan & Results Report: Seoul Airbnb Listings

## 1. Research Purpose & Analytical Framework

The primary purpose of this analysis is to construct **location-only spatial clusters** for Airbnb listings located in Seoul using K-Means clustering, and subsequently assess whether these geographic clusters exhibit meaningful **price differentiation by cluster** across two standardized price outcomes.

Specifically, the workflow is organized into two sequential stages:
1. **Unsupervised Spatial Partitioning**: Partition listings strictly on physical geography (projected coordinates in meters) without introducing any pricing, listing specification, host, or administrative boundary data.
2. **Post-Hoc Price Association Assessment**: Evaluate whether the derived spatial clusters capture systematic price variation across listings, serving as a secondary validation of geographic market segmentation.

---

## 2. Analysis Population & Boundary Criteria

- **Target Population**: Seoul Airbnb listings exclusively.
- **Inclusion Filter**: Only listings where `LISTING_GEOGRAPHY.is_in_seoul = 1` are included.
- **Exclusion Filter**: All listings outside Seoul (`is_in_seoul = 0` or missing) are strictly excluded.
- **Population Size & Integrity**: Exactly 1,920 listings meet this criterion in `raw_data/airbnb2.db`. Prior to modeling, the pipeline validates that all 1,920 listings possess complete, non-null latitude and longitude coordinates within valid bounds.

---

## 3. Clustering Input Variables & Exclusions

- **Input Features**: Exclusively `LISTING.latitude` and `LISTING.longitude` (transformed to projected planar meters).
- **Strict Exclusions from Clustering**:
  - No price outcomes or financial variables (`nightly_price_usd`, `total_stay_price_usd`, etc.).
  - No physical capacity or property attributes (`person_capacity`, `room_type`, `property_type`, bedrooms, bathrooms).
  - No amenities, ratings, reviews, or host characteristics.
  - No administrative boundary labels (e.g., `sigungu_name`, `sido_name`) or external neighborhood proxies.

*Rationale*: Clustering must reflect purely empirical spatial density and proximity patterns. Incorporating non-spatial attributes would confound spatial separation with property tiers or host behaviors, destroying the geographic integrity of the clusters.

---

## 4. Coordinate Transformation: WGS84 to EPSG:5179

### Why Raw Degrees Must Not Be Used Directly in Euclidean K-Means
Raw geographic coordinates (`latitude` and `longitude` in WGS84 / EPSG:4326) are angular measurements expressed in spherical degrees, not linear metric distances.

Using raw spherical degrees directly in Euclidean-distance K-Means introduces severe geometric distortion:
1. **Latitude vs. Longitude Anisotropy**: At Seoul's latitude (~37.55°N), 1 degree of latitude spans approximately 111.0 km, whereas 1 degree of longitude spans approximately $111.0 \times \cos(37.55^\circ) \approx 88.0\text{ km}$. Consequently, 1 longitudinal degree represents only ~79.3% of the physical ground distance of 1 latitudinal degree.
2. **Distortion of Distance Metrics**: Standard Euclidean distance ($\sqrt{\Delta \text{lat}^2 + \Delta \text{lon}^2}$) would treat $0.01^\circ$ longitude identically to $0.01^\circ$ latitude, effectively stretching clusters along the north-south axis and artificially penalizing east-west proximity.
3. **Requirement for Planar Equidistance**: For K-Means to partition points based on true physical Euclidean distance, coordinates must be projected onto a conformal, metric planar coordinate reference system.

### Projected Coordinate Reference System
- **Selected CRS**: **EPSG:5179** (Korea 2000 / Unified CS).
- **Properties**: Transverse Mercator projection based on the GRS80 ellipsoid, central meridian 127.5°E, origin latitude 38.0°N, false easting 1,000,000 m, false northing 2,000,000 m.
- **Unit**: Meters ($m$). In this metric space, spatial distances and cluster centroids represent true physical meters across the Seoul metropolitan area.

---

## 5. Candidate Cluster Counts & Evaluation Criteria

### Candidate Cluster Configurations
- Candidate values of $k$: **$k = 3$ through $k = 10$**.
- Initialization and Reproducibility: K-Means algorithm executed with `random_state = 42` and `n_init = 50` to guarantee robust global convergence away from local minima.

### Spatial Clustering Quality Criteria
1. **Inertia (Within-Cluster Sum of Squares)**: Measures cluster compactness; examined via the elbow heuristic.
2. **Silhouette Score**: Evaluates cluster cohesion against cluster separation (using Euclidean metric on projected meters).
3. **Minimum and Maximum Cluster Size**: Verifies cluster balance and guards against degenerate micro-clusters (e.g., clusters with too few observations to serve as valid statistical segments).
4. **Geographic Interpretability & Spatial Stability**: Ensures boundaries form contiguous, coherent urban submarkets (e.g., Gangnam/Seocho, Hongdae/Mapo, Jongno/Jung-gu, Yongsan/Itaewon, etc.) without erratic spatial fragmentation.

---

## 6. Price-Association Assessment (Secondary Validation)

### Methodological Distinction: Price Association vs. Correlation
Because cluster membership is a nominal/categorical variable with $k$ discrete groups, assessing its relationship with continuous price outcomes cannot be represented as a bivariate Pearson correlation.

Instead, the relationship must be evaluated as **price association** or **price differentiation by cluster**. This is assessed through:
- **One-Way Analysis of Variance (ANOVA) / Categorical OLS Regression**: Regressing each log price outcome on categorical cluster indicators.
- **Cluster Effect Size ($\eta^2$, Eta-Squared)**: The proportion of total log price variance accounted for by between-cluster differences:
  $$\eta^2 = \frac{SS_{\text{between}}}{SS_{\text{total}}}$$
- **Adjusted $R^2$**: Goodness-of-fit accounting for model degrees of freedom ($k - 1$).
- **5-Fold Cross-Validated Prediction Metrics (MAE & RMSE)**: Out-of-sample predictive error under a reproducible 5-fold cross-validation scheme (`random_state = 42`), assessing whether cluster price baselines generalize without severe overfitting.

### The Two Primary Outcome Variables
Both outcomes are sourced from `LISTING_PRICE_DERIVED`:
1. `LISTING_PRICE_DERIVED.ln_nightly_price_usd`: Natural logarithm of the nightly listing rate in USD.
2. `LISTING_PRICE_DERIVED.ln_nightly_price_per_capacity_usd`: Natural logarithm of the nightly listing rate divided by maximum listed person capacity (`LISTING.person_capacity`).

> [!IMPORTANT]
> **Capacity Normalization Caveat**: The second outcome metric represents nightly price divided by the *maximum listed capacity* of the accommodation, **not** the price paid by an actual booked party or actual guest count. It serves as a scale-standardized proxy of unit value.

---

## 7. Model Selection Principles & Governance

1. **Price Association as Secondary Validation**: Price differentiation by cluster is strictly a secondary validation criterion. A candidate $k$ must **not** be chosen solely because it achieves the highest in-sample adjusted $R^2$ or $\eta^2$. Over-partitioning space will mechanically inflate in-sample $R^2$ while degrading spatial interpretability and creating brittle micro-clusters.
2. **Holistic Joint Selection**: The final $k$ will be chosen by jointly evaluating spatial clustering quality (silhouette score, inertia curvature, minimum cluster size, spatial contiguity) and price differentiation across both price outcomes (out-of-sample CV MAE/RMSE and effect sizes).
3. **Parsimony Rule**: When performance metrics between candidate $k$ values are comparable or yield diminishing returns, the smallest interpretable $k$ is strongly preferred to maintain analytical parsimony and practical interpretability.
4. **Decoupled Decision Gate**: The analysis script records candidate metrics objectively across $k \in [3, 10]$ in the database and highlights prominent candidates without automatically declaring a final $k$, leaving the final selection open for research review.

---

## 8. Database Architecture & Data Dictionary Integration

All derived tables are created in `/Users/stevenjang/Documents/Projects/airbnb/raw_data/airbnb2.db`. Existing tables are strictly preserved.

### Derived Tables:
1. `LISTING_LOCATION_COORDINATES`:
   - `listing_id` (TEXT, PK, FK -> LISTING.id)
   - `source_latitude` (REAL)
   - `source_longitude` (REAL)
   - `x_epsg5179_m` (REAL)
   - `y_epsg5179_m` (REAL)
   - `coordinate_reference_system` (TEXT)
   - `analysis_population` (TEXT)

2. `LISTING_LOCATION_CLUSTER_CANDIDATE`:
   - `listing_id` (TEXT, FK -> LISTING.id)
   - `k` (INTEGER)
   - `cluster_id` (INTEGER)
   - `centroid_x_epsg5179_m` (REAL)
   - `centroid_y_epsg5179_m` (REAL)
   - `distance_to_centroid_m` (REAL)
   - `random_state` (INTEGER)
   - `n_init` (INTEGER)
   - `PRIMARY KEY (k, listing_id)`

3. `LOCATION_CLUSTER_EVALUATION`:
   - `k` (INTEGER)
   - `outcome_name` (TEXT)
   - `n_listings` (INTEGER)
   - `inertia` (REAL)
   - `silhouette_score` (REAL)
   - `minimum_cluster_size` (INTEGER)
   - `maximum_cluster_size` (INTEGER)
   - `adjusted_r_squared` (REAL)
   - `cluster_eta_squared` (REAL)
   - `cross_validated_mae` (REAL)
   - `cross_validated_rmse` (REAL)
   - `random_state` (INTEGER)
   - `n_init` (INTEGER)
   - `method_notes` (TEXT)
   - `calculated_at` (TEXT)
   - `PRIMARY KEY (k, outcome_name)`

All three tables and all their attributes are registered in `DATA_DICTIONARY` in alignment with the repository's metadata catalog standard. Idempotency is enforced through transactional replacement of derived rows. Integrity checks (`PRAGMA foreign_key_check` and `PRAGMA quick_check`) run upon completion.

---

## 9. Empirical Results & Findings Report

### 9.1 Data Processing & Pipeline Verification
The analysis was executed against `/Users/stevenjang/Documents/Projects/airbnb/raw_data/airbnb2.db` via `run_location_cluster_analysis.py`.
- **Validation**: All 1,920 Seoul listings passed non-null coordinate integrity and bounded range checks (Latitude: 37.4663°N to 37.6928°N; Longitude: 126.8112°E to 127.1426°E).
- **Transformation**: Projected coordinates were computed using EPSG:5179 ($X \in [939227, 968434]\text{ m}$; $Y \in [1940984, 1966023]\text{ m}$) and committed to `LISTING_LOCATION_COORDINATES`.
- **Reproducibility**: K-Means clustering was executed across $k \in [3, 10]$ with `random_state = 42` and `n_init = 50`. A total of 15,360 candidate cluster assignments were stored in `LISTING_LOCATION_CLUSTER_CANDIDATE`.
- **Integrity**: Post-execution `PRAGMA foreign_key_check` and `PRAGMA quick_check` returned 0 violations and `'ok'`.

---

### 9.2 Complete Candidate Evaluation Table ($k = 3 \dots 10$)

The table below reports spatial geometric quality and categorical price differentiation across both target outcomes:
- **$Y_1$**: `ln_nightly_price_usd` (Raw nightly rate in log USD)
- **$Y_2$**: `ln_nightly_price_per_capacity_usd` (Capacity-normalized nightly rate in log USD)

| $k$ | Spatial Inertia ($m^2$) | Silhouette Score | Min Size | Max Size | $R^2_{\text{adj}}(Y_1)$ | $\eta^2(Y_1)$ | 5-Fold CV MAE ($Y_1$) | 5-Fold CV RMSE ($Y_1$) | $R^2_{\text{adj}}(Y_2)$ | $\eta^2(Y_2)$ | 5-Fold CV MAE ($Y_2$) | 5-Fold CV RMSE ($Y_2$) |
|:---:|:-----------------------:|:----------------:|:--------:|:--------:|:-----------------------:|:-------------:|:---------------------:|:----------------------:|:-----------------------:|:-------------:|:---------------------:|:----------------------:|
| **3** | $2.088 \times 10^{10}$ | 0.5222 | 219 | 1,071 | 0.0385 | 0.0395 | 0.8775 | 1.0620 | 0.0659 | 0.0669 | 0.5066 | 0.7098 |
| **4** | $1.591 \times 10^{10}$ | 0.5188 | 180 | 1,055 | 0.1071 | 0.1085 | 0.8221 | 1.0246 | 0.0762 | 0.0777 | 0.5037 | 0.7060 |
| **5** | $1.237 \times 10^{10}$ | **0.5246** | 124 | 946 | 0.1339 | 0.1357 | 0.8039 | 1.0100 | 0.0893 | 0.0912 | 0.4972 | 0.7010 |
| **6** | $1.069 \times 10^{10}$ | 0.4314 | 92 | 691 | 0.1487 | 0.1509 | 0.7897 | 1.0021 | **0.1095** | 0.1118 | **0.4879** | **0.6937** |
| **7** | $9.291 \times 10^{9}$ | 0.4638 | 59 | 435 | 0.1627 | 0.1653 | 0.7730 | 0.9935 | 0.1055 | 0.1083 | 0.4879 | 0.6959 |
| **8** | $7.962 \times 10^{9}$ | 0.4623 | 59 | 431 | 0.1597 | 0.1628 | 0.7758 | 0.9959 | 0.1087 | 0.1120 | 0.4866 | 0.6947 |
| **9** | $6.754 \times 10^{9}$ | 0.4687 | 59 | 415 | 0.1592 | 0.1627 | 0.7742 | 0.9960 | 0.1104 | 0.1141 | 0.4856 | 0.6941 |
| **10** | $5.938 \times 10^{9}$ | 0.4859 | 30 | 407 | 0.1650 | 0.1689 | 0.7718 | 0.9935 | 0.1127 | 0.1168 | 0.4861 | 0.6945 |

---

### 9.3 In-Depth Methodological Interpretation

#### 1. Spatial Geometry and Clustering Cohesion
- **Silhouette Coefficient Dynamics**: Silhouette scores peak in the lower $k$ range ($k \in [3, 5]$) at $\approx 0.52$. The global maximum occurs at **$k = 5$ (0.5246)**, indicating that partitioning Seoul into 5 primary urban sectors optimizes within-cluster tightness relative to nearest-neighbor cluster separation.
- **Micro-Partitioning and Instability ($k \ge 7$)**: Starting at $k = 7$, the minimum cluster size drops sharply to 59 observations, and reaches 30 observations at $k = 10$. These small clusters represent fragmented fringe enclaves rather than meaningful macro-markets, introducing instability without substantive geometric gain.

#### 2. Price Differentiation by Cluster (Secondary Validation)
- **Sharp Inflection Point ($k = 3 \to 4 \to 5$)**:
  - Partitioning Seoul into only 3 clusters ($k = 3$) fails to separate price regimes, yielding a negligible $R^2_{\text{adj}}$ of 0.0385 on $Y_1$.
  - Increasing to $k = 4$ nearly triples the explanatory power ($R^2_{\text{adj}} = 0.1071$), and $k = 5$ further advances it to $0.1339$.
- **Diminishing Returns on Generalization Error ($k \ge 6$)**:
  - In-sample $R^2_{\text{adj}}$ continues to increase gradually up to $k = 10$ ($0.1650$ for $Y_1$). However, this is largely a mechanical artifact of adding parameters.
  - The 5-fold cross-validated generalization metrics (CV MAE and RMSE) demonstrate severe diminishing returns: CV MAE for $Y_1$ levels off around $0.77 \sim 0.79$, while for $Y_2$ it remains essentially flat at $0.486 \sim 0.488$ across all $k \ge 6$.

#### 3. Comparison of Outcome Variables ($Y_1$ vs. $Y_2$)
- **Confounding in $Y_1$**: $Y_1$ (`ln_nightly_price_usd`) exhibits higher raw $R^2_{\text{adj}}$ because it conflates geographic location with property physical size (e.g., higher guest capacity villas in Mapo/Jongno versus 1-person studios in Gangnam).
- **Purity and Precision in $Y_2$**: $Y_2$ (`ln_nightly_price_per_capacity_usd`) controls for capacity scaling. Consequently:
  - Cross-validated prediction error is reduced by over 38% compared to $Y_1$ (CV MAE $\approx 0.49$ vs. $0.80$; CV RMSE $\approx 0.70$ vs. $1.01$).
  - $Y_2$ isolates pure location premiums (effective price per person-night), making it the theoretically sound dependent variable for subsequent hedonic regression modeling.

---

### 9.4 Spatial Characterization of Key Candidate Configurations

#### Candidate A: $k = 4$ (Macro Quadrant Partition)
- **Cluster Structure**:
  1. *Southeast (Gangnam/Seocho/Songpa)*: $N = 209$ | Geometric Mean Price: \$154.5 | Per-Capita: \$45.6
  2. *Downtown / North Central (Jongno/Jung-gu/Yongsan/Seongbuk)*: $N = 1,055$ | Geometric Mean Price: \$306.9 | Per-Capita: \$81.7
  3. *Northwest (Mapo/Seodaemun/Eunpyeong)*: $N = 476$ | Geometric Mean Price: \$284.1 | Per-Capita: \$67.9
  4. *Southwest (Yeouido/Dongjak/Guro/Gwanak)*: $N = 180$ | Geometric Mean Price: \$107.5 | Per-Capita: \$31.9
- **Assessment**: Highly parsimonious (3 degrees of freedom) with robust cluster sizes ($\ge 180$), but lumps lower-cost Northeast outer districts into the high-priced Downtown cluster.

#### Candidate B: $k = 5$ (Optimal Cohesion & Balance — Recommended)
- **Cluster Structure**:
  1. *Downtown Core (Jongno/Jung-gu/Yongsan/Seongdong)*: $N = 946$ | Per-Capita Geometric Mean: \$89.8
  2. *Northwest Submarket (Mapo/Seodaemun)*: $N = 461$ | Per-Capita Geometric Mean: \$67.5
  3. *Southeast Submarket (Gangnam/Seocho/Songpa)*: $N = 209$ | Per-Capita Geometric Mean: \$45.6
  4. *Southwest Submarket (Yeouido/Dongjak/Guro)*: $N = 180$ | Per-Capita Geometric Mean: \$31.9
  5. *Northeast Outer Submarket (Nowon/Dobong/Gangbuk/Jungnang)*: $N = 124$ | Per-Capita Geometric Mean: \$37.7
- **Assessment**: **Global maximum silhouette score (0.5246)**. Successfully disentangles the low-priced Northeast outer districts ($N = 124$) from the historic Downtown core, providing well-balanced sample sizes and clean geographic contiguity.

#### Candidate C: $k = 6$ (Premium Submarket Isolation)
- **Cluster Structure**: Similar to $k = 5$, but further bisects the Downtown core into:
  - *Historic Downtown (Jongno/Jung-gu/Dongdaemun)*: $N = 691$ | Per-Capita Geometric Mean: \$67.7
  - *Yongsan/Itaewon/Hannam*: $N = 314$ | Per-Capita Geometric Mean: **\$121.7** (Highest in Seoul)
- **Assessment**: Captures the distinct high-end character of the Yongsan corridor, driving $Y_2$ $R^2_{\text{adj}}$ to its local peak of $10.95\%$. However, spatial silhouette drops to 0.4314 due to overlapping urban boundaries between Jung-gu and Yongsan.

---

### 9.5 Strategic Recommendation for Downstream Modeling

1. **Primary Cluster Choice**: **$k = 5$ paired with $Y_2$ (`ln_nightly_price_per_capacity_usd`)**.
   - Maximizes geometric compactness and cluster boundary clarity (Silhouette $= 0.5246$).
   - Avoids micro-clusters (smallest cluster has 124 listings).
   - Accurately captures major Seoul macroeconomic submarkets while consuming only 4 degrees of freedom in subsequent multivariate hedonic regression models.
2. **Alternative Consideration ($k = 6$)**:
   - Recommended only if separating the high-end Yongsan accommodation cluster from the Jongno/Jung-gu tourism hub is deemed essential for the specific qualitative policy or business narrative.
