# Limitations

- **Coverage:** the 2023 BDS release is annual and ends in 2023. Later post-COVID dynamics are not represented.
- **Aggregation:** BDS is an aggregate dataset. The project uses one-way tables, so it cannot attribute state changes to industries or compare firm age within a given firm size.
- **Non-additive fact:** the MART fact unions five independent margins. In 2023, each margin sums to 137,462,444 employment, so an unfiltered sum of the shared fact is exactly five times the national total. SQL provides five filter-specific Power BI views; summing across those views is still invalid.
- **Geography:** states and DC only; county, metro, and Puerto Rico data are outside scope.
- **Industry:** sectors are broad 2-digit NAICS groups; some are combined groups in the published classification.
- **Suppression and missingness:** source `X` markers are unavailable/structural and remain null in metrics. A suppressed or unavailable measure is not zero.
- **Disclosure avoidance:** Census applies noise infusion to employment and job-flow statistics. Small discrepancies between totals and components may be expected.
- **Definitions:** BDS net job creation rate is the selected employment growth rate proxy; source denominators and establishment versus firm concepts differ. Left-censored firms have unknown true age. They remain separate before 1982 and enter a mature-extended rollup from 1982; their exact ages remain unavailable. That rollup is non-additive with its components.
- **Age-flow missingness:** firm-age `X` cells remain null, so reported gross destruction sums may omit cells. Net-change reconciliation uses a 30,000-job tolerance, based on the maximum observed age-to-national gap across this release.
- **BDS time convention:** BDS year *t* measures employment in the payroll period including March 12 of *t*, while job flows compare March 12 of *t−1* with *t*. Thus, 2020 ends in March 2020 and is classified pre-shock; 2021 covers March 2020–March 2021 and is the shock window. See the [Census BDS codebook](https://www.census.gov/content/dam/Census/programs-surveys/business-dynamics-statistics/bds-codebook.pdf).
- **Time comparison:** pre-shock is six years (2015–2020), shock one year (2021), and rebound two years (2022–2023). Flow totals are not annualized comparisons; report annual averages and rates alongside totals. The BDS year 2007 ends in March 2007, so the recession comparison starts in 2008 and runs through 2010.
- **Interpretation:** changes are descriptive. They do not establish causes or forecast future performance.
- **State-rate outliers:** percentage rates can rank a small state above a much larger one after a modest job loss. Period contraction views report absolute losses and denominator-weighted rates side by side; stakeholders should read both before prioritizing a geography.
- **Power BI environment:** this project workspace is on macOS and has no Power BI Desktop authoring/runtime available. A `.pbix` is a proprietary Desktop artifact; the database, query outputs, model definitions, and dashboard specification are supplied, but a valid `.pbix` cannot be produced or cross-validated in this environment.
