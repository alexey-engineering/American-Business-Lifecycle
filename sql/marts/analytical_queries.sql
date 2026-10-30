CREATE OR REPLACE VIEW marts.state_employment_growth AS
SELECT dt.year, geography_key AS state_fips, geography_name AS state,
       employment, employment_denominator, net_employment_change, employment_growth_rate_pct,
       rank() OVER (PARTITION BY year ORDER BY employment_growth_rate_pct DESC NULLS LAST) AS growth_rate_rank,
       rank() OVER (PARTITION BY year ORDER BY net_employment_change DESC NULLS LAST) AS net_change_rank
FROM marts.fact_business_dynamics f JOIN marts.dim_geography g USING (geography_key)
JOIN marts.dim_date dt ON dt.date_key=f.date_key
WHERE observation_type='state';

CREATE OR REPLACE VIEW marts.state_employment_contraction AS
SELECT * FROM marts.state_employment_growth
WHERE net_employment_change < 0
QUALIFY rank() OVER (PARTITION BY year ORDER BY net_employment_change ASC NULLS LAST) <= 10;

CREATE OR REPLACE VIEW marts.state_long_run_growth AS
WITH history AS (
    SELECT state_fips, state,
           first_value(employment) OVER (PARTITION BY state_fips ORDER BY year ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS employment_1978,
           last_value(employment) OVER (PARTITION BY state_fips ORDER BY year ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS employment_2023
    FROM marts.state_employment_growth
)
SELECT DISTINCT state_fips, state, employment_1978, employment_2023,
       employment_2023-employment_1978 AS employment_change_1978_2023,
       (employment_2023/employment_1978::DOUBLE-1)*100 AS employment_growth_1978_2023_pct
FROM history;

CREATE OR REPLACE VIEW marts.state_worst_annual_change AS
SELECT state_fips, state, year AS worst_year, net_employment_change AS worst_year_net_change,
       employment_growth_rate_pct AS worst_year_growth_rate_pct
FROM marts.state_employment_growth
QUALIFY row_number() OVER (PARTITION BY state_fips ORDER BY net_employment_change ASC NULLS LAST)=1;

CREATE OR REPLACE VIEW marts.state_period_dynamics AS
WITH annual AS (
    SELECT s.date_key AS year, g.geography_key AS state_fips, g.geography_name AS state,
           s.employment, s.employment_denominator, s.net_employment_change,
           CASE WHEN s.date_key BETWEEN 2008 AND 2010 THEN 'Great Recession window (2008–2010)'
                WHEN s.date_key=2020 THEN 'Pre-shock BDS year (ends March 2020)'
                WHEN s.date_key=2021 THEN 'COVID shock BDS year (ends March 2021)' END AS period
    FROM marts.fact_business_dynamics s
    JOIN marts.dim_geography g USING (geography_key)
    WHERE s.observation_type='state'
      AND (s.date_key BETWEEN 2008 AND 2010 OR s.date_key IN (2020,2021))
), period_totals AS (
    SELECT period,state_fips,state,
           count(*) AS years_in_period,
           sum(net_employment_change) AS net_employment_change,
           avg(net_employment_change) AS mean_annual_net_employment_change,
           sum(employment_denominator) AS summed_annual_denominator,
           sum(net_employment_change)/nullif(sum(employment_denominator),0)::DOUBLE*100 AS weighted_mean_annual_net_rate_pct
    FROM annual GROUP BY period,state_fips,state
)
SELECT *,
       rank() OVER (PARTITION BY period ORDER BY net_employment_change ASC) AS loss_rank_absolute,
       rank() OVER (PARTITION BY period ORDER BY weighted_mean_annual_net_rate_pct ASC) AS loss_rank_rate
FROM period_totals;

CREATE OR REPLACE VIEW marts.state_period_contractions AS
SELECT * FROM marts.state_period_dynamics
WHERE net_employment_change < 0 AND weighted_mean_annual_net_rate_pct < 0;

CREATE OR REPLACE VIEW marts.state_rate_outliers AS
WITH rates AS (
    SELECT year,state_fips,state,employment,employment_denominator,employment_growth_rate_pct,
           quantile_cont(employment_growth_rate_pct,0.25) OVER (PARTITION BY year) AS q1,
           quantile_cont(employment_growth_rate_pct,0.75) OVER (PARTITION BY year) AS q3
    FROM marts.state_employment_growth
    WHERE employment_growth_rate_pct IS NOT NULL
), marked AS (
    SELECT *, q1-1.5*(q3-q1) AS lower_iqr_bound, q3+1.5*(q3-q1) AS upper_iqr_bound
    FROM rates
)
SELECT year,state_fips,state,employment,employment_denominator,employment_growth_rate_pct,
       lower_iqr_bound,upper_iqr_bound,
       CASE WHEN employment_growth_rate_pct < lower_iqr_bound THEN 'Low outlier' ELSE 'High outlier' END AS outlier_direction
FROM marked
WHERE employment_growth_rate_pct < lower_iqr_bound OR employment_growth_rate_pct > upper_iqr_bound;

CREATE OR REPLACE VIEW marts.industry_employment_growth AS
SELECT dt.year, f.industry_key AS naics_sector, i.industry_name AS industry,
       f.employment, f.net_employment_change, f.employment_growth_rate_pct,
       rank() OVER (PARTITION BY dt.year ORDER BY f.net_employment_change DESC NULLS LAST) AS net_change_rank,
       f.net_employment_change / nullif(n.net_employment_change, 0)::DOUBLE * 100 AS contribution_to_national_change_pct
FROM marts.fact_business_dynamics f JOIN marts.dim_industry i USING (industry_key)
JOIN marts.fact_business_dynamics n ON n.date_key=f.date_key AND n.observation_type='national'
JOIN marts.dim_date dt ON dt.date_key=f.date_key
WHERE f.observation_type='industry';

CREATE OR REPLACE VIEW marts.industry_employment_contraction AS
SELECT * FROM marts.industry_employment_growth
WHERE net_employment_change < 0
QUALIFY rank() OVER (PARTITION BY year ORDER BY net_employment_change ASC NULLS LAST) <= 10;

CREATE OR REPLACE VIEW marts.firm_age_comparison AS
SELECT dt.year, d.firm_age_label, d.firm_age_group, f.employment, f.job_creation,
       f.job_destruction, f.net_employment_change, f.employment_growth_rate_pct,
       f.age_comparison_group, f.left_censored_is_mature
FROM marts.fact_business_dynamics f JOIN marts.dim_firm_age d USING (firm_age_key)
JOIN marts.dim_date dt ON dt.date_key=f.date_key
WHERE observation_type='firm_age';

CREATE OR REPLACE VIEW marts.firm_age_grouped_comparison AS
WITH disjoint_groups AS (
    SELECT f.date_key AS year, f.age_comparison_group AS comparison_group,
           sum(f.employment) AS employment, sum(f.job_creation) AS job_creation,
           sum(f.job_destruction) AS job_destruction,
           sum(f.net_employment_change) AS net_employment_change,
           'disjoint category' AS group_type
    FROM marts.fact_business_dynamics f
    WHERE f.observation_type='firm_age'
    GROUP BY f.date_key, f.age_comparison_group
), extended AS (
    SELECT f.date_key AS year, 'Mature extended (6+, left-censored included)' AS comparison_group,
           sum(f.employment) AS employment, sum(f.job_creation) AS job_creation,
           sum(f.job_destruction) AS job_destruction,
           sum(f.net_employment_change) AS net_employment_change,
           'rollup; do not add to component groups' AS group_type
    FROM marts.fact_business_dynamics f
    JOIN marts.dim_firm_age a USING (firm_age_key)
    WHERE f.observation_type='firm_age'
      AND (a.firm_age_group='Mature (6+, known age)' OR f.left_censored_is_mature)
    GROUP BY f.date_key
)
SELECT * FROM disjoint_groups
UNION ALL BY NAME
SELECT * FROM extended;

CREATE OR REPLACE VIEW marts.firm_size_comparison AS
SELECT dt.year, d.firm_size_label, d.min_employees, d.max_employees,
       f.employment, f.job_creation, f.job_destruction, f.net_employment_change,
       f.employment_growth_rate_pct
FROM marts.fact_business_dynamics f JOIN marts.dim_firm_size d USING (firm_size_key)
JOIN marts.dim_date dt ON dt.date_key=f.date_key
WHERE observation_type='firm_size';

CREATE OR REPLACE VIEW marts.covid_comparison AS
SELECT d.covid_period, min(d.year) AS first_bds_year, max(d.year) AS last_bds_year,
       count(*) AS years_in_period, f.observation_type, f.observation_code,
       avg(f.employment_growth_rate_pct) AS mean_annual_employment_growth_rate_pct,
       sum(f.net_employment_change)/nullif(sum(f.employment_denominator),0)::DOUBLE*100 AS denominator_weighted_annual_net_rate_pct,
       sum(f.job_creation) AS job_creation_sum, sum(f.job_destruction) AS job_destruction_sum,
       sum(f.net_employment_change) AS net_employment_change_sum,
       avg(f.job_creation) AS mean_annual_job_creation,
       avg(f.job_destruction) AS mean_annual_job_destruction,
       avg(f.net_employment_change) AS mean_annual_net_employment_change,
       avg(f.employment) AS mean_annual_employment
FROM marts.fact_business_dynamics f JOIN marts.dim_date d USING (date_key)
WHERE f.observation_type='national' AND d.year BETWEEN 2015 AND 2023
GROUP BY d.covid_period, f.observation_type, f.observation_code;

CREATE OR REPLACE VIEW marts.national_employment_contribution AS
SELECT d.year, f.observation_type, f.observation_code, f.net_employment_change,
       n.net_employment_change AS national_net_employment_change,
       f.net_employment_change / nullif(n.net_employment_change, 0)::DOUBLE * 100 AS contribution_to_national_change_pct
FROM marts.fact_business_dynamics f
JOIN marts.fact_business_dynamics n ON n.date_key=f.date_key AND n.observation_type='national'
JOIN marts.dim_date d ON d.date_key=f.date_key
WHERE f.observation_type IN ('state','industry');

CREATE OR REPLACE VIEW marts.executive_overview AS
SELECT d.year, f.employment, f.job_creation, f.job_destruction,
       f.net_employment_change, f.employment_growth_rate_pct
FROM marts.fact_business_dynamics f JOIN marts.dim_date d ON d.date_key=f.date_key
WHERE f.observation_type='national';

CREATE OR REPLACE VIEW marts.employment_share AS
SELECT f.date_key AS year, f.observation_type, f.observation_code, f.employment,
       n.employment AS national_employment,
       f.employment / nullif(n.employment, 0)::DOUBLE * 100 AS employment_share_pct
FROM marts.fact_business_dynamics f
JOIN marts.fact_business_dynamics n ON n.date_key=f.date_key AND n.observation_type='national'
WHERE f.observation_type IN ('state','industry','firm_age','firm_size');

-- Power BI consumes one filtered view per independent BDS margin.
CREATE OR REPLACE VIEW marts.pbi_national_dynamics AS
SELECT * FROM marts.fact_business_dynamics WHERE observation_type='national';
CREATE OR REPLACE VIEW marts.pbi_state_dynamics AS
SELECT * FROM marts.fact_business_dynamics WHERE observation_type='state';
CREATE OR REPLACE VIEW marts.pbi_industry_dynamics AS
SELECT * FROM marts.fact_business_dynamics WHERE observation_type='industry';
CREATE OR REPLACE VIEW marts.pbi_firm_age_dynamics AS
SELECT * FROM marts.fact_business_dynamics WHERE observation_type='firm_age';
CREATE OR REPLACE VIEW marts.pbi_firm_size_dynamics AS
SELECT * FROM marts.fact_business_dynamics WHERE observation_type='firm_size';
