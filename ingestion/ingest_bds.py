#!/usr/bin/env python3
"""Download the five small official 2023 BDS time-series CSVs."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "bds"
BASE = "https://www2.census.gov/programs-surveys/bds/tables/time-series/2023/"
RELEASE_VERSION = "2023 BDS"
SOURCE_RELEASE_DATE = "2025-09-25"
LOCAL_TIMEZONE_NAME = "America/Monterrey"
LOCAL_TIMEZONE = ZoneInfo(LOCAL_TIMEZONE_NAME)
SOURCES = {
    "economy": "bds2023.csv",
    "firm_age": "bds2023_fa.csv",
    "firm_size": "bds2023_fz.csv",
    "state": "bds2023_st.csv",
    "sector": "bds2023_sec.csv",
}
EXPECTED_SHA256 = {
    "economy": "1278adb3a89d6d16950f8bdd0097de2dd9545934bd3f969bb86fa6057b430978",
    "firm_age": "52a36e61791aacfaedc0466a4d9b8c1c94a8b0dfbe05e967840119bf6d5695a1",
    "firm_size": "403bf76c2b8725993ed0bb657801ac6b5d78053d60fed490af8101d154b6729f",
    "state": "9e0c86610ee685c2f7c8c4dec60bd213177cd8644fe539e5f66457efc8ef603c",
    "sector": "758a263b166167e9557d4fc4ba8cd60229c5e05d341214b7494982c4764cf224",
}
REQUIRED = {"year", "emp", "job_creation", "job_destruction", "net_job_creation"}


def fetch(name: str, filename: str, offline: bool = False) -> dict:
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / f"bds2023_{name}.csv"
    url = BASE + filename
    operation = "validated-existing-file" if offline else "downloaded"
    downloaded_at_utc = None
    downloaded_at_local_date = None
    if not offline:
        request = Request(url, headers={"User-Agent": "american-business-lifecycle/1.0"})
        with urlopen(request, timeout=60) as response:
            if response.status != 200:
                raise RuntimeError(f"{url}: HTTP {response.status}")
            payload = response.read()
        if not payload.startswith(b"year,"):
            raise ValueError(f"Unexpected CSV response from {url}")
        digest = hashlib.sha256(payload).hexdigest()
        if digest != EXPECTED_SHA256[name]:
            raise ValueError(f"SHA-256 mismatch for {name}: got {digest}, expected {EXPECTED_SHA256[name]}; refusing to overwrite the pinned source")
        path.write_bytes(payload)
        downloaded_at = datetime.now(timezone.utc)
        downloaded_at_utc = downloaded_at.isoformat(timespec="microseconds").replace("+00:00", "Z")
        downloaded_at_local_date = downloaded_at.astimezone(LOCAL_TIMEZONE).date().isoformat()
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}; run without --offline first")
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        columns = reader.fieldnames or []
        if not REQUIRED.issubset(columns):
            raise ValueError(f"{path.name} is missing required columns: {REQUIRED - set(columns)}")
        rows = sum(1 for _ in reader)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256[name]:
        raise ValueError(f"SHA-256 mismatch for {name}: got {digest}, expected {EXPECTED_SHA256[name]}")
    return {"dataset": name, "url": url, "file": str(path.relative_to(ROOT)), "bytes": path.stat().st_size,
            "rows": rows, "columns": len(columns), "sha256": digest, "expected_sha256": EXPECTED_SHA256[name],
            **({"downloaded_at_utc": downloaded_at_utc,
                "downloaded_at_local_date": downloaded_at_local_date,
                "downloaded_timezone": LOCAL_TIMEZONE_NAME} if downloaded_at_utc else {}),
            "operation": operation}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="Validate existing downloaded CSVs only")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    log_path = ROOT / "data" / "raw" / "bds" / "ingestion_log.json"
    logs = [fetch(name, filename, args.offline) for name, filename in SOURCES.items()]
    if not args.offline:
        log_path.write_text(json.dumps({"release_version": RELEASE_VERSION, "source_release_date": SOURCE_RELEASE_DATE,
                                        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
                                        "timezone_for_download_dates": LOCAL_TIMEZONE_NAME, "sources": logs}, indent=2) + "\n")
    for item in logs:
        logging.info("%s: %s rows, %s columns, %s bytes", item["dataset"], item["rows"], item["columns"], item["bytes"])
    if args.offline:
        logging.info("Offline validation complete; provenance log left unchanged")
    else:
        logging.info("Wrote %s", log_path.relative_to(ROOT))


if __name__ == "__main__":
    main()
