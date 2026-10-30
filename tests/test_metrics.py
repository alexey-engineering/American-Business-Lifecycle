from pathlib import Path
import duckdb

DB = Path(__file__).resolve().parents[1] / "database/business_lifecycle.duckdb"


def test_metric_arithmetic_and_analytical_views():
    con = duckdb.connect(str(DB), read_only=True)
    # BDS noise infusion can create a one-job rounding difference in a source cell.
    assert con.execute("SELECT coalesce(max(abs(net_employment_change-(job_creation-job_destruction))),0) FROM marts.fact_business_dynamics WHERE job_creation IS NOT NULL AND job_destruction IS NOT NULL").fetchone()[0] <= 1
    assert con.execute("SELECT count(*) FROM marts.employment_share WHERE employment_share_pct IS NOT NULL AND (employment_share_pct < 0 OR employment_share_pct > 100.01)").fetchone()[0] == 0
    for view in ("state_employment_growth", "state_employment_contraction", "state_long_run_growth", "state_worst_annual_change", "state_period_dynamics", "state_period_contractions", "state_rate_outliers", "industry_employment_growth", "industry_employment_contraction", "firm_age_comparison", "firm_age_grouped_comparison", "firm_size_comparison", "covid_comparison", "national_employment_contribution", "executive_overview", "pbi_national_dynamics", "pbi_state_dynamics", "pbi_industry_dynamics", "pbi_firm_age_dynamics", "pbi_firm_size_dynamics"):
        assert con.execute(f"SELECT count(*) FROM marts.{view}").fetchone()[0] > 0
    con.close()


def test_bds_march_year_convention_keeps_2020_out_of_shock_window():
    con = duckdb.connect(str(DB), read_only=True)
    y2020 = con.execute("""SELECT d.covid_period,d.is_pre_covid,d.is_covid_period,
                                  f.employment_growth_rate_pct,f.net_employment_change
                           FROM marts.dim_date d JOIN marts.fact_business_dynamics f USING(date_key)
                           WHERE d.year=2020 AND f.observation_type='national'""").fetchone()
    y2021 = con.execute("""SELECT d.covid_period,d.is_pre_covid,d.is_covid_period,
                                  f.employment_growth_rate_pct,f.net_employment_change
                           FROM marts.dim_date d JOIN marts.fact_business_dynamics f USING(date_key)
                           WHERE d.year=2021 AND f.observation_type='national'""").fetchone()
    assert y2020[0] == 'Pre-COVID (2015–2020)' and y2020[1] and not y2020[2]
    assert y2020[3] > 0 and y2020[4] > 0
    assert y2021[0] == 'COVID shock (2021)' and not y2021[1] and y2021[2]
    assert y2021[3] < 0 and y2021[4] < 0
    recession_period = con.execute("SELECT count(*),min(years_in_period),max(years_in_period) FROM marts.state_period_dynamics WHERE period='Great Recession window (2008–2010)'").fetchone()
    assert recession_period == (51, 3, 3)
    con.close()


def test_kpis_recalculated_from_raw_match_mart():
    con = duckdb.connect(str(DB), read_only=True)
    raw = con.execute("""SELECT try_cast(emp AS BIGINT), try_cast(denom AS BIGINT),
                               try_cast(estabs_entry AS BIGINT), try_cast(estabs_exit AS BIGINT),
                               try_cast(job_creation AS BIGINT), try_cast(job_creation_rate AS DOUBLE),
                               try_cast(job_destruction AS BIGINT), try_cast(job_destruction_rate AS DOUBLE),
                               try_cast(net_job_creation AS BIGINT), try_cast(net_job_creation_rate AS DOUBLE)
                        FROM raw.bds_economy WHERE year='2023'""").fetchone()
    mart = con.execute("""SELECT employment,employment_denominator,establishment_births,establishment_deaths,
                                 job_creation,job_creation_rate_pct,job_destruction,job_destruction_rate_pct,
                                 net_employment_change,employment_growth_rate_pct
                          FROM marts.fact_business_dynamics WHERE date_key=2023 AND observation_type='national'""").fetchone()
    assert raw == mart
    con.close()


