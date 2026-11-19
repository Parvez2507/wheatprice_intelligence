# WheatPrice Intelligence

Exploratory one-trading-day-ahead forecasting of a defined Kansas City wheat cash-bid benchmark.

## Approved protocol
- Wheat: USDA AMS Report 3223; Mills and Processors -> Bid -> Ordinary protein -> FOB-R -> Current delivery -> Average; US No. 1 Hard Red Winter Wheat; USD/bushel.
- Corn: USDA AMS Report 3192; Country Elevators - Conventional -> North Central -> Bid -> DLVD-T -> Current delivery -> Average; US No. 2 Yellow Corn; USD/bushel.
- Forecast horizon: one subsequent trading day.
- Prediction cutoff: 06:00 Asia/Tashkent (UTC+5), only after both required reports and all inputs have been received.
- Primary assessed observations: collected by this system after written approval. Earlier feasibility records remain separate.
- Models: Persistence, Ridge Regression, Random Forest.
- Target: 20 complete matched observations, not a guaranteed sample size.
- Final outcome cutoff: 12 December 2026, 06:00 Asia/Tashkent.

## Setup
1. Create and activate a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Initialise the database: `python scripts/init_db.py`
4. Run tests: `pytest`

Record the actual assessed collection start in `config/project.yml` and `data/collection_log.csv` when the first approved collection run occurs. Do not use historical/feasibility records to supplement the assessed primary sample. Do not reconstruct missed forecasts or silently substitute a different series.
