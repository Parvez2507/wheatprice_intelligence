PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS data_sources (
    source_id INTEGER PRIMARY KEY,
    report_id TEXT NOT NULL,
    series_code TEXT NOT NULL,
    series_description TEXT NOT NULL,
    source_url TEXT NOT NULL,
    unit TEXT NOT NULL,
    UNIQUE(report_id, series_code)
);

CREATE TABLE IF NOT EXISTS collection_runs (
    run_id INTEGER PRIMARY KEY,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL CHECK (status IN ('running','success','partial','failed')),
    notes TEXT
);

CREATE TABLE IF NOT EXISTS raw_observations (
    raw_id INTEGER PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES data_sources(source_id),
    run_id INTEGER REFERENCES collection_runs(run_id),
    report_date TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    source_url TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    file_path TEXT NOT NULL,
    revision_label TEXT NOT NULL DEFAULT 'original',
    parse_status TEXT NOT NULL CHECK (parse_status IN ('pending','success','missing_series','parse_error')),
    UNIQUE(source_id, report_date, sha256)
);

CREATE TABLE IF NOT EXISTS market_prices (
    price_id INTEGER PRIMARY KEY,
    raw_id INTEGER NOT NULL REFERENCES raw_observations(raw_id),
    source_id INTEGER NOT NULL REFERENCES data_sources(source_id),
    series_code TEXT NOT NULL,
    observation_date TEXT NOT NULL,
    price REAL NOT NULL CHECK (price > 0),
    unit TEXT NOT NULL,
    extracted_text TEXT,
    validated_at TEXT NOT NULL,
    UNIQUE(raw_id, series_code, observation_date)
);

CREATE TABLE IF NOT EXISTS features (
    feature_id INTEGER PRIMARY KEY,
    forecast_origin TEXT NOT NULL,
    feature_name TEXT NOT NULL,
    feature_value REAL NOT NULL,
    available_at TEXT NOT NULL,
    input_price_ids TEXT NOT NULL,
    feature_version TEXT NOT NULL,
    UNIQUE(forecast_origin, feature_name, feature_version)
);

CREATE TABLE IF NOT EXISTS model_runs (
    model_run_id INTEGER PRIMARY KEY,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    parameters_json TEXT NOT NULL,
    feature_set TEXT NOT NULL,
    train_start_date TEXT NOT NULL,
    train_end_date TEXT NOT NULL,
    validation_end_date TEXT NOT NULL,
    frozen_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS forecasts (
    forecast_id INTEGER PRIMARY KEY,
    model_run_id INTEGER NOT NULL REFERENCES model_runs(model_run_id),
    origin_report_date TEXT NOT NULL,
    forecast_created_at TEXT NOT NULL,
    target_report_date TEXT NOT NULL,
    prediction REAL NOT NULL,
    input_version_ids TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending','observed','unobserved','missed')),
    actual REAL,
    outcome_received_at TEXT,
    UNIQUE(model_run_id, origin_report_date, target_report_date)
);

CREATE INDEX IF NOT EXISTS idx_market_prices_date ON market_prices(observation_date);
CREATE INDEX IF NOT EXISTS idx_raw_report_date ON raw_observations(report_date);
CREATE INDEX IF NOT EXISTS idx_forecasts_target ON forecasts(target_report_date);
