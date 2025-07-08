import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime, timedelta

def calculate_ief_ratio(num_negative_momentum):
    lookup = {
        0: 0.0,
        1: 1/6,
        2: 2/6,
        3: 3/6,
        4: 4/6,
        5: 5/6,
        6: 1.0
    }
    return lookup.get(num_negative_momentum, 1.0)

def paa_book_strategy_with_moving_avg(total_money, etfs, fallback_asset='IEF', top_n=6, lookback_months=12):
    date_today = datetime.today().strftime("%Y-%m-%d")
    db_name = "paa_allocation.db"
    csv_filename = f"paa_allocation_{date_today}.csv"

    all_tickers = etfs + [fallback_asset]
    end_date = datetime.today()
    start_date = end_date - timedelta(days=lookback_months * 30 + 30)

    data = yf.download(
        all_tickers,
        start=start_date,
        end=end_date,
        progress=False,
        threads=False
    )

    if isinstance(data.columns, pd.MultiIndex) and 'Close' in data.columns.levels[0]:
        price_data = data['Close']
    else:
        print("❌ 'Close' price data not found.")
        return

    price_data = price_data.dropna(axis=1)
    if price_data.empty:
        print("❌ No valid price data.")
        return

    # Calculate 12-month simple moving average
    rolling_avg = price_data.rolling(window=252).mean().iloc[-1]
    print ('rolling avg: ', rolling_avg)
    current_price = price_data.iloc[-1]
    momentum = (current_price / rolling_avg) - 1
    momentum = momentum.dropna()
    print ('momentum: ', momentum)

    selected = momentum[etfs].sort_values(ascending=False).head(top_n)
    num_negative = (momentum[etfs] < 0).sum()
    ief_ratio = calculate_ief_ratio(num_negative)
    print('ief_ratio: ', ief_ratio)
    offensive_ratio = 1 - ief_ratio

    ief_amount = round(total_money * ief_ratio, 2)
    remaining_amount = total_money - ief_amount
    offensive_allocation = round(remaining_amount / top_n, 2) if top_n != 0 else 0

    allocation = {}
    for etf in selected.index:
        if momentum[etf] >= 0:
            allocation[etf] = offensive_allocation

    if ief_amount > 0:
        allocation[fallback_asset] = ief_amount

    # Save to CSV
    allocation_df = pd.DataFrame(allocation.items(), columns=["ETF", "Allocated Amount"])
    allocation_df.to_csv(csv_filename, index=False)

    # Save to SQLite
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            etf TEXT,
            amount REAL
        )
    """)
    for etf, amount in allocation.items():
        c.execute("INSERT INTO allocations (date, etf, amount) VALUES (?, ?, ?)", (date_today, etf, amount))
    conn.commit()
    conn.close()

    # Save chart
    plt.figure(figsize=(10, 6))
    momentum[etfs].sort_values().plot(kind='barh')
    plt.title('ETFs - Price vs. 12-Month Moving Average')
    plt.xlabel('Relative Momentum')
    plt.tight_layout()
    plt.savefig(f"momentum_chart_{date_today}.png")
    plt.close()

    print(f"✅ Allocation saved to {csv_filename} and {db_name}")
    print("📈 Momentum chart saved.")
    print("💼 Final Allocation:", allocation)

# Run the Strategy
etfs = ['SPY', 'QQQ', 'IWM', 'VGK', 'EWJ', 'EEM', 'VNQ', 'GLD', 'DBC', 'HYG', 'LQD']
paa_book_strategy_with_moving_avg(2000, etfs)
