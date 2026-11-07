"""
backtest_engine.py — Mô phỏng Live Signal & Kiểm thử hiệu suất 90 ngày (Backtest Engine)
========================================================================================
Mô phỏng khớp lệnh thực tế chuẩn CQG cho 2 sản phẩm:
  - ZWAZ26 (Lúa Mì CBOT kỳ hạn Dec 2026) — Hệ số nhân 50 ($50/cent)
  - ZCEZ26 (Ngô CBOT kỳ hạn Dec 2026)    — Hệ số nhân 50 ($50/cent)

So sánh 3 phương pháp giao dịch:
  - Phương pháp 1: ICT MSS + Pullback EMA 21-50 (Thuận xu hướng SMC)
  - Phương pháp 2: FVG + Bắt Đáy / Đỉnh SMC Zone (Đảo chiều vùng cực trị 5 sao)
  - Phương pháp 3: Chiến Lược Hybrid Kết Hợp (M1 Trend + M2 Exhaustion Absorption)
"""

import sys
import os
import json
import datetime

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
from pathlib import Path
import pandas as pd
import numpy as np

# Thêm đường dẫn gốc và Data
BASE_DIR = Path(__file__).parent
DATA_OUTPUT = BASE_DIR / "Data" / "output"
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "Data"))

import technical_analysis
import ict_engine
import tv_webhook_client

BACKTEST_RESULT_FILE = DATA_OUTPUT / "live_signals_backtest.json"
CACHE_ALL_ZC = DATA_OUTPUT / "ZC_all_H1.csv"
CACHE_ALL_ZW = DATA_OUTPUT / "ZW_all_H1.csv"
CACHE_90D_ZC = DATA_OUTPUT / "ZC_90d_H1.csv"
CACHE_90D_ZW = DATA_OUTPUT / "ZW_90d_H1.csv"

CQG_MAP = {
    "ZW": "ZWAZ26",
    "ZC": "ZCEZ26"
}
MULTIPLIER = 50.0  # 1 cent = $50 / lot


def get_product_symbol(commodity: str, trade_time: str) -> str:
    """
    Quy tắc sản phẩm:
    - Trước tháng 11/2026 (Backtest lịch sử): Dùng HĐ liên tục ZC1! và ZW1! cho chuẩn TradingView.
    - Từ tháng 11/2026 trở đi (Hiện tại / Realtime): Dùng HĐ cụ thể ZCEZ26 và ZWAZ26 từ TradingView Webhook.
    """
    if str(trade_time)[:10] >= "2026-11-01":
        return CQG_MAP.get(commodity, commodity)
    return f"{commodity}1!"


def fetch_or_load_candles(commodity_code: str, force_download: bool = False) -> list:
    """
    Tải và ghép nối dữ liệu nến H1:
      - Lịch sử đến hết tháng 10/2026: Lấy chuỗi nến liên tục ZC1! (ZC=F) hoặc ZW1! (ZW=F) chuẩn TradingView.
      - Hiện tại từ tháng 11/2026: Lấy nến Hợp đồng tháng 12/2026 (ZCEZ26 / ZWAZ26) và nến M5 Realtime từ TradingView.
    """
    cache_file = CACHE_ALL_ZC if commodity_code == "ZC" else CACHE_ALL_ZW
    df = None
    
    if not force_download and cache_file.exists():
        try:
            mtime = datetime.datetime.fromtimestamp(cache_file.stat().st_mtime)
            if (datetime.datetime.now() - mtime).total_seconds() < 14400:
                df = pd.read_csv(cache_file)
        except Exception:
            df = None

    if df is None or df.empty or force_download:
        try:
            import yfinance as yf
            
            # 1. Lịch sử đến hết tháng 10/2026 (ZC1! / ZW1!)
            hist_ticker = f"{commodity_code}=F"
            print(f"  [Backtest] Đang tải lịch sử H1 (đến hết T10/2026) cho {commodity_code}1! ({hist_ticker}) từ Yahoo...")
            tk_hist = yf.Ticker(hist_ticker)
            try:
                raw_hist = tk_hist.history(period="700d", interval="1h")
            except Exception:
                raw_hist = None
            if raw_hist is None or raw_hist.empty:
                raw_hist = tk_hist.history(period="1y", interval="1h")
                
            if not raw_hist.empty:
                df_h = raw_hist.reset_index()
                if "Datetime" in df_h.columns:
                    df_h["Time"] = df_h["Datetime"].dt.tz_convert("Asia/Ho_Chi_Minh").dt.strftime("%Y-%m-%d %H:%M")
                elif "Date" in df_h.columns:
                    df_h["Time"] = df_h["Date"].dt.strftime("%Y-%m-%d %H:%M")
                df_h = df_h[["Time", "Open", "High", "Low", "Close", "Volume"]]
                # Giới hạn lịch sử đến hết tháng 10/2026
                df_h = df_h[df_h["Time"] < "2026-11-01 00:00"]
            else:
                df_h = pd.DataFrame()
                
            # 2. Hiện tại từ tháng 11/2026 (ZCEZ26 / ZWAZ26)
            curr_ticker = f"{commodity_code}Z26.CBT"
            print(f"  [Backtest] Đang tải nến H1 từ T11/2026 cho {CQG_MAP.get(commodity_code, commodity_code)} ({curr_ticker})...")
            tk_curr = yf.Ticker(curr_ticker)
            try:
                raw_curr = tk_curr.history(period="30d", interval="1h")
            except Exception:
                raw_curr = None
                
            if raw_curr is not None and not raw_curr.empty:
                df_c = raw_curr.reset_index()
                if "Datetime" in df_c.columns:
                    df_c["Time"] = df_c["Datetime"].dt.tz_convert("Asia/Ho_Chi_Minh").dt.strftime("%Y-%m-%d %H:%M")
                elif "Date" in df_c.columns:
                    df_c["Time"] = df_c["Date"].dt.strftime("%Y-%m-%d %H:%M")
                df_c = df_c[["Time", "Open", "High", "Low", "Close", "Volume"]]
                # Chỉ lấy nến từ tháng 11/2026 trở đi
                df_c = df_c[df_c["Time"] >= "2026-11-01 00:00"]
            else:
                df_c = pd.DataFrame()

            # 3. Ghép nối 2 chuỗi nến
            if not df_h.empty and not df_c.empty:
                df = pd.concat([df_h, df_c], ignore_index=True)
            elif not df_h.empty:
                df = df_h
            else:
                df = df_c
                
            if not df.empty:
                df = df.drop_duplicates(subset=["Time"]).sort_values("Time").reset_index(drop=True)
                
                # Tính các chỉ báo kỹ thuật
                df["EMA_21"] = df["Close"].ewm(span=21, adjust=False).mean()
                df["EMA_50"] = df["Close"].ewm(span=50, adjust=False).mean()
                df["Volatility"] = df["High"] - df["Low"]
                df["RSI"] = technical_analysis.calculate_rsi(df["Close"], period=14).fillna(50.0)
                df["ATR"] = technical_analysis.calculate_atr(df, period=14).fillna(df["Volatility"].mean())
                df["S1"] = df["Low"].rolling(20).min()
                df["S2"] = df["S1"] - 5.0
                df["R1"] = df["High"].rolling(20).max()
                df["R2"] = df["R1"] + 5.0
                
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(cache_file, index=False)
                print(f"  [Backtest] Đã lưu {len(df)} nến ghép ({commodity_code}1! đến T10/2026 + Z26 từ T11/2026) vào {cache_file.name}")
        except Exception as e:
            print(f"  [Backtest Lỗi] Không tải được dữ liệu mới: {e}")
            if cache_file.exists():
                df = pd.read_csv(cache_file)
            else:
                old_cache = CACHE_90D_ZC if commodity_code == "ZC" else CACHE_90D_ZW
                if old_cache.exists():
                    df = pd.read_csv(old_cache)
                else:
                    fallback_file = DATA_OUTPUT / f"{commodity_code}_active_H1.csv"
                    if fallback_file.exists():
                        df = pd.read_csv(fallback_file)

    if df is None or df.empty:
        return []

    df_ict = df.rename(columns={
        "Time": "time", "Open": "open", "High": "high", "Low": "low", "Close": "close",
        "EMA_21": "ema21", "EMA_50": "ema50", "RSI": "rsi", "ATR": "atr",
        "S1": "s1", "S2": "s2", "R1": "r1", "R2": "r2"
    })
    candles = df_ict.to_dict("records")
    
    # 4. Ghép nến M5 Realtime từ TradingView Webhook (nếu có)
    try:
        candles = tv_webhook_client.merge_realtime_m5_into_candles(candles, commodity_code)
    except Exception:
        pass
        
    return candles
    return candles


# Alias tương thích ngược
fetch_or_load_90d = fetch_or_load_candles


def apply_m5_live_status_to_trades(trades: list, commodity: str) -> list:
    """
    TẦNG 2 (M5 Realtime Order Tracker):
    Chỉ dùng giá nến M5 Realtime để cập nhật trạng thái khớp lệnh, PnL đang chạy và chạm TP/SL
    cho các vị thế mới nhất, tuyệt đối không làm thay đổi cấu trúc hay điểm Entry/SL/TP của Tầng 1.
    """
    if not trades:
        return trades
    m5_info = tv_webhook_client.get_latest_m5_price(commodity)
    if not m5_info:
        return trades

    m5_close = float(m5_info.get("close", 0))
    m5_high = float(m5_info.get("high", m5_close))
    m5_low = float(m5_info.get("low", m5_close))
    m5_time = m5_info.get("time_vn", "")
    if m5_close <= 0:
        return trades

    for t in trades:
        if t.get("commodity") != commodity:
            continue
        res = t.get("result")
        side = t.get("side")
        entry = float(t.get("entry_price", 0))
        sl = float(t.get("sl_price", 0))
        tp1 = float(t.get("tp1_price", 0))
        tp2 = float(t.get("tp2_price", 0))
        tp3 = float(t.get("tp3_price", 0))

        if res == "ĐANG MỞ":
            hit_tp1 = bool(t.get("hit_tp1_time"))
            cur_sl = entry if hit_tp1 else sl
            if side == "MUA":
                if m5_low <= cur_sl:
                    if hit_tp1:
                        t["result"] = "ENTRY"; t["exit_price"] = entry; t["pnl"] = 0.0; t["diff_points"] = 0.0
                        t["exit_time"] = m5_time[:16]
                        t["exit_desc"] = f"[Tầng 2 - M5 Live] Giá đã đạt TP1 ({tp1}) và dời SL về hòa vốn {entry}. Nến M5 vừa chạm SL hòa vốn ($0)."
                    else:
                        t["result"] = "SL"; t["exit_price"] = sl; t["pnl"] = round((sl - entry) * MULTIPLIER, 2)
                        t["diff_points"] = round(-(entry - sl), 2); t["exit_time"] = m5_time[:16]
                        t["exit_desc"] = f"[Tầng 2 - M5 Live] Giá M5 chạm mức cắt lỗ SL ({sl}) lúc {m5_time}."
                elif m5_high >= tp3:
                    t["result"] = "TP3"; t["exit_price"] = tp3; t["pnl"] = round((tp3 - entry) * MULTIPLIER, 2)
                    t["diff_points"] = round(tp3 - entry, 2); t["win"] = True; t["exit_time"] = m5_time[:16]
                    t["exit_desc"] = f"[Tầng 2 - M5 Live] Giá M5 bứt phá chạm chốt lời tối đa TP3 ({tp3}) lúc {m5_time}."
                else:
                    if m5_high >= tp1 and not hit_tp1:
                        t["hit_tp1_time"] = m5_time[:16]
                        hit_tp1 = True
                    t["exit_price"] = round(m5_close, 2)
                    cur_diff = round(m5_close - entry, 2)
                    t["diff_points"] = cur_diff
                    t["pnl"] = round(cur_diff * MULTIPLIER, 2)
                    t["exit_desc"] = (
                        f"[Tầng 2 - M5 Live ({m5_time})] Vị thế đang mở. Giá M5 hiện tại: {m5_close:.2f}. "
                        f"{'Đã đạt TP1 & dời SL về hòa vốn ' + str(entry) if hit_tp1 else 'SL cố định tại ' + str(sl)}."
                    )
            else:  # BÁN
                if m5_high >= cur_sl:
                    if hit_tp1:
                        t["result"] = "ENTRY"; t["exit_price"] = entry; t["pnl"] = 0.0; t["diff_points"] = 0.0
                        t["exit_time"] = m5_time[:16]
                        t["exit_desc"] = f"[Tầng 2 - M5 Live] Giá đã đạt TP1 ({tp1}) và dời SL về hòa vốn {entry}. Nến M5 vừa chạm SL hòa vốn ($0)."
                    else:
                        t["result"] = "SL"; t["exit_price"] = sl; t["pnl"] = round((entry - sl) * MULTIPLIER, 2)
                        t["diff_points"] = round(-(sl - entry), 2); t["exit_time"] = m5_time[:16]
                        t["exit_desc"] = f"[Tầng 2 - M5 Live] Giá M5 chạm mức cắt lỗ SL ({sl}) lúc {m5_time}."
                elif m5_low <= tp3:
                    t["result"] = "TP3"; t["exit_price"] = tp3; t["pnl"] = round((entry - tp3) * MULTIPLIER, 2)
                    t["diff_points"] = round(entry - tp3, 2); t["win"] = True; t["exit_time"] = m5_time[:16]
                    t["exit_desc"] = f"[Tầng 2 - M5 Live] Giá M5 giảm mạnh chạm chốt lời tối đa TP3 ({tp3}) lúc {m5_time}."
                else:
                    if m5_low <= tp1 and not hit_tp1:
                        t["hit_tp1_time"] = m5_time[:16]
                        hit_tp1 = True
                    t["exit_price"] = round(m5_close, 2)
                    cur_diff = round(entry - m5_close, 2)
                    t["diff_points"] = cur_diff
                    t["pnl"] = round(cur_diff * MULTIPLIER, 2)
                    t["exit_desc"] = (
                        f"[Tầng 2 - M5 Live ({m5_time})] Vị thế đang mở. Giá M5 hiện tại: {m5_close:.2f}. "
                        f"{'Đã đạt TP1 & dời SL về hòa vốn ' + str(entry) if hit_tp1 else 'SL cố định tại ' + str(sl)}."
                    )
    return trades


