
import re
from pathlib import Path
from datetime import datetime
from decimal import Decimal
import json


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_DIR = PROJECT_ROOT / "data" / "raw" / "usda"


def find_latest_report(report_id: str) -> Path:
    """Find the most recently downloaded text version of a report."""

    files = list(ARCHIVE_DIR.glob(f"report_{report_id}_*.txt"))

    if not files:
        raise FileNotFoundError(
            f"No text report found for USDA report {report_id}"
        )

    return max(files, key=lambda file: file.stat().st_mtime)


def extract_report_date(text: str) -> str:
    """Extract the USDA publication date."""

    match = re.search(
        r"\b(January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+"
        r"(\d{1,2}),\s+(\d{4})\b",
        text,
        re.IGNORECASE,
    )

    if not match:
        raise ValueError("Could not identify USDA report date")

    date = datetime.strptime(match.group(0), "%B %d, %Y")
    return date.date().isoformat()




def extract_wheat(text: str) -> Decimal:
    """Extract the approved Ordinary protein / FOB-R / Current wheat Average."""

    normalized = " ".join(text.split())

    pattern = (
        r"\bBid\s+Ordinary\s+"
        r"[\d.]+Z(?:\s+to\s+[\d.]+Z)?\s+"
        r"(?:UNCH|(?:UP|DN)\s+[\d.]+)"
        r"(?:\s*-\s*(?:UNCH|(?:UP|DN)\s+[\d.]+))?\s+"
        r"[\d.]+(?:-[\d.]+)?\s+"
        r"(?:UNCH|(?:UP|DN)\s+[\d.]+)"
        r"(?:\s*-\s*(?:UP|DN)\s+[\d.]+)?\s+"
        r"([\d.]+)\s+"          # Average
        r"(?:[\d.]+\s+)?"       # Year Ago (optional)
        r"FOB-R\s+Current\b"
    )

    matches = re.findall(pattern, normalized, re.IGNORECASE)

    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one matching wheat row, found {len(matches)}"
        )

    return Decimal(matches[0])



def extract_corn(text: str) -> Decimal:
    """Extract the approved North Central / DLVD-T / Current corn Average."""

    normalized = " ".join(text.split())

    change_pattern = (
        r"(?:UNCH|(?:UP|DN)\s+[\d.]+)"
        r"(?:-(?:UP|DN)\s+[\d.]+)?"
    )

    pattern = (
        r"\bNorth Central\s+Bid\s+"
        r"-?[\d.]+Z\s+to\s+-?[\d.]+Z\s+"
        + change_pattern + r"\s+"
        r"[\d.]+-[\d.]+\s+"
        + change_pattern + r"\s+"
        r"([\d.]+)\s+"       # Average
        r"[\d.]+\s+"         # Year Ago
        r"DLVD-T\s+Current\b"
    )

    matches = re.findall(pattern, normalized, re.IGNORECASE)

    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one matching corn row, found {len(matches)}"
        )

    return Decimal(matches[0])



def parse_report(report_id: str) -> dict:
    """Parse one USDA report and return its approved price."""

    path = find_latest_report(report_id)
    text = path.read_text(encoding="utf-8")

    report_date = extract_report_date(text)

    if report_id == "3223":
        price = extract_wheat(text)
        commodity = "wheat"
    elif report_id == "3192":
        price = extract_corn(text)
        commodity = "corn"
    else:
        raise ValueError(f"Unsupported report ID: {report_id}")

    return {
        "report_id": report_id,
        "commodity": commodity,
        "report_date": report_date,
        "price_usd_per_bushel": str(price),
        "source_file": path.name,
    }


def main():
    results = [
        parse_report("3223"),
        parse_report("3192"),
    ]

    print("\nEXTRACTED USDA OBSERVATIONS\n")

    print(json.dumps(results, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    main()
