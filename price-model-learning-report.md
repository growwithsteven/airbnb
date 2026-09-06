# Seoul Airbnb price model — external JSON evaluation report

> **Final evaluation design:** There is no internal 80:20 holdout. Candidate and hyperparameter selection use five-fold shuffled cross-validation on each full historical training population (`random_state=42`). The primary final comparison uses the same novel listings from the supplied external crawler JSON.

## 1. Evaluation question

Does excluding the known `PRICE_UNIT_ERROR` records improve nightly-price predictions on newly crawled listings? The observed outcome is each JSON record's displayed nightly USD price. This is an external, time-heterogeneous test: the JSON was collected at a different time and reservation dates may differ, so it is not a perfectly contemporaneous benchmark.

## 2. Historical training populations and data-quality audit

| population | PRICE_UNIT_ERROR excluded | 3×IQR statistical outliers | additional 3×IQR exclusions | final training rows |
| --- | --- | --- | --- | --- |
| Baseline | 0 | 1 | 0 | 1919 |
| Corrected | 11 | 1 | 0 | 1909 |

The baseline intentionally reproduces the earlier population logic: it retains the known price-unit-error listings except any row removed by the prescribed 3×IQR rule. The corrected model excludes all 11 `LISTING_EXCLUSION` rows with `exclusion_category = PRICE_UNIT_ERROR` before applying the same log-price fence. The fence identified 1 row and added 0 exclusions beyond that register.

## 3. Predictors and model selection

| model | algorithm | feature set | training rows | input features |
| --- | --- | --- | --- | --- |
| Baseline (unresolved PRICE_UNIT_ERROR retained) | HistGradientBoosting | coordinates | 1919 | person_capacity, room_type, cluster_id, property_type, bedrooms, beds, bathrooms, amenity_count, has_kitchen, has_washer, has_dryer, has_workspace, has_elevator, has_free_parking, has_hot_tub, has_bathtub, has_self_check_in, has_private_entrance, x_km, y_km |
| Corrected (PRICE_UNIT_ERROR excluded) | HistGradientBoosting | coordinates | 1909 | person_capacity, room_type, cluster_id, property_type, bedrooms, beds, bathrooms, amenity_count, has_kitchen, has_washer, has_dryer, has_workspace, has_elevator, has_free_parking, has_hot_tub, has_bathtub, has_self_check_in, has_private_entrance, x_km, y_km |

Predictors never include host variables, dates, price-derived fields, listing IDs, exclusion flags, or targets. The coordinate feature set contains `x_km` and `y_km` as two projected continuous coordinates; they are not treated as separate locations. K=5 `cluster_id` is categorical and may overlap with coordinates, so this choice is predictive rather than causal. Amenities remain individual interpretable flags plus `amenity_count`; PCA was not used because this is a small, mixed-type feature group and PCA would obscure amenity meaning.

## 4. Five-fold CV used for selection

Each row below is the selected candidate evaluated with shuffled five-fold CV on its entire historical training population. Metrics are on the log nightly-price target and are used only for model selection, not as the primary final comparison.

| model | CV MAE (log USD) | CV RMSE (log USD) | CV R² |
| --- | --- | --- | --- |
| Baseline | 0.334227 | 0.507924 | 0.771828 |
| Corrected | 0.312527 | 0.458754 | 0.803381 |

## 5. Primary external JSON test

The JSON contains 1249 records. 857 IDs already occur in the historical database and are excluded from external testing. The same **392 novel listing IDs** are scored by both models. MAPE is `mean(|predicted USD − displayed USD| / displayed USD)` over records with a positive displayed nightly price.

| model | prediction_coverage | observed_price_count | mae_usd | rmse_usd | mape | median_absolute_error_usd | bias_usd |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Baseline | 392 | 392 | 56.814931 | 87.017723 | 0.353215 | 35.543113 | 3.958025 |
| Corrected | 392 | 392 | 53.763499 | 84.632691 | 0.323202 | 31.179505 | -1.820170 |
| Corrected minus baseline | 0 | 0 | -3.051432 | -2.385031 | -0.030013 | -4.363607 | -5.778195 |

A negative corrected-minus-baseline value is an improvement for MAE, RMSE, MAPE, and median absolute error. Prediction coverage is the count of novel JSON listings passed to each pipeline; it is expected to be identical.

## 6. Conclusion

**The external JSON comparison above is the final performance evidence.** The corrected model is evaluated on the same 392 novel listings as the baseline, after removing all 11 registered price-unit errors from corrected training. No internal holdout was created, stored, or used to make this conclusion. Because displayed prices are from a different crawl time and may reflect different stay dates, the result measures external time-heterogeneous transfer rather than a contemporaneous production benchmark.

## 7. Reproducibility and validation

Script: `/Users/stevenjang/Documents/Projects/airbnb/run_price_model_analysis.py`. Run `PYTHONDONTWRITEBYTECODE=1 python3 -B /Users/stevenjang/Documents/Projects/airbnb/run_price_model_analysis.py --external-evaluation`. Package versions: `{"numpy": "2.5.1", "pandas": "3.0.5", "python": "3.14.6", "scikit_learn": "1.9.0", "scipy": "1.18.1", "sqlite": "3.53.4"}`. Only workflow-owned SQLite tables, this script, and this report are updated.

| check | result |
| --- | --- |
| corrected_PRICE_UNIT_ERROR_training_rows | 0 |
| external_JSON_novel_only | True |
| same_external_listing_ids | True |
| internal_holdout_prediction_rows | 0 |
| feature_rows_one_per_listing | True |
| foreign_key_check | empty |
| quick_check | ok |
| raw_tables_and_columns_unchanged | True |
