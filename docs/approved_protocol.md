# Approved protocol — source of truth

Written approval granted by Sanjar Bekov. Assessed collection starts only after written approval.

## Exact series
### Wheat
USDA AMS Report 3223: US No. 1 Hard Red Winter Wheat; Mills and Processors; Bid; Ordinary protein; FOB-R; Current delivery; Average; USD/bushel.

### Corn
USDA AMS Report 3192: US No. 2 Yellow Corn (Bulk); Country Elevators - Conventional; North Central; Bid; DLVD-T; Current delivery; Average; USD/bushel.

Missing or changed specifications are flagged. Never silently substitute another row.

## Collection and prediction
- Record actual first assessed collection date/time.
- Keep pre-approval feasibility records separate.
- Prediction cutoff: 06:00 Asia/Tashkent (UTC+5).
- Both required reports and all required inputs must have been received before prediction.
- Archive prediction, model version, input versions and timestamps before outcome arrival.
- Missed forecasts remain missed; never reconstruct retrospectively.
- Preserve original and revised source responses separately.
- Final outcome cutoff: 12 December 2026, 06:00 Asia/Tashkent. If unavailable, mark `unobserved`; do not substitute a later date or extend the deadline.

## Evaluation
- Forecast horizon: one subsequent trading day.
- Models: Persistence, Ridge Regression, Random Forest.
- Target: 20 complete matched observations; report actual usable sample after exclusions.
- Split: fixed chronological sequence, not a moving 60/20/20 recalculation. Planned example: first 10 eligible origins for training, next 3 validation, subsequent eligible origins test.
- Every training and validation outcome used for model selection must be available before the first test prediction.
- Freeze preprocessing, features, hyperparameters and all robustness comparisons before test evaluation.
- Do not use test results to select a preferred configuration.
- Report every test forecast, MAE, RMSE and paired error differences on identical eligible origins.
- Four test forecasts support descriptive/exploratory comparison only; do not claim established model superiority.

## Association analysis
- Use percentage price changes over identical consecutive trading-date intervals.
- Regression: wheat percentage change on corn percentage change, with intercept.
- Null: zero slope; two-sided alternative; 5% significance level.
- HAC/Newey-West standard errors with two lags, preserving trading-date gaps. Do not delete missing dates and silently treat remaining rows as consecutive. Analyse continuous consecutive segments; disclose if insufficient for meaningful HAC inference.
- Report Pearson correlation separately, plus slope, confidence interval, actual sample size and exploratory limitations.
- Conduct full-period association analysis only after features and model settings are frozen.

## Robustness checks
1. Lookback of one vs two previous trading observations.
2. Wheat-only vs wheat-plus-corn feature set.
3. Ridge alpha=1 vs alpha=10.
Freeze all settings before examining test results.

## Required evidence
- SQLite snapshot and provenance.
- Five useful SQL queries.
- Five visualisations.
- At least eight meaningful automated tests.
- Four runnable GitHub checkpoint commits.
- AI usage record.
- LO1, LO2 and LO5 mapping.
- Final repository URL and full 40-character final commit hash in report.
