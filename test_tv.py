from tvDatafeed import TvDatafeed, Interval
import pandas as pd

def main():
    print("Initializing TvDatafeed...")
    # Initialize without credentials for guest access
    tv = TvDatafeed()
    
    print("\n--- Fetching ZC (Corn) ---")
    try:
        # TradingView uses 'ZC1!' for Corn continuous futures on CBOT
        zc_data = tv.get_hist(symbol='ZC1!', exchange='CBOT', interval=Interval.in_1_hour, n_bars=10)
        if zc_data is not None:
            print(zc_data)
        else:
            print("Failed to fetch ZC1!")
    except Exception as e:
        print(f"Error fetching ZC: {e}")

    print("\n--- Fetching ZW (Wheat) ---")
    try:
        # TradingView uses 'ZW1!' for Wheat continuous futures on CBOT
        zw_data = tv.get_hist(symbol='ZW1!', exchange='CBOT', interval=Interval.in_1_hour, n_bars=10)
        if zw_data is not None:
            print(zw_data)
        else:
            print("Failed to fetch ZW1!")
    except Exception as e:
        print(f"Error fetching ZW: {e}")

if __name__ == "__main__":
    main()
