#!/usr/bin/env python3
"""Build the layered DuckDB database from the downloaded Census CSV files."""
from __future__ import annotations

import argparse
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "database" / "business_lifecycle.duckdb"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, default=DB)
    args = parser.parse_args()
    args.database.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(args.database))
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    for name in ("economy", "state", "sector", "firm_age", "firm_size"):
        path = (ROOT / "data/raw/bds" / f"bds2023_{name}.csv").as_posix().replace("'", "''")
        con.execute(f"CREATE OR REPLACE TABLE raw.bds_{name} AS SELECT * FROM read_csv_auto('{path}', all_varchar=true, header=true)")
    for area in ("staging", "intermediate", "marts"):
        models = sorted((ROOT / "sql" / area).glob("*.sql"), key=lambda p: (0 if p.name == "dimensional_model.sql" else 1, p.name))
        for model in models:
            con.execute(model.read_text())
            print(f"built {area}/{model.name}")
    print("RAW source counts:")
    for name in ("economy", "state", "sector", "firm_age", "firm_size"):
        print(name, con.execute(f"SELECT count(*) FROM raw.bds_{name}").fetchone()[0])
    for table in ("dim_date", "dim_geography", "dim_industry", "dim_firm_age", "dim_firm_size", "fact_business_dynamics"):
        print(f"marts.{table}: {con.execute(f'SELECT count(*) FROM marts.{table}').fetchone()[0]}")
    con.close()


if __name__ == "__main__":
    main()
