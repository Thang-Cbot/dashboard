import yfinance as yf
import pandas as pd

target_date = '2025-10-10'

tickers = {
    'ZW (Wheat)': 'ZW=F',
    'WTI Crude': 'CL=F'
}

print("Fetching data for Oct 2025...")
for name, ticker in tickers.items():
    t = yf.Ticker(ticker)
    hist = t.history(start='2025-10-01', end='2025-10-15')
    if hist.empty:
        print(f"No data for {name}")
        continue
    
    dt = pd.to_datetime(target_date).tz_localize(hist.index.tz)
    # find closest date on or before target
    mask = hist.index <= dt
    if mask.any():
        closest = hist[mask].index[-1]
        print(f"{name} at {closest.strftime('%Y-%m-%d')}: {hist.loc[closest, 'Close']:.2f}")
