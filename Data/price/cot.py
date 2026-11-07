"""
fetch_cot.py - Fetch Du lieu COT Managed Money (COT Data Fetcher)
===================================================================
Keo du lieu Commitments of Traders (COT) Disaggregated tu CFTC ZIP File.
cho 2 hang hoa: ZC, ZW.

Tinh nang nang cap:
  - Luu 13 tuan lich su COT (history) trong cot_data.json
  - Match gia close ngay T3 (cutoff) tu ZW/ZC D1 CSV
  - Tinh Rolling Beta 13-tuan: so HDD thay doi / cent gia thay doi
  - Uoc tinh Net Position hien tai (realtime estimate) dua tren lag gia

Output:
  - Data/output/cot_data.json  (gom ca history 13 tuan + beta + estimate)
  - Cap nhat truong cot_report trong fundamental_data.json (ZC, ZW)

Chay doc lap:
    python Data/price/cot.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import json
import datetime
import urllib.request
import zipfile
import io
import pandas as pd
import numpy as np
from pathlib import Path
from data_config import (
    COT_DATA, FUNDAMENTAL_DATA, CFTC_CODES,
    ensure_output_dir, update_status
)

CODE_TO_FUND_KEY = {
    "002602": "ZC",
    "001602": "ZW"
}

# D1 CSV paths (de lay gia close ngay T3)
CBOT_ROOT = Path(__file__).parent.parent.parent
D1_CSV = {
    "001602": CBOT_ROOT / "Data" / "output" / "ZW_active_D1.csv",
    "002602": CBOT_ROOT / "Data" / "output" / "ZC_active_D1.csv",
}

HISTORY_WEEKS = 13   # So tuan luu lich su


# ─────────────────────────────────────────────────────────────────────────────
def _classify_quadrant(net, change):
    """Phan loai vao Ma Tran 4 O (Smart Money Matrix)."""
    if net > 0 and change > 0:
        return "Q1 (XANH LA) - GOM LONG", "Uu tien LONG. Xu huong tang ben vung."
    elif net > 0 and change < 0:
        return "Q2 (DO NHAT) - XA LONG", "Cam bat day. Canh gia hoi de danh SHORT."
    elif net < 0 and change < 0:
        return "Q3 (DO DAM) - NHOI SHORT", "Uu tien SHORT thuan xu huong."
    elif net < 0 and change > 0:
        return "Q4 (CAM) - COVER SHORT", "Cam Short duoi. Canh LONG bat hoi."
    else:
        return "NEUTRAL", "Cho tin hieu ro rang."


# ─────────────────────────────────────────────────────────────────────────────
def _load_d1_price_map(code):
    """Doc D1 CSV va tra ve dict {date_str -> close_price}."""
    csv_path = D1_CSV.get(code)
    price_map = {}
    if not csv_path or not csv_path.exists():
        return price_map
    try:
        df = pd.read_csv(csv_path)
        df['Time'] = pd.to_datetime(df['Time'])
        df['date_str'] = df['Time'].dt.strftime('%Y-%m-%d')
        for _, row in df.iterrows():
            price_map[row['date_str']] = float(row['Close'])
    except Exception as e:
        print(f"  [WARN] Khong doc duoc D1 CSV cho {code}: {e}")
    return price_map


def _find_nearest_price(price_map, target_date_str, max_lookback=3):
    """
    Tim gia close cua ngay target hoac ngay giao dich gan nhat truoc do
    (toi da max_lookback ngay - xu ly weekend/holiday).
    """
    target = datetime.datetime.strptime(target_date_str, '%Y-%m-%d')
    for offset in range(max_lookback + 1):
        d = (target - datetime.timedelta(days=offset)).strftime('%Y-%m-%d')
        if d in price_map:
            return price_map[d], d
    return None, None


# ─────────────────────────────────────────────────────────────────────────────
def _calc_rolling_beta(history):
    """
    Tinh Rolling Beta = trung binh (delta_net / delta_price)
    cua cac cap tuan ke tiep nhau trong history.
    history: list cac dict {report_date, net_position, price_close_tue}
             sap xep tu cu -> moi
    Tra ve beta (float) hoac None neu khong du du lieu.
    """
    if len(history) < 2:
        return None

    deltas = []
    for i in range(1, len(history)):
        prev = history[i - 1]
        curr = history[i]
        if prev.get('price_close_tue') and curr.get('price_close_tue'):
            d_net   = curr['net_position'] - prev['net_position']
            d_price = curr['price_close_tue'] - prev['price_close_tue']
            if abs(d_price) > 0.1:          # Loai tuan gia khong doi
                deltas.append(d_net / d_price)

    if not deltas:
        return None

    # Trung binh co trong: tuan gan day trong nhieu hon
    weights = np.arange(1, len(deltas) + 1, dtype=float)
    beta = float(np.average(deltas, weights=weights))
    return round(beta, 2)


# ─────────────────────────────────────────────────────────────────────────────
def _calc_z_scores(code, current_history):
    """
    Tính Z56 (56 tuần ~ 1 năm) và Z192 (192 tuần ~ 3.7-4 năm)
    bằng cách kết hợp file lịch sử 10 năm cot_10y_history.csv với current_history.
    """
    csv_path = CBOT_ROOT / "Data" / "output" / "cot_10y_history.csv"
    rows = []
    if csv_path.exists():
        try:
            df_hist = pd.read_csv(csv_path)
            df_hist['CFTC_Contract_Market_Code'] = df_hist['CFTC_Contract_Market_Code'].astype(str).str.zfill(6)
            sub = df_hist[df_hist['CFTC_Contract_Market_Code'] == str(code).zfill(6)].copy()
            sub['Report_Date_as_YYYY-MM-DD'] = pd.to_datetime(sub['Report_Date_as_YYYY-MM-DD'])
            for _, r in sub.iterrows():
                rows.append({
                    "date": r['Report_Date_as_YYYY-MM-DD'],
                    "net": float(r['Net_Position'])
                })
        except Exception:
            pass

    for h in current_history:
        try:
            hdate = pd.to_datetime(h.get('report_date'))
            if not rows or hdate > rows[-1]['date']:
                rows.append({
                    "date": hdate,
                    "net": float(h.get('net_position', 0))
                })
        except Exception:
            pass

    if not rows:
        return 0.0, 0.0, "Normal"

    df_s = pd.DataFrame(rows).drop_duplicates(subset=['date']).sort_values('date').reset_index(drop=True)
    if len(df_s) < 10:
        return 0.0, 0.0, "Normal"

    # Z56 (56 tuần)
    s56 = df_s['net'].tail(56)
    m56 = s56.mean()
    std56 = s56.std() if s56.std() and s56.std() > 0 else 1.0
    z56 = round(float((df_s['net'].iloc[-1] - m56) / std56), 2)

    # Z192 (192 tuần)
    s192 = df_s['net'].tail(192)
    m192 = s192.mean()
    std192 = s192.std() if s192.std() and s192.std() > 0 else 1.0
    z192 = round(float((df_s['net'].iloc[-1] - m192) / std192), 2)

    # Crowd
    if z56 > 2.0 or z192 > 2.0:
        crowd = "Extreme Long"
    elif z56 < -2.0 or z192 < -2.0:
        crowd = "Extreme Short"
    elif abs(z56) > 1.5:
        crowd = "Crowded"
    else:
        crowd = "Normal"

    return z56, z192, crowd


def _generate_cot_commentary(net, change, delta_long, delta_short, quadrant):
    """Tạo nhận định phân tích hành vi Quỹ Managed Money theo chuẩn COT Matrix."""
    # Dòng 1: Xu hướng vị thế ròng
    if net > 0:
        if change > 0:
            line1 = f"COT tiếp tục NET LONG nhưng lực mua gia tăng mạnh mẽ."
        else:
            line1 = f"COT vẫn NET LONG nhưng lực mua suy yếu."
    else:
        if change < 0:
            line1 = f"COT đang NET SHORT sâu và phe Bán tiếp tục áp đảo."
        else:
            line1 = f"COT vẫn NET SHORT nhưng phe Bán đang giảm bớt bán khống."

    # Dòng 2: Chi tiết Long vs Short
    if delta_long < 0 and delta_short > 0:
        line2 = "Long giảm, Short tăng: xả Long + thêm Short, "
        line2 += "chưa đảo chiều sang Net Short." if net > 0 else "củng cố xu hướng giảm."
    elif delta_long > 0 and delta_short < 0:
        line2 = "Long tăng, Short giảm: gom Long + đóng Short, dòng tiền Smart Money tích cực."
    elif delta_long > 0 and delta_short > 0:
        line2 = "Long tăng, Short tăng: mở rộng vị thế 2 đầu, thị trường phân hóa giằng co."
    elif delta_long < 0 and delta_short < 0:
        line2 = "Long giảm, Short giảm: Quỹ đồng loạt chốt lời và hạ đòn bẩy rủi ro."
    else:
        line2 = f"Long {'+' if delta_long >= 0 else ''}{delta_long/1000:.1f}K, Short {'+' if delta_short >= 0 else ''}{delta_short/1000:.1f}K."

    return [line1, line2]


# ─────────────────────────────────────────────────────────────────────────────
def fetch_all_cot():
    """Fetch COT data, backfill 13 tuan history, tinh beta va net estimate."""
    ensure_output_dir()

    # Doc cot_data.json hien tai (neu co) de preserve history
    existing_history = {}
    if COT_DATA.exists():
        try:
            with open(COT_DATA, 'r', encoding='utf-8') as f:
                existing_json = json.load(f)
            for code, info in existing_json.get('commodities', {}).items():
                existing_history[code] = info.get('history', [])
        except Exception:
            pass

    all_results = {
        "fetched_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "CFTC ZIP (Disaggregated Futures Only) + Rolling Beta 13W",
        "commodities": {}
    }

    print("  Fetching CFTC COT data from ZIP (full year 2026)...")
    url = "https://www.cftc.gov/files/dea/history/fut_disagg_txt_2026.zip"
    df_raw = None
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req, timeout=45)
        with zipfile.ZipFile(io.BytesIO(response.read())) as z:
            for filename in z.namelist():
                if filename.endswith(".txt") or filename.endswith(".csv"):
                    with z.open(filename) as f:
                        df_raw = pd.read_csv(f, low_memory=False)
                    break
        if df_raw is None:
            raise Exception("No valid TXT/CSV found in ZIP")
        df_raw['Report_Date_as_YYYY-MM-DD'] = pd.to_datetime(df_raw['Report_Date_as_YYYY-MM-DD'])
        df_raw = df_raw.sort_values('Report_Date_as_YYYY-MM-DD', ascending=False)
        print(f"  [OK] CFTC ZIP: {len(df_raw)} rows loaded.")
    except Exception as e:
        print(f"  [ERROR] Khong tai duoc CFTC ZIP: {e}")
        df_raw = None

    for code, name in CFTC_CODES.items():
        fund_key = CODE_TO_FUND_KEY.get(code, code)
        price_map = _load_d1_price_map(code)

        # ── Xay dung history 13 tuan tu CFTC ZIP ─────────────────────────────
        history = []
        if df_raw is not None:
            df_sym = df_raw[df_raw['CFTC_Contract_Market_Code'] == code].copy()
            df_sym = df_sym.sort_values('Report_Date_as_YYYY-MM-DD', ascending=False)
            # Lay toi da HISTORY_WEEKS + 1 tuan (can them 1 de tinh delta dau tien)
            for _, row in df_sym.head(HISTORY_WEEKS + 1).iterrows():
                long_val  = float(row.get("M_Money_Positions_Long_All", 0))
                short_val = float(row.get("M_Money_Positions_Short_All", 0))
                net_val   = round(long_val - short_val, 0)
                rdate     = row['Report_Date_as_YYYY-MM-DD'].strftime('%Y-%m-%d')
                price_close, matched_date = _find_nearest_price(price_map, rdate)
                history.append({
                    "report_date":     rdate,
                    "net_position":    net_val,
                    "long":            round(long_val, 0),
                    "short":           round(short_val, 0),
                    "price_close_tue": price_close,
                    "price_date":      matched_date,
                })
            history.reverse()   # Sap xep cu -> moi

        if not history:
            # Fallback: dung history cu tu file
            history = existing_history.get(code, [])

        # ── Tinh Rolling Beta 13 tuan ─────────────────────────────────────────
        beta = _calc_rolling_beta(history)

        # ── Lay 2 ky gan nhat de tinh quadrant & delta ───────────────────────
        if len(history) >= 2:
            curr_entry = history[-1]
            prev_entry = history[-2]
            net_curr = curr_entry['net_position']
            net_prev = prev_entry['net_position']
            change   = net_curr - net_prev
            report_date = curr_entry['report_date']
            long_curr = curr_entry.get('long', 0)
            short_curr = curr_entry.get('short', 0)
            long_prev = prev_entry.get('long', long_curr)
            short_prev = prev_entry.get('short', short_curr)
            delta_long = long_curr - long_prev
            delta_short = short_curr - short_prev
        elif len(history) == 1:
            curr_entry = history[-1]
            net_curr = curr_entry['net_position']
            net_prev = net_curr
            change   = 0
            report_date = curr_entry['report_date']
            long_curr = curr_entry.get('long', 0)
            short_curr = curr_entry.get('short', 0)
            delta_long = 0
            delta_short = 0
        else:
            net_curr = 0; net_prev = 0; change = 0
            long_curr = 0; short_curr = 0; delta_long = 0; delta_short = 0
            report_date = datetime.date.today().strftime('%Y-%m-%d')
            curr_entry = {}

        quadrant, action = _classify_quadrant(net_curr, change)

        # ── Tinh Z56, Z192, Crowd & Commentary ───────────────────────────────
        z56, z192, crowd = _calc_z_scores(code, history)
        commentary = _generate_cot_commentary(net_curr, change, delta_long, delta_short, quadrant)

        if "Q1" in quadrant:
            sentiment_bias = "BULL · Q1"
        elif "Q2" in quadrant:
            sentiment_bias = "BEAR · Q2"
        elif "Q3" in quadrant:
            sentiment_bias = "BEAR · Q3"
        elif "Q4" in quadrant:
            sentiment_bias = "BULL · Q4"
        else:
            sentiment_bias = "NEUTRAL"

        try:
            report_date_short = datetime.datetime.strptime(report_date, '%Y-%m-%d').strftime('%d/%m')
        except Exception:
            report_date_short = report_date[-5:] if report_date else "—" 

        # ── Uoc tinh Net hien tai (dua tren gia lag tu T3 -> hom nay) ────────
        net_estimated = None
        price_lag_change = None
        estimated_extra_contracts = None
        cutoff_price = curr_entry.get('price_close_tue')
        
        # Gia hien tai = close cua ngay hom qua (hoac gan nhat trong D1)
        today_str  = datetime.date.today().strftime('%Y-%m-%d')
        latest_price, latest_date = _find_nearest_price(price_map, today_str, max_lookback=5)

        if beta and cutoff_price and latest_price and latest_date != curr_entry.get('price_date'):
            price_lag_change = round(latest_price - cutoff_price, 2)
            estimated_extra_contracts = round(price_lag_change * beta, 0)
            net_estimated = round(net_curr + estimated_extra_contracts, 0)
            quadrant_est, action_est = _classify_quadrant(net_estimated, estimated_extra_contracts)
        else:
            quadrant_est = quadrant
            action_est   = action

        # ── Build result ──────────────────────────────────────────────────────
        result = {
            "commodity":          name,
            "cftc_code":          code,
            "report_date":        report_date,
            "report_date_short":  report_date_short,
            "sentiment_bias":     sentiment_bias,
            "long_curr":          long_curr,
            "short_curr":         short_curr,
            "delta_long":         delta_long,
            "delta_short":        delta_short,
            "net_position":       net_curr,
            "net_prev":           net_prev,
            "change":             change,
            "quadrant":           quadrant,
            "action":             action,
            "z56":                z56,
            "z192":               z192,
            "crowd":              crowd,
            "commentary":         commentary,
            # ── Rolling Beta & Realtime Estimate
            "rolling_beta_13w":           beta,
            "cutoff_price_tue":           cutoff_price,
            "latest_price":               latest_price,
            "latest_price_date":          latest_date,
            "price_lag_change":           price_lag_change,
            "estimated_extra_contracts":  estimated_extra_contracts,
            "net_estimated":              net_estimated,
            "quadrant_estimated":         quadrant_est,
            "action_estimated":           action_est,
            # ── History 13 tuan
            "history":        history[-HISTORY_WEEKS:],
            "fetched_at":     datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        all_results["commodities"][code] = result

        print(f"  [{fund_key}] Net={net_curr:+,.0f} | Change={change:+,.0f} | {quadrant}")
        if net_estimated is not None:
            print(f"       Beta13W={beta:.1f} | Lag={price_lag_change:+.2f}c | "
                  f"Est.Net={net_estimated:+,.0f} | {quadrant_est}")

    return all_results


# ─────────────────────────────────────────────────────────────────────────────
def save_cot_data(data):
    """Luu COT data ra cot_data.json."""
    ensure_output_dir()
    with open(COT_DATA, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  [SAVED] {COT_DATA}")


# ─────────────────────────────────────────────────────────────────────────────
def update_fundamental_cot(cot_data):
    """Cap nhat truong cot_report trong fundamental_data.json (ZC, ZW)."""
    if not FUNDAMENTAL_DATA.exists():
        print("  [WARN] fundamental_data.json khong ton tai, bo qua update.")
        return
    try:
        with open(FUNDAMENTAL_DATA, "r", encoding="utf-8") as f:
            fund = json.load(f)

        commodities = cot_data.get("commodities", {})

        for cftc_code, fund_key in CODE_TO_FUND_KEY.items():
            if fund_key not in fund:
                continue
            cot_entry = commodities.get(cftc_code, {})
            if not cot_entry:
                continue

            report_date   = cot_entry.get("report_date", "")
            net_position  = cot_entry.get("net_position", 0)
            change        = cot_entry.get("change", 0)
            quadrant      = cot_entry.get("quadrant", "")
            action        = cot_entry.get("action", "")
            net_estimated = cot_entry.get("net_estimated")
            quadrant_est  = cot_entry.get("quadrant_estimated", quadrant)
            beta          = cot_entry.get("rolling_beta_13w")
            lag_change    = cot_entry.get("price_lag_change")

            try:
                report_dt  = datetime.datetime.strptime(report_date, "%Y-%m-%d")
                days_ahead = (4 - report_dt.weekday()) % 7
                if days_ahead == 0: days_ahead = 7
                next_friday   = report_dt + datetime.timedelta(days=days_ahead)
                next_date_str = next_friday.strftime("%d/%m/%Y") + " (Hang tuan, Thu Sau)"
            except Exception:
                next_date_str = "Hang tuan (Thu Sau)"

            direction = "Long" if net_position > 0 else "Short"
            trend     = "tang them" if change > 0 else "giam bot"

            est_note = ""
            if net_estimated is not None:
                est_dir  = "Long" if net_estimated > 0 else "Short"
                est_note = (f" | UOC TINH HIEN TAI ({cot_entry.get('latest_price_date','')}):"
                            f" {net_estimated:+,.0f} HD ({quadrant_est})"
                            f" [Lag={lag_change:+.2f}c, Beta={beta:.1f}]")

            logic_summary = (
                f"[{report_date}] MM nam {direction} rong {abs(net_position):,.0f} HD. "
                f"Tuan nay {trend} {abs(change):,.0f} HD. "
                f"Ma tran: {quadrant}. Khuyen nghi: {action}.{est_note}"
            )

            fund[fund_key]["cot_report"] = {
                "latest":    f"[{report_date}] Net {direction} {abs(net_position):,.0f} HD | {change:+,.0f}",
                "next_date": next_date_str,
                "forecast":  quadrant,
                "action":    action,
                "logic":     logic_summary,
                "raw_data":  {
                    "net_position":   net_position,
                    "change":         change,
                    "long":           cot_entry.get("long_curr", 0),
                    "short":          cot_entry.get("short_curr", 0),
                    "net_estimated":  net_estimated,
                    "quadrant_est":   quadrant_est,
                    "beta_13w":       beta,
                }
            }

        fund["last_updated_cot"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(FUNDAMENTAL_DATA, "w", encoding="utf-8") as f:
            json.dump(fund, f, ensure_ascii=False, indent=2)
        print("  [SAVED] Da cap nhat cot_report trong fundamental_data.json (ZC, ZW)")
    except Exception as e:
        print(f"  [ERROR] Cap nhat fundamental_data.json (COT) that bai: {e}")


# ─────────────────────────────────────────────────────────────────────────────
def run_cot():
    print("=======================================================")
    print("  FETCH COT DATA - MANAGED MONEY + ROLLING BETA 13W")
    print("=======================================================")
    data = fetch_all_cot()
    save_cot_data(data)
    update_fundamental_cot(data)
    update_status("cot", "[OK] Success")

    print("\n--- COT Summary ---")
    for code, info in data.get("commodities", {}).items():
        if "error" not in info:
            fund_key = CODE_TO_FUND_KEY.get(code, code)
            print(f"  {fund_key}: Net={info['net_position']:+,} | {info['quadrant']}")
            if info.get('net_estimated') is not None:
                print(f"       Est.Net={info['net_estimated']:+,} | {info['quadrant_estimated']}")
            hist_len = len(info.get('history', []))
            beta = info.get('rolling_beta_13w')
            print(f"       History={hist_len} tuan | Beta13W={beta}")
    print("Done.")


if __name__ == "__main__":
    run_cot()
