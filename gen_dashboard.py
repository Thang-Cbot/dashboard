import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

def load_json(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load {filepath} - {e}")
        return {}

def load_h1_candles(base_dir):
    """Load H1 candles from Mon 7:00 of current week for all 3 commodities."""
    try:
        import pandas as pd
        from datetime import datetime, timedelta

        now = datetime.now()
        days_since_mon = now.weekday()  # Mon=0
        week_start = (now - timedelta(days=days_since_mon)).replace(
            hour=7, minute=0, second=0, microsecond=0)

        result = {}
        for code in ['ZC', 'ZW']:
            filepath = os.path.join(base_dir, 'Data', 'output', f'{code}_active_H1.csv')
            if not os.path.exists(filepath):
                result[code] = []
                continue

            df = pd.read_csv(filepath)
            df['_dt'] = pd.to_datetime(df['Time'], errors='coerce')
            df = df.dropna(subset=['_dt']).sort_values('_dt')
            df = df[df['_dt'] >= week_start].reset_index(drop=True)

            candles = []
            for _, row in df.iterrows():
                try:
                    candles.append({
                        't':    str(row['Time']),
                        'o':    round(float(row['Open']),  2),
                        'h':    round(float(row['High']),  2),
                        'l':    round(float(row['Low']),   2),
                        'c':    round(float(row['Close']), 2),
                        'v':    int(row['Volume'])       if pd.notna(row['Volume'])       else 0,
                        'oi':   int(row['OpenInterest']) if pd.notna(row['OpenInterest']) else 0,
                        'rsi':  round(float(row['RSI']),   2) if pd.notna(row['RSI'])   else 50.0,
                        'ema21':round(float(row['EMA_21']),2) if pd.notna(row['EMA_21']) else 0,
                        'ema50':round(float(row['EMA_50']),2) if pd.notna(row['EMA_50']) else 0,
                        'atr':  round(float(row['ATR']),   2) if pd.notna(row['ATR'])   else 0,
                        's1':   round(float(row['S1']),    2) if pd.notna(row['S1'])    else 0,
                        'r1':   round(float(row['R1']),    2) if pd.notna(row['R1'])    else 0,
                    })
                except Exception:
                    continue
            result[code] = candles
        return result
    except Exception as e:
        print(f"Warning: Could not load H1 candles: {e}")
        return {'ZC': [], 'ZW': []}

def main():
    base_dir = os.path.dirname(__file__)
    
    # 1. Load Data
    future_chart_data = load_json(os.path.join(base_dir, 'Future chart', 'future_chart_data.json'))
    macro_data = load_json(os.path.join(base_dir, 'Data', 'output', 'macro_data.json'))
    fundamental_data = load_json(os.path.join(base_dir, 'Data', 'output', 'fundamental_data.json'))
    cot_data = load_json(os.path.join(base_dir, 'Data', 'output', 'cot_data.json'))
    last_signals = load_json(os.path.join(base_dir, 'Data', 'output', 'last_signals.json'))
    rsi_data = load_json(os.path.join(base_dir, 'Data', 'output', 'rsi_data.json'))
    snapshot_data = load_json(os.path.join(base_dir, 'Data', 'output', 'v3_state_snapshot.json'))
    h1_candles = load_h1_candles(base_dir)
    weather_short = load_json(os.path.join(base_dir, 'Data', 'output', 'weather_short.json'))
    weather_long = load_json(os.path.join(base_dir, 'Data', 'output', 'weather_long.json'))
    export_sales = load_json(os.path.join(base_dir, 'Data', 'output', 'export_sales.json'))
    
    # 2. Combine Data into single Payload
    payload = {
        "future_chart": future_chart_data,
        "macro": macro_data,
        "fundamentals": fundamental_data,
        "cot": cot_data,
        "last_signals": last_signals,
        "rsi": rsi_data,
        "snapshot": snapshot_data,
        "h1_candles": h1_candles,
        "news": {
            "weather_short": weather_short,
            "weather_long": weather_long,
            "export_sales": export_sales
        }
    }
    
    json_str = json.dumps(payload, ensure_ascii=False)
    injection_code = f"window.APP_DATA = {json_str};"
    
    # 3. Read Template
    template_path = os.path.join(base_dir, 'dashboard_template.html')
    if not os.path.exists(template_path):
        print(f"Error: Template file {template_path} not found.")
        sys.exit(1)
        
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()
        
    # 4. Inject
    html = html.replace("/* INJECT_DATA_HERE */", injection_code)
    
    # 5. Output
    output_path = os.path.join(base_dir, 'CBOT_Dashboard.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
        
    print(f"Done! File size: {len(html)} bytes. Generated: {output_path}")

if __name__ == '__main__':
    main()
