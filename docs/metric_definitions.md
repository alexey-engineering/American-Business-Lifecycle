# Metric definitions

All measures use the BDS annual source grain (year and one observation category). Source rate values are percentage points. `X`/unavailable cells are NULL, never zero. A zero denominator yields an undefined rate (NULL). Totals across periods are sums of annual flows; rates are not summed.

BDS year *t* reports employment for the payroll period including March 12 of *t*; job-flow measures compare March 12 in *t−1* with March 12 in *t*. Therefore 2020 is the pre-shock year ending March 2020, and 2021 is the COVID shock window ending March 2021. Source: [Census BDS codebook](https://www.census.gov/content/dam/Census/programs-surveys/business-dynamics-statistics/bds-codebook.pdf).

| KPI | Definition / formula | Numerator / denominator | Grain and filters | Missing / zero handling |
|---|---|---|---|---|
| Employment | BDS employment stock (`emp`) | Source measure | Year x source category | NULL source cells stay NULL |
| Job Creation | BDS gross jobs created (`job_creation`) | Source measure | Year x source category | NULL stays NULL |
| Job Destruction | BDS gross jobs destroyed (`job_destruction`), shown as a positive magnitude | Source measure | Year x source category | NULL stays NULL |
| Net Employment Change | `job_creation - job_destruction`; BDS `net_job_creation` retained as authoritative | Net jobs | Year x source category | May be negative; NULL if unavailable |
| Employment Growth Rate | BDS `net_job_creation_rate` | BDS rate over its published denominator (`denom`) | Year x source category | Zero/undefined denominator or suppression -> NULL |
| Establishment Births | BDS `estabs_entry` | Source count | Year x source category | NULL stays NULL |
| Establishment Deaths | BDS `estabs_exit` | Source count | Year x source category | NULL stays NULL |
| Employment Share | Category employment / U.S. total employment in same year * 100 | Slice `emp` / national `emp` | Compare only compatible one-way category margins | NULL when either cell missing or national employment is zero |
| Contribution to National Employment Change | Slice `net_job_creation` / national `net_job_creation` * 100 | Slice net change / national net change | Year and state or industry; positive, negative, or above 100% possible | NULL when national net change is zero or either measure unavailable |

For state contraction period rankings, the displayed period rate is `SUM(net_job_creation) / SUM(denom) * 100`. This is the denominator-weighted mean annual BDS net job creation rate over the selected years, not the cumulative percent change in employment stock. Period windows are 2008–2010, the pre-shock BDS year 2020, and the COVID shock BDS year 2021. COVID comparison windows are 2015–2020, 2021, and 2022–2023; totals are also shown as annual averages because window lengths differ.

Young is firm age 0–5. Mature known-age is 6+. Census describes left-censored firms as born before 1977 with unknown true age. This model keeps them separate before 1982; from 1982, their minimum possible age is six and the `Mature extended` rollup includes them. The fact remains one year x one source code and has a derived `left_censored_is_mature` flag; the key is unchanged. Mature extended is a non-additive rollup, not a separate disjoint category. See the [Census BDS FAQ](https://www.census.gov/programs-surveys/bds/about/faq.html) and [glossary](https://www.census.gov/content/dam/Census/programs-surveys/business-dynamics-statistics/codebook-glossary.pdf).

Age-level source `X` cells remain missing, so reported gross destruction sums may omit cells. The published net-change values are retained as authoritative. Census noise means age-table net-change sums may differ from the national total; validation uses a 30,000-job absolute tolerance, above the maximum observed gap of 22,037 across 1978–2023.
