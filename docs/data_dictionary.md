# Data dictionary and dimensional model

## Official source

- **Source:** U.S. Census Bureau, Business Dynamics Statistics (BDS), 2023 release.
- **Dataset:** BDS time series, 1978–2023; official comma-separated files.
- **Downloads:** `https://www2.census.gov/programs-surveys/bds/tables/time-series/2023/bds2023.csv` (economy), suffixes `_st.csv` (state), `_sec.csv` (sector), `_fa.csv` (firm age), `_fz.csv` (firm size).
- **API:** `https://api.census.gov/data/timeseries/bds`; queries require an API key. API variable metadata: `https://api.census.gov/data/timeseries/bds/variables.html`.
- **Dimensions:** national/state geography; 2-digit NAICS sectors; firm age; firm size.
- **Relevant measures:** EMP, DENOM, JOB_CREATION, JOB_DESTRUCTION, NET_JOB_CREATION, establishment entry/exit, firms, establishments, rates, and firm death measures.

## Source fields retained in analytics

All selected measure names map back to the official CSV columns below.

| Source field | Analytical name | Meaning / unit |
|---|---|---|
| `year` | `year`, `year_date` | Reference year; date key normalized to Jan 1 |
| `st` | `geography_code` | Two-character state FIPS |
| `sector` | `industry_code` | BDS NAICS sector group code |
| `fage` | `firm_age_code` | BDS firm age band, including left-censored |
| `fsize` | `firm_size_code` | BDS employment-size band |
| `emp` | `employment` | Employment stock (persons/jobs as defined by BDS) |
| `denom` | `employment_denominator` | BDS rate denominator |
| `estabs_entry` | `establishment_births` | Establishment entries |
| `estabs_exit` | `establishment_deaths` | Establishment exits |
| `job_creation` | `job_creation` | Jobs created |
| `job_creation_rate` | `job_creation_rate_pct` | BDS job creation rate, percent |
| `job_destruction` | `job_destruction` | Jobs destroyed |
| `job_destruction_rate` | `job_destruction_rate_pct` | BDS job destruction rate, percent |
| `net_job_creation` | `net_employment_change` | Job creation less destruction |
| `net_job_creation_rate` | `employment_growth_rate_pct` | BDS net job creation rate, used as the annual employment growth rate proxy |
| literal `X` in measures | NULL + `has_suppression_marker` | Unavailable/structural marker; retained verbatim in RAW |

Other columns delivered in the original small CSVs remain available only in the RAW tables and are excluded from STAGING/MART because they are not needed for the questions (for example firm counts, establishment counts, component flows, firm-death counts, and rates for component flows).

## Categories

- States: 50 states and District of Columbia, with Census two-digit FIPS codes.
- Industry: 19 BDS NAICS sector groupings, including combined NAICS groups `31-33`, `44-45`, and `48-49`.
- Firm age source codes (preserved exactly): `a) 0`, `b) 1`, `c) 2`, `d) 3`, `e) 4`, `f) 5`, `g) 6 to 10`, `h) 11 to 15`, `i) 16 to 20`, `j) 21 to 25`, `k) 26+`, and `l) Left Censored`. Young means 0–5; known-age mature means 6+. BDS defines left-censored firms as born before 1977 with unknown true age. The project conservatively flags them mature from 1982 onward; before then their age class remains unknown.
- Firm size source codes (preserved exactly): `a) 1 to 4`, `b) 5 to 9`, `c) 10 to 19`, `d) 20 to 99`, `e) 100 to 499`, `f) 500 to 999`, `g) 1000 to 2499`, `h) 2500 to 4999`, `i) 5000 to 9999`, `j) 10000+` employees.

## Model tables

| Table | Purpose and grain | Primary key | Foreign keys / main columns | Source |
|---|---|---|---|---|
| `marts.dim_date` | One row per year | `date_key` | year, date, pre-shock (2015–2020), shock (2021), and post-shock (2022–2023) flags | `year` |
| `marts.dim_geography` | One row per U.S. total or state | `geography_key` | FIPS, name, level | `st` |
| `marts.dim_industry` | One row per all-industry or sector category | `industry_key` | NAICS sector code, label, level | `sector` |
| `marts.dim_firm_age` | One row per all-age or age category | `firm_age_key` | exact source code, label, static age group, left-censored flag, year 1982 maturity threshold | `fage` |
| `marts.dim_firm_size` | One row per all-size or size band | `firm_size_key` | size code, label, employee range | `fsize` |
| `marts.fact_business_dynamics` | One year and one BDS source category from a one-way series | Natural key `(date_key, observation_type, observation_code)` | `date_key`, `geography_key`, `industry_key`, `firm_age_key`, `firm_size_key`, `age_comparison_group`, `left_censored_is_mature`, `observation_type`, `observation_code`, `source_file`, `employment`, `employment_denominator`, `establishment_births`, `establishment_deaths`, `job_creation`, `job_creation_rate_pct`, `job_destruction`, `job_destruction_rate_pct`, `net_employment_change`, `employment_growth_rate_pct`, `has_suppression_marker` | Five selected CSVs |

Each fact row uses its actual category key in one relevant dimension and the explicit `ALL`/U.S.-total member in the other dimensions. `observation_type` and `observation_code` are retained because the source tables are separate one-way margins. The `left_censored_is_mature` fact flag is true for left-censored firm-age rows from 1982 onward. `age_comparison_group` is year-dependent; the mature-extended analytical view is a non-additive rollup. The fact is not additive across observation types: each of its five margins independently contains the national employment stock. Power BI should connect only to the five margin-filtered `marts.pbi_*_dynamics` views; do not sum the mixed fact across margins. This model does not assert combinations the source does not provide.
