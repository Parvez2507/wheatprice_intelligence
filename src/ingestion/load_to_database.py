
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from zoneinfo import ZoneInfo

from usda_parser import parse_report


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "wheatprice.sqlite"
ARCHIVE_DIR = ROOT / "data" / "raw" / "usda"

TIMEZONE = ZoneInfo("Asia/Tashkent")

SERIES = {
    "3223": {
        "series_code": "WHEAT_HRW_ORDINARY_FOB_R_CURRENT",
        "commodity": "wheat",
        "description": (
            "US No. 1 Hard Red Winter Wheat; Mills and Processors; "
            "Bid; Ordinary protein; FOB-R; Current; Average"
        ),
        "unit": "USD/bushel",
    },
    "3192": {
        "series_code": "CORN_YELLOW_NORTH_CENTRAL_DLVD_T_CURRENT",
        "commodity": "corn",
        "description": (
            "US No. 2 Yellow Corn; Country Elevators - Conventional; "
            "North Central; Bid; DLVD-T; Current; Average"
        ),
        "unit": "USD/bushel",
    },
}


def now_tashkent() -> str:
    return datetime.now(TIMEZONE).isoformat()


def load_metadata(source_file: str) -> dict:
    """Load metadata belonging to the exact parsed text file."""
    metadata_path = (ARCHIVE_DIR / source_file).with_suffix(".json")

    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata not found: {metadata_path}")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    pdf_path = ARCHIVE_DIR / metadata["filename"]

    if not pdf_path.exists():
        raise FileNotFoundError(f"Original PDF not found: {pdf_path}")

    actual_hash = hashlib.sha256(pdf_path.read_bytes()).hexdigest()

    if actual_hash != metadata["sha256"]:
        raise ValueError(f"SHA-256 mismatch for {pdf_path.name}")

    return metadata


def validate_observation(observation: dict) -> None:
    """Validate extracted values before database insertion."""
    if observation["report_id"] not in SERIES:
        raise ValueError("Unsupported USDA report ID")

    report_date = datetime.strptime(
        observation["report_date"], "%Y-%m-%d"
    ).date()

    try:
        price = Decimal(observation["price_usd_per_bushel"])
    except InvalidOperation as error:
        raise ValueError("Invalid price value") from error

    if not price.is_finite() or price <= 0:
        raise ValueError("Price must be a finite positive number")

    if report_date > datetime.now(TIMEZONE).date():
        raise ValueError("Report date cannot be in the future")


def save_observation(
    conn: sqlite3.Connection,
    run_id: int,
    observation: dict,
) -> str:
    """Save source, preserve PDF versions and insert market price."""
    validate_observation(observation)

    report_id = observation["report_id"]
    series = SERIES[report_id]
    metadata = load_metadata(observation["source_file"])

    report_date = observation["report_date"]
    price = Decimal(observation["price_usd_per_bushel"])
    sha256 = metadata["sha256"]
    retrieved_at = metadata["retrieved_at_tashkent"]

    # 1. Register the data source if it does not exist.
    conn.execute(
        """
        INSERT INTO data_sources (
            report_id,
            series_code,
            series_description,
            source_url,
            unit
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(report_id, series_code) DO NOTHING
        """,
        (
            report_id,
            series["series_code"],
            series["description"],
            metadata["source_url"],
            series["unit"],
        ),
    )

    source_row = conn.execute(
        """
        SELECT source_id
        FROM data_sources
        WHERE report_id = ? AND series_code = ?
        """,
        (report_id, series["series_code"]),
    ).fetchone()

    if source_row is None:
        raise RuntimeError("Could not retrieve data source ID")

    source_id = source_row[0]

    # 2. Check whether this exact PDF version is already archived.
    existing_raw = conn.execute(
        """
        SELECT raw_id, revision_label
        FROM raw_observations
        WHERE source_id = ? AND report_date = ? AND sha256 = ?
        """,
        (source_id, report_date, sha256),
    ).fetchone()

    if existing_raw is not None:
        raw_id = existing_raw[0]
        revision_label = existing_raw[1]
        raw_inserted = False

    else:
        # 3. Assign a version label without overwriting earlier files.
        previous_versions = conn.execute(
            """
            SELECT COUNT(*)
            FROM raw_observations
            WHERE source_id = ? AND report_date = ?
            """,
            (source_id, report_date),
        ).fetchone()[0]

        if previous_versions == 0:
            revision_label = "original"
        else:
            revision_label = f"version_{previous_versions + 1}"

        relative_pdf_path = (
            Path("data") / "raw" / "usda" / metadata["filename"]
        ).as_posix()

        cursor = conn.execute(
            """
            INSERT INTO raw_observations (
                source_id,
                run_id,
                report_date,
                retrieved_at,
                source_url,
                sha256,
                file_path,
                revision_label,
                parse_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'success')
            """,
            (
                source_id,
                run_id,
                report_date,
                retrieved_at,
                metadata["source_url"],
                sha256,
                relative_pdf_path,
                revision_label,
            ),
        )

        raw_id = cursor.lastrowid
        raw_inserted = True

    # 4. Insert the extracted price for this exact PDF version.
    price_cursor = conn.execute(
        """
        INSERT INTO market_prices (
            raw_id,
            source_id,
            series_code,
            observation_date,
            price,
            unit,
            extracted_text,
            validated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(raw_id, series_code, observation_date) DO NOTHING
        """,
        (
            raw_id,
            source_id,
            series["series_code"],
            report_date,
            float(price),
            series["unit"],
            observation["price_usd_per_bushel"],
            now_tashkent(),
        ),
    )

    price_inserted = price_cursor.rowcount == 1

    # 5. Return an accurate status instead of always saying "Saved".
    if raw_inserted and price_inserted:
        status = "INSERTED"
    elif raw_inserted:
        status = "NEW SOURCE VERSION; PRICE ALREADY EXISTS"
    elif price_inserted:
        status = "EXISTING SOURCE; PRICE ADDED"
    else:
        status = "ALREADY EXISTS; NO DUPLICATES"

    return (
        f"{status}: {series['commodity']} = "
        f"{price} {series['unit']} ({report_date}), "
        f"PDF version: {revision_label}"
    )


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    observations = [
        parse_report("3223"),
        parse_report("3192"),
    ]

    started_at = now_tashkent()

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")

        if conn.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
            raise RuntimeError("SQLite foreign keys are not enabled")

        cursor = conn.execute(
            """
            INSERT INTO collection_runs (started_at, status, notes)
            VALUES (?, 'running', ?)
            """,
            (
                started_at,
                "USDA PDF parsing and database ingestion",
            ),
        )

        run_id = cursor.lastrowid
        conn.commit()

        try:
            with conn:
                results = []

                for observation in observations:
                    result = save_observation(
                        conn,
                        run_id,
                        observation,
                    )
                    results.append(result)

                conn.execute(
                    """
                    UPDATE collection_runs
                    SET finished_at = ?,
                        status = 'success',
                        notes = ?
                    WHERE run_id = ?
                    """,
                    (
                        now_tashkent(),
                        " | ".join(results),
                        run_id,
                    ),
                )

            for result in results:
                print(result)

        except Exception as error:
            conn.execute(
                """
                UPDATE collection_runs
                SET finished_at = ?,
                    status = 'failed',
                    notes = ?
                WHERE run_id = ?
                """,
                (now_tashkent(), str(error), run_id),
            )
            conn.commit()
            raise

    print(f"\nDatabase: {DB_PATH}")
    print(f"Collection run ID: {run_id}")
    print("Ingestion completed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"\nINGESTION FAILED: {error}")
        sys.exit(1)
