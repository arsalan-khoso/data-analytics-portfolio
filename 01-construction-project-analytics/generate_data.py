"""Builds the raw dataset for the construction cost-overrun analysis.

Figures are modelled on published Saudi contracting benchmarks: most packages
land within +/-8% of budget, while MEP and finishing packages carry the long
right tail of overruns.
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

CITIES = ["Dammam", "Riyadh", "Jubail", "Khobar", "Jeddah"]
CATEGORIES = ["Civil Works", "MEP", "Finishing", "Steel Structure",
              "Site Preparation", "HVAC", "Electrical"]
CLIENTS = ["Government", "Private", "Semi-Government"]

n_projects = 24
projects = pd.DataFrame({
    "project_id": [f"PRJ-{i:03d}" for i in range(1, n_projects + 1)],
    "city": rng.choice(CITIES, n_projects, p=[0.34, 0.24, 0.16, 0.16, 0.10]),
    "client_type": rng.choice(CLIENTS, n_projects, p=[0.45, 0.40, 0.15]),
})

rows = []
for _, prj in projects.iterrows():
    for category in rng.choice(CATEGORIES, rng.integers(4, 8), replace=False):
        planned_cost = float(rng.integers(180, 2600)) * 1000
        planned_days = int(rng.integers(25, 180))

        # Delay driver: MEP and Finishing slip the most, site prep the least.
        slip_factor = {"MEP": 0.22, "Finishing": 0.18, "HVAC": 0.15,
                       "Electrical": 0.12, "Civil Works": 0.08,
                       "Steel Structure": 0.06, "Site Preparation": 0.03}[category]
        delay_ratio = max(0, rng.normal(slip_factor, 0.12))
        actual_days = int(round(planned_days * (1 + delay_ratio)))

        # Cost follows schedule, plus an independent materials/market shock.
        cost_ratio = 1 + delay_ratio * 0.55 + rng.normal(0, 0.05)
        actual_cost = round(planned_cost * max(0.86, cost_ratio), 2)

        start = pd.Timestamp("2024-01-01") + pd.Timedelta(days=int(rng.integers(0, 600)))
        rows.append({
            "project_id": prj.project_id,
            "city": prj.city,
            "client_type": prj.client_type,
            "work_package": category,
            "start_date": start,
            "end_date": start + pd.Timedelta(days=actual_days),
            "planned_cost_sar": planned_cost,
            "actual_cost_sar": actual_cost,
            "planned_days": planned_days,
            "actual_days": actual_days,
        })

df = pd.DataFrame(rows)

# Real-world messiness the cleaning step has to handle.
dirty = rng.choice(df.index, 18, replace=False)
df.loc[dirty[:9], "actual_cost_sar"] = np.nan
df.loc[dirty[9:], "city"] = df.loc[dirty[9:], "city"].str.upper()
df = pd.concat([df, df.iloc[:6]], ignore_index=True)  # duplicate rows

df.to_csv("data/raw_work_packages.csv", index=False)
print(f"Raw dataset written: {len(df)} rows, {df.project_id.nunique()} projects")
