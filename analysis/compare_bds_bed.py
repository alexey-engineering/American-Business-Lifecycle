#!/usr/bin/env python3
"""Compare project BDS national flows with the separate BLS BED annual table."""
from pathlib import Path
import csv
import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "database/business_lifecycle.duckdb"
OUT = ROOT / "data/processed/external_validation.csv"
# Values transcribed from the BLS Table 1 linked below; published in thousands.
# BLS table rows are year ended March; the published table rounds to whole thousands.
BLS_BED_THOUSANDS = {
    2021: {"job_creation": 12522, "job_destruction": 18001, "net_employment_change": -5479},
    2022: {"job_creation": 17911, "job_destruction": 10982, "net_employment_change": 6929},
    2023: {"job_creation": 16008, "job_destruction": 12669, "net_employment_change": 3339},
}
BLS_URL = "https://www.bls.gov/web/cewbd/anntab1_1.txt"


def main() -> None:
    con = duckdb.connect(str(DB), read_only=True)
    rows = con.execute("""SELECT date_key AS year, job_creation, job_destruction, net_employment_change
                          FROM marts.fact_business_dynamics
                          WHERE observation_type='national' AND date_key IN (2021,2022,2023)
                          ORDER BY date_key""").fetchall()
    con.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["year", "metric", "bds_value_jobs", "bls_bed_value_thousands", "bls_bed_value_jobs_rounded", "difference_bds_minus_bls_jobs", "source_url", "comparison_note"])
        writer.writeheader()
        for year, creation, destruction, net in rows:
            for metric, value in (("job_creation", creation), ("job_destruction", destruction), ("net_employment_change", net)):
                bls_thousands = BLS_BED_THOUSANDS[year][metric]
                writer.writerow({"year": year, "metric": metric, "bds_value_jobs": value,
                                 "bls_bed_value_thousands": bls_thousands,
                                 "bls_bed_value_jobs_rounded": bls_thousands * 1000,
                                 "difference_bds_minus_bls_jobs": value - bls_thousands * 1000,
                                 "source_url": BLS_URL,
                                 "comparison_note": "BED total private; March-to-March; published in 000s. Coverage, production methods and revisions differ from BDS."})
    print(OUT.relative_to(ROOT))
    print(OUT.read_text())


if __name__ == "__main__":
    main()
