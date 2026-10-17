# Construction Portfolio — Cost Overrun & Schedule Analysis

**Tools:** Python (pandas, NumPy, matplotlib) · Excel (XlsxWriter dashboard) · SAR 169M portfolio, 24 projects, 122 work packages

## Business question
A contracting company was finishing projects over budget but could not say *which*
part of the work was causing it, or whether delays and cost overruns were connected.

## What I did
1. **Cleaned the raw export** — removed 6 duplicate rows, standardised inconsistent city
   names (`DAMMAM` → `Dammam`), and imputed 9 missing actual-cost values at the
   package-level median ratio instead of dropping them, so portfolio totals stayed complete.
2. **Engineered the metrics** the PMO actually needs: cost variance (SAR and %),
   schedule slippage %, delay days, and an over-budget flag.
3. **Segmented** the variance by work package, city and client type.
4. **Tested the delay → cost hypothesis** with a correlation and a fitted trend line.

## Key findings
| Finding | Number |
|---|---|
| Portfolio cost overrun | **+8.18%** (SAR 13.87M over a SAR 169.6M budget) |
| Work packages over budget | **85%** |
| Average delay per package | **14.9 days** |
| Correlation: schedule slip ↔ cost overrun | **r = 0.82** |

- **MEP and Finishing packages cause half the loss** — SAR 6.7M of the SAR 13.9M total
  variance, at 13.2% and 12.0% average overrun, with the longest delays (23 and 21 days).
- **Delay is the cost driver, not a side effect.** Every 1% of schedule slippage adds
  **+0.57% to package cost** (r = 0.82). Controlling the schedule controls the budget.
- **Site Preparation is the only package that finishes on budget** (−0.2% variance) —
  it is also the least delayed, which confirms the same relationship from the other side.

## Recommendation
Put MEP and Finishing on weekly earned-value tracking rather than monthly. Based on the
fitted trend, cutting their average slippage from 23 days to 10 would recover roughly
**SAR 3.5M per portfolio cycle**.

## Files
- `generate_data.py` — builds the raw dataset
- `analysis.py` — cleaning, KPIs, segmentation, charts, Excel report
- `Construction_Cost_Dashboard.xlsx` — KPI dashboard + 6 analysis sheets with conditional formatting
- `charts/` — variance by package, delay vs overrun, monthly spend, overrun by city
- `data/` — raw and cleaned datasets

> Dataset is synthetic, modelled on published Saudi contracting cost-overrun benchmarks,
> so the project can be shared publicly. The pipeline runs unchanged on real ERP exports.
