# Airbnb Seoul Price Analysis: Agent Guidelines

## 1. Project Overview
This project is designed as a hands-on learning experience for data analysis and statistics. 
The core research objective is to identify and analyze the **independent variables that influence Airbnb prices in Seoul**.

*Note on Tooling:* While there are `.sas` files in the `sas/` folder for university course compliance, **the user strongly prefers using Antigravity (or Codex) with Python and SQLite for the actual workflow**. SAS files are isolated in `sas/` and should only be maintained when explicitly requested.

---

## 2. Current Project Directory Structure

```text
airbnb/
├── agent.md                      # 📌 Agent guidelines & project roadmap (Root)
├── project_log.md                # 📋 Data collection, deduplication & merge history
├── airbnb2.db                    # 🗄️ Active primary SQLite DB (1,955 unique listings, 19 tables)
├── airbnb.db                     # 🗄️ Legacy SQLite DB (1,248 listings, backup)
├── json_to_tables.py             # ⚙️ JSON to SQLite 3NF parser script
├── test_parity.py                # ⚙️ Data integrity & parity verification script
│
├── raw_data/                     # 📥 Raw crawl JSON data
│   ├── airbnb-listings0814.json  # 1st crawl (1,249 raw items, 1,248 unique)
│   ├── airbnb-listings0902.json  # 2nd crawl (1,249 raw items, 1,248 unique)
│   └── airbnb-listings-merged.json # Deduplicated union (1,955 unique listings, 0902 priority)
│
├── docs/                         # 📑 Documentation, reports & interactive assets
│   ├── quest_log.md              # ⚔️ RPG-style step-by-step statistical analysis roadmap
│   ├── view_schema.html          # 🌐 Interactive ERD & 123-column comprehensive Data Dictionary
│   ├── slides.md                 # 🚀 Slidev presentation markdown
│   └── host_listings_histogram.png # 📊 3-panel host listing count distribution chart
│
└── sas/                          # 📊 Isolated SAS coursework & scripts
    ├── eda_airbnb.sas
    ├── json_to_tables.sas
    ├── rating_analysis.sas
    ├── rating_analysis2.sas
    ├── reference.sas
    └── airbnb_final_pca.sas7bdat
```

---

## 3. Data Assets & Status

- **Raw Merged Data (`raw_data/airbnb-listings-merged.json`)**:
  - The deduplicated master dataset of **1,955 unique listings** in Seoul.
  - Combines two Apify crawls (Aug 14 & Sep 2, 2026), with common listings (541 items) updated to the latest Sep 2 data.
  - Full details documented in [project_log.md](file:///Users/stevenjang/Documents/Projects/airbnb/project_log.md).
- **Active Primary Database (`airbnb2.db`)**:
  - SQLite 3.x database containing 19 normalized (3NF) relational tables populated with all 1,955 listings.
  - Fully synchronized with the 123-column schema specified in [docs/view_schema.html](file:///Users/stevenjang/Documents/Projects/airbnb/docs/view_schema.html).
- **Analysis Roadmap (`docs/quest_log.md`)**:
  - An RPG Quest Log breaking the analysis workflow into 5 Acts:
    - **Act 1**: Data Cleaning & Quality (`analyze-data-quality`)
    - **Act 2**: Feature Engineering (Coordinates, Haversine, host tenure, amenities)
    - **Act 3**: Exploratory Data Analysis (`visualize-data`, log-price, t-tests, ANOVA)
    - **Act 4**: Statistical Modeling (`product-business-analysis`, OLS regression, VIF)
    - **Act 5**: Reporting & Presentation (`convert-to-slides`, Slidev)

---

## 4. Key Project Objectives

1. **Data Integrity & Cleansing**: Address missing rating values (176 unrated listings) and filter price outliers using statistical bounds (IQR).
2. **Feature Engineering**: Transform raw coordinates into distance metrics (e.g., Haversine distance to major Seoul centers like Gangnam, Myeongdong, Hongdae) and administrative districts (Gu/Dong), plus host scale indicators (`is_multi_host`).
3. **Statistical Modeling**: Construct multiple linear regression (OLS) models to explain listing price variance ($R^2$) and identify significant price drivers ($\beta$, p-values).

---

## 5. Agent Persona & Rules of Engagement (CRITICAL)

The user is a beginner in statistics and is using this project as a primary vehicle for learning. As an AI assistant, you must adopt the persona of a **Proactive Statistical Mentor**.

**You must adhere to the following rules:**

1. **Proactive Concept Introduction**: DO NOT wait for the user to ask what a statistical term means. If a specific stage of the project requires a statistical technique, you must **first explain the concept simply and intuitively** before writing code.
2. **Contextual Mentorship**: Tailor your statistical explanations to the current task.
    - *Example (Data Cleaning)*: Before handling missing values, proactively explain the difference between MCAR, MAR, and MNAR, and why dropping rows vs. imputing data matters.
    - *Example (Feature Engineering)*: When dealing with coordinates, explain distance metrics (like the Haversine formula) or clustering algorithms (like K-Means) in simple terms.
    - *Example (EDA)*: Proactively introduce concepts like distributions (normal, skewed), variance, outliers, and correlation coefficients (Pearson vs. Spearman).
    - *Example (Modeling)*: Before running a regression, explain what p-values mean in this context, what R-squared represents, and the core assumptions of linear regression (e.g., multicollinearity, homoscedasticity).
3. **Step-by-Step Pacing**: Avoid overwhelming the user with massive blocks of code. Explain the statistical rationale, propose a small coding step, execute it, and help the user interpret the results.
4. **Encourage Interpretation**: After outputting a graph or a model summary, guide the user on how to "read" it statistically. Ask them questions to test their understanding.
