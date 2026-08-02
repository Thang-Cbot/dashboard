import json
import pandas as pd
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
DB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "CBOT_PowerApps_Database.xlsx")

def load_json(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def process_macro():
    data = load_json("macro_data.json")
    rows = []
    timestamp = data.get("timestamp", "")
    for k, v in data.items():
        if k != "timestamp" and isinstance(v, dict):
            rows.append({
                "Indicator": k.upper(),
                "Price": v.get("price", 0),
                "Previous": v.get("prev", 0),
                "ChangePct": v.get("pct", 0),
                "Timestamp": timestamp
            })
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Indicator", "Price", "Previous", "ChangePct", "Timestamp"])

def process_signals():
    data = load_json("last_signals.json")
    rows = []
    for k, v in data.items():
        if isinstance(v, dict):
            rows.append({
                "Symbol": k,
                "SetupType": str(v.get("setup_type", "")),
                "EntryRange": str(v.get("setup_entry_range", "")),
                "Message": str(v.get("msg", "")).replace("\n", " | "),
                "Timestamp": str(v.get("timestamp", ""))
            })
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Symbol", "SetupType", "EntryRange", "Message", "Timestamp"])

def process_fundamentals():
    data = load_json("fundamental_data.json")
    rows = []
    for sym in ["ZC", "ZW", "ZS"]:
        if sym in data:
            item = data[sym]
            cot = item.get("cot_report", {})
            rows.append({
                "Symbol": sym,
                "IntradayStrategy": str(item.get("intraday_strategy", "")),
                "EntryZone": str(item.get("entry_zone", "")),
                "StopLoss": str(item.get("stop_loss", "")),
                "TakeProfit1": str(item.get("take_profit_1", "")),
                "TakeProfit2": str(item.get("take_profit_2", "")),
                "SwingLogic": str(item.get("swing_logic", "")),
                "CotAction": str(cot.get("action", "")),
                "WeatherShort": str(item.get("short_term_weather", ""))
            })
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Symbol", "IntradayStrategy", "EntryZone", "StopLoss", "TakeProfit1", "TakeProfit2", "SwingLogic", "CotAction", "WeatherShort"])

def process_prices():
    rows = []
    for sym in ["ZC", "ZW", "ZS"]:
        path = os.path.join(OUTPUT_DIR, f"{sym}_active_H1.csv")
        if os.path.exists(path):
            df = pd.read_csv(path)
            df = df.tail(24).copy()
            df.insert(0, 'Symbol', sym) # Insert Symbol at start
            rows.append(df)
    
    if rows:
        combined = pd.concat(rows, ignore_index=True)
        if "time" in combined.columns:
            combined["time"] = combined["time"].astype(str)
        # Clean any float NaN
        combined = combined.fillna(0)
        return combined
    return pd.DataFrame(columns=["Symbol", "time", "open", "high", "low", "close", "volume"])

def write_to_excel_with_tables(df_dict, filepath):
    writer = pd.ExcelWriter(filepath, engine='xlsxwriter')
    
    for sheet_name, df in df_dict.items():
        if df.empty:
            df.loc[0] = [''] * len(df.columns)
            
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        worksheet = writer.sheets[sheet_name]
        
        # Get dataframe dimensions
        (max_row, max_col) = df.shape
        
        # Create a list of column headers, to use in add_table()
        column_settings = [{'header': column} for column in df.columns]
        
        # Add the Excel table structure.
        worksheet.add_table(0, 0, max_row, max_col - 1, {
            'columns': column_settings,
            'name': f'Table_{sheet_name}',
            'style': 'Table Style Medium 9'
        })
        
        # Autofit columns
        worksheet.autofit()
        
    writer.close()

def repair_excel_with_com(filepath):
    try:
        import win32com.client as win32
        logging.info("Repairing Excel file metadata via COM...")
        excel = win32.Dispatch('Excel.Application')
        excel.Visible = False
        wb = excel.Workbooks.Open(os.path.abspath(filepath))
        wb.Save()
        wb.Close()
        excel.Quit()
        logging.info("COM Repair successful.")
    except Exception as e:
        logging.warning(f"COM Repair skipped or failed: {e}")

def main():
    logging.info("Starting Power Apps data export with xlsxwriter...")
    
    dfs = {
        "Macro": process_macro(),
        "Signals": process_signals(),
        "Fundamentals": process_fundamentals(),
        "Prices": process_prices()
    }
    
    write_to_excel_with_tables(dfs, DB_FILE)
    repair_excel_with_com(DB_FILE)
    logging.info(f"Excel file successfully generated natively at {DB_FILE}")

if __name__ == "__main__":
    main()

