# Findings

All findings are descriptive. Recent rankings use the latest available year (2023); long-run state growth uses 1978–2023 endpoints. Annual employment growth rate is the Census BDS net job creation rate. Source: [2023 BDS release and datasets](https://www.census.gov/programs-surveys/bds/data.Datasets.html).

## 1. Which states have experienced the strongest employment growth?

**Metric:** percentage change in employment stock, 1978 to 2023; absolute employment change for scale. Also show the latest-year rate and net change separately.

**Observed evidence:** Nevada had the largest proportional increase from 1978 to 2023 (+362.54%), followed by Arizona (+307.85%) and Utah (+293.81%). California had the largest absolute increase (+8,544,842), ahead of Texas (+7,556,675). For 2023 alone, Delaware led on BDS net job creation rate (6.794%), while Texas added the most jobs (+448,722) and Florida the second most (+341,432).

**Interpretation:** relative growth and absolute contribution produce different state leaders. Nevada's growth rate is measured from a much smaller base than California's; California's absolute increase was largest despite lower percentage growth.

**Hypothesis:** population and business migration may help explain the relative gains; this dataset alone cannot establish that.

**Limitation:** endpoint comparison does not reveal the path between years and employment counts are affected by BDS disclosure avoidance noise. The 2023 rate and volume are separate annual views.

## 2. Which states have experienced the strongest employment contraction?

**Metric:** period sum of BDS net employment change and denominator-weighted mean annual net rate for the 2008–2010 recession window, the pre-shock BDS year ending March 2020, and the COVID shock BDS year ending March 2021. BDS year *t* measures the change from March 12 of *t−1* to March 12 of *t*, per the [Census BDS codebook](https://www.census.gov/content/dam/Census/programs-surveys/business-dynamics-statistics/bds-codebook.pdf). Absolute-loss rank and rate rank are both reported.

**Observed evidence:** In 2008–2010, California had the largest summed loss (-1,377,566; weighted annual rate -3.507%), while Nevada had the worst rate (-5.916%; -194,970 jobs). In BDS year 2020, which ends in March 2020 and is pre-shock, Louisiana had the largest absolute decline (-13,346; -0.781%); West Virginia had the worst rate (-1.999%; -11,018). In the COVID shock BDS year 2021, California had the largest absolute decline (-844,599; -5.652%), while Hawaii had the worst rate (-15.327%; -78,049). Fourteen states had negative net change in 2020 versus 48 in 2021. No state contracted in 2023; Vermont had the smallest positive net change (+2,560; +1.006%). The period output is generated at `data/processed/state_contraction.csv`.

**Interpretation:** absolute losses favor large employment bases: California leads by jobs in the revised recession window and the 2021 shock. Rate rankings surface smaller-base contractions: Nevada leads the recession window and Hawaii 2021. Those rates are volatile; Hawaii's 2021 denominator was 509,233, versus California's 14,944,546. Excluding 2007 removes a positive year from the old recession window; California's summed loss changes from -1,404,591 to -1,377,566, while Nevada's rate changes from -3.831% to -5.916%.

**Hypothesis:** different state industry mixes may have shaped the timing and depth of contractions; the one-way state tables cannot test that.

**Limitation:** 2008–2010 is a three-year sum; 2020 and 2021 are single-year values ending in March of the stated BDS year. The denominator-weighted rate is a mean annual rate, not a cumulative percentage change in employment stock. State rates based on small denominators are volatile. The one-way state source does not provide state-by-industry intersections.

## 3. Which industries are driving employment growth?

**Metric:** 2023 net employment change and contribution to U.S. net change.

**Observed evidence:** Health care and social assistance added 881,400 jobs, about 25.6% of national net change. Accommodation and food services added 791,588 (23.0%). Professional, scientific, and technical services added 249,750 (7.3%).

**Interpretation:** health care and accommodation/food together accounted for nearly half of national net employment change in 2023.

**Hypothesis:** demand and reopening patterns may have supported those sectors; BDS alone does not identify causes.

**Limitation:** contribution percentages can be negative or exceed 100% when sector changes offset each other. Industries are broad BDS 2-digit NAICS groupings.

## 4. Which industries are contracting?

**Metric:** 2023 net employment change by NAICS sector.

**Observed evidence:** Administrative and support and waste management services had the largest decline (-130,391), followed by Information (-8,797) and Agriculture, forestry, fishing and hunting (-5,816). The other 16 sector groups had positive 2023 net change.

**Interpretation:** contraction was concentrated in three broad sector groups in the latest year, with one decline much larger than the others.

**Hypothesis:** firm mix, technology, or post-pandemic adjustment could contribute to the pattern; these are hypotheses only.

**Limitation:** sector aggregates mask variation within sectors and do not show geography-specific contraction.

## 5. How do young and mature firms differ in employment dynamics?

**Metric:** sum of official age-band employment and flows in 2023. BDS defines left-censored firms as born before 1977 with unknown true age. The LBD begins in 1976; this project uses a conservative rule that treats left-censored firms as mature only from 1982 onward, once even the 1976 cohort has reached age six. See the [Census BDS FAQ](https://www.census.gov/programs-surveys/bds/about/faq.html) and [BDS glossary](https://www.census.gov/content/dam/Census/programs-surveys/business-dynamics-statistics/codebook-glossary.pdf). Before 1982, their age remains unknown and they are kept separate.

**Observed evidence:** Young (0–5) firms had 14,733,404 employment, 4,897,739 job creation, 2,413,709 reported job destruction, and +2,484,030 net change. Mature firms with known ages 6+ had 70,396,171 employment, 8,392,821 creation, 8,447,256 destruction, and -54,435 net change. Left-censored firms had 52,332,869 employment, 5,177,489 creation, 4,158,822 reported destruction, and +1,018,667 net change. Mature extended (known-age 6+ plus left-censored) had 122,729,040 employment, 13,570,310 creation, 12,606,078 reported destruction, and +964,232 net change.

The three disjoint age groups' employment sums exactly to national employment (137,462,444). Their creation, destruction, and net-change sums are 18,468,049, 15,019,787, and +3,448,262 versus national values 18,450,927, 15,011,588, and +3,439,339. Net change differs by +8,923; Census noise infusion can cause differences between table margins. Mature extended is a rollup and must not be added to the component groups. In 1978, left-censored firms represented 65,357,166 jobs (93.0% of national employment), so they are kept as unknown age. Age-related `X` cells remain missing; reported gross destruction sums omit unavailable cells.

**Interpretation:** excluding left-censored firms understated the mature group's 2023 net contribution by 1,018,667 jobs. Adding them changes mature net change from -54,435 to +964,232. This is a material composition effect. Young plus known-age mature firms cover 61.2% of national employment; young plus mature extended reconciles the employment stock.

**Hypothesis:** firm longevity and scale may be associated with different net job flows; these aggregates cannot identify why.

**Limitation:** exact left-censored firm ages are unknown. The 1982 cutoff is conservative across the Census glossary/FAQ definitions. Gross destruction can be incomplete where `X` cells occur. Age-level sums are subject to disclosure noise and do not describe firm-level trajectories.

## 6. How do firm-size categories differ in employment dynamics?

**Metric:** 2023 net employment change and BDS net job creation rate across ten official size bands.

**Observed evidence:** Every size band had positive net employment change. Firms with 20–99 employees added the most (+701,903), narrowly ahead of 10,000+ employees (+690,312). The 1,000–2,499 band had the highest net job creation rate (3.630%); the 5–9 band had the smallest positive absolute gain (+113,828).

**Interpretation:** growth was broad across size groups. The 20–99 band added slightly more net jobs than the 10,000+ band despite a smaller employment base (22.1 million versus 41.1 million). This is a useful distinction between absolute contribution and rate: the 20–99 band grew at 3.229%, while the 10,000+ band grew at 1.694%.

**Hypothesis:** the mix of firms and their employment base likely affects absolute contribution; this analysis does not isolate those mechanisms.

**Limitation:** BDS size categories are broad, and the question compares a single annual cross-section. BDS classifies firm size using the average size in adjacent years, so cross-year cell movement can reflect category reclassification as well as employment flows. Size bands are not firm-level growth trajectories.

## 7. How did business dynamics change before, during, and after COVID-19?

**Metric:** arithmetic mean of annual U.S. BDS net job creation rates plus denominator-weighted rate, net-flow total, and mean annual net flow for 2015–2020 pre-shock, 2021 shock, and 2022–2023 rebound. BDS year *t* measures March 12 employment change from *t−1* to *t*; see the [Census BDS codebook](https://www.census.gov/content/dam/Census/programs-surveys/business-dynamics-statistics/bds-codebook.pdf).

**Observed evidence:** In 2015–2020, the six-year net-flow total was +12,825,966 (+2,137,661 mean annual net flow); the arithmetic mean annual rate was 1.693% and the denominator-weighted rate 1.679%. The 2021 shock year had -5,518,197 net jobs (annual rate -4.245%). In 2022–2023, the two-year total was +10,523,761 (+5,261,881 mean annual net flow); mean annual rate was 3.979% and denominator-weighted rate 3.951%. The 2020 national rate was +0.632% (+835,961 jobs), while 2022 was +5.424% (+7,084,422).

**Interpretation:** The March-to-March BDS convention places 2020 in the pre-shock period and identifies 2021 as the shock year. The rebound's mean annual net change was positive and its mean annual rate exceeded the pre-shock average.

**Hypothesis:** the reversal may reflect both disruption and subsequent recovery, but this descriptive series cannot attribute changes to COVID or policy.

**Limitation:** the periods have different lengths (six, one, and two years); period totals are not annualized, so annual averages and rates are shown alongside totals. The 2023 BDS release does not measure conditions after 2023.
