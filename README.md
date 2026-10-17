# Arsalan Ahmed — Data Analytics Portfolio

Python · SQL · Excel · Power BI · Data Automation
📧 ahmedarslan599@gmail.com · 📞 +92 314 4466958 · [LinkedIn](https://linkedin.com/in/arslankhoso) · [GitHub](https://github.com/arsalan-khoso)

Three end-to-end analyses: raw messy data in, cleaned dataset, KPIs, segmentation,
visualisations, an Excel dashboard, and a costed business recommendation out.

---

### 1. [Construction Cost Overrun & Schedule Analysis](01-construction-project-analytics/)
SAR 169M contracting portfolio, 24 projects, 122 work packages.

Found a **+8.18% portfolio overrun (SAR 13.87M)** concentrated in MEP and Finishing
packages, and proved statistically that schedule slippage drives it — **every 1% of
delay adds 0.57% to cost (r = 0.82)**. Recommendation worth ~SAR 3.5M per cycle.

`pandas` · `NumPy` · `matplotlib` · `XlsxWriter` · data cleaning · correlation analysis

---

### 2. [Sales Performance, Cohort Retention & RFM Segmentation](02-sales-customer-retention/)
790 B2B customers, 2,863 orders, SAR 25.2M revenue.

Built a cohort-retention matrix and an RFM segmentation. **Champions (25% of customers)
drive 48.5% of revenue**, and **SAR 5.96M sits in 133 "At Risk — High Value" accounts**
that stopped ordering — a recoverable pool worth ~SAR 1.19M at a 20% win-back rate.

`pandas` · cohort analysis · RFM scoring · quartile segmentation · heatmaps · Excel dashboard

---

### 3. [Workforce Attendance & Overtime Cost Analysis](03-workforce-attendance/)
280 employees, 4 sites, 73,000+ daily attendance records.

Converted attendance behaviour into money: **SAR 6.46M lost in 2025** to absenteeism and
the overtime paid to cover it. Maintenance absenteeism runs at 11.4%, night shift at 1.3×
the day shift, and the **top 10% of staff carry 24.4% of all overtime** — a burnout risk.

`pandas` · cost modelling · cross-tab analysis · concentration analysis · Excel dashboard

---

## How to run
```bash
pip install pandas numpy matplotlib XlsxWriter
cd 01-construction-project-analytics && python generate_data.py && python analysis.py
```

Every script is reproducible with a fixed random seed. Datasets are synthetic — modelled
on published industry benchmarks so the work can be shared publicly — and each pipeline
runs unchanged on a real ERP, CRM or HRMS export by swapping the source file.
