"""Cost-overrun and schedule-slippage analysis for a contracting portfolio.

Answers four questions for the PMO:
  1. How much of the portfolio budget is lost to overruns?
  2. Which work packages drive those overruns?
  3. Does schedule delay actually predict cost overrun?
  4. Which city / client segment is the most reliable?
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams.update({"figure.dpi": 130, "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False})
NAVY, ORANGE, GREY = "#1f3a5f", "#e07b39", "#9aa5b1"

# ---------------------------------------------------------------- load + clean
df = pd.read_csv("data/raw_work_packages.csv", parse_dates=["start_date", "end_date"])
before = len(df)

df = df.drop_duplicates()
df["city"] = df["city"].str.title().str.strip()
# 9 packages were still open at export time; impute at the package-level median
# ratio rather than dropping them, so the portfolio total stays complete.
median_ratio = (df["actual_cost_sar"] / df["planned_cost_sar"]).median()
missing = df["actual_cost_sar"].isna()
df.loc[missing, "actual_cost_sar"] = (df.loc[missing, "planned_cost_sar"] * median_ratio).round(2)

print("Cleaning: {} -> {} rows ({} duplicates removed, {} costs imputed)".format(
    before, len(df), before - len(df), int(missing.sum())))

# ---------------------------------------------------------------- feature prep
df["cost_variance_sar"] = df["actual_cost_sar"] - df["planned_cost_sar"]
df["cost_overrun_pct"] = df["cost_variance_sar"] / df["planned_cost_sar"] * 100
df["delay_days"] = df["actual_days"] - df["planned_days"]
df["schedule_slip_pct"] = df["delay_days"] / df["planned_days"] * 100
df["over_budget"] = df["cost_variance_sar"] > 0
df["month"] = df["start_date"].dt.to_period("M").dt.to_timestamp()

df.to_csv("data/clean_work_packages.csv", index=False)

# ---------------------------------------------------------------- headline KPIs
planned, actual = df["planned_cost_sar"].sum(), df["actual_cost_sar"].sum()
correlation = df["schedule_slip_pct"].corr(df["cost_overrun_pct"])
kpis = {
    "Work packages analysed": len(df),
    "Projects": df["project_id"].nunique(),
    "Planned budget (SAR)": planned,
    "Actual cost (SAR)": actual,
    "Total cost variance (SAR)": actual - planned,
    "Portfolio overrun %": (actual - planned) / planned * 100,
    "Packages over budget %": df["over_budget"].mean() * 100,
    "Average delay (days)": df["delay_days"].mean(),
    "Delay vs overrun correlation": correlation,
}
print("\n--- HEADLINE KPIs ---")
for k, v in kpis.items():
    print("{:>32}: {:,.2f}".format(k, v) if isinstance(v, float) else "{:>32}: {:,}".format(k, v))

# ---------------------------------------------------------------- breakdowns
by_package = (df.groupby("work_package")
                .agg(packages=("project_id", "size"),
                     planned_sar=("planned_cost_sar", "sum"),
                     actual_sar=("actual_cost_sar", "sum"),
                     variance_sar=("cost_variance_sar", "sum"),
                     avg_overrun_pct=("cost_overrun_pct", "mean"),
                     avg_delay_days=("delay_days", "mean"))
                .sort_values("variance_sar", ascending=False).round(2))

by_city = (df.groupby("city")
             .agg(projects=("project_id", "nunique"),
                  actual_sar=("actual_cost_sar", "sum"),
                  avg_overrun_pct=("cost_overrun_pct", "mean"),
                  on_budget_rate=("over_budget", lambda s: (1 - s.mean()) * 100))
             .sort_values("avg_overrun_pct", ascending=False).round(2))

by_client = (df.groupby("client_type")
               .agg(packages=("project_id", "size"),
                    avg_overrun_pct=("cost_overrun_pct", "mean"),
                    avg_delay_days=("delay_days", "mean"))
               .sort_values("avg_overrun_pct", ascending=False).round(2))

monthly = (df.groupby("month")
             .agg(planned_sar=("planned_cost_sar", "sum"),
                  actual_sar=("actual_cost_sar", "sum")).round(2))
monthly["cumulative_variance_sar"] = (monthly["actual_sar"] - monthly["planned_sar"]).cumsum()

worst = (df.nlargest(10, "cost_variance_sar")
           [["project_id", "city", "work_package", "planned_cost_sar",
             "actual_cost_sar", "cost_variance_sar", "cost_overrun_pct", "delay_days"]]
           .round(2))

print("\n--- COST VARIANCE BY WORK PACKAGE ---")
print(by_package.to_string())

# ---------------------------------------------------------------- charts
fig, ax = plt.subplots(figsize=(8, 4.5))
d = by_package.sort_values("variance_sar")
ax.barh(d.index, d["variance_sar"] / 1e6,
        color=[ORANGE if v > 0 else NAVY for v in d["variance_sar"]])
ax.set_title("Cost variance by work package", fontweight="bold", loc="left")
ax.set_xlabel("Variance (SAR millions)  -  positive = over budget")
ax.axvline(0, color="#333", lw=0.8)
fig.tight_layout(); fig.savefig("charts/01_variance_by_package.png"); plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.scatter(df["schedule_slip_pct"], df["cost_overrun_pct"],
           s=df["planned_cost_sar"] / 25000, alpha=0.6, color=NAVY, edgecolor="white")
m, b = np.polyfit(df["schedule_slip_pct"], df["cost_overrun_pct"], 1)
xs = np.linspace(df["schedule_slip_pct"].min(), df["schedule_slip_pct"].max(), 50)
ax.plot(xs, m * xs + b, color=ORANGE, lw=2,
        label="trend: +{:.2f}% cost per 1% slip  (r = {:.2f})".format(m, correlation))
ax.set_title("Schedule slippage drives cost overrun", fontweight="bold", loc="left")
ax.set_xlabel("Schedule slippage (%)"); ax.set_ylabel("Cost overrun (%)")
ax.legend(frameon=False)
fig.tight_layout(); fig.savefig("charts/02_delay_vs_overrun.png"); plt.close(fig)

fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(monthly.index, monthly["planned_sar"] / 1e6, marker="o", color=GREY, label="Planned")
ax.plot(monthly.index, monthly["actual_sar"] / 1e6, marker="o", color=NAVY, label="Actual")
ax.fill_between(monthly.index, monthly["planned_sar"] / 1e6, monthly["actual_sar"] / 1e6,
                where=monthly["actual_sar"] >= monthly["planned_sar"], color=ORANGE, alpha=0.25)
ax.set_title("Monthly planned vs actual spend", fontweight="bold", loc="left")
ax.set_ylabel("SAR millions"); ax.legend(frameon=False)
fig.autofmt_xdate()
fig.tight_layout(); fig.savefig("charts/03_monthly_spend.png"); plt.close(fig)

fig, ax = plt.subplots(figsize=(7.5, 4.2))
d = by_city.sort_values("avg_overrun_pct")
ax.barh(d.index, d["avg_overrun_pct"], color=NAVY)
for i, (pct_val, rate) in enumerate(zip(d["avg_overrun_pct"], d["on_budget_rate"])):
    ax.text(pct_val + 0.3, i, "{:.1f}%  ({:.0f}% on budget)".format(pct_val, rate),
            va="center", fontsize=9)
ax.set_title("Average cost overrun by city", fontweight="bold", loc="left")
ax.set_xlabel("Average overrun (%)"); ax.set_xlim(0, d["avg_overrun_pct"].max() * 1.45)
fig.tight_layout(); fig.savefig("charts/04_overrun_by_city.png"); plt.close(fig)

# ---------------------------------------------------------------- excel report
with pd.ExcelWriter("Construction_Cost_Dashboard.xlsx", engine="xlsxwriter") as xl:
    wb = xl.book
    money = wb.add_format({"num_format": "#,##0", "border": 1})
    pct = wb.add_format({"num_format": "0.0%", "border": 1})
    head = wb.add_format({"bold": True, "bg_color": "#1f3a5f", "font_color": "white",
                          "border": 1, "align": "center", "valign": "vcenter"})
    title = wb.add_format({"bold": True, "font_size": 15, "font_color": "#1f3a5f"})

    ws = wb.add_worksheet("Dashboard")
    xl.sheets["Dashboard"] = ws
    ws.hide_gridlines(2)
    ws.set_column("A:A", 2); ws.set_column("B:B", 34); ws.set_column("C:C", 20)
    ws.write("B2", "Construction Portfolio - Cost & Schedule Performance", title)
    ws.write("B3", "24 projects | 2024-2025 | SAR", wb.add_format({"font_color": "#666666"}))
    ws.write_row("B5", ["KPI", "Value"], head)
    rows_out = [
        ("Planned budget (SAR)", planned, money),
        ("Actual cost (SAR)", actual, money),
        ("Cost variance (SAR)", actual - planned, money),
        ("Portfolio overrun", kpis["Portfolio overrun %"] / 100, pct),
        ("Packages over budget", kpis["Packages over budget %"] / 100, pct),
        ("Average delay (days)", round(kpis["Average delay (days)"], 1), money),
        ("Delay vs overrun correlation", round(correlation, 2), money),
    ]
    for i, (label, value, fmt) in enumerate(rows_out, start=6):
        ws.write("B{}".format(i), label, wb.add_format({"border": 1}))
        ws.write("C{}".format(i), value, fmt)
    ws.insert_image("E2", "charts/01_variance_by_package.png", {"x_scale": 0.55, "y_scale": 0.55})
    ws.insert_image("E22", "charts/02_delay_vs_overrun.png", {"x_scale": 0.55, "y_scale": 0.55})
    ws.insert_image("B16", "charts/04_overrun_by_city.png", {"x_scale": 0.5, "y_scale": 0.5})

    for name, frame in [("By work package", by_package), ("By city", by_city),
                        ("By client", by_client), ("Monthly trend", monthly),
                        ("Top 10 overruns", worst), ("Clean data", df)]:
        frame.to_excel(xl, sheet_name=name)
        sheet = xl.sheets[name]
        sheet.set_column(0, 0, 24)
        sheet.set_column(1, len(frame.columns), 17)
        sheet.freeze_panes(1, 1)
        if "avg_overrun_pct" in frame.columns:
            col = list(frame.columns).index("avg_overrun_pct") + 1
            sheet.conditional_format(1, col, len(frame), col,
                                     {"type": "3_color_scale", "min_color": "#63be7b",
                                      "mid_color": "#ffeb84", "max_color": "#f8696b"})

print("\nWrote Construction_Cost_Dashboard.xlsx + 4 charts")
