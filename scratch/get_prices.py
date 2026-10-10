import yfinance as yf
import pandas as pd

# Target WASDE dates
# September WASDE 2026 was likely Sept 11
# October WASDE 2026 was yesterday Oct 9
dates = ['2026-09-11', '2026-10-09']

tickers = {
    'ZW (Wheat)': 'ZW=F',
    'ZC (Corn)': 'ZC=F',
    'WTI Crude': 'CL=F',
    'Brent Crude': 'BZ=F'
}

print("Fetching data...")
for name, ticker in tickers.items():
    try:
        t = yf.Ticker(ticker)
        hist = t.history(start='2026-09-08', end='2026-10-11')
        if hist.empty:
            print(f"No data for {name}")
            continue
        
        print(f"\n--- {name} ---")
        for d in dates:
            # Match date
            dt = pd.to_datetime(d).tz_localize(hist.index.tz)
            if dt in hist.index:
                print(f"{dt.strftime('%Y-%m-%d')}: {hist.loc[dt, 'Close']:.2f}")
            else:
                # Find closest earlier date
                mask = hist.index <= dt
                if mask.any():
                    closest = hist[mask].index[-1]
                    print(f"Closest {closest.strftime('%Y-%m-%d')}: {hist.loc[closest, 'Close']:.2f}")
    except Exception as e:
        print(f"Error for {name}: {e}")
