
# Survey of Consumer Finances (SCF) Racial Wealth Gap Analysis

### Contains code to download triennial SCF data from 1989-2019 & assess racial wealth gap over time

#### Source details: https://www.federalreserve.gov/econres/scfindex.htm

Code adapted from Dan Valanzuela in `scf_collector.py`. Racial wealth gap analysis & plotting in `wealth_stats_overtime.py`. Use `Examples.py` to replicate these results and for conducting further analysis.

Vehicle values are subtracted from household net wealth to reduce skew from consumer durables in cross-demographic analyses. For racial wealth gap analysis, all five implicates for each housold are weighted with a factor of 1/5.

To load a Pandas dataframe or CSV for a given year, use `wealth_stats_overtime.load_df(year, filetype)`
- `summary` data indicates the Federal Reserves's public analysis with decoded variables, including household net wealth calculations (351 key named variables). Full codebook available at https://www.federalreserve.gov/econres/files/codebk2019.txt
- `raw` data indicates 5,333 original encoded variables corresponding to survey questions.
  - Data dictionary: https://www.federalreserve.gov/econres/files/2019map.txt

### Latest data:

![Underwater Households 1989-2019](https://raw.githubusercontent.com/js-fitz/SCF-analysis/main/SCF-racial-wealth-gap/underwater_households_1992_2019.png)


## [View Interactive →](https://chart-studio.plotly.com/~3joemail/32/#/)


For question/comments contact Joe Fitzgerald (Data Consultant, Institute for Policy Studied): 3joemail@gmail.com