def simulate_method_1(candles: list, commodity: str) -> list:
    """
    Phương pháp 1: ICT MSS + Pullback EMA 21-50 (Trend-Following)
    """
    cqg_sym = CQG_MAP.get(commodity, commodity)
    trades = []
    pos_end_idx = 0
    min_opposing_dist = 7.0 if commodity == "ZW" else 4.0
    
    for i in range(50, len(candles) - 5):
        if i < pos_end_idx:
            continue
            
        c_i = candles[i]
        atr_i = c_i.get("atr", 3.0)
        
        # Chop / Range Filter: Không giao dịch khi biên độ 14 nến hẹp < 1.3 * ATR
        recent_14 = candles[max(0, i-13):i+1]
        hi_14 = max(c["high"] for c in recent_14)
        lo_14 = min(c["low"] for c in recent_14)
        if (hi_14 - lo_14) < 1.3 * atr_i:
            continue
            
        window = candles[max(0, i - 350):i + 1]
        ana = ict_engine.analyze(window)
        setup = ana.get("setup")
        
        if setup and setup.get("winRate", 0) >= 70:
            side = "MUA" if setup["type"] == "LONG" else "BÁN"
            entry = round(candles[i]["ema21"], 2)
            sl = round(setup["stopLoss"], 2)
            risk = abs(entry - sl)
            
            if risk < 2.5 or risk > 16.0:
                continue

            # Anti-Whipsaw Filter: Bỏ qua lệnh ngược chiều nếu khoảng cách < min_opposing_dist
            dyn_min_dist = max(min_opposing_dist, 2.0 * atr_i)
            skip_trade = False
            if trades:
                for prev_t in reversed(trades[-3:]):
                    if prev_t["side"] != side and abs(entry - prev_t["entry_price"]) < dyn_min_dist:
                        skip_trade = True
                        break
            if skip_trade:
                continue
                
            tp1 = round(entry + (1.0 * risk if side == "MUA" else -1.0 * risk), 2)
            tp2 = round(entry + (1.5 * risk if side == "MUA" else -1.5 * risk), 2)
            tp3 = round(entry + (2.0 * risk if side == "MUA" else -2.0 * risk), 2)
            
            filled = False
            fill_idx = 0
            for j in range(i+1, min(i+25, len(candles))):
                if side == "MUA" and candles[j]["low"] <= entry:
                    filled = True; fill_idx = j; break
                elif side == "BÁN" and candles[j]["high"] >= entry:
                    filled = True; fill_idx = j; break
                    
            if not filled:
                trades.append({
                    "date": candles[i]["time"][:10],
                    "time": candles[i]["time"],
                    "signal_time": candles[i]["time"],
                    "fill_time": None,
                    "exit_time": candles[min(i+24, len(candles)-1)]["time"],
                    "side": side,
                    "product": get_product_symbol(commodity, candles[i]["time"]),
                    "commodity": commodity,
                    "method": "M1 (ICT MSS + EMA Pullback)",
                    "result": "CHƯA KHỚP",
                    "entry_price": entry,
                    "exit_price": None,
                    "sl_price": sl,
                    "tp1_price": tp1,
                    "tp2_price": tp2,
                    "tp3_price": tp3,
                    "risk_points": round(risk, 2),
                    "bars_held": 0,
                    "multiplier": MULTIPLIER,
                    "diff_points": 0.0,
                    "pnl": 0.0,
                    "win": False,
                    "tag": "M1 Trend",
                    "reason": setup.get("reason", ""),
                    "exit_desc": "Hết hạn chờ 24 nến (24 giờ) giá không hồi về khớp lệnh Limit tại EMA21. Hệ thống tự động hủy lệnh để bảo toàn vốn."
                })
                pos_end_idx = i + 12
                continue
                
            res = "ENTRY"
            exit_p = entry
            pnl = 0.0
            hit_tp1 = False
            hit_tp2 = False
            hit_tp1_time = None
            end_bar = min(fill_idx + 48, len(candles))
            exit_time = candles[end_bar - 1]["time"]
            exit_idx = end_bar - 1
            exit_desc = ""
            
            for k in range(fill_idx, end_bar):
                ck = candles[k]
                cur_sl = entry if hit_tp1 else sl
                
                if side == "MUA":
                    if ck["low"] <= cur_sl:
                        if hit_tp1:
                            res = "ENTRY"; exit_p = entry; pnl = 0.0
                            exit_desc = f"Giá đã đạt TP1 ({tp1}) và dời SL về hòa vốn {entry}. Sau đó giá quay đầu cắn SL hòa vốn (Bảo toàn vốn $0)."
                        else:
                            res = "SL"; exit_p = sl; pnl = round((sl - entry) * MULTIPLIER, 2)
                            exit_desc = f"Giá chạm mức cắt lỗ ban đầu SL ({sl}) — Lỗ {abs(sl - entry):.2f} pts."
                        pos_end_idx = k + 6
                        exit_time = ck["time"]
                        exit_idx = k
                        break
                    if ck["high"] >= tp3:
                        res = "TP3"; exit_p = tp3; pnl = round((tp3 - entry) * MULTIPLIER, 2)
                        exit_desc = f"Giá bứt phá mạnh chạm chốt lời mục tiêu tối đa TP3 ({tp3}) tỷ lệ 2.0R."
                        pos_end_idx = k + 6
                        exit_time = ck["time"]
                        exit_idx = k
                        break
                    elif ck["high"] >= tp2:
                        hit_tp2 = True; hit_tp1 = True
                    elif ck["high"] >= tp1:
                        if not hit_tp1: hit_tp1_time = ck["time"]
                        hit_tp1 = True
                else: # BÁN
                    if ck["high"] >= cur_sl:
                        if hit_tp1:
                            res = "ENTRY"; exit_p = entry; pnl = 0.0
                            exit_desc = f"Giá đã đạt TP1 ({tp1}) và dời SL về hòa vốn {entry}. Sau đó giá quay đầu cắn SL hòa vốn (Bảo toàn vốn $0)."
                        else:
                            res = "SL"; exit_p = sl; pnl = round((entry - sl) * MULTIPLIER, 2)
                            exit_desc = f"Giá chạm mức cắt lỗ ban đầu SL ({sl}) — Lỗ {abs(entry - sl):.2f} pts."
                        pos_end_idx = k + 6
                        exit_time = ck["time"]
                        exit_idx = k
                        break
                    if ck["low"] <= tp3:
                        res = "TP3"; exit_p = tp3; pnl = round((entry - tp3) * MULTIPLIER, 2)
                        exit_desc = f"Giá giảm mạnh chạm chốt lời mục tiêu tối đa TP3 ({tp3}) tỷ lệ 2.0R."
                        pos_end_idx = k + 6
                        exit_time = ck["time"]
                        exit_idx = k
                        break
                    elif ck["low"] <= tp2:
                        hit_tp2 = True; hit_tp1 = True
                    elif ck["low"] <= tp1:
                        if not hit_tp1: hit_tp1_time = ck["time"]
                        hit_tp1 = True
            else:
                exit_time = candles[end_bar - 1]["time"]
                exit_idx = end_bar - 1
                is_currently_open = (end_bar == len(candles) and (end_bar - 1 - fill_idx < 48))
                if is_currently_open:
                    res = "ĐANG MỞ"
                    exit_p = candles[-1]["close"]
                    cur_diff = (exit_p - entry) if side == "MUA" else (entry - exit_p)
                    pnl = round(cur_diff * MULTIPLIER, 2)
                    exit_time = "Đang chạy..."
                    exit_desc = f"Vị thế đang hoạt động ở nến mới nhất ({candles[-1]['time']}). Giá hiện tại: {exit_p}. {'Đã dời SL về hòa vốn ' + str(entry) if hit_tp1 else 'SL đang đặt tại ' + str(sl)}."
                elif hit_tp2:
                    res = "TP2"; exit_p = tp2; pnl = round(abs(tp2 - entry) * MULTIPLIER, 2)
                    exit_desc = f"Đạt TP2 ({tp2}) tỷ lệ 1.5R và tự động chốt lời khi hết thời gian giữ lệnh 48 nến."
                elif hit_tp1:
                    res = "TP1"; exit_p = tp1; pnl = round(abs(tp1 - entry) * MULTIPLIER, 2)
                    exit_desc = f"Đạt TP1 ({tp1}) tỷ lệ 1.0R và tự động chốt lời khi hết thời gian giữ lệnh 48 nến."
                else:
                    res = "ENTRY"; exit_p = entry; pnl = 0.0
                    exit_desc = "Hết thời gian giữ lệnh 48 nến quanh vùng hòa vốn."
                pos_end_idx = end_bar
                
            diff_pts = round(abs(exit_p - entry) if res != "SL" else -abs(exit_p - entry), 2)
            trades.append({
                "date": candles[fill_idx]["time"][:10],
                "time": candles[fill_idx]["time"],
                "signal_time": candles[i]["time"],
                "fill_time": candles[fill_idx]["time"],
                "exit_time": exit_time,
                "hit_tp1_time": hit_tp1_time,
                "side": side,
                "product": get_product_symbol(commodity, candles[fill_idx]["time"]),
                "commodity": commodity,
                "method": "M1 (ICT MSS + EMA Pullback)",
                "result": res,
                "entry_price": entry,
                "exit_price": exit_p,
                "sl_price": sl,
                "tp1_price": tp1,
                "tp2_price": tp2,
                "tp3_price": tp3,
                "risk_points": round(risk, 2),
                "bars_held": exit_idx - fill_idx,
                "multiplier": MULTIPLIER,
                "diff_points": diff_pts,
                "pnl": pnl,
                "win": res in ["TP1", "TP2", "TP3"],
                "tag": "M1 Trend",
                "reason": setup.get("reason", ""),
                "exit_desc": exit_desc
            })
            
    return trades


