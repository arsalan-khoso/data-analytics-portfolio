"""Sales performance, cohort retention and RFM customer segmentation.

Business questions:
  1. Where is revenue actually coming from - product, channel, region?
  2. How many customers come back after their first purchase, month by month?
  3. Which customers are worth retaining, and which are already slipping away?
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams.update({"figure.dpi": 130, "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False})
NAVY, ORANGE, TEAL, GREY = "#1f3a5f", "#e07b39", "#2a9d8f", "#9aa5b1"
rng = np.random.default_rng(7)

# ---------------------------------------------------------------- build source
# Transaction log for a B2B supplier: 1,200 customers acquired over 24 months,
# each with a decaying probability of repeat purchase.
PRODUCTS = {"Safety Equipment": 420, "Power Tools": 1250, "Electrical Supplies": 310,
            "Plumbing Fixtures": 680, "Building Materials": 95, "HVAC Parts": 1580}
CHANNELS = ["Direct Sales", "Online Portal", "Distributor", "Phone Order"]
REGIONS = ["Eastern Province", "Riyadh", "Makkah", "Qassim", "Asir"]

records = []
for cid in range(1, 1201):
    first = pd.Timestamp("2024-01-01") + pd.Timedelta(days=int(rng.integers(0, 730)))
    region = rng.choice(REGIONS, p=[0.38, 0.27, 0.18, 0.1, 0.07])
    channel = rng.choice(CHANNELS, p=[0.3, 0.35, 0.2, 0.15])
    # Online portal customers are stickier; phone orders churn fastest.
    stickiness = {"Online Portal": 0.78, "Direct Sales": 0.70,
                  "Distributor": 0.62, "Phone Order": 0.48}[channel]

    order_date, n_orders = first, 0
    while order_date <= pd.Timestamp("2025-12-31") and rng.random() < stickiness ** (n_orders * 0.6 + 1):
        for _ in range(int(rng.integers(1, 4))):
            product = rng.choice(list(PRODUCTS))
            qty = int(rng.integers(1, 25))
            unit = PRODUCTS[product] * rng.normal(1, 0.08)
            discount = rng.choice([0, 0.05, 0.1, 0.15], p=[0.55, 0.25, 0.15, 0.05])
            records.append({
                "customer_id": "CUST-{:04d}".format(cid),
                "order_id": "SO-{:06d}".format(len(records) + 1),
                "order_date": order_date,
                "region": region,
                "channel": channel,
                "product": product,
                "quantity": qty,
                "unit_price_sar": round(unit, 2),
                "discount_pct": discount,
                "revenue_sar": round(qty * unit * (1 - discount), 2),
            })
        n_orders += 1
        order_date += pd.Timedelta(days=int(rng.integers(20, 150)))

df = pd.DataFrame(records)
df.to_csv("data/sales_transactions.csv", index=False)
print("Transactions: {:,} rows | {:,} customers | {:,} orders".format(
    len(df), df.customer_id.nunique(), df.order_id.nunique()))

# ---------------------------------------------------------------- sales KPIs
df["month"] = df["order_date"].dt.to_period("M")
order_level = df.groupby("order_id").agg(revenue_sar=("revenue_sar", "sum"))
kpis = {
    "Total revenue (SAR)": df["revenue_sar"].sum(),
    "Orders": df["order_id"].nunique(),
    "Customers": df["customer_id"].nunique(),
    "Average order value (SAR)": order_level["revenue_sar"].mean(),
    "Orders per customer": df.groupby("customer_id")["order_id"].nunique().mean(),
    "Repeat customer rate %": (df.groupby("customer_id")["order_id"].nunique() > 1).mean() * 100,
    "Revenue lost to discounts (SAR)":
        (df["quantity"] * df["unit_price_sar"] * df["discount_pct"]).sum(),
}
print("\n--- SALES KPIs ---")
for k, v in kpis.items():
    print("{:>34}: {:,.2f}".format(k, v) if isinstance(v, float) else "{:>34}: {:,}".format(k, v))

by_product = (df.groupby("product")
                .agg(revenue_sar=("revenue_sar", "sum"),
                     units=("quantity", "sum"),
                     orders=("order_id", "nunique"))
                .sort_values("revenue_sar", ascending=False))
by_product["revenue_share_pct"] = (by_product["revenue_sar"] / by_product["revenue_sar"].sum() * 100).round(1)

by_channel = (df.groupby("channel")
                .agg(revenue_sar=("revenue_sar", "sum"),
                     customers=("customer_id", "nunique"),
                     orders=("order_id", "nunique")))
by_channel["revenue_per_customer"] = (by_channel["revenue_sar"] / by_channel["customers"]).round(2)
by_channel = by_channel.sort_values("revenue_per_customer", ascending=False)

by_region = (df.groupby("region")
               .agg(revenue_sar=("revenue_sar", "sum"),
                    customers=("customer_id", "nunique"))
               .sort_values("revenue_sar", ascending=False).round(2))

monthly = df.groupby("month").agg(revenue_sar=("revenue_sar", "sum"),
                                  orders=("order_id", "nunique")).round(2)
monthly.index = monthly.index.to_timestamp()
monthly["mom_growth_pct"] = (monthly["revenue_sar"].pct_change() * 100).round(1)

print("\n--- REVENUE BY PRODUCT ---")
print(by_product.round(2).to_string())

# ---------------------------------------------------------------- cohort retention
first_order = df.groupby("customer_id")["order_date"].min().dt.to_period("M")
df["cohort"] = df["customer_id"].map(first_order)
df["period_index"] = (df["month"] - df["cohort"]).apply(lambda x: x.n)

cohort_counts = (df.groupby(["cohort", "period_index"])["customer_id"]
                   .nunique().unstack(fill_value=0))
cohort_size = cohort_counts.iloc[:, 0]
retention = (cohort_counts.divide(cohort_size, axis=0) * 100).round(1)
retention.index = retention.index.astype(str)

print("\n--- RETENTION (% of cohort still ordering) ---")
print(retention.iloc[:8, :7].to_string())

# ---------------------------------------------------------------- RFM segments
snapshot = df["order_date"].max() + pd.Timedelta(days=1)
rfm = df.groupby("customer_id").agg(
    recency_days=("order_date", lambda s: (snapshot - s.max()).days),
    frequency=("order_id", "nunique"),
    monetary_sar=("revenue_sar", "sum")).round(2)

rfm["R"] = pd.qcut(rfm["recency_days"], 4, labels=[4, 3, 2, 1]).astype(int)
rfm["F"] = pd.qcut(rfm["frequency"].rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)
rfm["M"] = pd.qcut(rfm["monetary_sar"], 4, labels=[1, 2, 3, 4]).astype(int)
rfm["rfm_score"] = rfm[["R", "F", "M"]].sum(axis=1)


def segment(row):
    if row["rfm_score"] >= 10:
        return "Champions"
    if row["R"] >= 3 and row["F"] >= 2:
        return "Loyal"
    if row["R"] >= 3:
        return "Promising"
    if row["M"] >= 3:
        return "At Risk - High Value"
    return "Lapsed"


rfm["segment"] = rfm.apply(segment, axis=1)
seg_summary = (rfm.groupby("segment")
                  .agg(customers=("rfm_score", "size"),
                       avg_recency_days=("recency_days", "mean"),
                       avg_orders=("frequency", "mean"),
                       total_revenue_sar=("monetary_sar", "sum"))
                  .sort_values("total_revenue_sar", ascending=False).round(1))
seg_summary["revenue_share_pct"] = (seg_summary["total_revenue_sar"]
                                    / seg_summary["total_revenue_sar"].sum() * 100).round(1)
rfm.to_csv("data/rfm_segments.csv")

print("\n--- RFM SEGMENTS ---")
print(seg_summary.to_string())

at_risk_value = seg_summary.loc["At Risk - High Value", "total_revenue_sar"]
print("\nSAR {:,.0f} of historic revenue sits in the At Risk - High Value segment.".format(at_risk_value))

# ---------------------------------------------------------------- charts
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.bar(monthly.index, monthly["revenue_sar"] / 1000, width=22, color=NAVY)
ax2 = ax.twinx()
ax2.plot(monthly.index, monthly["orders"], color=ORANGE, marker="o", ms=4, lw=1.8)
ax2.set_ylabel("Orders", color=ORANGE); ax2.spines["top"].set_visible(False)
ax.set_title("Monthly revenue and order volume", fontweight="bold", loc="left")
ax.set_ylabel("Revenue (SAR thousands)")
fig.autofmt_xdate(); fig.tight_layout()
fig.savefig("charts/01_monthly_revenue.png"); plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 4.2))
d = by_product.sort_values("revenue_sar")
ax.barh(d.index, d["revenue_sar"] / 1000, color=TEAL)
for i, (val, share) in enumerate(zip(d["revenue_sar"], d["revenue_share_pct"])):
    ax.text(val / 1000 + 20, i, "{:.1f}%".format(share), va="center", fontsize=9)
ax.set_title("Revenue by product line", fontweight="bold", loc="left")
ax.set_xlabel("Revenue (SAR thousands)")
ax.set_xlim(0, d["revenue_sar"].max() / 1000 * 1.18)
fig.tight_layout(); fig.savefig("charts/02_revenue_by_product.png"); plt.close(fig)

view = retention.iloc[:12, :9]
fig, ax = plt.subplots(figsize=(9, 5))
im = ax.imshow(view.values, cmap="YlGnBu", aspect="auto", vmin=0, vmax=100)
ax.set_xticks(range(view.shape[1])); ax.set_xticklabels(["M{}".format(c) for c in view.columns])
ax.set_yticks(range(view.shape[0])); ax.set_yticklabels(view.index, fontsize=8)
for i in range(view.shape[0]):
    for j in range(view.shape[1]):
        val = view.values[i, j]
        if val > 0:
            ax.text(j, i, "{:.0f}".format(val), ha="center", va="center", fontsize=7,
                    color="white" if val > 55 else "#222222")
ax.set_title("Cohort retention (% of customers still ordering)", fontweight="bold", loc="left")
ax.set_xlabel("Months since first order"); ax.set_ylabel("Acquisition cohort")
fig.colorbar(im, ax=ax, shrink=0.8, label="% retained")
fig.tight_layout(); fig.savefig("charts/03_cohort_retention.png"); plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 4.5))
d = seg_summary.sort_values("total_revenue_sar")
colors = [ORANGE if "At Risk" in s else NAVY for s in d.index]
ax.barh(d.index, d["total_revenue_sar"] / 1000, color=colors)
for i, (val, cust) in enumerate(zip(d["total_revenue_sar"], d["customers"])):
    ax.text(val / 1000 + 25, i, "{:,} customers".format(int(cust)), va="center", fontsize=9)
ax.set_title("Revenue by RFM segment", fontweight="bold", loc="left")
ax.set_xlabel("Lifetime revenue (SAR thousands)")
ax.set_xlim(0, d["total_revenue_sar"].max() / 1000 * 1.3)
fig.tight_layout(); fig.savefig("charts/04_rfm_segments.png"); plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 4.2))
d = by_channel.sort_values("revenue_per_customer")
ax.barh(d.index, d["revenue_per_customer"], color=NAVY)
ax.set_title("Revenue per customer by sales channel", fontweight="bold", loc="left")
ax.set_xlabel("SAR per customer (lifetime)")
fig.tight_layout(); fig.savefig("charts/05_channel_value.png"); plt.close(fig)

# ---------------------------------------------------------------- excel report
with pd.ExcelWriter("Sales_Retention_Dashboard.xlsx", engine="xlsxwriter") as xl:
    wb = xl.book
    money = wb.add_format({"num_format": "#,##0", "border": 1})
    num = wb.add_format({"num_format": "#,##0.00", "border": 1})
    head = wb.add_format({"bold": True, "bg_color": "#1f3a5f", "font_color": "white",
                          "border": 1, "align": "center"})
    title = wb.add_format({"bold": True, "font_size": 15, "font_color": "#1f3a5f"})

    ws = wb.add_worksheet("Dashboard")
    xl.sheets["Dashboard"] = ws
    ws.hide_gridlines(2)
    ws.set_column("A:A", 2); ws.set_column("B:B", 34); ws.set_column("C:C", 20)
    ws.write("B2", "Sales Performance & Customer Retention", title)
    ws.write("B3", "{:,} customers | {:,} orders | 2024-2025 | SAR".format(
        df["customer_id"].nunique(), df["order_id"].nunique()),
        wb.add_format({"font_color": "#666666"}))
    ws.write_row("B5", ["KPI", "Value"], head)
    for i, (label, value) in enumerate(kpis.items(), start=6):
        ws.write("B{}".format(i), label, wb.add_format({"border": 1}))
        ws.write("C{}".format(i), value, money if value > 100 else num)
    ws.insert_image("E2", "charts/01_monthly_revenue.png", {"x_scale": 0.55, "y_scale": 0.55})
    ws.insert_image("E22", "charts/03_cohort_retention.png", {"x_scale": 0.55, "y_scale": 0.55})
    ws.insert_image("B15", "charts/04_rfm_segments.png", {"x_scale": 0.5, "y_scale": 0.5})

    for name, frame in [("By product", by_product.round(2)), ("By channel", by_channel),
                        ("By region", by_region), ("Monthly trend", monthly),
                        ("Cohort retention", retention), ("RFM segments", seg_summary),
                        ("RFM customers", rfm)]:
        frame.to_excel(xl, sheet_name=name)
        sheet = xl.sheets[name]
        sheet.set_column(0, 0, 24); sheet.set_column(1, len(frame.columns), 18)
        sheet.freeze_panes(1, 1)
    xl.sheets["Cohort retention"].conditional_format(
        1, 1, len(retention), len(retention.columns),
        {"type": "3_color_scale", "min_color": "#ffffff",
         "mid_color": "#9ecae1", "max_color": "#08519c"})

print("\nWrote Sales_Retention_Dashboard.xlsx + 5 charts")
