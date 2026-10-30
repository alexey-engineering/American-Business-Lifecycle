CREATE SCHEMA IF NOT EXISTS marts;

CREATE OR REPLACE TABLE marts.dim_date AS
SELECT DISTINCT year AS date_key, year, year_date, covid_period,
       year BETWEEN 2015 AND 2020 AS is_pre_covid,
       year = 2021 AS is_covid_period,
       year BETWEEN 2022 AND 2023 AS is_post_covid
FROM intermediate.business_dynamics;

CREATE OR REPLACE TABLE marts.dim_geography AS
SELECT DISTINCT CASE WHEN slice_type = 'state' THEN slice_code ELSE 'US' END AS geography_key,
       CASE WHEN slice_type = 'state' THEN slice_code ELSE 'US' END AS geography_code,
       CASE WHEN slice_type <> 'state' THEN 'United States' ELSE CASE slice_code
         WHEN '01' THEN 'Alabama' WHEN '02' THEN 'Alaska' WHEN '04' THEN 'Arizona' WHEN '05' THEN 'Arkansas'
         WHEN '06' THEN 'California' WHEN '08' THEN 'Colorado' WHEN '09' THEN 'Connecticut' WHEN '10' THEN 'Delaware'
         WHEN '11' THEN 'District of Columbia' WHEN '12' THEN 'Florida' WHEN '13' THEN 'Georgia' WHEN '15' THEN 'Hawaii'
         WHEN '16' THEN 'Idaho' WHEN '17' THEN 'Illinois' WHEN '18' THEN 'Indiana' WHEN '19' THEN 'Iowa'
         WHEN '20' THEN 'Kansas' WHEN '21' THEN 'Kentucky' WHEN '22' THEN 'Louisiana' WHEN '23' THEN 'Maine'
         WHEN '24' THEN 'Maryland' WHEN '25' THEN 'Massachusetts' WHEN '26' THEN 'Michigan' WHEN '27' THEN 'Minnesota'
         WHEN '28' THEN 'Mississippi' WHEN '29' THEN 'Missouri' WHEN '30' THEN 'Montana' WHEN '31' THEN 'Nebraska'
         WHEN '32' THEN 'Nevada' WHEN '33' THEN 'New Hampshire' WHEN '34' THEN 'New Jersey' WHEN '35' THEN 'New Mexico'
         WHEN '36' THEN 'New York' WHEN '37' THEN 'North Carolina' WHEN '38' THEN 'North Dakota' WHEN '39' THEN 'Ohio'
         WHEN '40' THEN 'Oklahoma' WHEN '41' THEN 'Oregon' WHEN '42' THEN 'Pennsylvania' WHEN '44' THEN 'Rhode Island'
         WHEN '45' THEN 'South Carolina' WHEN '46' THEN 'South Dakota' WHEN '47' THEN 'Tennessee' WHEN '48' THEN 'Texas'
         WHEN '49' THEN 'Utah' WHEN '50' THEN 'Vermont' WHEN '51' THEN 'Virginia' WHEN '53' THEN 'Washington'
         WHEN '54' THEN 'West Virginia' WHEN '55' THEN 'Wisconsin' WHEN '56' THEN 'Wyoming' ELSE 'Unknown' END END AS geography_name,
       CASE WHEN slice_type = 'state' THEN 'State' ELSE 'National' END AS geography_level
FROM intermediate.business_dynamics WHERE slice_type IN ('state','national');