def simulate_method_2(candles: list, commodity: str) -> list:
    """
    Phương pháp 2: FVG + Bắt Đáy / Đỉnh SMC Zone (Contrarian Reversal)
    """
    cqg_sym = CQG_MAP.get(commodity, commodity)
    trades = []
    min_opposing_dist = 7.0 if commodity == "ZW" else 4.0
    
    ana = ict_engine.analyze(candles)
    bzs = [b for b in ana.get("bottom_zones", []) if b["score"] >= 5]
    tzs = [t for t in ana.get("top_zones", []) if t["score"] >= 5]
    
    events = []
    for b in bzs: events.append(("MUA", b["index"], b["price"], b["score"], b.get("factors", [])))
    for t in tzs: events.append(("BÁN", t["index"], t["price"], t["score"], t.get("factors", [])))
    events.sort(key=lambda x: x[1])
    
    pos_end_idx = 0
    for side, idx, swing_price, score, factors in events:
        if idx < pos_end_idx or idx + 4 >= len(candles):
            continue
            
        entry_c = candles[idx + 3] # nến xác nhận swing
        entry = round(entry_c["close"], 2)
        atr = entry_c.get("atr", 3.0)
        
        # 1. Swing Preservation Check: Đảm bảo nến xác nhận không làm thủng đáy / vỡ đỉnh
        if side == "MUA":
            if entry < swing_price or entry_c["low"] < swing_price - 0.4 * atr:
                continue
            sl = round(swing_price - 0.75 * atr, 2)
            risk = entry - sl
            if risk < 2.0 or risk > 22.0: continue
            tp1 = round(entry + 1.0 * risk, 2)
            tp2 = round(entry + 1.5 * risk, 2)
            tp3 = round(entry + 2.0 * risk, 2)
        else: # BÁN
            if entry > swing_price or entry_c["high"] > swing_price + 0.4 * atr:
                continue
            sl = round(swing_price + 0.75 * atr, 2)
            risk = sl - entry
            if risk < 2.0 or risk > 22.0: continue
            tp1 = round(entry - 1.0 * risk, 2)
            tp2 = round(entry - 1.5 * risk, 2)
            tp3 = round(entry - 2.0 * risk, 2)
            
        # 2. Anti-Whipsaw Filter: Bỏ qua nếu cách lệnh ngược chiều gần nhất < min_opposing_dist
        dyn_min_dist = max(min_opposing_dist, 2.0 * atr)
        skip_trade = False
        if trades:
            for prev_t in reversed(trades[-3:]):
                if prev_t["side"] != side and abs(entry - prev_t["entry_price"]) < dyn_min_dist:
                    skip_trade = True
                    break
        if skip_trade:
            continue
            
        res = "ENTRY"
        exit_p = entry
        pnl = 0.0
        hit_tp1 = False
        hit_tp2 = False
        hit_tp1_time = None
        end_bar = min(idx + 4 + 48, len(candles))
        exit_time = candles[end_bar - 1]["time"]
        exit_idx = end_bar - 1
        exit_desc = ""
        
        for k in range(idx + 4, end_bar):
            ck = candles[k]
            cur_sl = entry if hit_tp1 else sl
            
            if side == "MUA":
                if ck["low"] <= cur_sl:
                    if hit_tp1:
                        res = "ENTRY"; exit_p = entry; pnl = 0.0
                        exit_desc = f"Giá đã đạt TP1 ({tp1}) và dời SL về hòa vốn {entry}. Sau đó giá hồi cắn SL hòa vốn (Bảo toàn vốn $0)."
                    else:
                        res = "SL"; exit_p = sl; pnl = round((sl - entry) * MULTIPLIER, 2)
                        exit_desc = f"Giá chạm mức cắt lỗ ban đầu SL ({sl}) — Lỗ {abs(sl - entry):.2f} pts."
                    pos_end_idx = k + 6
                    exit_time = ck["time"]
                    exit_idx = k
                    break
                if ck["high"] >= tp3:
                    res = "TP3"; exit_p = tp3; pnl = round((tp3 - entry) * MULTIPLIER, 2)
                    exit_desc = f"Giá đảo chiều tăng mạnh chạm chốt lời mục tiêu tối đa TP3 ({tp3}) tỷ lệ 2.0R."
                    pos_end_idx = k + 6
                    exit_time = ck["time"]
                    exit_idx = k
                    break
                elif ck["high"] >= tp2:
                    hit_tp2 = True; hit_tp1 = True
                elif ck["high"] >= tp1:
                    if not hit_tp1: hit_tp1_time = ck["time"]
                    hit_tp1 = True
            else: # BÁN
                if ck["high"] >= cur_sl:
                    if hit_tp1:
                        res = "ENTRY"; exit_p = entry; pnl = 0.0
                        exit_desc = f"Giá đã đạt TP1 ({tp1}) và dời SL về hòa vốn {entry}. Sau đó giá hồi cắn SL hòa vốn (Bảo toàn vốn $0)."
                    else:
                        res = "SL"; exit_p = sl; pnl = round((entry - sl) * MULTIPLIER, 2)
                        exit_desc = f"Giá chạm mức cắt lỗ ban đầu SL ({sl}) — Lỗ {abs(entry - sl):.2f} pts."
                    pos_end_idx = k + 6
                    exit_time = ck["time"]
                    exit_idx = k
                    break
                if ck["low"] <= tp3:
                    res = "TP3"; exit_p = tp3; pnl = round((entry - tp3) * MULTIPLIER, 2)
                    exit_desc = f"Giá đảo chiều giảm mạnh chạm chốt lời mục tiêu tối đa TP3 ({tp3}) tỷ lệ 2.0R."
                    pos_end_idx = k + 6
                    exit_time = ck["time"]
                    exit_idx = k
                    break
                elif ck["low"] <= tp2:
                    hit_tp2 = True; hit_tp1 = True
                elif ck["low"] <= tp1:
                    if not hit_tp1: hit_tp1_time = ck["time"]
                    hit_tp1 = True
        else:
            exit_time = candles[end_bar - 1]["time"]
            exit_idx = end_bar - 1
            is_currently_open = (end_bar == len(candles) and (end_bar - 1 - (idx + 3) < 48))
            if is_currently_open:
                res = "ĐANG MỞ"
                exit_p = candles[-1]["close"]
                cur_diff = (exit_p - entry) if side == "MUA" else (entry - exit_p)
                pnl = round(cur_diff * MULTIPLIER, 2)
                exit_time = "Đang chạy..."
                exit_desc = f"Vị thế đang hoạt động ở nến mới nhất ({candles[-1]['time']}). Giá hiện tại: {exit_p}. {'Đã dời SL về hòa vốn ' + str(entry) if hit_tp1 else 'SL đang đặt tại ' + str(sl)}."
            elif hit_tp2:
                res = "TP2"; exit_p = tp2; pnl = round(abs(tp2 - entry) * MULTIPLIER, 2)
                exit_desc = f"Đạt TP2 ({tp2}) tỷ lệ 1.5R và tự động chốt lời khi hết thời gian giữ lệnh 48 nến."
            elif hit_tp1:
                res = "TP1"; exit_p = tp1; pnl = round(abs(tp1 - entry) * MULTIPLIER, 2)
                exit_desc = f"Đạt TP1 ({tp1}) tỷ lệ 1.0R và tự động chốt lời khi hết thời gian giữ lệnh 48 nến."
            else:
                res = "ENTRY"; exit_p = entry; pnl = 0.0
                exit_desc = "Hết thời gian giữ lệnh 48 nến quanh vùng hòa vốn."
            pos_end_idx = end_bar
            
        diff_pts = round(abs(exit_p - entry) if res != "SL" else -abs(exit_p - entry), 2)
        trades.append({
            "date": entry_c["time"][:10],
            "time": entry_c["time"],
            "signal_time": candles[idx]["time"],
            "fill_time": entry_c["time"],
            "exit_time": exit_time,
            "hit_tp1_time": hit_tp1_time,
            "side": side,
            "product": get_product_symbol(commodity, entry_c["time"]),
            "commodity": commodity,
            "method": "M2 (SMC Zone 5-Sao Reversal)",
            "result": res,
            "entry_price": entry,
            "exit_price": exit_p,
            "sl_price": sl,
            "tp1_price": tp1,
            "tp2_price": tp2,
            "tp3_price": tp3,
            "risk_points": round(risk, 2),
            "bars_held": exit_idx - (idx + 3),
            "multiplier": MULTIPLIER,
            "diff_points": diff_pts,
            "pnl": pnl,
            "win": res in ["TP1", "TP2", "TP3"],
            "tag": "M2 Reversal",
            "reason": f"SMC Zone {score}/8: " + ", ".join(factors[:2]),
            "exit_desc": exit_desc
        })
        
    return trades


