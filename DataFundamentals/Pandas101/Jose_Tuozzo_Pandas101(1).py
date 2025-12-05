# Pandas101 — PastHires analysis (ready-to-submit)
# Steps:
# 1) Load CSV if present; otherwise use embedded fallback that mirrors lab data.
# 2) Print dataset overview, completeness, value counts, numeric describe.
# 3) Compute hire rate by education and plot a labeled, sorted bar chart.

import pandas as pd
import matplotlib.pyplot as plt
import os

# 1) Load data
csv_path = "PastHires.csv"  # place file next to this script if you want to use the CSV
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
else:
    df = pd.DataFrame({
        "Years Experience": [10, 0, 7, 2, 20, 0, 5, 0, 3, 15, 1, 9, 0],
        "Employed?": ['Y', 'N', 'N', 'Y', 'N', 'N', 'Y', 'N', 'Y', 'N', 'N', 'Y', 'Y'],
        "Previous employers": [4, 0, 6, 1, 5, 0, 2, 0, 1, 4, 0, 2, 0],
        "Level of Education": ['BS', 'BS', 'BS', 'BS', 'BS', 'BS', 'MS', 'PhD', 'PhD', 'PhD', 'PhD', 'MS', 'BS'],
        "Top-tier school": ['N', 'Y', 'N', 'N', 'Y', 'Y', 'N', 'N', 'Y', 'N', 'Y', 'N', 'Y'],
        "Interned": ['N', 'Y', 'N', 'Y', 'N', 'Y', 'Y', 'N', 'N', 'N', 'Y', 'Y', 'Y'],
        "Hired": ['Y', 'Y', 'N', 'N', 'Y', 'Y', 'Y', 'N', 'Y', 'N', 'Y', 'Y', 'Y'],
    })

# 2) Overview & quality checks
print("Shape:", df.shape)
print("\nHead:\n", df.head(3).to_string(index=False))
df.info()
print("\nMissing values per column:\n", df.isna().sum().to_string())
for col in ["Level of Education","Employed?","Interned","Top-tier school","Hired"]:
    print(f"\nValue counts for {col}:\n" + df[col].value_counts().to_string())
print("\nNumeric describe():\n", df.select_dtypes(include="number").describe().to_string())

# 3) Hire rate by education + plot
hire_rate = df.groupby("Level of Education")["Hired"].apply(lambda x: (x=="Y").mean()).sort_values(ascending=False)
print("\nHire rate by education (descending):")
for lvl, val in hire_rate.items():
    print(f"{lvl:>3}  {val*100:6.1f}%")

fig, ax = plt.subplots(figsize=(9.5, 5.5))
bars = ax.bar(hire_rate.index, hire_rate.values, color="teal")
ax.set_title("Hire Rate by Education")
ax.set_xlabel("Level of Education")
ax.set_ylabel("Hire Rate")
ax.set_ylim(0, 1.05)
ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
ax.set_yticklabels([f"{int(t*100)}%" for t in [0, 0.25, 0.5, 0.75, 1.0]])
for b in bars:
    v = b.get_height()
    ax.text(b.get_x()+b.get_width()/2, v+0.03, f"{v*100:.1f}%", ha="center", va="bottom", fontsize=11)
ax.grid(axis="y", linestyle="--", alpha=0.4)
fig.tight_layout()
plt.show()  # In notebooks: displays chart