CREATE SCHEMA IF NOT EXISTS intermediate;
CREATE OR REPLACE TABLE intermediate.business_dynamics AS
SELECT * FROM staging.business_dynamics
WHERE year BETWEEN 1978 AND 2023;
