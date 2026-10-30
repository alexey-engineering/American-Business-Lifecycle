# Data quality and source profile

## Selected data profile

| Source file | Rows | Columns | Year range | Category coverage |
|---|---:|---:|---|---|
| Economy-wide | 46 | 25 | 1978–2023 | U.S. total |
| State | 2,346 | 26 | 1978–2023 | 51 geographies (50 states + DC) |
| Sector | 874 | 26 | 1978–2023 | 19 NAICS sector groups |
| Firm age | 552 | 26 | 1978–2023 | 12 categories |
| Firm size | 460 | 26 | 1978–2023 | 10 categories |
| **Total** | **4,278** | — | **1978–2023** | Separate one-way margins |

All five files were checked for header shape, row counts, year range, unique categories, and duplicate key combinations. Each has a unique year/category combination at its own source grain. The exact counts and checksums are in `data/raw/bds/ingestion_log.json`.

## Detailed profile results

- RAW fields load as `VARCHAR` to preserve every source token. STAGING converts year to `SMALLINT`, counts/levels to `BIGINT`, rates to `DOUBLE`, dates to `DATE`, and suppression marker to `BOOLEAN`.
- All source records cover every year from 1978 through 2023. The state, sector, age, and size sources have respectively 51, 19, 12, and 10 category values. Expected rows per category match 46 years in each source.
- Full-row duplicates: 0 in every source. Duplicate `(year, category)` combinations: 0 in every classified source. Duplicate natural fact keys: 0 across all 4,278 records.
- The raw economy sample contains 46 rows x 25 columns. The complete selected sources contain 4,278 rows and 25–26 columns. Numeric employment ranges from 106,933 (minimum published state-year value) to 137,462,444 (U.S. total in 2023); BDS net change includes negative annual values.
- The 85 missing analytical employment and net-change values occur in firm-age rows carrying structural/unavailable `X` markers. There are 131 firm-age rows with at least one `X` marker. Other selected series have no missing employment/net-change values. Raw CSV columns themselves contain no blank cells.
- `firm_age_missingness_by_year.csv` profiles the null pattern: the 85 missing employment, denominator, establishment-birth, job-creation, and net-change cells run from 1978 to 2002. Employment nulls decline from 9 in 1978 to 1 per year in 1998–2002, then are zero from 2003 onward. Death and job-destruction nulls total 131 because `X` remains present in firm-age rows across years as well as in early left-censored-age cells.
- Employment, job creation, and job destruction have no negative values. Zero counts are valid and preserved; no selected employment observations are zero. Net change may be negative by definition.
- Census noise infusion yields one one-job difference between job creation less destruction and published net change (Louisiana, 1985); metric tests allow that observed rounding tolerance and the official net field remains authoritative.

## Issues and treatment