CREATE OR REPLACE TABLE marts.dim_industry AS
SELECT DISTINCT CASE WHEN slice_type = 'industry' THEN slice_code ELSE '00' END AS industry_key,
       CASE WHEN slice_type = 'industry' THEN slice_code ELSE '00' END AS industry_code,
       CASE WHEN slice_type <> 'industry' THEN 'All industries' ELSE CASE slice_code
         WHEN '11' THEN 'Agriculture, forestry, fishing and hunting' WHEN '21' THEN 'Mining, quarrying, and oil and gas extraction'
         WHEN '22' THEN 'Utilities' WHEN '23' THEN 'Construction' WHEN '31-33' THEN 'Manufacturing'
         WHEN '42' THEN 'Wholesale trade' WHEN '44-45' THEN 'Retail trade' WHEN '48-49' THEN 'Transportation and warehousing'
         WHEN '51' THEN 'Information' WHEN '52' THEN 'Finance and insurance' WHEN '53' THEN 'Real estate and rental and leasing'
         WHEN '54' THEN 'Professional, scientific, and technical services' WHEN '55' THEN 'Management of companies and enterprises'
         WHEN '56' THEN 'Administrative and support and waste management services' WHEN '61' THEN 'Educational services'
         WHEN '62' THEN 'Health care and social assistance' WHEN '71' THEN 'Arts, entertainment, and recreation'
         WHEN '72' THEN 'Accommodation and food services' WHEN '81' THEN 'Other services (except public administration)'
         ELSE 'Unknown' END END AS industry_name,
       CASE WHEN slice_type = 'industry' THEN 'NAICS sector' ELSE 'All industries' END AS industry_level
FROM intermediate.business_dynamics WHERE slice_type IN ('industry','national');

CREATE OR REPLACE TABLE marts.dim_firm_age AS
SELECT DISTINCT CASE WHEN slice_type = 'firm_age' THEN slice_code ELSE 'ALL' END AS firm_age_key,
       CASE WHEN slice_type = 'firm_age' THEN slice_code ELSE 'ALL' END AS firm_age_code,
       CASE WHEN slice_type = 'firm_age' THEN slice_code ELSE 'All firm ages' END AS firm_age_label,
       CASE WHEN slice_type <> 'firm_age' THEN 'All firm ages'
            WHEN slice_code IN ('a) 0','b) 1','c) 2','d) 3','e) 4','f) 5') THEN 'Young (0–5)'
            WHEN slice_code IN ('g) 6 to 10','h) 11 to 15','i) 16 to 20','j) 21 to 25','k) 26+') THEN 'Mature (6+, known age)'
            ELSE 'Left-censored (age unknown)' END AS firm_age_group,
       slice_type = 'firm_age' AND slice_code = 'l) Left Censored' AS is_left_censored,
       CASE WHEN slice_type = 'firm_age' AND slice_code = 'l) Left Censored' THEN 1982 ELSE NULL END AS left_censored_mature_from_year
FROM intermediate.business_dynamics WHERE slice_type IN ('firm_age','national');

CREATE OR REPLACE TABLE marts.dim_firm_size AS
SELECT DISTINCT CASE WHEN slice_type = 'firm_size' THEN slice_code ELSE 'ALL' END AS firm_size_key,
       CASE WHEN slice_type = 'firm_size' THEN slice_code ELSE 'ALL' END AS firm_size_code,
       CASE WHEN slice_type = 'firm_size' THEN slice_code ELSE 'All firm sizes' END AS firm_size_label,
       CASE WHEN slice_type = 'firm_size' THEN try_cast(regexp_extract(slice_code, '([0-9]+)', 1) AS INTEGER) ELSE NULL END AS min_employees,
       CASE WHEN slice_type = 'firm_size' THEN try_cast(regexp_extract(slice_code, 'to ([0-9]+)', 1) AS INTEGER) ELSE NULL END AS max_employees
FROM intermediate.business_dynamics WHERE slice_type IN ('firm_size','national');

CREATE OR REPLACE TABLE marts.fact_business_dynamics AS
SELECT year AS date_key,
       CASE WHEN slice_type = 'state' THEN slice_code ELSE 'US' END AS geography_key,
       CASE WHEN slice_type = 'industry' THEN slice_code ELSE '00' END AS industry_key,
       CASE WHEN slice_type = 'firm_age' THEN slice_code ELSE 'ALL' END AS firm_age_key,
       CASE WHEN slice_type = 'firm_size' THEN slice_code ELSE 'ALL' END AS firm_size_key,
       age_comparison_group,
       left_censored_is_mature,
       slice_type AS observation_type, slice_code AS observation_code, source_file,
       employment, employment_denominator,
       establishment_births, establishment_deaths,
       job_creation, job_creation_rate_pct,
       job_destruction, job_destruction_rate_pct,
       net_employment_change, employment_growth_rate_pct,
       has_suppression_marker
FROM intermediate.business_dynamics;
