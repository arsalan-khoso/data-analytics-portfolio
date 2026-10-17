# Workforce Attendance, Absenteeism & Overtime Cost Analysis

**Tools:** Python (pandas, NumPy, matplotlib) · Excel dashboard · 280 employees, 4 sites, 73,000+ attendance records (2025)

## Business question
Overtime spend kept rising while headcount stayed flat. HR needed to know whether
overtime was covering genuine workload or covering absenteeism — and where.

## What I did
1. **Built a daily attendance log** for 280 employees across 4 sites and 7 departments
   (Present / Late / Absent / Sick Leave, hours worked, overtime hours).
2. **Costed every row** — overtime at 1.5× the department hourly rate, lost hours at 1.0× —
   so attendance behaviour converts directly into SAR.
3. **Segmented** absence and overtime by department, site and shift, and cross-tabbed
   department × site to find local problems rather than company-wide averages.
4. **Checked concentration** — whether overtime is spread evenly or carried by a few people.

## Key findings
| Metric | Value |
|---|---|
| Attendance rate | **91.2%** |
| Absenteeism rate | **7.8%** |
| Late arrival rate | **4.9%** |
| Overtime cost (2025) | **SAR 4.32M** |
| Cost of lost hours | **SAR 2.14M** |

- **Absence and overtime together cost SAR 6.46M in 2025** — the equivalent of a
  mid-sized department's annual payroll, invisible in standard headcount reporting.
- **Maintenance has the worst absenteeism (11.4%)**, followed by Site Operations (9.6%).
  Site Operations alone loses **SAR 785K** in unworked paid hours.
- **Night shift absenteeism runs 1.3× the day shift** — a scheduling and supervision
  issue, not an individual-performance one.
- **The top 10% of employees carry 24.4% of all overtime hours** — a burnout and
  key-person risk concentrated in a small group, flagged on a 90th-percentile watchlist.

## Recommendation
Target Maintenance and Site Operations first. Cutting their absenteeism to the company
average of 7.8% would recover roughly **SAR 420K per year** in lost hours, plus the
overtime currently being paid at 1.5× to cover those gaps.

## Files
- `analysis.py` — data build, cost model, segmentation, concentration analysis, charts, Excel report
- `Workforce_Attendance_Dashboard.xlsx` — KPI dashboard + 6 sheets with conditional formatting
- `charts/` — absence by department, monthly cost stack, overtime concentration, department × site heatmap
- `data/attendance_log.csv` — full costed attendance log

> Dataset is synthetic and reproducible (fixed seed). The pipeline runs unchanged on a
> real biometric or HRMS attendance export.
