# Methodology

## Source grain

Each source row is one year crossed with exactly one category of a single one-way BDS table. The five selected tables are economy-wide, state, NAICS sector, firm age, and firm size. Source row counts are 46, 2,346, 874, 552, and 460 respectively. Rows are not a single cube; dimensions in separate one-way tables cannot be crossed or summed together.

The economy-wide file begins in 1978 and includes through 2023. Each classified source row is an annual aggregate; one row represents the full U.S. economy or one state, sector, firm-age group, or firm-size group for one year. The selected table keys are `(year)` for economy-wide and `(year, source category code)` for each one-way table.

## Sample inspection and profiling

The economy-wide CSV is the representative sample. It has 46 rows, 25 columns, integer-like measure fields, decimal rate fields, and no category code. The complete selected set has 4,278 rows and 25–26 columns. Detailed counts, categories, and null/suppression checks are recorded in `data_quality.md` and in `data/raw/bds/ingestion_log.json`.

## Transformation rules

1. Retain source CSV bytes unchanged in `data/raw/bds/`.
2. Load source fields as text into DuckDB RAW tables.
3. Cast numeric measures with `TRY_CAST`; literal `X` becomes NULL in the analytical layer and is tracked as a suppression marker. Raw source cells remain intact.
4. Normalize year to an integer and January 1 date key.
5. Standardize names and map state, sector, firm-age, and firm-size categories.
6. Union one-way rows in the staging/intermediate layers while retaining `observation_type`, `observation_code`, and `source_file` so the independent margins remain distinguishable.

## BDS annual time convention

BDS employment is measured in the payroll period including March 12 of each year, and job creation/destruction in BDS year *t* compare March 12 employment in *t−1* with March 12 employment in *t*. Thus, BDS year 2020 ends in March 2020 and is treated as pre-shock; BDS year 2021 captures the March 2020–March 2021 shock window. See the Census [BDS codebook](https://www.census.gov/content/dam/Census/programs-surveys/business-dynamics-statistics/bds-codebook.pdf) and [BDS FAQ](https://www.census.gov/programs-surveys/bds/about/faq.html).

## COVID comparison

Compare 2015–2020 as pre-shock (six BDS years ending by March 2020), 2021 as the COVID shock (March 2020–March 2021), and 2022–2023 as the rebound. Period flow totals, mean annual flows, arithmetic mean annual BDS rates, and denominator-weighted rates are shown separately. Unequal period lengths mean summed flow totals should not be interpreted as annualized comparisons.

The state recession comparison starts in BDS year 2008 because year 2007 ends in March 2007, before the recession contraction shown in the queried series. The selected state view also retains BDS years 2020 and 2021 as separate pre-shock and shock windows.

## Fact grain and key

`marts.fact_business_dynamics` grain: one year and one selected BDS observation category. Natural key: `(date_key, observation_type, observation_code)`. The four dimension FKs point to the selected category dimension; all other dimension keys use the explicit all-category member. The observation type/code pair preserves the source's independent one-way table grain and prevents false cross-dimensional inference.

The fact contains only the selected measures: employment and BDS denominator; establishment births/deaths; job creation and rate; job destruction and rate; net employment change and rate; source/suppression indicators; and firm-age comparison flags. Firm count, establishment stock, component flows, reallocation, and firm-death measures remain only in RAW and are excluded from the analytical fact. The five dimension FKs are date, geography, industry, firm age, and firm size.

## Scope limitations

The state and industry one-way files support independent rankings. They do not identify which industry drove a particular state's change. To answer state-by-industry questions would require a larger crossing outside this minimum scope.

For firm age, the fact grain remains one year x one BDS age code. The year-dependent `left_censored_is_mature` flag is a fact attribute and does not alter the natural key. Since the Census describes left-censored firms as born before 1977 but true age is unknown, the project treats them as mature from 1982, the first year guaranteed to meet the 6+ threshold even under the more inclusive Census FAQ wording. Before then they remain an unknown-age group. `Mature extended` is a non-additive rollup over known-age 6+ plus left-censored, from 1982 onward.

The fact is deliberately non-additive across `observation_type`: it contains five independent one-way margins. Every margin separately covers the same national employment stock in 2023, so summing the mixed fact without a margin filter yields five times national employment. Power BI therefore uses five filtered MART views, one for each observation type; the shared mixed fact is not a report source.
