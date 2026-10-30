from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "database/business_lifecycle.duckdb"


def test_required_tables_and_columns():
    con = duckdb.connect(str(DB), read_only=True)
    expected = {
        "dim_date": {"date_key", "year", "year_date"},
        "dim_geography": {"geography_key", "geography_code", "geography_name"},
        "dim_industry": {"industry_key", "industry_code", "industry_name"},
        "dim_firm_age": {"firm_age_key", "firm_age_label", "firm_age_group", "is_left_censored", "left_censored_mature_from_year"},
        "dim_firm_size": {"firm_size_key", "firm_size_label"},
        "fact_business_dynamics": {"date_key", "geography_key", "industry_key", "firm_age_key", "firm_size_key", "observation_type", "employment", "job_creation", "job_destruction", "net_employment_change", "left_censored_is_mature", "age_comparison_group"},
    }
    for table, columns in expected.items():
        actual = {row[0] for row in con.execute(f"DESCRIBE marts.{table}").fetchall()}
        assert columns <= actual
    types = {row[0]: row[1] for row in con.execute("DESCRIBE marts.fact_business_dynamics").fetchall()}
    assert types["date_key"] == "SMALLINT"
    assert types["employment"] == "BIGINT"
    assert types["employment_growth_rate_pct"] == "DOUBLE"
    assert con.execute("SELECT count(*) FROM marts.dim_date WHERE year BETWEEN 1978 AND 2023").fetchone()[0] == 46
    assert con.execute("SELECT count(*) FROM marts.dim_geography WHERE geography_level='State'").fetchone()[0] == 51
    assert con.execute("SELECT count(*) FROM marts.dim_industry WHERE industry_level='NAICS sector'").fetchone()[0] == 19
    assert con.execute("SELECT count(*) FROM marts.dim_firm_age WHERE firm_age_code <> 'ALL'").fetchone()[0] == 12
    assert con.execute("SELECT count(*) FROM marts.dim_firm_size WHERE firm_size_code <> 'ALL'").fetchone()[0] == 10
    con.close()