- **Suppression/structural marker:** the firm-age series contains literal `X` cells in measures (for example, 1978 age-zero exits). Census API documentation defines `X` as structurally missing/zero and warns API result values may be returned as 0 with a flag. This CSV uses the marker directly. RAW keeps it; staging converts it to NULL and sets `has_suppression_marker`.
- **Missing numeric values:** after conversion, NULL means the source did not publish a usable numeric cell. No NULL is replaced with zero. Aggregate calculations should ignore unavailable cells and show coverage.
- **Negative values:** net employment change is allowed to be negative. Employment and event counts should be nonnegative; these checks are encoded in quality tests.
- **Zero values:** valid zeros are retained. Rates whose denominators are zero or whose source value is unavailable remain NULL.
- **Duplicate combinations:** duplicate year/category combinations fail quality tests; no deduplication is performed silently.
- **Noise infusion:** Census documents disclosure avoidance noise infusion for employment/job-flow statistics; small differences between aggregates and component sums can occur.
- **Coverage and BDS timing:** the selected latest release is annual 1978–2023. BDS year *t* uses the payroll period including March 12 of *t* and compares job flows with March 12 of *t−1*. Thus, 2020 ends in March 2020 and is pre-shock; 2021 is the March 2020–March 2021 shock window. Source: [Census BDS codebook](https://www.census.gov/content/dam/Census/programs-surveys/business-dynamics-statistics/bds-codebook.pdf).

## Validation outputs

Run `python ingestion/build_database.py` to recreate the database, then use the SQL assertions in `tests/` to validate schema, keys, categories, nulls, relationships, and representative metric arithmetic.

## Firm-age reconciliation

For 2023, employment by disjoint firm-age categories sums exactly to the national stock of 137,462,444. The age-margin flow sums are 17,122 higher for job creation, 8,199 higher for job destruction, and 8,923 higher for net change than the national table. Across the full 1978–2023 series, the maximum absolute age-to-national differences are 28,068 for creation, 8,199 for destruction, and 22,037 for net change; employment reconciles exactly in every year. Tests therefore use zero tolerance for employment and a 30,000-job tolerance for those noisy flow margins.

For 2023, young (0–5) + known-age mature (6+) employment covers 84,129,575 (61.2% of the national stock). Left-censored firms account for another 52,332,869. Mature extended includes the 6+ known-age rows and left-censored rows from 1982 onward. The 1978 left-censored employment cell is 65,357,166, or 93.0% of national employment, and remains age-unknown rather than being forced into mature.

## Non-additive fact and margin checks

For 2023, each margin separately sums to 137,462,444 employment (national, state, industry, firm age, and firm size). A sum of the shared fact with no `observation_type` filter is 687,312,220, exactly 5 times the national total. This is not a data defect; the source is five separate one-way tables. Tests assert the five-times result, and Power BI uses the five margin-filtered MART views instead of the shared mixed fact.

Across 1978–2023, the maximum annual absolute difference in net employment change between each margin and the national series was: states 1,427 (2001), sectors 7,257 (2021), firm age 22,037 (1984), and firm size 7,099 (1978). The test uses a shared 30,000-job absolute tolerance, above the largest observed gap; state employment stock totals are exact in every year. Tests also recalculate ten source measures (including the seven primary KPIs) from RAW against the national MART row and run an intentional corrupted-copy test to confirm duplicate fact keys are rejected.

For state contraction, `state_contraction.csv` contains 110 negative state-period rows across the 2008–2010 recession window, the pre-shock BDS year 2020, and the COVID shock BDS year 2021. The recession window excludes BDS year 2007 because it ends in March 2007. `state_period_comparison.csv` retains all state-period observations so absolute-loss and rate ranks can be compared; the rate is a denominator-weighted mean annual BDS rate. `state_rate_outliers.csv` uses the 1.5×IQR rule within each year and includes employment denominators to make small-base volatility visible.

Idempotence was checked by running `ingestion/build_database.py` twice in succession. Row counts were unchanged: RAW 46/2,346/874/552/460; STAGING and INTERMEDIATE 4,278 each; MART dimensions 46/52/20/13/11 and fact 4,278. The corruption demonstration copied the DuckDB file, inserted a duplicate fact row, then invoked `test_fact_key_uniqueness`; pytest failed as expected with `duplicate_count == 1`.

The BDS FAQ defines left-censored firms as born before 1977 with unknown true age; the glossary notes the LBD age series starts in 1976 and describes left censoring at the pre-observation boundary. To avoid assigning maturity too early under the FAQ definition, 1982 is the earliest year used for the 6+ lower-bound flag. Sources: [BDS FAQ](https://www.census.gov/programs-surveys/bds/about/faq.html), [BDS glossary](https://www.census.gov/content/dam/Census/programs-surveys/business-dynamics-statistics/codebook-glossary.pdf).

## External validation

The national job-creation, job-destruction, and net-change series were compared with the BLS Business Employment Dynamics (BED) annual March-to-March table, published in thousands. The BDS API did not allow an unauthenticated query (`Missing Key`), so BED provides the independent external check. The comparison table and reproducible script are `data/processed/external_validation.csv` and `analysis/compare_bds_bed.py`.

| Year ended in March | Metric | Project BDS (jobs) | Published BLS BED (thousands) | BLS converted to jobs | Difference BDS − BLS |
|---:|---|---:|---:|---:|---:|
| 2021 | Job creation | 15,069,167 | 12,522 | 12,522,000 | +2,547,167 |
| 2021 | Job destruction | 20,587,364 | 18,001 | 18,001,000 | +2,586,364 |
| 2021 | Net change | -5,518,197 | -5,479 | -5,479,000 | -39,197 |
| 2022 | Job creation | 21,652,177 | 17,911 | 17,911,000 | +3,741,177 |
| 2022 | Job destruction | 14,567,755 | 10,982 | 10,982,000 | +3,585,755 |
| 2022 | Net change | 7,084,422 | 6,929 | 6,929,000 | +155,422 |
| 2023 | Job creation | 18,450,927 | 16,008 | 16,008,000 | +2,442,927 |
| 2023 | Job destruction | 15,011,588 | 12,669 | 12,669,000 | +2,342,588 |
| 2023 | Net change | 3,439,339 | 3,339 | 3,339,000 | +100,339 |

**Interpretation and limitations:** BED provides an independent reference with annual March-to-March periods; the table is rounded to thousands. BDS employment refers to the payroll period including March 12. Although the periods are close, BED comes from quarterly QCEW/UI reports while BDS uses the LBD linked with the Business Register/County Business Patterns. Coverage, linkage rules, revisions, and flow tabulations differ. Gross job-creation/destruction values are therefore not interchangeable, and no equality tolerance is imposed between programs. BDS net change is close to BED in each compared year: the relative differences, using absolute BED net as denominator, are -0.72% in 2021, +2.24% in 2022, and +3.01% in 2023. Gross flows differ more; this is an external plausibility check, not an equality validation. Sources: [BLS BED annual table](https://www.bls.gov/web/cewbd/anntab1_1.txt), [BED method and coverage](https://www.bls.gov/bdm/bdmfaq.htm), [BDS employment definition](https://www.census.gov/programs-surveys/bds/about.html).

The Census API returned `Missing Key` without credentials; no Census values were invented to fill that gap. The BDS download is pinned to the SHA-256 values in `ingestion_log.json`; `ingest_bds.py` rejects changed content before overwriting a file. The release is **2023 BDS**, published on 2025-09-25; the local copies were downloaded on 2026-10-29 (America/Monterrey). Expected hashes are stored in the script and observed hashes in the log.
