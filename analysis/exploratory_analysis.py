#!/usr/bin/env python3
"""Question-led exploratory analysis of the selected BDS dimensions."""
from __future__ import annotations

import csv
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "database/business_lifecycle.duckdb"
OUT = ROOT / "data/processed"

QUERIES = {
    # Question 7: annual national history and pre/during/post comparison.
    "executive_overview": "SELECT * FROM marts.executive_overview ORDER BY year",
    "covid_periods": "SELECT * FROM marts.covid_comparison ORDER BY first_bds_year",
    # Questions 1–2: current and long-run state differences plus period-specific contractions.
    "state_growth": "SELECT * FROM marts.state_employment_growth WHERE year=2023 ORDER BY employment_growth_rate_pct DESC LIMIT 10",
    "state_contraction": "SELECT * FROM marts.state_period_contractions ORDER BY period,loss_rank_rate,loss_rank_absolute",
    "state_long_run_growth": "SELECT * FROM marts.state_long_run_growth ORDER BY employment_growth_1978_2023_pct DESC LIMIT 10",
    "state_worst_annual_change": "SELECT * FROM marts.state_worst_annual_change ORDER BY worst_year_net_change LIMIT 10",
    "state_period_comparison": "SELECT * FROM marts.state_period_dynamics ORDER BY period,loss_rank_rate",
    "state_comparison_2023": "SELECT * FROM marts.state_employment_growth WHERE year=2023 ORDER BY employment_growth_rate_pct DESC",
    "state_rate_outliers": "SELECT * FROM marts.state_rate_outliers ORDER BY year,state_fips",
    # Questions 3–4: industry levels and changes.
    "industry_growth": "SELECT * FROM marts.industry_employment_growth WHERE year=2023 ORDER BY net_employment_change DESC LIMIT 10",
    "industry_contraction": "SELECT * FROM marts.industry_employment_contraction WHERE year=2023 ORDER BY net_employment_change",
    "industry_comparison_2023": "SELECT * FROM marts.industry_employment_growth WHERE year=2023 ORDER BY net_employment_change DESC",
    "national_contribution": "SELECT * FROM marts.national_employment_contribution WHERE year=2023 ORDER BY observation_type,contribution_to_national_change_pct DESC",
    # Questions 5–6: business structure.
    "firm_age": "SELECT * FROM marts.firm_age_grouped_comparison WHERE year=2023 ORDER BY group_type,comparison_group",
    "firm_size": "SELECT * FROM marts.firm_size_comparison WHERE year=2023 ORDER BY net_employment_change DESC",
    "firm_age_missingness_by_year": """SELECT d.year,
        count(*) FILTER(WHERE f.employment IS NULL) AS employment_nulls,
        count(*) FILTER(WHERE f.employment_denominator IS NULL) AS denominator_nulls,
        count(*) FILTER(WHERE f.establishment_births IS NULL) AS birth_nulls,
        count(*) FILTER(WHERE f.establishment_deaths IS NULL) AS death_nulls,
        count(*) FILTER(WHERE f.job_creation IS NULL) AS job_creation_nulls,
        count(*) FILTER(WHERE f.job_destruction IS NULL) AS job_destruction_nulls,
        count(*) FILTER(WHERE f.net_employment_change IS NULL) AS net_change_nulls,
        count(*) FILTER(WHERE f.has_suppression_marker) AS rows_with_x
      FROM marts.fact_business_dynamics f JOIN marts.dim_date d USING(date_key)
      WHERE f.observation_type='firm_age'
      GROUP BY d.year ORDER BY d.year""",
    # Distribution summary across the five selected margins (not additive across rows).
    "distribution_summary": """SELECT observation_type, count(*) AS row_count,
        count(employment) AS employment_nonnull_rows,
        min(employment) AS employment_min, quantile_cont(employment,0.25) AS employment_q1,
        median(employment) AS employment_median, avg(employment) AS employment_mean,
        quantile_cont(employment,0.75) AS employment_q3, max(employment) AS employment_max,
        min(net_employment_change) AS net_change_min, median(net_employment_change) AS net_change_median,
        max(net_employment_change) AS net_change_max,
        count(*) FILTER(WHERE net_employment_change<0) AS negative_net_rows,
        count(*) FILTER(WHERE has_suppression_marker) AS rows_with_x
      FROM marts.fact_business_dynamics GROUP BY observation_type ORDER BY observation_type""",
}


def export_query(con: duckdb.DuckDBPyConnection, name: str, query: str) -> int:
    result = con.execute(query)
    columns = [item[0] for item in result.description]
    rows = result.fetchall()
    with (OUT / f"{name}.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(columns)
        writer.writerows(rows)
    return len(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB), read_only=True)
    for name, query in QUERIES.items():
        count = export_query(con, name, query)
        print(f"{name}: {count} rows")
    con.close()


if __name__ == "__main__":
    main()
