# Sales Performance, Cohort Retention & RFM Segmentation

**Tools:** Python (pandas, NumPy, matplotlib) · Excel dashboard · 790 customers, 2,863 orders, SAR 25.2M revenue

## Business question
A B2B supplier knew its total revenue but not *where growth was coming from*, how long
customers kept buying after their first order, or which customers were quietly slipping away.

## What I did
1. **Built the transaction model** — order-level revenue with quantity, unit price and
   discount, so discount leakage could be measured separately from gross sales.
2. **Revenue breakdown** by product line, sales channel and region, including
   revenue-per-customer so channels are compared on value, not just volume.
3. **Cohort retention analysis** — grouped customers by first-purchase month and tracked
   what share of each cohort was still ordering in every following month.
4. **RFM segmentation** — scored every customer on Recency, Frequency and Monetary value
   (quartiles, 1–4), then mapped the combined score to five actionable segments.

## Key findings
| Metric | Value |
|---|---|
| Total revenue | **SAR 25.19M** |
| Average order value | **SAR 8,798** |
| Repeat customer rate | **83.8%** |
| Revenue lost to discounts | **SAR 949K (3.8%)** |

- **Two product lines carry 66% of revenue** — HVAC Parts (36.5%) and Power Tools (29.7%).
  Building Materials moves the most units but returns only 2.2% of revenue: high handling
  cost, negligible margin contribution.
- **Champions (200 customers, 25% of the base) generate 48.5% of all revenue.**
- **SAR 5.96M sits in "At Risk — High Value"** — 133 customers who used to buy often
  (4 orders on average) but have not ordered in ~477 days. This is the single largest
  recoverable revenue pool in the dataset.
- **Channel quality differs sharply:** Online Portal customers return far more often than
  Phone Order customers, so revenue per customer — not order count — is the channel KPI.

## Recommendation
Run a win-back campaign on the 133 At-Risk high-value accounts before spending on new
acquisition: recovering even 20% of them is worth roughly **SAR 1.19M**, at a fraction of
the cost of acquiring 133 new customers.

## Files
- `analysis.py` — data build, cleaning, KPIs, cohort matrix, RFM scoring, charts, Excel report
- `Sales_Retention_Dashboard.xlsx` — KPI dashboard + 7 sheets (cohort heatmap with conditional formatting)
- `charts/` — monthly revenue, product mix, cohort retention heatmap, RFM segments, channel value
- `data/` — transaction log and scored RFM table

> Dataset is synthetic and reproducible (fixed seed). The same pipeline runs on a real
> ERP or CRM export by swapping the source file.
