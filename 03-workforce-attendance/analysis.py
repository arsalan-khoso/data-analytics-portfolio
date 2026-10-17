"""Workforce attendance, overtime and absenteeism analysis.

Business questions:
  1. What is absenteeism costing the company per month?
  2. Which departments and sites rely on overtime to cover attendance gaps?
  3. Is overtime concentrated on a small group of employees (burnout risk)?
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams.update({"figure.dpi": 130, "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False})
NAVY, ORANGE, TEAL = "#1f3a5f", "#e07b39", "#2a9d8f"
rng = np.random.default_rng(11)

DEPTS = {"Site Operations": 0.09, "Logistics": 0.07, "Maintenance": 0.11,
         "Procurement": 0.04, "Finance": 0.03, "HSE": 0.05, "Administration": 0.06}
SITES = ["Dammam HQ", "Jubail Yard", "Riyadh Site", "Khobar Depot"]
HOURLY_RATE = {"Site Operations": 38, "Logistics": 34, "Maintenance": 45,
               "Procurement": 52, "Finance": 60, "HSE": 48, "Administration": 40}

employees = pd.DataFrame({
    "employee_id": ["EMP-{:04d}".format(i) for i in range(1, 281)],
    "department": rng.choice(list(DEPTS), 280,
                             p=[0.3, 0.14, 0.16, 0.08, 0.08, 0.1, 0.14]),
    "site": rng.choice(SITES, 280, p=[0.35, 0.25, 0.25, 0.15]),
    "shift": rng.choice(["Day", "Night"], 280, p=[0.72, 0.28]),
})

workdays = pd.bdate_range("2025-01-01", "2025-12-31")
rows = []
for _, emp in employees.iterrows():
    absence_rate = DEPTS[emp["department"]] * (1.25 if emp["shift"] == "Night" else 1.0)
    # ~15% of staff are chronic overtime carriers.
    ot_propensity = 2.4 if rng.random() < 0.15 else 0.6
    for day in workdays:
        roll = rng.random()
        if roll < absence_rate * 0.55:
            status, hours = "Absent", 0.0
        elif roll < absence_rate:
            status, hours = "Sick Leave", 0.0
        elif roll < absence_rate + 0.05:
            status, hours = "Late", round(rng.uniform(5.0, 7.5), 1)
        else:
            status, hours = "Present", 8.0
        overtime = round(max(0, rng.normal(ot_propensity, 1.1)), 1) if status in ("Present", "Late") else 0.0
        rows.append({
            "employee_id": emp["employee_id"], "department": emp["department"],
            "site": emp["site"], "shift": emp["shift"], "date": day,
            "status": status, "hours_worked": hours, "overtime_hours": overtime,
        })

df = pd.DataFrame(rows)
df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()
df["hourly_rate_sar"] = df["department"].map(HOURLY_RATE)
df["overtime_cost_sar"] = (df["overtime_hours"] * df["hourly_rate_sar"] * 1.5).round(2)
df["lost_hours"] = np.where(df["status"].isin(["Absent", "Sick Leave"]), 8.0,
                            np.where(df["status"] == "Late", 8.0 - df["hours_worked"], 0.0))
df["absence_cost_sar"] = (df["lost_hours"] * df["hourly_rate_sar"]).round(2)
df.to_csv("data/attendance_log.csv", index=False)

scheduled = len(df) * 8.0
kpis = {
    "Attendance records": len(df),
    "Employees": df["employee_id"].nunique(),
    "Attendance rate %": df["hours_worked"].sum() / scheduled * 100,
    "Absenteeism rate %": df["status"].isin(["Absent", "Sick Leave"]).mean() * 100,
    "Late arrival rate %": (df["status"] == "Late").mean() * 100,
    "Overtime hours": df["overtime_hours"].sum(),
    "Overtime cost (SAR)": df["overtime_cost_sar"].sum(),
    "Cost of lost hours (SAR)": df["absence_cost_sar"].sum(),
}
print("--- WORKFORCE KPIs ---")
for k, v in kpis.items():
    print("{:>28}: {:,.2f}".format(k, v) if isinstance(v, float) else "{:>28}: {:,}".format(k, v))

by_dept = (df.groupby("department")
             .agg(employees=("employee_id", "nunique"),
                  absence_rate_pct=("status", lambda s: s.isin(["Absent", "Sick Leave"]).mean() * 100),
                  overtime_hours=("overtime_hours", "sum"),
                  overtime_cost_sar=("overtime_cost_sar", "sum"),
                  absence_cost_sar=("absence_cost_sar", "sum"))
             .sort_values("absence_rate_pct", ascending=False).round(2))
by_dept["overtime_hrs_per_employee"] = (by_dept["overtime_hours"] / by_dept["employees"]).round(1)

by_site = (df.groupby("site")
             .agg(employees=("employee_id", "nunique"),
                  absence_rate_pct=("status", lambda s: s.isin(["Absent", "Sick Leave"]).mean() * 100),
                  overtime_cost_sar=("overtime_cost_sar", "sum"))
             .sort_values("absence_rate_pct", ascending=False).round(2))

by_shift = (df.groupby("shift")
              .agg(employees=("employee_id", "nunique"),
                   absence_rate_pct=("status", lambda s: s.isin(["Absent", "Sick Leave"]).mean() * 100),
                   avg_overtime_hours=("overtime_hours", "mean"))
              .round(2))

monthly = (df.groupby("month")
             .agg(absence_rate_pct=("status", lambda s: s.isin(["Absent", "Sick Leave"]).mean() * 100),
                  overtime_cost_sar=("overtime_cost_sar", "sum"),
                  absence_cost_sar=("absence_cost_sar", "sum")).round(2))

per_emp = (df.groupby(["employee_id", "department"])
             .agg(overtime_hours=("overtime_hours", "sum"),
                  absence_days=("status", lambda s: s.isin(["Absent", "Sick Leave"]).sum()),
                  overtime_cost_sar=("overtime_cost_sar", "sum"))
             .reset_index().round(2))
top_ot = per_emp.nlargest(15, "overtime_hours")

# Concentration check: what share of overtime sits with the top 10% of staff?
ot_sorted = per_emp["overtime_hours"].sort_values(ascending=False)
top10_share = ot_sorted.head(int(len(ot_sorted) * 0.1)).sum() / ot_sorted.sum() * 100

print("\n--- BY DEPARTMENT ---")
print(by_dept.to_string())
print("\nTop 10% of employees carry {:.1f}% of all overtime hours.".format(top10_share))
print("Night-shift absenteeism is {:.1f}x the day shift.".format(
    by_shift.loc["Night", "absence_rate_pct"] / by_shift.loc["Day", "absence_rate_pct"]))

# ---------------------------------------------------------------- charts
fig, ax = plt.subplots(figsize=(8.5, 4.5))
d = by_dept.sort_values("absence_rate_pct")
ax.barh(d.index, d["absence_rate_pct"], color=NAVY)
for i, (rate, cost) in enumerate(zip(d["absence_rate_pct"], d["absence_cost_sar"])):
    ax.text(rate + 0.15, i, "{:.1f}%  (SAR {:,.0f} lost)".format(rate, cost), va="center", fontsize=8.5)
ax.set_title("Absenteeism rate by department", fontweight="bold", loc="left")
ax.set_xlabel("Absence rate (%)"); ax.set_xlim(0, d["absence_rate_pct"].max() * 1.75)
fig.tight_layout(); fig.savefig("charts/01_absence_by_department.png"); plt.close(fig)

fig, ax = plt.subplots(figsize=(9, 4.5))
ax.bar(monthly.index, monthly["overtime_cost_sar"] / 1000, width=20, color=ORANGE, label="Overtime cost")
ax.bar(monthly.index, monthly["absence_cost_sar"] / 1000, width=20,
       bottom=monthly["overtime_cost_sar"] / 1000, color=NAVY, label="Cost of lost hours")
ax.set_title("Monthly cost of absence and overtime", fontweight="bold", loc="left")
ax.set_ylabel("SAR thousands"); ax.legend(frameon=False)
fig.autofmt_xdate(); fig.tight_layout()
fig.savefig("charts/02_monthly_cost.png"); plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.scatter(per_emp["absence_days"], per_emp["overtime_hours"], alpha=0.5, color=TEAL, edgecolor="white")
ax.set_title("Overtime hours vs absence days, per employee", fontweight="bold", loc="left")
ax.set_xlabel("Absence days (2025)"); ax.set_ylabel("Overtime hours (2025)")
ax.axhline(per_emp["overtime_hours"].quantile(0.9), color=ORANGE, ls="--", lw=1.4,
           label="90th percentile overtime - burnout watchlist")
ax.legend(frameon=False)
fig.tight_layout(); fig.savefig("charts/03_overtime_concentration.png"); plt.close(fig)

pivot = df.pivot_table(index="department", columns="site",
                       values="status", aggfunc=lambda s: s.isin(["Absent", "Sick Leave"]).mean() * 100)
fig, ax = plt.subplots(figsize=(8, 4.6))
im = ax.imshow(pivot.values, cmap="OrRd", aspect="auto")
ax.set_xticks(range(len(pivot.columns))); ax.set_xticklabels(pivot.columns, rotation=20, ha="right")
ax.set_yticks(range(len(pivot.index))); ax.set_yticklabels(pivot.index, fontsize=9)
for i in range(pivot.shape[0]):
    for j in range(pivot.shape[1]):
        ax.text(j, i, "{:.1f}".format(pivot.values[i, j]), ha="center", va="center", fontsize=8)
ax.set_title("Absence rate (%) by department and site", fontweight="bold", loc="left")
fig.colorbar(im, ax=ax, shrink=0.8, label="% absent")
fig.tight_layout(); fig.savefig("charts/04_absence_heatmap.png"); plt.close(fig)

# ---------------------------------------------------------------- excel report
with pd.ExcelWriter("Workforce_Attendance_Dashboard.xlsx", engine="xlsxwriter") as xl:
    wb = xl.book
    money = wb.add_format({"num_format": "#,##0", "border": 1})
    num = wb.add_format({"num_format": "#,##0.00", "border": 1})
    head = wb.add_format({"bold": True, "bg_color": "#1f3a5f", "font_color": "white",
                          "border": 1, "align": "center"})
    title = wb.add_format({"bold": True, "font_size": 15, "font_color": "#1f3a5f"})

    ws = wb.add_worksheet("Dashboard")
    xl.sheets["Dashboard"] = ws
    ws.hide_gridlines(2)
    ws.set_column("A:A", 2); ws.set_column("B:B", 32); ws.set_column("C:C", 20)
    ws.write("B2", "Workforce Attendance & Overtime - 2025", title)
    ws.write("B3", "{:,} employees | 4 sites | SAR".format(df["employee_id"].nunique()),
             wb.add_format({"font_color": "#666666"}))
    ws.write_row("B5", ["KPI", "Value"], head)
    for i, (label, value) in enumerate(kpis.items(), start=6):
        ws.write("B{}".format(i), label, wb.add_format({"border": 1}))
        ws.write("C{}".format(i), value, money if value > 1000 else num)
    ws.write("B15", "Top 10% of staff carry this share of overtime", wb.add_format({"border": 1}))
    ws.write("C15", round(top10_share, 1), num)
    ws.insert_image("E2", "charts/01_absence_by_department.png", {"x_scale": 0.55, "y_scale": 0.55})
    ws.insert_image("E22", "charts/02_monthly_cost.png", {"x_scale": 0.55, "y_scale": 0.55})
    ws.insert_image("B18", "charts/04_absence_heatmap.png", {"x_scale": 0.5, "y_scale": 0.5})

    for name, frame in [("By department", by_dept), ("By site", by_site), ("By shift", by_shift),
                        ("Monthly trend", monthly), ("Top overtime staff", top_ot),
                        ("Per employee", per_emp)]:
        frame.to_excel(xl, sheet_name=name, index=name not in ("Top overtime staff", "Per employee"))
        sheet = xl.sheets[name]
        sheet.set_column(0, 0, 24); sheet.set_column(1, len(frame.columns), 20)
        sheet.freeze_panes(1, 1)
        if "absence_rate_pct" in frame.columns:
            col = list(frame.columns).index("absence_rate_pct") + 1
            sheet.conditional_format(1, col, len(frame), col,
                                     {"type": "3_color_scale", "min_color": "#63be7b",
                                      "mid_color": "#ffeb84", "max_color": "#f8696b"})

print("\nWrote Workforce_Attendance_Dashboard.xlsx + 4 charts")
