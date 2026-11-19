-- Q1: chronological prices for both approved series
SELECT observation_date, series_code, price, unit
FROM market_prices
ORDER BY observation_date, series_code;

-- Q2: observation counts by series
SELECT series_code, COUNT(*) AS observation_count
FROM market_prices
GROUP BY series_code;

-- Q3: collection and parsing failures
SELECT report_date, retrieved_at, parse_status, revision_label
FROM raw_observations
WHERE parse_status <> 'success'
ORDER BY retrieved_at;

-- Q4: forecasts and observed outcomes
SELECT origin_report_date, target_report_date, prediction, actual, status
FROM forecasts
ORDER BY target_report_date;

-- Q5: forecast errors by model (only observed outcomes)
SELECT m.model_name,
       AVG(ABS(f.actual - f.prediction)) AS mae,
       SQRT(AVG((f.actual - f.prediction) * (f.actual - f.prediction))) AS rmse
FROM forecasts f
JOIN model_runs m ON m.model_run_id = f.model_run_id
WHERE f.status = 'observed'
GROUP BY m.model_name;
