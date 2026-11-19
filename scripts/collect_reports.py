from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pymupdf
import requests

import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_DIR = PROJECT_ROOT / "data" / "raw" / "usda"
LOG_FILE = PROJECT_ROOT / "data" / "collection_runs.jsonl"

TIMEZONE = ZoneInfo("Asia/Tashkent")

REPORTS = {
    "3223": {
        "name": "Kansas City Board of Trade Daily Wheat Bids",
        "url": "https://www.ams.usda.gov/mnreports/ams_3223.pdf",
    },
    "3192": {
        "name": "Illinois Grain Bids",
        "url": "https://www.ams.usda.gov/mnreports/ams_3192.pdf",
    },
}


def download_report(report_id: str, report: dict) -> None:
    retrieved_at = datetime.now(TIMEZONE)
    timestamp = retrieved_at.strftime("%Y%m%dT%H%M%S%z")

    print(f"\nDownloading USDA report {report_id}...")

    response = requests.get(
        report["url"],
        timeout=60,
        headers={"User-Agent": "WheatPriceIntelligence/1.0"},
    )
    response.raise_for_status()

    content = response.content

    # Проверяем, что сервер действительно вернул PDF.
    if not content.startswith(b"%PDF"):
        raise ValueError(
            f"Report {report_id}: response is not a valid PDF file."
        )

    sha256 = hashlib.sha256(content).hexdigest()

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Уникальное имя: повторные загрузки и исправления не перезаписываются.
    filename = f"report_{report_id}_{timestamp}_{sha256[:8]}.pdf"
    pdf_path = ARCHIVE_DIR / filename

    pdf_path.write_bytes(content)

    # Извлекаем текст только для предварительной проверки.
    with pymupdf.open(pdf_path) as pdf:
        page_count = len(pdf)
        preview = "\n\n".join(
            page.get_text() for page in pdf[:3]
        )

    text_path = pdf_path.with_suffix(".txt")
    text_path.write_text(preview, encoding="utf-8")

    metadata = {
        "report_id": report_id,
        "report_name": report["name"],
        "source_url": report["url"],
        "retrieved_at_tashkent": retrieved_at.isoformat(),
        "sha256": sha256,
        "filename": filename,
        "page_count": page_count,
        "report_date": None,
        "report_date_status": "requires_manual_verification",
    }

    metadata_path = pdf_path.with_suffix(".json")
    metadata_path.write_text(
        json.dumps(metadata, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )

    with LOG_FILE.open("a", encoding="utf-8") as log:
        log.write(json.dumps(metadata, ensure_ascii=False) + "\n")

    print(f"Saved: {pdf_path.relative_to(PROJECT_ROOT)}")
    print(f"Pages: {page_count}")
    print(f"SHA-256: {sha256}")
    print("\n--- TEXT PREVIEW ---")
    print(preview[:2500] or "[No text extracted]")
    print("--- END PREVIEW ---")


def main() -> None:
    failed = []

    for report_id, report in REPORTS.items():
        try:
            download_report(report_id, report)
        except Exception as error:
            failed.append(report_id)
            print(f"\nERROR downloading report {report_id}: {error}")

    if failed:
        print(f"\nFailed reports: {', '.join(failed)}")
        sys.exit(1)

    print("\nAll reports downloaded successfully.")


if __name__ == "__main__":
    main()