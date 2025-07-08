import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# Load allocation history from the database
conn = sqlite3.connect("paa_allocation.db")
df = pd.read_sql_query("SELECT date, etf, amount FROM allocations", conn)
conn.close()

# Convert date string to datetime
df['date'] = pd.to_datetime(df['date'])

# Pivot the data: rows = dates, columns = ETFs, values = amount
pivot_df = df.pivot(index='date', columns='etf', values='amount').fillna(0)

# Plot stacked area chart of allocation over time
plt.figure(figsize=(12, 6))
pivot_df.plot(kind='area', stacked=True, colormap='tab20', figsize=(12, 6))
plt.title("Monthly ETF Allocation (PAA Strategy)")
plt.ylabel("Amount ($)")
plt.xlabel("Date")
plt.legend(loc='center left', bbox_to_anchor=(1.0, 0.5))
plt.grid(True)
plt.tight_layout()
plt.savefig("paa_allocation_trend.png")
plt.show()