def test_state_stock_and_margin_flow_reconciliation():
    con = duckdb.connect(str(DB), read_only=True)
    # Census noise infusion tolerance: max observed annual net-change difference is 22,037 jobs.
    tolerance = 30_000
    state_employment_diff = con.execute("""WITH s AS (SELECT date_key,sum(employment) v FROM marts.fact_business_dynamics WHERE observation_type='state' GROUP BY date_key),
                                     n AS (SELECT date_key,employment v FROM marts.fact_business_dynamics WHERE observation_type='national')
                               SELECT max(abs(s.v-n.v)) FROM s JOIN n USING(date_key)""").fetchone()[0]
    assert state_employment_diff == 0
    for margin in ("state", "industry", "firm_age", "firm_size"):
        max_diff = con.execute(f"""WITH x AS (SELECT date_key,sum(net_employment_change) v FROM marts.fact_business_dynamics WHERE observation_type='{margin}' GROUP BY date_key),
                                          n AS (SELECT date_key,net_employment_change v FROM marts.fact_business_dynamics WHERE observation_type='national')
                                    SELECT max(abs(x.v-n.v)) FROM x JOIN n USING(date_key)""").fetchone()[0]
        assert max_diff <= tolerance, f"{margin} net flow diff {max_diff} exceeds {tolerance}"
    con.close()


def test_unfiltered_fact_exposes_five_margin_double_count():
    con = duckdb.connect(str(DB), read_only=True)
    unfiltered, national, margins = con.execute("""SELECT
        sum(employment), max(employment) FILTER (WHERE observation_type='national'),
        count(DISTINCT observation_type)
        FROM marts.fact_business_dynamics WHERE date_key=2023""").fetchone()
    assert margins == 5
    assert unfiltered == national * 5
    con.close()


def test_powerbi_views_are_single_margin_only():
    con = duckdb.connect(str(DB), read_only=True)
    expected = {
        "pbi_national_dynamics": "national",
        "pbi_state_dynamics": "state",
        "pbi_industry_dynamics": "industry",
        "pbi_firm_age_dynamics": "firm_age",
        "pbi_firm_size_dynamics": "firm_size",
    }
    for view, margin in expected.items():
        assert con.execute(f"SELECT count(DISTINCT observation_type) FROM marts.{view}").fetchone()[0] == 1
        assert con.execute(f"SELECT min(observation_type) FROM marts.{view}").fetchone()[0] == margin
    con.close()


def test_firm_age_reconciliation_and_left_censored_maturity():
    con = duckdb.connect(str(DB), read_only=True)
    # Census cell-level noise tolerance: the largest observed annual age-vs-national flow gap is 28,068.
    tolerance = 30_000
    diffs = con.execute("""WITH a AS (
        SELECT date_key, sum(employment) employment, sum(job_creation) creation,
               sum(job_destruction) destruction, sum(net_employment_change) net
        FROM marts.fact_business_dynamics WHERE observation_type='firm_age' GROUP BY date_key
    ), n AS (
        SELECT date_key, employment, job_creation creation, job_destruction destruction,
               net_employment_change net FROM marts.fact_business_dynamics WHERE observation_type='national'
    ) SELECT max(abs(a.employment-n.employment)), max(abs(a.creation-n.creation)),
             max(abs(a.destruction-n.destruction)), max(abs(a.net-n.net)) FROM a JOIN n USING(date_key)""").fetchone()
    assert diffs[0] == 0
    assert max(diffs[1:]) <= tolerance
    cutoff = con.execute("SELECT left_censored_mature_from_year FROM marts.dim_firm_age WHERE firm_age_key='l) Left Censored'").fetchone()[0]
    assert cutoff == 1982
    row = con.execute("SELECT employment,job_creation,job_destruction,net_employment_change FROM marts.firm_age_grouped_comparison WHERE year=2023 AND group_type='rollup; do not add to component groups'").fetchone()
    assert row == (122729040,13570310,12606078,964232)
    con.close()
