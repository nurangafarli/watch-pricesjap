"""
Are Watches from Japan Really Cheaper?
======================================
A simple data analysis using pandas and matplotlib.

How to use:
    1. Fill in watch_prices.csv with real data from Chrono24
    2. Run: python3 analysis.py
    3. Charts save to the same folder
"""

import pandas as pd
import matplotlib.pyplot as plt

# ============================================================
# STEP 1: Load the data
# ============================================================

df = pd.read_csv("watch_prices.csv")

print(f"Loaded {len(df)} listings")
print(f"Watches: {df['watch'].nunique()}")
print(f"Regions: {df['region'].unique().tolist()}")
print()

# ============================================================
# STEP 2: Calculate landed cost for non-EU regions
# ============================================================

# Estonian import costs
DUTY_RATE = 0.045   # 4.5% on watches
VAT_RATE = 0.22     # 22% Estonian VAT

# EU countries have no extra import costs
eu_countries = ["Germany", "Italy", "France"]

df["is_eu"] = df["region"].isin(eu_countries)

# Landed cost = price + shipping + duty + VAT (for non-EU)
df["base_cost"] = df["price_eur"] + df["shipping_eur"]
df["duty"] = df["base_cost"] * DUTY_RATE * (~df["is_eu"])
df["vat"] = (df["base_cost"] + df["duty"]) * VAT_RATE * (~df["is_eu"])
df["landed_cost"] = df["base_cost"] + df["duty"] + df["vat"]

# ============================================================
# STEP 3: Summary table — Japan vs EU
# ============================================================

japan = df[df["region"] == "Japan"].groupby("watch").agg(
    japan_median_price=("price_eur", "median"),
    japan_median_landed=("landed_cost", "median"),
    japan_count=("price_eur", "count")
)

eu = df[df["is_eu"]].groupby("watch").agg(
    eu_median_price=("price_eur", "median"),
    eu_count=("price_eur", "count")
)

summary = japan.join(eu)
summary["listed_gap_%"] = ((summary["eu_median_price"] - summary["japan_median_price"])
                            / summary["eu_median_price"] * 100).round(1)
summary["landed_gap_%"] = ((summary["eu_median_price"] - summary["japan_median_landed"])
                            / summary["eu_median_price"] * 100).round(1)

print("=" * 65)
print("JAPAN vs EU — PRICE COMPARISON")
print("=" * 65)
print(summary.to_string())
print()

# Save summary to CSV (handy for Tableau)
summary.to_csv("summary.csv")
print("Saved summary.csv (you can open this in Tableau)\n")

# ============================================================
# CHART 1: Median price by region for each watch
# ============================================================

fig, ax = plt.subplots(figsize=(10, 5))

median_by_region = df.groupby(["watch", "region"])["price_eur"].median().unstack()
colors = {"Japan": "#e74c3c", "Germany": "#3498db", "Italy": "#2ecc71"}
median_by_region[list(colors.keys())].plot(
    kind="bar", ax=ax, color=list(colors.values()), width=0.75
)

ax.set_title("Median Listed Price by Region", fontsize=14, fontweight="bold")
ax.set_ylabel("Price (EUR)")
ax.set_xlabel("")
ax.tick_params(axis="x", rotation=25)
ax.legend(title="Region")
ax.grid(axis="y", alpha=0.3)

# Add price labels on bars
for container in ax.containers:
    ax.bar_label(container, fmt="€%.0f", fontsize=7, padding=2)

plt.tight_layout()
plt.savefig("chart1_price_by_region.png", dpi=150)
plt.close()
print("Saved chart1_price_by_region.png")

# ============================================================
# CHART 2: Japan discount — listed vs landed
# ============================================================

fig, ax = plt.subplots(figsize=(9, 5))

x = range(len(summary))
width = 0.35

bars1 = ax.bar([i - width/2 for i in x], summary["listed_gap_%"],
               width, label="Listed Price Gap", color="#2ecc71")
bars2 = ax.bar([i + width/2 for i in x], summary["landed_gap_%"],
               width, label="After Import Costs", color="#e74c3c")

ax.set_title("Japan Discount: Before and After Import Costs",
             fontsize=14, fontweight="bold")
ax.set_ylabel("Savings vs EU (%)")
ax.set_xticks(x)
ax.set_xticklabels(summary.index, rotation=25, ha="right", fontsize=9)
ax.legend()
ax.grid(axis="y", alpha=0.3)
ax.axhline(y=0, color="black", linewidth=0.5)

