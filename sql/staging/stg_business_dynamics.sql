CREATE SCHEMA IF NOT EXISTS staging;
CREATE OR REPLACE TABLE staging.business_dynamics AS
WITH combined AS (
    SELECT 'national' AS slice_type, 'US' AS slice_code, 'bds2023_economy.csv' AS source_file, * FROM raw.bds_economy
    UNION ALL BY NAME
    SELECT 'state' AS slice_type, st AS slice_code, 'bds2023_state.csv' AS source_file, * EXCLUDE (st) FROM raw.bds_state
    UNION ALL BY NAME
    SELECT 'industry' AS slice_type, sector AS slice_code, 'bds2023_sector.csv' AS source_file, * EXCLUDE (sector) FROM raw.bds_sector
    UNION ALL BY NAME
    SELECT 'firm_age' AS slice_type, fage AS slice_code, 'bds2023_firm_age.csv' AS source_file, * EXCLUDE (fage) FROM raw.bds_firm_age
    UNION ALL BY NAME
    SELECT 'firm_size' AS slice_type, fsize AS slice_code, 'bds2023_firm_size.csv' AS source_file, * EXCLUDE (fsize) FROM raw.bds_firm_size
), parsed AS (
    SELECT
        try_cast(year AS SMALLINT) AS year,
        slice_type,
        slice_code,
        source_file,
        try_cast(emp AS BIGINT) AS employment,
        try_cast(denom AS BIGINT) AS employment_denominator,
        try_cast(estabs_entry AS BIGINT) AS establishment_births,
        try_cast(estabs_exit AS BIGINT) AS establishment_deaths,
        try_cast(job_creation AS BIGINT) AS job_creation,
        try_cast(job_creation_rate AS DOUBLE) AS job_creation_rate_pct,
        try_cast(job_destruction AS BIGINT) AS job_destruction,
        try_cast(job_destruction_rate AS DOUBLE) AS job_destruction_rate_pct,
        try_cast(net_job_creation AS BIGINT) AS net_employment_change,
        try_cast(net_job_creation_rate AS DOUBLE) AS employment_growth_rate_pct,
        CASE WHEN concat_ws('|', emp, denom, estabs_entry, estabs_exit, job_creation, job_creation_rate, job_destruction, job_destruction_rate, net_job_creation, net_job_creation_rate) LIKE '%X%' THEN TRUE ELSE FALSE END AS has_suppression_marker
    FROM combined
)
SELECT *, make_date(year, 1, 1) AS year_date,
       CASE WHEN slice_type = 'firm_age' AND slice_code IN ('a) 0','b) 1','c) 2','d) 3','e) 4','f) 5') THEN 'Young (0–5)'
            WHEN slice_type = 'firm_age' AND slice_code IN ('g) 6 to 10','h) 11 to 15','i) 16 to 20','j) 21 to 25','k) 26+') THEN 'Mature (6+, known age)'
            WHEN slice_type = 'firm_age' AND slice_code = 'l) Left Censored' THEN 'Left-censored (age unknown)'
            ELSE NULL END AS firm_age_group,
       slice_type = 'firm_age' AND slice_code = 'l) Left Censored' AND year >= 1982 AS left_censored_is_mature,
       CASE WHEN slice_type <> 'firm_age' THEN NULL
            WHEN slice_code IN ('a) 0','b) 1','c) 2','d) 3','e) 4','f) 5') THEN 'Young (0–5)'
            WHEN slice_code IN ('g) 6 to 10','h) 11 to 15','i) 16 to 20','j) 21 to 25','k) 26+') THEN 'Mature (6+, known age)'
            WHEN slice_code = 'l) Left Censored' AND year < 1982 THEN 'Left-censored (age unknown)'
            WHEN slice_code = 'l) Left Censored' THEN 'Left-censored (mature by lower bound)' END AS age_comparison_group,
       CASE WHEN year BETWEEN 2015 AND 2020 THEN 'Pre-COVID (2015–2020)'
            WHEN year = 2021 THEN 'COVID shock (2021)'
            WHEN year BETWEEN 2022 AND 2023 THEN 'Rebound (2022–2023)'
            ELSE 'Outside comparison window' END AS covid_period
FROM parsed;
