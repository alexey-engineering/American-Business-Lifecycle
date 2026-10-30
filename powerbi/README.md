# Power BI handoff

The intended report uses the five filtered views `marts.pbi_national_dynamics`, `marts.pbi_state_dynamics`, `marts.pbi_industry_dynamics`, `marts.pbi_firm_age_dynamics`, and `marts.pbi_firm_size_dynamics`, plus the five dimensions, from `database/business_lifecycle.duckdb`, with DuckDB ODBC as the connection. Import the view for the page's margin. Do not import the mixed `marts.fact_business_dynamics` table, RAW, or STAGING.

This workspace runs on macOS and has no Power BI Desktop authoring runtime. A valid `.pbix` cannot be generated or validated here. Use the model specification and DAX below in Power BI Desktop on Windows; create and save the final file as `american_business_lifecycle.pbix` in this directory. The analytical output and project remain reproducible without Power BI.

## Report pages (five maximum)

1. **Executive Overview:** employment, job creation, job destruction, net change cards; national annual trend; 2023 top growing states and contractions by selected period (2023 has no state net losses).
2. **Geography:** state employment and net-change comparison, rate and absolute-loss rankings for 2008–2010, pre-shock BDS year 2020, and COVID shock BDS year 2021, annual trend; year/state/period slicers.
3. **Industry:** sector comparison, net-change ranking, contribution to national net change, annual trend.
4. **Business Structure:** firm age and firm-size comparisons with employment, job creation, destruction, net change, and rate.
5. **Time:** long-term national trend; pre-shock (2015–2020), shock (2021), and rebound (2022–2023) comparisons. BDS year *t* measures change from March 12 of *t−1* to March 12 of *t*.

## Model relationships

Create one-to-many, single-direction relationships from each dimension key to the matching FK in each filtered view: Date, Geography, Industry, Firm Age, and Firm Size. Hide keys and source columns from report view. Set `dim_date[year]` as the date table only after ensuring it has one row per year; use `year_date` as the date column. Add a year hierarchy and a state-name geography hierarchy.

### Double-counting risk

The underlying fact unions five one-way BDS margins, each of which independently sums to the national employment stock. An unfiltered `SUM(employment)` across the shared fact therefore counts the national stock five times. The MART supplies one filter-specific view per margin, and report measures below reference only that page's view. Trade-off: the semantic model has five logical fact sources and some repeated relationships/measures; the DuckDB physical fact remains one copy. This is safer than relying on users to remember a hidden `observation_type` filter.

## Power BI measures (DAX)

```DAX
Employment — National = SUM(pbi_national_dynamics[employment])
Employment — State = SUM(pbi_state_dynamics[employment])
Employment — Industry = SUM(pbi_industry_dynamics[employment])
Employment — Firm Age = SUM(pbi_firm_age_dynamics[employment])
Employment — Firm Size = SUM(pbi_firm_size_dynamics[employment])
Job Creation — National = SUM(pbi_national_dynamics[job_creation])
Job Destruction — National = SUM(pbi_national_dynamics[job_destruction])
Net Change — National = SUM(pbi_national_dynamics[net_employment_change])
Net Change — State = SUM(pbi_state_dynamics[net_employment_change])
Net Change — Industry = SUM(pbi_industry_dynamics[net_employment_change])
Employment Growth Rate — National = 100 * DIVIDE([Net Change — National], SUM(pbi_national_dynamics[employment_denominator]))
Employment Growth Rate — State = 100 * DIVIDE([Net Change — State], SUM(pbi_state_dynamics[employment_denominator]))
Employment Growth Rate — Industry = 100 * DIVIDE([Net Change — Industry], SUM(pbi_industry_dynamics[employment_denominator]))
Establishment Births — National = SUM(pbi_national_dynamics[establishment_births])
Establishment Deaths — National = SUM(pbi_national_dynamics[establishment_deaths])
Employment Share — State = DIVIDE([Employment — State], CALCULATE([Employment — National], REMOVEFILTERS(dim_geography)))
Employment Share — Industry = DIVIDE([Employment — Industry], CALCULATE([Employment — National], REMOVEFILTERS(dim_industry)))
National Contribution — State = DIVIDE([Net Change — State], CALCULATE([Net Change — National], REMOVEFILTERS(dim_geography)))
National Contribution — Industry = DIVIDE([Net Change — Industry], CALCULATE([Net Change — National], REMOVEFILTERS(dim_industry)))
```

Each growth-rate measure divides that margin's net change by its published BDS denominator in the current filter context; do not take a simple average of category rates. The year/date filter remains in context for shares and contributions; geography or industry filters are removed only on the national denominator. The age comparison page may use `marts.firm_age_grouped_comparison`; the `Mature extended` record is a non-additive rollup and must not be added to its component rows. Never interpret missing values as zero.
