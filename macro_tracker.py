import yfinance as yf
import datetime

def fetch_macro_data():
    try:
        # Brent Crude Oil
        brent = yf.Ticker("BZ=F")
        brent_data = brent.history(period="1d")
        brent_price = brent_data['Close'].iloc[-1] if not brent_data.empty else "N/A"
        
        # US Dollar Index
        dxy = yf.Ticker("DX-Y.NYB")
        dxy_data = dxy.history(period="1d")
        dxy_price = dxy_data['Close'].iloc[-1] if not dxy_data.empty else "N/A"
        
        print("--- MACRO INDICATORS ---")
        print(f"Brent Crude Oil: ${brent_price:.2f}" if isinstance(brent_price, float) else f"Brent Crude Oil: {brent_price}")
        print(f"US Dollar Index (DXY): {dxy_price:.2f}" if isinstance(dxy_price, float) else f"US Dollar Index (DXY): {dxy_price}")
        
    except Exception as e:
        print(f"Error fetching macro data: {e}")

if __name__ == '__main__':
    fetch_macro_data()