# Add percentage labels
ax.bar_label(bars1, fmt="%.1f%%", fontsize=8, padding=2)
ax.bar_label(bars2, fmt="%.1f%%", fontsize=8, padding=2)

plt.tight_layout()
plt.savefig("chart2_japan_discount.png", dpi=150)
plt.close()
print("Saved chart2_japan_discount.png")

# ============================================================
# CHART 3: Cost breakdown — where the money goes (Japan)
# ============================================================

japan_breakdown = df[df["region"] == "Japan"].groupby("watch").agg(
    price=("price_eur", "median"),
    shipping=("shipping_eur", "median"),
    duty=("duty", "median"),
    vat=("vat", "median"),
).round(0)

eu_median = df[df["is_eu"]].groupby("watch")["price_eur"].median()

fig, ax = plt.subplots(figsize=(9, 5))

x = range(len(japan_breakdown))
ax.bar(x, japan_breakdown["price"], label="Watch Price", color="#3498db")
ax.bar(x, japan_breakdown["shipping"], bottom=japan_breakdown["price"],
       label="Shipping", color="#f39c12")
ax.bar(x, japan_breakdown["duty"],
       bottom=japan_breakdown["price"] + japan_breakdown["shipping"],
       label="Duty (4.5%)", color="#e67e22")
ax.bar(x, japan_breakdown["vat"],
       bottom=japan_breakdown["price"] + japan_breakdown["shipping"] + japan_breakdown["duty"],
       label="VAT (22%)", color="#e74c3c")

# EU reference line
for i, watch in enumerate(japan_breakdown.index):
    if watch in eu_median.index:
        ax.hlines(eu_median[watch], i - 0.35, i + 0.35,
                  colors="#2c3e50", linestyles="--", linewidth=2,
                  label="EU Median" if i == 0 else "")

ax.set_title("Japan: Where Does the Money Go?\n(Dashed line = EU median price)",
             fontsize=14, fontweight="bold")
ax.set_ylabel("Total Cost (EUR)")
ax.set_xticks(x)
ax.set_xticklabels(japan_breakdown.index, rotation=25, ha="right", fontsize=9)
ax.legend(loc="upper left", fontsize=8)
ax.grid(axis="y", alpha=0.3)

plt.tight_layout()
plt.savefig("chart3_cost_breakdown.png", dpi=150)
plt.close()
print("Saved chart3_cost_breakdown.png")

# ============================================================
# CHART 4: Simple scatter — price spread by region
# ============================================================

fig, axes = plt.subplots(2, 3, figsize=(12, 7))
axes = axes.flatten()

for i, watch in enumerate(df["watch"].unique()):
    if i >= 6:
        break
    ax = axes[i]
    subset = df[df["watch"] == watch]
    for region in subset["region"].unique():
        region_data = subset[subset["region"] == region]
        ax.scatter(
            [region] * len(region_data),
            region_data["price_eur"],
            color=colors.get(region, "#999"),
            alpha=0.6, s=40
        )
    median_line = subset.groupby("region")["price_eur"].median()
    ax.plot(median_line.index, median_line.values, "k--", alpha=0.4, linewidth=1)
    ax.set_title(watch, fontsize=10, fontweight="bold")
    ax.tick_params(axis="x", rotation=30, labelsize=8)
    ax.tick_params(axis="y", labelsize=8)
    ax.grid(axis="y", alpha=0.3)

# Hide unused subplots
for j in range(i + 1, 6):
    axes[j].set_visible(False)

fig.suptitle("Price Spread by Region", fontsize=14, fontweight="bold", y=1.01)
plt.tight_layout()
plt.savefig("chart4_price_spread.png", dpi=150)
plt.close()
print("Saved chart4_price_spread.png")

# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 65)
print("FINDINGS")
print("=" * 65)

for watch in summary.index:
    row = summary.loc[watch]
    listed = row["listed_gap_%"]
    landed = row["landed_gap_%"]

    if landed > 2:
        verdict = f"Still cheaper from Japan by ~{landed:.0f}%"
    elif landed > -2:
        verdict = "About the same after import costs"
    else:
        verdict = "Actually MORE expensive from Japan"

    print(f"\n  {watch}:")
    print(f"    Japan listed price:   €{row['japan_median_price']:,.0f}")
    print(f"    EU listed price:      €{row['eu_median_price']:,.0f}")
    print(f"    Discount (listed):    {listed:+.1f}%")
    print(f"    Discount (landed):    {landed:+.1f}%")
    print(f"    → {verdict}")

print("\n\nDone! Check the chart images in your project folder.")
print("Open summary.csv in Tableau for further exploration.")