def simulate_method_3_hybrid(candles: list, commodity: str) -> list:
    """
    Phương pháp 3: Chiến Lược Hybrid (M1 Trend-Following + M2 Exhaustion Absorption)
    Quy tắc phối hợp:
      1. Bắt Đáy / Bắt Đỉnh (M2) CHỈ kích hoạt khi có sự xác nhận cạn kiệt sóng:
         - Bắt Đáy: Bottom Zone score >= 5, có tín hiệu quét thanh khoản (SSL Sweep) hoặc RSI quá bán < 35.
         - Bắt Đỉnh: Top Zone score >= 5, có tín hiệu quét thanh khoản (BSL Sweep) hoặc RSI quá mua > 65.
      2. Khi không có vùng cực trị: Hệ thống đi lệnh theo sóng chính của M1 (EMA Pullback) khi cấu trúc MSS xác nhận.
      3. Quản trị xung đột: Không mở lệnh đảo chiều ngược hướng khi đang có vị thế M1 đang chạy.
    """
    cqg_sym = CQG_MAP.get(commodity, commodity)
    trades = []
    pos_end_idx = 0
    min_opposing_dist = 7.0 if commodity == "ZW" else 4.0
    
    ana_full = ict_engine.analyze(candles)
    bzs = {b['index']: b for b in ana_full.get('bottom_zones', []) if b['score'] >= 5}
    tzs = {t['index']: t for t in ana_full.get('top_zones', []) if t['score'] >= 5}
    
    for i in range(50, len(candles) - 5):
        if i < pos_end_idx:
            continue
        c = candles[i]
        atr = c.get('atr', 3.0)
        dyn_min_dist = max(min_opposing_dist, 2.0 * atr)
        
        # 1. Kiểm tra ưu tiên: Vùng đảo chiều cực trị (M2 Exhaustion)
        bz = bzs.get(i - 3)
        tz = tzs.get(i - 3)
        triggered_reversal = False
        
        if bz:
            has_sweep = any('sweep' in f.lower() for f in bz.get('factors', []))
            is_oversold = (c.get('rsi', 50) < 35) or any('oversold' in f.lower() for f in bz.get('factors', []))
            bottom_held = (c['close'] >= bz['price']) and (c['low'] >= bz['price'] - 0.4 * atr)
            if (has_sweep or is_oversold) and bottom_held:
                entry = round(c['close'], 2)
                sl = round(bz['price'] - 0.75 * atr, 2)
                risk = entry - sl
                if 2.0 <= risk <= 20.0:
                    skip = False
                    if trades:
                        for prev_t in reversed(trades[-3:]):
                            if prev_t['side'] != 'MUA' and abs(entry - prev_t['entry_price']) < dyn_min_dist:
                                skip = True; break
                    if not skip:
                        tp1 = round(entry + 1.0 * risk, 2)
                        tp2 = round(entry + 1.5 * risk, 2)
                        tp3 = round(entry + 2.0 * risk, 2)
                        
                        res = 'ENTRY'; exit_p = entry; pnl = 0.0; hit_tp1 = False; hit_tp2 = False; hit_tp1_time = None
                        end_bar = min(i + 48, len(candles))
                        exit_time = candles[end_bar - 1]["time"]
                        exit_idx = end_bar - 1
                        exit_desc = ""

                        for k in range(i+1, end_bar):
                            ck = candles[k]
                            cur_sl = entry if hit_tp1 else sl
                            if ck['low'] <= cur_sl:
                                if hit_tp1:
                                    res = 'ENTRY'; exit_p = entry; pnl = 0.0
                                    exit_desc = f"Giá đã đạt TP1 ({tp1}) và dời SL về hòa vốn {entry}. Sau đó giá hồi cắn SL hòa vốn (Bảo toàn vốn $0)."
                                else:
                                    res = 'SL'; exit_p = sl; pnl = round((sl - entry) * MULTIPLIER, 2)
                                    exit_desc = f"Giá chạm mức cắt lỗ ban đầu SL ({sl}) — Lỗ {abs(sl - entry):.2f} pts."
                                pos_end_idx = k + 6
                                exit_time = ck["time"]
                                exit_idx = k
                                break
                            if ck['high'] >= tp3:
                                res = 'TP3'; exit_p = tp3; pnl = round((tp3 - entry) * MULTIPLIER, 2)
                                exit_desc = f"Giá bắt đáy bật tăng mạnh chạm chốt lời mục tiêu tối đa TP3 ({tp3}) tỷ lệ 2.0R."
                                pos_end_idx = k + 6
                                exit_time = ck["time"]
                                exit_idx = k
                                break
                            elif ck['high'] >= tp2: hit_tp2 = True; hit_tp1 = True
                            elif ck['high'] >= tp1:
                                if not hit_tp1: hit_tp1_time = ck["time"]
                                hit_tp1 = True
                        else:
                            exit_time = candles[end_bar - 1]["time"]
                            exit_idx = end_bar - 1
                            is_currently_open = (end_bar == len(candles) and (end_bar - 1 - i < 48))
                            if is_currently_open:
                                res = "ĐANG MỞ"
                                exit_p = candles[-1]["close"]
                                cur_diff = exit_p - entry
                                pnl = round(cur_diff * MULTIPLIER, 2)
                                exit_time = "Đang chạy..."
                                exit_desc = f"Vị thế bắt đáy SMC đang hoạt động ở nến mới nhất ({candles[-1]['time']}). Giá hiện tại: {exit_p}. {'Đã dời SL về hòa vốn ' + str(entry) if hit_tp1 else 'SL đang đặt tại ' + str(sl)}."
                            elif hit_tp2:
                                res = 'TP2'; exit_p = tp2; pnl = round((tp2 - entry) * MULTIPLIER, 2)
                                exit_desc = f"Đạt TP2 ({tp2}) tỷ lệ 1.5R và tự động chốt lời khi hết thời gian giữ lệnh 48 nến."
                            elif hit_tp1:
                                res = 'TP1'; exit_p = tp1; pnl = round((tp1 - entry) * MULTIPLIER, 2)
                                exit_desc = f"Đạt TP1 ({tp1}) tỷ lệ 1.0R và tự động chốt lời khi hết thời gian giữ lệnh 48 nến."
                            else:
                                res = 'ENTRY'; exit_p = entry; pnl = 0.0
                                exit_desc = "Hết thời gian giữ lệnh 48 nến quanh vùng hòa vốn."
                            pos_end_idx = end_bar
                        diff_pts = round(abs(exit_p - entry) if res != 'SL' else -abs(exit_p - entry), 2)
                        trades.append({
                            'date': c['time'][:10], 'time': c['time'],
                            'signal_time': candles[i-3]['time'] if i >= 3 else c['time'],
                            'fill_time': c['time'],
                            'exit_time': exit_time,
                            'hit_tp1_time': hit_tp1_time,
                            'side': 'MUA', 'product': get_product_symbol(commodity, c['time']),
                            'commodity': commodity, 'method': 'M3 (Hybrid: Bắt Đáy Hấp Thụ)', 'result': res,
                            'entry_price': entry, 'exit_price': exit_p,
                            'sl_price': sl, 'tp1_price': tp1, 'tp2_price': tp2, 'tp3_price': tp3,
                            'risk_points': round(risk, 2), 'bars_held': exit_idx - i,
                            'multiplier': MULTIPLIER, 'diff_points': diff_pts,
                            'pnl': pnl, 'win': res in ['TP1', 'TP2', 'TP3'], 'tag': 'M3 Bắt Đáy',
                            'reason': f"Hấp thụ đáy Climax: " + ", ".join(bz.get('factors', [])[:2]),
                            'exit_desc': exit_desc
                        })
                        triggered_reversal = True
                        
        elif tz and not triggered_reversal:
            has_sweep = any('sweep' in f.lower() for f in tz.get('factors', []))
            is_overbought = (c.get('rsi', 50) > 65) or any('overbought' in f.lower() for f in tz.get('factors', []))
            top_held = (c['close'] <= tz['price']) and (c['high'] <= tz['price'] + 0.4 * atr)
            if (has_sweep or is_overbought) and top_held:
                entry = round(c['close'], 2)
                sl = round(tz['price'] + 0.75 * atr, 2)
                risk = sl - entry
                if 2.0 <= risk <= 20.0:
                    skip = False
                    if trades:
                        for prev_t in reversed(trades[-3:]):
                            if prev_t['side'] != 'BÁN' and abs(entry - prev_t['entry_price']) < dyn_min_dist:
                                skip = True; break
                    if not skip:
                        tp1 = round(entry - 1.0 * risk, 2)
                        tp2 = round(entry - 1.5 * risk, 2)
                        tp3 = round(entry - 2.0 * risk, 2)
                        res = 'ENTRY'; exit_p = entry; pnl = 0.0; hit_tp1 = False; hit_tp2 = False; hit_tp1_time = None
                        end_bar = min(i + 48, len(candles))
                        exit_time = candles[end_bar - 1]["time"]
                        exit_idx = end_bar - 1
                        exit_desc = ""

                        for k in range(i+1, end_bar):
                            ck = candles[k]
                            cur_sl = entry if hit_tp1 else sl
                            if ck['high'] >= cur_sl:
                                if hit_tp1:
                                    res = 'ENTRY'; exit_p = entry; pnl = 0.0
                                    exit_desc = f"Giá đã đạt TP1 ({tp1}) và dời SL về hòa vốn {entry}. Sau đó giá hồi cắn SL hòa vốn (Bảo toàn vốn $0)."
                                else:
                                    res = 'SL'; exit_p = sl; pnl = round((entry - sl) * MULTIPLIER, 2)
                                    exit_desc = f"Giá chạm mức cắt lỗ ban đầu SL ({sl}) — Lỗ {abs(entry - sl):.2f} pts."
                                pos_end_idx = k + 6
                                exit_time = ck["time"]
                                exit_idx = k
                                break
                            if ck['low'] <= tp3:
                                res = 'TP3'; exit_p = tp3; pnl = round((entry - tp3) * MULTIPLIER, 2)
                                exit_desc = f"Giá bắt đỉnh đảo chiều giảm mạnh chạm chốt lời mục tiêu tối đa TP3 ({tp3}) tỷ lệ 2.0R."
                                pos_end_idx = k + 6
                                exit_time = ck["time"]
                                exit_idx = k
                                break
                            elif ck['low'] <= tp2: hit_tp2 = True; hit_tp1 = True
                            elif ck['low'] <= tp1:
                                if not hit_tp1: hit_tp1_time = ck["time"]
                                hit_tp1 = True
                        else:
                            exit_time = candles[end_bar - 1]["time"]
                            exit_idx = end_bar - 1
                            is_currently_open = (end_bar == len(candles) and (end_bar - 1 - i < 48))
                            if is_currently_open:
                                res = "ĐANG MỞ"
                                exit_p = candles[-1]["close"]
                                cur_diff = entry - exit_p
                                pnl = round(cur_diff * MULTIPLIER, 2)
                                exit_time = "Đang chạy..."
                                exit_desc = f"Vị thế bắt đỉnh SMC đang hoạt động ở nến mới nhất ({candles[-1]['time']}). Giá hiện tại: {exit_p}. {'Đã dời SL về hòa vốn ' + str(entry) if hit_tp1 else 'SL đang đặt tại ' + str(sl)}."
                            elif hit_tp2:
                                res = 'TP2'; exit_p = tp2; pnl = round((entry - tp2) * MULTIPLIER, 2)
                                exit_desc = f"Đạt TP2 ({tp2}) tỷ lệ 1.5R và tự động chốt lời khi hết thời gian giữ lệnh 48 nến."
                            elif hit_tp1:
                                res = 'TP1'; exit_p = tp1; pnl = round((entry - tp1) * MULTIPLIER, 2)
                                exit_desc = f"Đạt TP1 ({tp1}) tỷ lệ 1.0R và tự động chốt lời khi hết thời gian giữ lệnh 48 nến."
                            else:
                                res = 'ENTRY'; exit_p = entry; pnl = 0.0
                                exit_desc = "Hết thời gian giữ lệnh 48 nến quanh vùng hòa vốn."
                            pos_end_idx = end_bar
                        diff_pts = round(abs(exit_p - entry) if res != 'SL' else -abs(exit_p - entry), 2)
                        trades.append({
                            'date': c['time'][:10], 'time': c['time'],
                            'signal_time': candles[i-3]['time'] if i >= 3 else c['time'],
                            'fill_time': c['time'],
                            'exit_time': exit_time,
                            'hit_tp1_time': hit_tp1_time,
                            'side': 'BÁN', 'product': get_product_symbol(commodity, c['time']),
                            'commodity': commodity, 'method': 'M3 (Hybrid: Bắt Đỉnh Quá Mua)', 'result': res,
                            'entry_price': entry, 'exit_price': exit_p,
                            'sl_price': sl, 'tp1_price': tp1, 'tp2_price': tp2, 'tp3_price': tp3,
                            'risk_points': round(risk, 2), 'bars_held': exit_idx - i,
                            'multiplier': MULTIPLIER, 'diff_points': diff_pts,
                            'pnl': pnl, 'win': res in ['TP1', 'TP2', 'TP3'], 'tag': 'M3 Bắt Đỉnh',
                            'reason': f"Quét đỉnh Quá mua: " + ", ".join(tz.get('factors', [])[:2]),
                            'exit_desc': exit_desc
                        })
                        triggered_reversal = True

        # 2. Nếu không có vùng cực trị: Đánh thuận xu hướng M1 (EMA Pullback)
        if not triggered_reversal:
            # Chop / Range Filter: 14 nến có biên độ hẹp < 1.3 * ATR
            recent_14 = candles[max(0, i-13):i+1]
            hi_14 = max(cand["high"] for cand in recent_14)
            lo_14 = min(cand["low"] for cand in recent_14)
            if (hi_14 - lo_14) < 1.3 * atr:
                continue

            window = candles[max(0, i - 350):i + 1]
            ana = ict_engine.analyze(window)
            setup = ana.get('setup')
            if setup and setup.get('winRate', 0) >= 70:
                side = 'MUA' if setup['type'] == 'LONG' else 'BÁN'
                entry = round(candles[i]['ema21'], 2)
                sl = round(setup['stopLoss'], 2)
                risk = abs(entry - sl)
                if 2.5 <= risk <= 16.0:
                    skip = False
                    if trades:
                        for prev_t in reversed(trades[-3:]):
                            if prev_t['side'] != side and abs(entry - prev_t['entry_price']) < dyn_min_dist:
                                skip = True; break
                    if skip:
                        continue
                        
                    tp1 = round(entry + (1.0 * risk if side == 'MUA' else -1.0 * risk), 2)
                    tp2 = round(entry + (1.5 * risk if side == 'MUA' else -1.5 * risk), 2)
                    tp3 = round(entry + (2.0 * risk if side == 'MUA' else -2.0 * risk), 2)
                    
                    filled = False; fill_idx = 0
                    for j in range(i+1, min(i+25, len(candles))):
                        if side == 'MUA' and candles[j]['low'] <= entry: filled = True; fill_idx = j; break
                        elif side == 'BÁN' and candles[j]['high'] >= entry: filled = True; fill_idx = j; break
                        
                    if not filled:
                        trades.append({
                            'date': c['time'][:10], 'time': c['time'],
                            'signal_time': c['time'],
                            'fill_time': None,
                            'exit_time': candles[min(i+24, len(candles)-1)]['time'],
                            'side': side, 'product': get_product_symbol(commodity, c['time']),
                            'commodity': commodity, 'method': 'M3 (Hybrid: Thuận Sóng M1)', 'result': 'CHƯA KHỚP',
                            'entry_price': entry, 'exit_price': None,
                            'sl_price': sl, 'tp1_price': tp1, 'tp2_price': tp2, 'tp3_price': tp3,
                            'risk_points': round(risk, 2), 'bars_held': 0,
                            'multiplier': MULTIPLIER, 'diff_points': 0.0,
                            'pnl': 0.0, 'win': False, 'tag': 'M3 Trend',
                            'reason': setup.get('reason', ''),
                            'exit_desc': 'Hết hạn chờ 24 nến (24 giờ) giá không hồi về khớp lệnh Limit tại EMA21. Hệ thống tự động hủy lệnh để bảo toàn vốn.'
                        })
                        pos_end_idx = i + 12
                        continue
                        
                    res = 'ENTRY'; exit_p = entry; pnl = 0.0; hit_tp1 = False; hit_tp2 = False; hit_tp1_time = None
                    end_bar = min(fill_idx + 48, len(candles))
                    exit_time = candles[end_bar - 1]['time']
                    exit_idx = end_bar - 1
                    exit_desc = ""

                    for k in range(fill_idx, end_bar):
                        ck = candles[k]
                        cur_sl = entry if hit_tp1 else sl
                        if side == 'MUA':
                            if ck['low'] <= cur_sl:
                                if hit_tp1:
                                    res = 'ENTRY'; exit_p = entry; pnl = 0.0
                                    exit_desc = f"Giá đã đạt TP1 ({tp1}) và dời SL về hòa vốn {entry}. Sau đó giá hồi cắn SL hòa vốn (Bảo toàn vốn $0)."
                                else:
                                    res = 'SL'; exit_p = sl; pnl = round((sl - entry) * MULTIPLIER, 2)
                                    exit_desc = f"Giá chạm mức cắt lỗ ban đầu SL ({sl}) — Lỗ {abs(sl - entry):.2f} pts."
                                pos_end_idx = k + 6
                                exit_time = ck['time']
                                exit_idx = k
                                break
                            if ck['high'] >= tp3:
                                res = 'TP3'; exit_p = tp3; pnl = round((tp3 - entry) * MULTIPLIER, 2)
                                exit_desc = f"Giá bứt phá mạnh chạm chốt lời mục tiêu tối đa TP3 ({tp3}) tỷ lệ 2.0R."
                                pos_end_idx = k + 6
                                exit_time = ck['time']
                                exit_idx = k
                                break
                            elif ck['high'] >= tp2: hit_tp2 = True; hit_tp1 = True
                            elif ck['high'] >= tp1:
                                if not hit_tp1: hit_tp1_time = ck['time']
                                hit_tp1 = True
                        else:
                            if ck['high'] >= cur_sl:
                                if hit_tp1:
                                    res = 'ENTRY'; exit_p = entry; pnl = 0.0
                                    exit_desc = f"Giá đã đạt TP1 ({tp1}) và dời SL về hòa vốn {entry}. Sau đó giá hồi cắn SL hòa vốn (Bảo toàn vốn $0)."
                                else:
                                    res = 'SL'; exit_p = sl; pnl = round((entry - sl) * MULTIPLIER, 2)
                                    exit_desc = f"Giá chạm mức cắt lỗ ban đầu SL ({sl}) — Lỗ {abs(entry - sl):.2f} pts."
                                pos_end_idx = k + 6
                                exit_time = ck['time']
                                exit_idx = k
                                break
                            if ck['low'] <= tp3:
                                res = 'TP3'; exit_p = tp3; pnl = round((entry - tp3) * MULTIPLIER, 2)
                                exit_desc = f"Giá giảm mạnh chạm chốt lời mục tiêu tối đa TP3 ({tp3}) tỷ lệ 2.0R."
                                pos_end_idx = k + 6
                                exit_time = ck['time']
                                exit_idx = k
                                break
                            elif ck['low'] <= tp2: hit_tp2 = True; hit_tp1 = True
                            elif ck['low'] <= tp1:
                                if not hit_tp1: hit_tp1_time = ck['time']
                                hit_tp1 = True
                    else:
                        exit_time = candles[end_bar - 1]['time']
                        exit_idx = end_bar - 1
                        is_currently_open = (end_bar == len(candles) and (end_bar - 1 - fill_idx < 48))
                        if is_currently_open:
                            res = "ĐANG MỞ"
                            exit_p = candles[-1]["close"]
                            cur_diff = (exit_p - entry) if side == "MUA" else (entry - exit_p)
                            pnl = round(cur_diff * MULTIPLIER, 2)
                            exit_time = "Đang chạy..."
                            exit_desc = f"Vị thế theo xu hướng M1 đang hoạt động ở nến mới nhất ({candles[-1]['time']}). Giá hiện tại: {exit_p}. {'Đã dời SL về hòa vốn ' + str(entry) if hit_tp1 else 'SL đang đặt tại ' + str(sl)}."
                        elif hit_tp2:
                            res = 'TP2'; exit_p = tp2; pnl = round(abs(tp2 - entry) * MULTIPLIER, 2)
                            exit_desc = f"Đạt TP2 ({tp2}) tỷ lệ 1.5R và tự động chốt lời khi hết thời gian giữ lệnh 48 nến."
                        elif hit_tp1:
                            res = 'TP1'; exit_p = tp1; pnl = round(abs(tp1 - entry) * MULTIPLIER, 2)
                            exit_desc = f"Đạt TP1 ({tp1}) tỷ lệ 1.0R và tự động chốt lời khi hết thời gian giữ lệnh 48 nến."
                        else:
                            res = 'ENTRY'; exit_p = entry; pnl = 0.0
                            exit_desc = "Hết thời gian giữ lệnh 48 nến quanh vùng hòa vốn."
                        pos_end_idx = end_bar
                        
                    diff_pts = round(abs(exit_p - entry) if res != 'SL' else -abs(exit_p - entry), 2)
                    trades.append({
                        'date': candles[fill_idx]['time'][:10], 'time': candles[fill_idx]['time'],
                        'signal_time': c['time'],
                        'fill_time': candles[fill_idx]['time'],
                        'exit_time': exit_time,
                        'hit_tp1_time': hit_tp1_time,
                        'side': side,
                        'product': get_product_symbol(commodity, candles[fill_idx]['time']), 'commodity': commodity, 'method': 'M3 (Hybrid: Thuận Sóng M1)',
                        'result': res, 'entry_price': entry, 'exit_price': exit_p,
                        'sl_price': sl, 'tp1_price': tp1, 'tp2_price': tp2, 'tp3_price': tp3,
                        'risk_points': round(risk, 2), 'bars_held': exit_idx - fill_idx,
                        'multiplier': MULTIPLIER, 'diff_points': diff_pts,
                        'pnl': pnl, 'win': res in ['TP1', 'TP2', 'TP3'], 'tag': 'M3 Trend',
                        'reason': setup.get('reason', ''),
                        'exit_desc': exit_desc
                    })
    return trades


