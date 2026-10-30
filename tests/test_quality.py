from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import duckdb
import pytest

ROOT = Path(__file__).resolve().parents[1]
DB = Path(os.environ.get("BUSINESS_LIFECYCLE_DB", ROOT / "database/business_lifecycle.duckdb"))


def test_keys_categories_and_relationships():
    con = duckdb.connect(str(DB), read_only=True)
    assert con.execute("SELECT count(*)-count(DISTINCT (date_key,observation_type,observation_code)) FROM marts.fact_business_dynamics").fetchone()[0] == 0
    for dim, key in [("dim_date", "date_key"), ("dim_geography", "geography_key"), ("dim_industry", "industry_key"), ("dim_firm_age", "firm_age_key"), ("dim_firm_size", "firm_size_key")]:
        assert con.execute(f"SELECT count(*)-count(DISTINCT {key}) FROM marts.{dim}").fetchone()[0] == 0
    checks = [("dim_date", "date_key"), ("dim_geography", "geography_key"), ("dim_industry", "industry_key"), ("dim_firm_age", "firm_age_key"), ("dim_firm_size", "firm_size_key")]
    for dim, key in checks:
        assert con.execute(f"SELECT count(*) FROM marts.fact_business_dynamics f LEFT JOIN marts.{dim} d USING ({key}) WHERE d.{key} IS NULL").fetchone()[0] == 0
    assert con.execute("SELECT count(*) FROM marts.fact_business_dynamics WHERE employment < 0 OR job_creation < 0 OR job_destruction < 0").fetchone()[0] == 0
    assert con.execute("SELECT count(*) FROM marts.fact_business_dynamics f LEFT JOIN marts.dim_date d USING (date_key) WHERE d.date_key IS NULL").fetchone()[0] == 0
    con.close()


def test_fact_key_uniqueness():
    con = duckdb.connect(str(DB), read_only=True)
    duplicate_count = con.execute("SELECT count(*)-count(DISTINCT (date_key,observation_type,observation_code)) FROM marts.fact_business_dynamics").fetchone()[0]
    con.close()
    assert duplicate_count == 0


def test_corrupted_copy_is_rejected_by_fact_key_test():
    """Demonstrate that the actual pytest grain check fails on a duplicated fact row."""
    with tempfile.TemporaryDirectory(prefix="bds-corrupt-") as temporary:
        corrupt_db = Path(temporary) / "corrupt.duckdb"
        shutil.copy2(DB, corrupt_db)
        con = duckdb.connect(str(corrupt_db))
        con.execute("INSERT INTO marts.fact_business_dynamics SELECT * FROM marts.fact_business_dynamics WHERE date_key=2023 AND observation_type='national' LIMIT 1")
        con.close()
        env = os.environ.copy()
        env["BUSINESS_LIFECYCLE_DB"] = str(corrupt_db)
        result = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_quality.py::test_fact_key_uniqueness"],
                                cwd=ROOT, env=env, capture_output=True, text=True)
        assert result.returncode != 0, "the grain test unexpectedly passed against a corrupted database"
        assert "assert duplicate_count == 0" in result.stdout
        print("Expected failure from the duplicated-row database:\n" + result.stdout)


def test_suppression_is_not_coerced_to_zero():
    con = duckdb.connect(str(DB), read_only=True)
    assert con.execute("SELECT count(*) FROM staging.business_dynamics WHERE has_suppression_marker AND job_destruction IS NULL").fetchone()[0] > 0
    assert con.execute("SELECT count(*) FROM raw.bds_firm_age WHERE job_destruction='X'").fetchone()[0] > 0
    con.close()
