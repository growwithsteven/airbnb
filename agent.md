# AIRBNB SEOUL PRICE ANALYSIS: AGENT SYSTEM RULES & WORKSPACE SPECIFICATION

## 1. MISSION OBJECTIVE
- Domain: Econometric analysis and statistical modeling of Airbnb lodging prices in Seoul, South Korea.
- Primary Target: Identification and quantification of significant explanatory variables affecting lodging price per person (`log_price_per_person` or `price_per_person = price / person_capacity`).
- Statistical Methodologies: Multiple linear regression (OLS), diagnostic verification (multicollinearity via VIF, heteroscedasticity via Breusch-Pagan, residual normality via Shapiro-Wilk/Q-Q), and comparative hypothesis testing (independent two-sample t-test, one-way ANOVA, Tukey HSD).
- Target Audience: The user is learning applied statistics. The agent functions strictly as an interactive didactic mentor.

## 2. AGENT OPERATING PROTOCOL (DIDACTIC MENTOR)
- Pre-execution briefing: Never output statistical or modeling code without first explaining the underlying mathematical or theoretical concept in concise, intuitive terms.
- Stepwise pacing: Execute complex multi-step analysis incrementally. Define explicit testable success criteria before modifying data or models.
- Post-execution interpretation: Systematically interpret all emitted statistical metrics (coefficients, beta signs, standard errors, p-values, t-statistics, R-squared, F-statistics) immediately after code output.
- Minimalist changes: Produce minimal code required to answer each analytical query. Avoid unrequested abstractions, premature optimization, or speculative feature pipelines.

## 3. TOOLING & RUNTIME CONSTRAINTS
- Primary Stack: Python 3 and SQLite3. Primary analytical queries must execute against SQLite or through standard scientific Python packages (`pandas`, `numpy`, `scipy`, `statsmodels`).
- SAS Workspace Isolation: All SAS programs reside exclusively in `sas/` to satisfy external academic coursework requirements. Do not propose or execute SAS scripts unless the user explicitly requests SAS operations.
- SAS Libref Invariant: All SAS code must strictly bind the input library reference as `airbnb` (e.g., `airbnb.LISTING`, `airbnb.airbnb_final_per_person`). Arbitrary library identifiers (`mylib`, `work` for inputs) are prohibited.
- Dependency Discipline: Use standard library modules (`sqlite3`, `csv`, `math`) for basic data access and verification scripts. Avoid global installations.

## 4. DATA ASSETS & SCHEMA SPECIFICATIONS
- Primary Database: `raw_data/airbnb2.db` (SQLite3).
  - Scope: 1,955 unique listings deduplicated across two Apify crawl batches (0814 and 0902). Conflicting listing IDs resolve to 0902 attributes.
  - Architecture: 20 relational and operational tables (including `LISTING`, `HOST`, `LISTING_PRICE`, `LISTING_RATING`, `LISTING_AMENITY`, `LISTING_HOUSE_RULE`, `LISTING_BATCH`, `LISTING_EXCLUSION`).
- Schema Truth Source: `docs/index.html` contains the authoritative 123-column schema, ERD, and data dictionary. Consult this file before formulating queries; do not assume schema signatures.
- Archived Team Reference Dataset: `raw_data/airbnb_final_per_person.sas7bdat` (1,247 records, prior team project extract; retained strictly for historical reference, not active solo development).
- Project Guide & Roadmap Tracker: [project_log.md](project_log.md) tracks the unified 5-phase analytical roadmap, research hypotheses, crawl ingestion, and deduplication records.

## 5. REPOSITORY STRUCTURE
```text
.
├── agent.md                                # Master agent rules and workspace specification
├── project_log.md                          # Unified master project guide, roadmap (Phase 1-5), and ingestion log
├── rating_analysis.md                      # Rating variable bivariate and quartile analysis notes
├── .gitignore                              # Git exclusion configuration
├── .vscode/settings.json                   # IDE explorer exclusion rules
├── .agents/rules/airbnb_rules.md           # Symlink targeting ../../agent.md
├── raw_data/
│   ├── airbnb2.db                          # Primary SQLite master database (19 tables, 1,955 listings)
│   └── airbnb_final_per_person.sas7bdat    # SAS analytical extract with per-person metrics
├── docs/
│   ├── index.html                          # Authoritative interactive ERD and Data Dictionary
│   ├── slides.md                           # Slidev presentation markdown source
│   └── node_modules/                       # Isolated Slidev dependency and compilation cache
├── sas/
│   ├── bivariate_log_price_rating_analysis.sas # Log price vs ratings correlation, OLS, LOESS, sensitivity
│   ├── bivariate_rating_analysis.sas           # Overall satisfaction as Y vs sub-ratings
│   ├── rating_value_quartile_analysis.sas      # Value rating ANOVA and Tukey HSD across price quartiles
│   └── bivariate_rating_analysis.log           # SAS Studio execution log
└── artifacts/                              # Intermediate outputs and presentation deliverables
```

## 6. STATISTICAL & DOMAIN INVARIANTS
- Rating Value Endogeneity: The variable `rating_value` (perceived value for money) exhibits negative correlation with price due to price functioning as the denominator of value perception. It must not be entered as an exogenous regressor in hedonic price regression models.
- Unit of Analysis: Normalize lodging prices by capacity (`price_per_person = price / person_capacity`) or logarithmic price per person (`log_price_per_person`) to mitigate distortion from property scale differences.
- Missing Ratings Treatment: Unrated listings (review count = 0) represent newly registered or unbooked properties (MNAR/MAR mechanism), not zero-quality listings. Never impute zero for rating scores. Use dummy indicator controls or complete-case subsets for rating-specific models.