from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]

def test_schema_creates_required_tables(tmp_path):
    db_path = tmp_path / "test.sqlite"
    schema = (ROOT / "sql" / "schema.sql").read_text(encoding="utf-8")
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema)
        names = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
    required = {
        "data_sources", "collection_runs", "raw_observations",
        "market_prices", "features", "model_runs", "forecasts"
    }
    assert required.issubset(names)

def test_foreign_keys_are_enforced_when_enabled(tmp_path):
    db_path = tmp_path / "test.sqlite"
    schema = (ROOT / "sql" / "schema.sql").read_text(encoding="utf-8")
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(schema)
        try:
            conn.execute(
                "INSERT INTO raw_observations "
                "(source_id, report_date, retrieved_at, source_url, sha256, "
                "file_path, parse_status) "
                "VALUES (999, '2026-11-12', '2026-11-12T06:00:00+05:00', "
                "'https://example.test/report.pdf', 'abc', 'x.pdf', 'pending')"
            )
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("Foreign key constraint was not enforced")