def compute_metrics(trades: list, days_filter = None) -> dict:
    """Tính các chỉ số KPI: Tổng PnL, Win Rate, Tổng lệnh, Max Drawdown, ROI trên 10k USD."""
    if not trades:
        return {
            "total_pnl": 0.0, "win_rate": 0.0, "total_trades": 0, "closed_trades": 0,
            "decisive_trades": 0,
            "win_trades": 0, "loss_trades": 0, "breakeven_trades": 0, "pending_trades": 0,
            "open_trades": 0,
            "profit_factor": 0.0, "max_drawdown": 0.0, "roi_pct": 0.0, "recommended_capital": 10000,
            "filtered_trades": []
        }
        
    if days_filter is not None and str(days_filter).upper() not in ["ALL", "MAX", "NONE"]:
        all_dates = sorted([t["date"] for t in trades])
        if all_dates:
            last_date = datetime.datetime.strptime(all_dates[-1], "%Y-%m-%d")
            if str(days_filter).upper() == "YTD":
                cutoff_date = f"{last_date.year}-01-01"
            else:
                days = int(days_filter)
                cutoff_date = (last_date - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
            filtered = [t for t in trades if t["date"] >= cutoff_date]
        else:
            filtered = trades
    else:
        filtered = trades
        
    if not filtered:
        return compute_metrics([])
        
    total_pnl = round(sum(t["pnl"] for t in filtered), 2)
    win_list = [t for t in filtered if t["result"] in ["TP1", "TP2", "TP3"]]
    loss_list = [t for t in filtered if t["result"] == "SL"]
    be_list = [t for t in filtered if t["result"] == "ENTRY"]
    pending_list = [t for t in filtered if t["result"] == "CHƯA KHỚP"]
    open_list = [t for t in filtered if t["result"] == "ĐANG MỞ"]
    
    closed_trades = len(win_list) + len(loss_list) + len(be_list)
    decisive_trades = len(win_list) + len(loss_list)
    # Win Rate chuẩn tài chính (loại trừ lệnh hòa vốn $0): Win / (Win + Loss)
    win_rate = round((len(win_list) / decisive_trades * 100), 1) if decisive_trades > 0 else 0.0
    
    gross_profit = sum(t["pnl"] for t in win_list)
    gross_loss = abs(sum(t["pnl"] for t in loss_list))
    profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else (99.0 if gross_profit > 0 else 0.0)
    
    # Tính Max Drawdown
    equity = 10000.0
    peak = equity
    max_dd = 0.0
    for t in filtered:
        equity += t["pnl"]
        if equity > peak:
            peak = equity
        dd = peak - equity
        if dd > max_dd:
            max_dd = dd
            
    roi_pct = round((total_pnl / 10000.0) * 100, 1)
    
    return {
        "total_pnl": total_pnl,
        "win_rate": win_rate,
        "total_trades": len(filtered),
        "closed_trades": closed_trades,
        "decisive_trades": decisive_trades,
        "win_trades": len(win_list),
        "loss_trades": len(loss_list),
        "breakeven_trades": len(be_list),
        "pending_trades": len(pending_list),
        "open_trades": len(open_list),
        "profit_factor": profit_factor,
        "max_drawdown": round(max_dd, 2),
        "roi_pct": roi_pct,
        "recommended_capital": 10000,
        "filtered_trades": filtered
    }


def compute_upcoming_radar(zc_candles: list, zw_candles: list) -> list:
    """
    KIẾN TRÚC 2 TẦNG THÍCH ỨNG (ADAPTIVE 2-LAYER RADAR):
      - TẦNG 1A (Phiên Á/Âu & Sideway): Xác định cấu trúc & khóa cố định điểm Entry/SL/TP trên Nến H1 Đóng Cửa.
      - TẦNG 1B (Phiên Mỹ & Sóng Xung Lực Mạnh): Kích hoạt sớm kịch bản Xung Lực (Fast Impulse) trên cụm nến
        M15/M30 Đóng Cửa (hoặc nến Displacement bứt phá xa EMA21), đón nhịp hồi nông tại 50% FVG/Equilibrium
        để không bị trễ 60 phút và không bị hụt lệnh khi sóng chạy mạnh.
      - TẦNG 2 (Con trỏ Giá M5 Realtime): Chỉ dùng giá M5 để cập nhật Giá Live, đo khoảng cách tiếp cận
        và báo trạng thái chạm vùng chờ (tuyệt đối không dùng M5 để vẽ lại cấu trúc hay dịch chuyển SL/TP).
    """
    radar = []
    commodities = [
        ("ZC", "ZCEZ26", zc_candles),
        ("ZW", "ZWAZ26", zw_candles)
    ]
    
    for comm, prod, candles in commodities:
        if not candles:
            continue
        # TẦNG 1: Chỉ lấy nến H1 đã đóng cửa để tính cấu trúc chuẩn
        c_last = candles[-1]
        h1_time = str(c_last.get("time", ""))
        h1_close = round(float(c_last["close"]), 2)
        h1_open = round(float(c_last.get("open", h1_close)), 2)
        h1_high = round(float(c_last.get("high", h1_close)), 2)
        h1_low = round(float(c_last.get("low", h1_close)), 2)
        atr = round(float(c_last.get("atr", 3.0)), 2)
        rsi = round(float(c_last.get("rsi", 50.0)), 1)
        ema21 = round(float(c_last.get("ema21", h1_close)), 2)
        ema50 = round(float(c_last.get("ema50", h1_close)), 2)
        
        ana = ict_engine.analyze(candles)
        trend = ana.get("trend", "neutral")
        setup_h1 = ana.get("setup") or {}
        m1_has_m3 = bool(setup_h1 and setup_h1.get("winRate", 0) >= 70)

        # TẦNG 2: Lấy Giá M5 Realtime chỉ để làm Con trỏ Giá Live & đo khoảng cách
        m5_live = tv_webhook_client.get_latest_m5_price(comm)
        cur_p = round(float(m5_live["close"]), 2) if m5_live and m5_live.get("close") else h1_close
        m5_high = round(float(m5_live["high"]), 2) if m5_live and m5_live.get("high") else cur_p
        m5_low = round(float(m5_live["low"]), 2) if m5_live and m5_live.get("low") else cur_p

        # ── 0. TẦNG 1B: KỊCH BẢN XUNG LỰC NHANH (M15/M30 ĐÓNG CỬA HOẶC DISPLACEMENT PHIÊN MỸ) ──
        impulse_m15 = tv_webhook_client.get_m15_m30_closed_impulse(comm, c_last)
        if impulse_m15.get("is_active"):
            imp_side = impulse_m15["side"]
            imp_entry = impulse_m15["entry_target"]
            imp_sl = impulse_m15["sl_price"]
            imp_tp1 = impulse_m15["tp1_price"]
            imp_tp2 = impulse_m15["tp2_price"]
            imp_tp3 = impulse_m15["tp3_price"]
            imp_risk = impulse_m15["risk_pts"]
            tf_lbl = impulse_m15["timeframe_label"]
            reg_lbl = impulse_m15["regime_label"]
            dist = round(abs(cur_p - imp_entry), 2)
            touched = (m5_low <= imp_entry <= m5_high)
            status = "⚡ SẴN SÀNG (Đang khớp FVG)" if (touched or dist <= 0.6 * atr) else "⏳ CHỜ HỒI NÔNG (FVG 50%)"
            radar.append({
                "commodity": comm,
                "product": prod,
                "method": f"⚡ M1-Fast ({tf_lbl} • FVG 50%)",
                "side": imp_side,
                "current_price": cur_p,
                "entry_target": imp_entry,
                "distance_pts": dist,
                "sl_price": imp_sl,
                "tp1_price": imp_tp1,
                "tp2_price": imp_tp2,
                "tp3_price": imp_tp3,
                "risk_pts": imp_risk,
                "risk_usd": round(imp_risk * MULTIPLIER, 2),
                "rr": "1 : 2.0",
                "status": status,
                "structure_time": impulse_m15.get("time_vn", h1_time),
                "latest_h1_time": h1_time,
                "m3_confluence": True,
                "action_hint": f"[{reg_lbl}] Đặt Limit {imp_side} đón nhịp hồi nông tại 50% nến xung lực ({imp_entry:.2f}) thay vì chờ EMA21 H1 ở xa ({ema21:.2f}). SL cố định: {imp_sl:.2f}, TP3: {imp_tp3:.2f}.",
                "condition": f"[Tầng 1B - {tf_lbl}] Phát hiện nến Xung Lực ({impulse_m15['atr_ratio']}x ATR, thân nến đặc {impulse_m15['body_pct']}%). Khóa điểm đón FVG/Equilibrium 50%; Tầng 2 (M5) chỉ đo khoảng cách.",
                "priority": "Rất cao"
            })
        else:
            # Kiểm tra nếu nến H1 vừa đóng là nến Xung Lực mạnh (Displacement) đẩy giá rời xa EMA21 (> 0.85 ATR)
            h1_range = max(0.01, h1_high - h1_low)
            h1_body = abs(h1_close - h1_open)
            dist_from_ema21 = abs(h1_close - ema21)
            if h1_range >= 0.85 * atr and (h1_body / h1_range) >= 0.55 and dist_from_ema21 >= 0.85 * atr:
                imp_side = "MUA" if (trend == "bullish" and h1_close > h1_open) else ("BÁN" if (trend == "bearish" and h1_close < h1_open) else None)
                if imp_side:
                    imp_entry = round((h1_open + h1_close) / 2.0, 2)
                    if imp_side == "MUA":
                        imp_sl = round(h1_low - 0.35 * atr, 2)
                        imp_risk = round(max(2.0, imp_entry - imp_sl), 2)
                        imp_tp1 = round(imp_entry + 1.0 * imp_risk, 2)
                        imp_tp2 = round(imp_entry + 1.5 * imp_risk, 2)
                        imp_tp3 = round(imp_entry + 2.0 * imp_risk, 2)
                    else:
                        imp_sl = round(h1_high + 0.35 * atr, 2)
                        imp_risk = round(max(2.0, imp_sl - imp_entry), 2)
                        imp_tp1 = round(imp_entry - 1.0 * imp_risk, 2)
                        imp_tp2 = round(imp_entry - 1.5 * imp_risk, 2)
                        imp_tp3 = round(imp_entry - 2.0 * imp_risk, 2)
                    dist = round(abs(cur_p - imp_entry), 2)
                    touched = (m5_low <= imp_entry <= m5_high)
                    status = "⚡ SẴN SÀNG (Gần vùng FVG)" if (touched or dist <= 0.75 * atr) else "⏳ CHỜ HỒI NÔNG (FVG 50%)"
                    radar.append({
                        "commodity": comm,
                        "product": prod,
                        "method": "⚡ M1-Fast (Xung Lực • FVG 50%)",
                        "side": imp_side,
                        "current_price": cur_p,
                        "entry_target": imp_entry,
                        "distance_pts": dist,
                        "sl_price": imp_sl,
                        "tp1_price": imp_tp1,
                        "tp2_price": imp_tp2,
                        "tp3_price": imp_tp3,
                        "risk_pts": imp_risk,
                        "risk_usd": round(imp_risk * MULTIPLIER, 2),
                        "rr": "1 : 2.0",
                        "status": status,
                        "structure_time": h1_time,
                        "latest_h1_time": h1_time,
                        "m3_confluence": True,
                        "action_hint": f"[Chế độ Sóng Mạnh] Giá đã bứt phá xa EMA21 ({ema21:.2f}). Đặt Limit {imp_side} đón nhịp hồi nông tại 50% thân nến xung lực ({imp_entry:.2f}). SL: {imp_sl:.2f}, TP3: {imp_tp3:.2f}.",
                        "condition": f"[Tầng 1B - Displacement] Nến bứt phá biên độ {h1_range:.2f} pts ({h1_range/atr:.1f}x ATR), cách EMA21 {dist_from_ema21:.2f} pts. Đón tại vùng cân bằng 50% để tránh hụt lệnh.",
                        "priority": "Rất cao"
                    })

        # ── 1. TẦNG 1A: KỊCH BẢN M1 CHUẨN (THUẬN XU HƯỚNG PULLBACK EMA 21-50 H1 ĐÓNG CỬA) ──
        if trend == "bearish":
            entry = ema21
            sl = round(entry + 1.25 * atr, 2)
            risk = round(sl - entry, 2)
            tp1 = round(entry - 1.0 * risk, 2)
            tp2 = round(entry - 1.5 * risk, 2)
            tp3 = round(entry - 2.0 * risk, 2)
            dist = round(abs(entry - cur_p), 2)
            touched = (m5_low <= entry <= m5_high)
            status = "⚡ SẴN SÀNG (Gần chạm)" if (touched or dist <= atr) else "⏳ ĐANG CHỜ HỒI"
            radar.append({
                "commodity": comm,
                "product": prod,
                "method": "M1 (H1 Closed • EMA Pullback)",
                "side": "BÁN",
                "current_price": cur_p,
                "entry_target": entry,
                "distance_pts": dist,
                "sl_price": sl,
                "tp1_price": tp1,
                "tp2_price": tp2,
                "tp3_price": tp3,
                "risk_pts": risk,
                "risk_usd": round(risk * MULTIPLIER, 2),
                "rr": "1 : 2.0",
                "status": status,
                "structure_time": h1_time,
                "latest_h1_time": h1_time,
                "m3_confluence": m1_has_m3,
                "action_hint": f"Đặt Limit BÁN cố định @ {entry:.2f} (EMA21 H1 đã đóng nến). SL: {sl:.2f}, TP3: {tp3:.2f}",
                "condition": f"[Tầng 1A - H1 Đóng Cửa] Xu hướng GIẢM. Điểm đón khóa cố định tại EMA21-50 ({min(ema21, ema50):.2f} - {max(ema21, ema50):.2f}); Giá M5 Live cách {dist:.2f} pts.",
                "priority": "Cao" if dist <= atr else "Trung bình"
            })
        elif trend == "bullish":
            entry = ema21
            sl = round(entry - 1.25 * atr, 2)
            risk = round(entry - sl, 2)
            tp1 = round(entry + 1.0 * risk, 2)
            tp2 = round(entry + 1.5 * risk, 2)
            tp3 = round(entry + 2.0 * risk, 2)
            dist = round(abs(cur_p - entry), 2)
            touched = (m5_low <= entry <= m5_high)
            status = "⚡ SẴN SÀNG (Gần chạm)" if (touched or dist <= atr) else "⏳ ĐANG CHỜ HỒI"
            radar.append({
                "commodity": comm,
                "product": prod,
                "method": "M1 (H1 Closed • EMA Pullback)",
                "side": "MUA",
                "current_price": cur_p,
                "entry_target": entry,
                "distance_pts": dist,
                "sl_price": sl,
                "tp1_price": tp1,
                "tp2_price": tp2,
                "tp3_price": tp3,
                "risk_pts": risk,
                "risk_usd": round(risk * MULTIPLIER, 2),
                "rr": "1 : 2.0",
                "status": status,
                "structure_time": h1_time,
                "latest_h1_time": h1_time,
                "m3_confluence": m1_has_m3,
                "action_hint": f"Đặt Limit MUA cố định @ {entry:.2f} (EMA21 H1 đã đóng nến). SL: {sl:.2f}, TP3: {tp3:.2f}",
                "condition": f"[Tầng 1A - H1 Đóng Cửa] Xu hướng TĂNG. Điểm đón khóa cố định tại EMA21-50 ({min(ema21, ema50):.2f} - {max(ema21, ema50):.2f}); Giá M5 Live cách {dist:.2f} pts.",
                "priority": "Cao" if dist <= atr else "Trung bình"
            })
            
        # ── 2 & 3. TẦNG 1A: KỊCH BẢN M2 SMC 5★ - 6★ (H1 ĐÓNG CỬA - BẮT ĐÁY / BẮT ĐỈNH) ──
        # BỘ LỌC VÙNG CÒN HIỆU LỰC (ACTIVE ZONE FILTER):
        # - Vùng Đáy chỉ hợp lệ khi giá chưa bị xuyên thủng sâu: bz["price"] <= cur_p + 0.3 * atr
        # - Vùng Đỉnh chỉ hợp lệ khi giá chưa vượt qua sâu: tz["price"] >= cur_p - 0.3 * atr
        min_opposing_dist = 7.0 if comm == "ZW" else 4.0
        valid_tzs = [z for z in ana.get("top_zones", []) if z.get("score", 0) >= 5 and z.get("price", 0) >= cur_p - 0.3 * atr]
        valid_bzs = [z for z in ana.get("bottom_zones", []) if z.get("score", 0) >= 5 and z.get("price", 0) <= cur_p + 0.3 * atr]

        chosen_tz = valid_tzs[-1] if valid_tzs else None
        chosen_bz = valid_bzs[-1] if valid_bzs else None

        # BỘ LỌC XUNG ĐỘT (CONFLICT RESOLUTION):
        # Nếu cả 2 kịch bản Đỉnh và Đáy quá gần nhau (< min_opposing_dist), ưu tiên theo xu hướng H1:
        # - Downtrend (Bearish): Ưu tiên BÁN (Đỉnh / Kháng cự), bỏ kịch bản Bắt Đáy sát sạt
        # - Uptrend (Bullish): Ưu tiên MUA (Đáy / Hỗ trợ), bỏ kịch bản Bắt Đỉnh sát sạt
        if chosen_tz and chosen_bz:
            if (chosen_tz["price"] - chosen_bz["price"]) < min_opposing_dist:
                if trend == "bearish":
                    chosen_bz = None
                elif trend == "bullish":
                    chosen_tz = None
                else:
                    if chosen_tz.get("score", 0) >= chosen_bz.get("score", 0):
                        chosen_bz = None
                    else:
                        chosen_tz = None

        if chosen_tz:
            tz_p = round(chosen_tz["price"], 2)
            sc = chosen_tz.get("score", 5)
            tz_idx = chosen_tz.get("index", len(candles) - 1)
            tz_time = str(candles[tz_idx].get("time", h1_time)) if 0 <= tz_idx < len(candles) else h1_time
            tz_m3 = any("sweep" in f.lower() or "overbought" in f.lower() for f in chosen_tz.get("factors", [])) or (rsi > 65)
            sl = round(tz_p + 0.75 * atr, 2)
            risk = round(sl - tz_p, 2)
            tp1 = round(tz_p - 1.0 * risk, 2)
            tp2 = round(tz_p - 1.5 * risk, 2)
            tp3 = round(tz_p - 2.0 * risk, 2)
            dist = round(abs(cur_p - tz_p), 2)
            status = "⚡ SẴN SÀNG (Đang test đỉnh)" if dist <= atr else "🔍 THEO DÕI VÙNG ĐỈNH"
            radar.append({
                "commodity": comm,
                "product": prod,
                "method": f"M2 (H1 SMC {sc}★ Bắt Đỉnh)",
                "side": "BÁN",
                "current_price": cur_p,
                "entry_target": tz_p,
                "distance_pts": dist,
                "sl_price": sl,
                "tp1_price": tp1,
                "tp2_price": tp2,
                "tp3_price": tp3,
                "risk_pts": risk,
                "risk_usd": round(risk * MULTIPLIER, 2),
                "rr": "1 : 2.0",
                "status": status,
                "structure_time": tz_time,
                "latest_h1_time": h1_time,
                "m3_confluence": tz_m3,
                "action_hint": f"Vùng đỉnh H1 cố định tại {tz_p:.2f}. Canh giá quét qua {tz_p:.2f} rồi đóng nến M15/H1 rút râu để BÁN. SL: {sl:.2f}, TP3: {tp3:.2f}",
                "condition": f"[Tầng 1A - H1 Đóng Cửa] Đỉnh SMC {sc}/8★ tại {tz_p:.2f}. " + ", ".join(chosen_tz.get("factors", [])[:2]),
                "priority": "Cao" if dist <= atr else "Trung bình"
            })

        if chosen_bz:
            bz_p = round(chosen_bz["price"], 2)
            sc = chosen_bz.get("score", 5)
            bz_idx = chosen_bz.get("index", len(candles) - 1)
            bz_time = str(candles[bz_idx].get("time", h1_time)) if 0 <= bz_idx < len(candles) else h1_time
            bz_m3 = any("sweep" in f.lower() or "oversold" in f.lower() for f in chosen_bz.get("factors", [])) or (rsi < 35)
            sl = round(bz_p - 0.75 * atr, 2)
            risk = round(bz_p - sl, 2)
            tp1 = round(bz_p + 1.0 * risk, 2)
            tp2 = round(bz_p + 1.5 * risk, 2)
            tp3 = round(bz_p + 2.0 * risk, 2)
            dist = round(abs(cur_p - bz_p), 2)
            status = "⚡ SẴN SÀNG (Đang test đáy)" if dist <= atr else "🔍 THEO DÕI VÙNG ĐÁY"
            radar.append({
                "commodity": comm,
                "product": prod,
                "method": f"M2 (H1 SMC {sc}★ Bắt Đáy)",
                "side": "MUA",
                "current_price": cur_p,
                "entry_target": bz_p,
                "distance_pts": dist,
                "sl_price": sl,
                "tp1_price": tp1,
                "tp2_price": tp2,
                "tp3_price": tp3,
                "risk_pts": risk,
                "risk_usd": round(risk * MULTIPLIER, 2),
                "rr": "1 : 2.0",
                "status": status,
                "structure_time": bz_time,
                "latest_h1_time": h1_time,
                "m3_confluence": bz_m3,
                "action_hint": f"Vùng đáy H1 cố định tại {bz_p:.2f}. Canh giá nhúng qua {bz_p:.2f} rồi đóng nến M15/H1 rút chân để MUA. SL: {sl:.2f}, TP3: {tp3:.2f}",
                "condition": f"[Tầng 1A - H1 Đóng Cửa] Đáy SMC {sc}/8★ tại {bz_p:.2f}. " + ", ".join(chosen_bz.get("factors", [])[:2]),
                "priority": "Cao" if dist <= atr else "Trung bình"
            })

    # Sắp xếp theo mức độ sẵn sàng: Sẵn sàng & M1-Fast lên đầu, khoảng cách gần lên trước
    radar = sorted(radar, key=lambda x: (0 if "SẴN SÀNG" in x["status"] else 1, 0 if "M1-Fast" in x["method"] else 1, x["distance_pts"]))
    return radar


def run_full_backtest(force_download: bool = False) -> dict:
    """Chạy toàn bộ backtest toàn bộ lịch sử nến H1 cho 3 phương pháp trên cả ZC và ZW."""
    print("=" * 60)
    print("  KHỞI ĐỘNG LIVE SIGNAL BACKTEST (3 PHƯƠNG PHÁP - TOÀN BỘ LỊCH SỬ & YTD)")
    print("=" * 60)
    
    zc_candles = fetch_or_load_candles("ZC", force_download=force_download)
    zw_candles = fetch_or_load_candles("ZW", force_download=force_download)
    
    # ── Phương pháp 1 (ICT Pullback - Tầng 1 H1 Structure + Tầng 2 M5 Status) ──
    print("▶ Chạy Phương pháp 1 (ICT MSS + Pullback EMA)...")
    m1_zc = apply_m5_live_status_to_trades(simulate_method_1(zc_candles, "ZC"), "ZC")
    m1_zw = apply_m5_live_status_to_trades(simulate_method_1(zw_candles, "ZW"), "ZW")
    m1_all = sorted(m1_zc + m1_zw, key=lambda x: x["time"], reverse=True)
    
    # ── Phương pháp 2 (SMC Reversal Zone - Tầng 1 H1 Structure + Tầng 2 M5 Status) ──
    print("▶ Chạy Phương pháp 2 (FVG + Bắt Đáy / Đỉnh SMC Zone)...")
    m2_zc = apply_m5_live_status_to_trades(simulate_method_2(zc_candles, "ZC"), "ZC")
    m2_zw = apply_m5_live_status_to_trades(simulate_method_2(zw_candles, "ZW"), "ZW")
    m2_all = sorted(m2_zc + m2_zw, key=lambda x: x["time"], reverse=True)

    # ── Phương pháp 3 (Hybrid: M1 + M2 - Tầng 1 H1 Structure + Tầng 2 M5 Status) ──
    print("▶ Chạy Phương pháp 3 (Chiến Lược Hybrid Kết Hợp M1 + M2)...")
    m3_zc = apply_m5_live_status_to_trades(simulate_method_3_hybrid(zc_candles, "ZC"), "ZC")
    m3_zw = apply_m5_live_status_to_trades(simulate_method_3_hybrid(zw_candles, "ZW"), "ZW")
    m3_all = sorted(m3_zc + m3_zw, key=lambda x: x["time"], reverse=True)
    
    # Tính metrics đa tầng thời gian
    m1_stats_all  = compute_metrics(m1_all, days_filter="ALL")
    m1_stats_ytd  = compute_metrics(m1_all, days_filter="YTD")
    m1_stats_365d = compute_metrics(m1_all, days_filter=365)
    m1_stats_90d  = compute_metrics(m1_all, days_filter=90)
    m1_stats_30d  = compute_metrics(m1_all, days_filter=30)
    m1_stats_7d   = compute_metrics(m1_all, days_filter=7)
    
    m2_stats_all  = compute_metrics(m2_all, days_filter="ALL")
    m2_stats_ytd  = compute_metrics(m2_all, days_filter="YTD")
    m2_stats_365d = compute_metrics(m2_all, days_filter=365)
    m2_stats_90d  = compute_metrics(m2_all, days_filter=90)
    m2_stats_30d  = compute_metrics(m2_all, days_filter=30)
    m2_stats_7d   = compute_metrics(m2_all, days_filter=7)

    m3_stats_all  = compute_metrics(m3_all, days_filter="ALL")
    m3_stats_ytd  = compute_metrics(m3_all, days_filter="YTD")
    m3_stats_365d = compute_metrics(m3_all, days_filter=365)
    m3_stats_90d  = compute_metrics(m3_all, days_filter=90)
    m3_stats_30d  = compute_metrics(m3_all, days_filter=30)
    m3_stats_7d   = compute_metrics(m3_all, days_filter=7)
    
    print("▶ Quét Radar Điểm Vào Lệnh Tương Lai (Upcoming Future Setups)...")
    radar_list = compute_upcoming_radar(zc_candles, zw_candles)
    
    result = {
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "period_days": "ALL",
        "total_candles": {"ZC": len(zc_candles), "ZW": len(zw_candles)},
        "upcoming_radar": radar_list,
        "method_1": {
            "name": "Phương Pháp 1: ICT MSS + Pullback EMA 21-50",
            "type": "Trend-Following (Thuận xu hướng SMC)",
            "description": "Bắt sóng hồi về dải EMA 21-50 sau khi cấu trúc MSS xác nhận xu hướng.",
            "stats_all":  {k: v for k, v in m1_stats_all.items() if k != "filtered_trades"},
            "stats_ytd":  {k: v for k, v in m1_stats_ytd.items() if k != "filtered_trades"},
            "stats_365d": {k: v for k, v in m1_stats_365d.items() if k != "filtered_trades"},
            "stats_90d":  {k: v for k, v in m1_stats_90d.items() if k != "filtered_trades"},
            "stats_30d":  {k: v for k, v in m1_stats_30d.items() if k != "filtered_trades"},
            "stats_7d":   {k: v for k, v in m1_stats_7d.items() if k != "filtered_trades"},
            "trades": m1_all
        },
        "method_2": {
            "name": "Phương Pháp 2: FVG + Bắt Đáy / Đỉnh SMC Zone",
            "type": "Contrarian / Reversal (Đảo chiều vùng cực trị)",
            "description": "Bắt đảo chiều tại các vùng thanh khoản cực trị (Quét BSL/SSL Sweep + RSI Phân kỳ + Cản S1/R1 + FVG).",
            "stats_all":  {k: v for k, v in m2_stats_all.items() if k != "filtered_trades"},
            "stats_ytd":  {k: v for k, v in m2_stats_ytd.items() if k != "filtered_trades"},
            "stats_365d": {k: v for k, v in m2_stats_365d.items() if k != "filtered_trades"},
            "stats_90d":  {k: v for k, v in m2_stats_90d.items() if k != "filtered_trades"},
            "stats_30d":  {k: v for k, v in m2_stats_30d.items() if k != "filtered_trades"},
            "stats_7d":   {k: v for k, v in m2_stats_7d.items() if k != "filtered_trades"},
            "trades": m2_all
        },
        "method_3": {
            "name": "Phương Pháp 3: Chiến Lược Hybrid (M1 + M2 Kết Hợp)",
            "type": "Hybrid Dynamic (Phối hợp Xu hướng & Vùng Cực Trị)",
            "description": "Chỉ bắt đáy/đỉnh khi sóng xả/tăng đã hoàn tất (quét Sweep + cạn kiệt), còn lại đi lệnh thuận sóng M1 khi có MSS xác nhận.",
            "stats_all":  {k: v for k, v in m3_stats_all.items() if k != "filtered_trades"},
            "stats_ytd":  {k: v for k, v in m3_stats_ytd.items() if k != "filtered_trades"},
            "stats_365d": {k: v for k, v in m3_stats_365d.items() if k != "filtered_trades"},
            "stats_90d":  {k: v for k, v in m3_stats_90d.items() if k != "filtered_trades"},
            "stats_30d":  {k: v for k, v in m3_stats_30d.items() if k != "filtered_trades"},
            "stats_7d":   {k: v for k, v in m3_stats_7d.items() if k != "filtered_trades"},
            "trades": m3_all
        }
    }
    
    BACKTEST_RESULT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(BACKTEST_RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        
    print(f"✅ Đã lưu kết quả Backtest thành công vào {BACKTEST_RESULT_FILE}")
    print(f"   - M1 YTD: Lãi ${m1_stats_ytd['total_pnl']:+,.2f} | Win Rate: {m1_stats_ytd['win_rate']}% | Lệnh: {m1_stats_ytd['total_trades']}")
    print(f"   - M2 YTD: Lãi ${m2_stats_ytd['total_pnl']:+,.2f} | Win Rate: {m2_stats_ytd['win_rate']}% | Lệnh: {m2_stats_ytd['total_trades']}")
    print(f"   - M3 Hybrid YTD: Lãi ${m3_stats_ytd['total_pnl']:+,.2f} | Win Rate: {m3_stats_ytd['win_rate']}% | Lệnh: {m3_stats_ytd['total_trades']}")
    return result


# ── HỆ THỐNG CẢNH BÁO TELEGRAM: CBOT RADAR ──────────────────────────────────
RADAR_STATE_FILE = DATA_OUTPUT / "radar_telegram_state.json"
TELEGRAM_CONFIGS = [
    {"token": "8723627742:AAEpZFbfd8RSOGi9jxoh2tKQ8TdFViXivc0", "chat_id": "5294991069"},
    {"token": "8723627742:AAEpZFbfd8RSOGi9jxoh2tKQ8TdFViXivc0", "chat_id": "-1003920117828"},  # Group: Cbot Thắng
]


def _format_vn_time_str(raw_str: str) -> str:
    """Chuyển đổi YYYY-MM-DD HH:MM sang DD/MM/YYYY HH:MM."""
    if not raw_str:
        return "N/A"
    s = str(raw_str).strip()
    try:
        parts = s.split(" ")
        d_parts = parts[0].split("-")
        if len(d_parts) == 3:
            t_part = f" {parts[1][:5]}" if len(parts) > 1 else ""
            return f"{d_parts[2]}/{d_parts[1]}/{d_parts[0]}{t_part}"
    except Exception:
        pass
    return s


def format_cbot_radar_message(r: dict, is_test: bool = False) -> str:
    """Định dạng tin nhắn Telegram chuẩn tiêu đề 'CBOT RADAR' với đầy đủ thời gian & chiến lược M1/M2/M3."""
    now_vn = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%d/%m/%Y %H:%M:%S")
    comm = r.get("commodity", "")
    prod = r.get("product", comm)
    icon_prod = "🌾" if comm == "ZW" else "🌽"
    name_vn = "Lúa Mì" if comm == "ZW" else "Ngô"
    side = r.get("side", "MUA")
    side_icon = "🟢 MUA" if side == "MUA" else "🔴 BÁN"
    method = r.get("method", "")
    m3_conf = r.get("m3_confluence", False)
    m3_str = " <i>(Đồng thuận M3 Hybrid)</i>" if m3_conf and "M3" not in method else ""

    struct_t = _format_vn_time_str(r.get("structure_time", ""))
    h1_t = _format_vn_time_str(r.get("latest_h1_time", ""))
    time_candle_line = f"{struct_t}" if struct_t == h1_t or not h1_t else f"{struct_t} (Nến H1 mới nhất: {h1_t})"

    cur_p = float(r.get("current_price", 0))
    entry_p = float(r.get("entry_target", 0))
    dist = float(r.get("distance_pts", 0))
    sl_p = float(r.get("sl_price", 0))
    tp1_p = float(r.get("tp1_price", 0))
    tp2_p = float(r.get("tp2_price", 0))
    tp3_p = float(r.get("tp3_price", 0))
    risk_pts = float(r.get("risk_pts", 0))
    risk_usd = float(r.get("risk_usd", 0))
    status_str = r.get("status", "⚡ SẴN SÀNG")
    condition = r.get("condition", "")
    action_hint = r.get("action_hint", "")

    header_tag = "📡 <b>CBOT RADAR [TEST]</b>" if is_test else "📡 <b>CBOT RADAR</b>"
    msg = (
        f"{header_tag} — <b>{icon_prod} {prod} ({name_vn}) | {side_icon}</b>\n"
        f"{'─'*28}\n"
        f"• 🕒 <b>Thời gian báo:</b> <code>{now_vn}</code> (Giờ VN)\n"
        f"• ⏱ <b>Nến cấu trúc gốc:</b> <code>{time_candle_line}</code>\n"
        f"• 📊 <b>Chiến lược:</b> <b>{method}</b>{m3_str}\n"
        f"• 📡 <b>Trạng thái:</b> <b>{status_str}</b>\n"
        f"• 💹 <b>Giá Live (M5):</b> <b>{cur_p:.2f}</b> <i>(Cách điểm đón {dist:.2f} pts)</i>\n"
        f"• 🎯 <b>Điểm Đón ({side}):</b> <b>{entry_p:.2f}</b>\n"
        f"• 🛑 <b>Cắt lỗ (SL):</b> <code>{sl_p:.2f}</code> <i>(Rủi ro: {risk_pts:.2f} pts = ${risk_usd:,.0f}/HĐ)</i>\n"
        f"• 🏆 <b>Chốt lời (TP):</b>\n"
        f"   ├ TP1 (Dời BE): <b>{tp1_p:.2f}</b>\n"
        f"   ├ TP2 (1.5R): <b>{tp2_p:.2f}</b>\n"
        f"   └ TP3 (2.0R): <b>{tp3_p:.2f}</b>\n"
        f"• 🧠 <b>Căn cứ kỹ thuật:</b> {condition}\n"
        f"• 💡 <b>Hành động:</b> <i>{action_hint}</i>"
    )
    return msg


def send_cbot_radar_telegram(text: str, target_chat_id: str = None):
    """Gửi tin nhắn CBOT RADAR qua Telegram."""
    import requests
    configs = [{"token": TELEGRAM_CONFIGS[0]["token"], "chat_id": target_chat_id}] if target_chat_id else TELEGRAM_CONFIGS
    for cfg in configs:
        url = f"https://api.telegram.org/bot{cfg['token']}/sendMessage"
        payload = {
            "chat_id": cfg["chat_id"],
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": {
                "inline_keyboard": [[{"text": "🔍 Quét CBOT RADAR", "callback_data": "scan_market"}]]
            }
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                print(f"[CBOT RADAR] Đã gửi Telegram tới {cfg['chat_id']} thành công.")
            else:
                print(f"[CBOT RADAR] Lỗi gửi Telegram tới {cfg['chat_id']}: {resp.text}")
        except Exception as e:
            print(f"[CBOT RADAR] Lỗi kết nối Telegram ({cfg['chat_id']}): {e}")


def scan_and_send_cbot_radar_telegram(force_test_nearest: bool = False, target_chat_id: str = None) -> bool:
    """
    Quét Radar Điểm Vào Lệnh Sắp Tới (M1, M1-Fast, M2, M3 Hybrid) và gửi tin nhắn 'CBOT RADAR' qua Telegram.
    - Nếu force_test_nearest=True: gửi ngay 1 tin nhắn test của tín hiệu gần nhất trên Radar.
    - Nếu force_test_nearest=False: chỉ gửi các kịch bản đang '⚡ SẴN SÀNG' chưa từng gửi (chống spam).
    """
    now_str = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n--- [{now_str}] QUÉT CBOT RADAR (LIVE SIGNAL) ---")

    zc_candles = fetch_or_load_90d("ZC", force_download=False)
    zw_candles = fetch_or_load_90d("ZW", force_download=False)
    radar_list = compute_upcoming_radar(zc_candles, zw_candles)

    if not radar_list:
        print("[CBOT RADAR] Không có kịch bản nào trên Radar.")
        return False

    state = {"sent_keys": {}, "last_messages": {}}
    if RADAR_STATE_FILE.exists():
        try:
            with open(RADAR_STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            pass

    sent_keys = state.get("sent_keys", {})
    last_messages = state.get("last_messages", {})
    any_sent = False

    if force_test_nearest:
        nearest = radar_list[0]
        msg = format_cbot_radar_message(nearest, is_test=True)
        send_cbot_radar_telegram(msg, target_chat_id=target_chat_id)
        key = f"{nearest['product']}|{nearest['method']}|{nearest['side']}|{nearest['entry_target']:.2f}"
        sent_keys[key] = now_str
        last_messages[nearest["product"]] = {"timestamp": now_str, "msg": msg}
        state["sent_keys"] = sent_keys
        state["last_messages"] = last_messages
        RADAR_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(RADAR_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        return True

    ready_items = [r for r in radar_list if "SẴN SÀNG" in r.get("status", "")]
    for r in ready_items:
        key = f"{r['product']}|{r['method']}|{r['side']}|{r['entry_target']:.2f}"
        if key in sent_keys:
            continue
        msg = format_cbot_radar_message(r, is_test=False)
        send_cbot_radar_telegram(msg, target_chat_id=target_chat_id)
        sent_keys[key] = now_str
        last_messages[r["product"]] = {"timestamp": now_str, "msg": msg}
        any_sent = True

    if len(sent_keys) > 100:
        keys_sorted = list(sent_keys.keys())[-80:]
        sent_keys = {k: sent_keys[k] for k in keys_sorted}

    state["sent_keys"] = sent_keys
    state["last_messages"] = last_messages
    RADAR_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RADAR_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    return any_sent


if __name__ == "__main__":
    run_full_backtest(force_download=True)
