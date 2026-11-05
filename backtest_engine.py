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
CACHE_90D_ZC = DATA_OUTPUT / "ZC_90d_H1.csv"
CACHE_90D_ZW = DATA_OUTPUT / "ZW_90d_H1.csv"

CQG_MAP = {
    "ZW": "ZWAZ26",
    "ZC": "ZCEZ26"
}
MULTIPLIER = 50.0  # 1 cent = $50 / lot


def fetch_or_load_90d(commodity_code: str, force_download: bool = False) -> list:
    """Tải từ Yahoo Finance hoặc nạp từ file cache 90 ngày."""
    cache_file = CACHE_90D_ZC if commodity_code == "ZC" else CACHE_90D_ZW
    df = None
    
    if not force_download and cache_file.exists():
        try:
            mtime = datetime.datetime.fromtimestamp(cache_file.stat().st_mtime)
            if (datetime.datetime.now() - mtime).total_seconds() < 14400:
                df = pd.read_csv(cache_file)
        except Exception:
            df = None

    if df is None or df.empty:
        try:
            import yfinance as yf
            ticker = f"{commodity_code}Z26.CBT"
            print(f"  [Backtest] Đang tải dữ liệu 90 ngày cho {ticker} từ Yahoo...")
            tk = yf.Ticker(ticker)
            raw = tk.history(period="90d", interval="1h")
            if not raw.empty:
                df = raw.reset_index()
                if "Datetime" in df.columns:
                    df["Time"] = df["Datetime"].dt.tz_convert("Asia/Ho_Chi_Minh").dt.strftime("%Y-%m-%d %H:%M")
                elif "Date" in df.columns:
                    df["Time"] = df["Date"].dt.strftime("%Y-%m-%d %H:%M")
                df = df[["Time", "Open", "High", "Low", "Close", "Volume"]]
                
                # Tính các chỉ báo
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
                print(f"  [Backtest] Đã lưu {len(df)} nến 90d vào {cache_file.name}")
        except Exception as e:
            print(f"  [Backtest Lỗi] Không tải được dữ liệu mới: {e}")
            if cache_file.exists():
                df = pd.read_csv(cache_file)
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
    # Ghép dữ liệu nến M5 Realtime từ TradingView Webhook (nếu có)
    candles = tv_webhook_client.merge_realtime_m5_into_candles(candles, commodity_code)
    return candles


def simulate_method_1(candles: list, commodity: str) -> list:
    """
    Phương pháp 1: ICT MSS + Pullback EMA 21-50 (Trend-Following)
    """
    cqg_sym = CQG_MAP.get(commodity, commodity)
    trades = []
    pos_end_idx = 0
    
    for i in range(50, len(candles) - 5):
        if i < pos_end_idx:
            continue
            
        window = candles[:i+1]
        ana = ict_engine.analyze(window)
        setup = ana.get("setup")
        
        if setup and setup.get("winRate", 0) >= 70:
            side = "MUA" if setup["type"] == "LONG" else "BÁN"
            entry = round(candles[i]["ema21"], 2)
            sl = round(setup["stopLoss"], 2)
            risk = abs(entry - sl)
            
            if risk < 2.5 or risk > 16.0:
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
                    "product": cqg_sym,
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
                "product": cqg_sym,
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
        
        if side == "MUA":
            sl = round(swing_price - 0.75 * atr, 2)
            risk = entry - sl
            if risk < 2.0 or risk > 22.0: continue
            tp1 = round(entry + 1.0 * risk, 2)
            tp2 = round(entry + 1.5 * risk, 2)
            tp3 = round(entry + 2.0 * risk, 2)
        else: # BÁN
            sl = round(swing_price + 0.75 * atr, 2)
            risk = sl - entry
            if risk < 2.0 or risk > 22.0: continue
            tp1 = round(entry - 1.0 * risk, 2)
            tp2 = round(entry - 1.5 * risk, 2)
            tp3 = round(entry - 2.0 * risk, 2)
            
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
            "product": cqg_sym,
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
    
    ana_full = ict_engine.analyze(candles)
    bzs = {b['index']: b for b in ana_full.get('bottom_zones', []) if b['score'] >= 5}
    tzs = {t['index']: t for t in ana_full.get('top_zones', []) if t['score'] >= 5}
    
    for i in range(50, len(candles) - 5):
        if i < pos_end_idx:
            continue
        c = candles[i]
        
        # 1. Kiểm tra ưu tiên: Vùng đảo chiều cực trị (M2 Exhaustion)
        bz = bzs.get(i - 3)
        tz = tzs.get(i - 3)
        triggered_reversal = False
        
        if bz:
            has_sweep = any('sweep' in f.lower() for f in bz.get('factors', []))
            is_oversold = (c.get('rsi', 50) < 35) or any('oversold' in f.lower() for f in bz.get('factors', []))
            if has_sweep or is_oversold:
                entry = round(c['close'], 2)
                atr = c.get('atr', 3.0)
                sl = round(bz['price'] - 0.75 * atr, 2)
                risk = entry - sl
                if 2.0 <= risk <= 20.0:
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
                        'side': 'MUA', 'product': cqg_sym,
                        'commodity': commodity, 'method': 'M3 (Hybrid: Bắt Đáy Hấp Thụ)', 'result': res,
                        'entry_price': entry, 'exit_price': exit_p,
                        'sl_price': sl, 'tp1_price': tp1, 'tp2_price': tp2, 'tp3_price': tp3,
                        'risk_points': round(risk, 2), 'bars_held': exit_idx - i,
                        'multiplier': MULTIPLIER, 'diff_points': diff_pts,
                        'pnl': pnl, 'win': res in ['TP1', 'TP2', 'TP3'], 'tag': 'M2 Bắt Đáy',
                        'reason': f"Hấp thụ đáy Climax: " + ", ".join(bz.get('factors', [])[:2]),
                        'exit_desc': exit_desc
                    })
                    triggered_reversal = True
                    
        elif tz and not triggered_reversal:
            has_sweep = any('sweep' in f.lower() for f in tz.get('factors', []))
            is_overbought = (c.get('rsi', 50) > 65) or any('overbought' in f.lower() for f in tz.get('factors', []))
            if has_sweep or is_overbought:
                entry = round(c['close'], 2)
                atr = c.get('atr', 3.0)
                sl = round(tz['price'] + 0.75 * atr, 2)
                risk = sl - entry
                if 2.0 <= risk <= 20.0:
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
                        'side': 'BÁN', 'product': cqg_sym,
                        'commodity': commodity, 'method': 'M3 (Hybrid: Bắt Đỉnh Quá Mua)', 'result': res,
                        'entry_price': entry, 'exit_price': exit_p,
                        'sl_price': sl, 'tp1_price': tp1, 'tp2_price': tp2, 'tp3_price': tp3,
                        'risk_points': round(risk, 2), 'bars_held': exit_idx - i,
                        'multiplier': MULTIPLIER, 'diff_points': diff_pts,
                        'pnl': pnl, 'win': res in ['TP1', 'TP2', 'TP3'], 'tag': 'M2 Bắt Đỉnh',
                        'reason': f"Quét đỉnh Quá mua: " + ", ".join(tz.get('factors', [])[:2]),
                        'exit_desc': exit_desc
                    })
                    triggered_reversal = True

        # 2. Nếu không có vùng cực trị: Đánh thuận xu hướng M1 (EMA Pullback)
        if not triggered_reversal:
            window = candles[:i+1]
            ana = ict_engine.analyze(window)
            setup = ana.get('setup')
            if setup and setup.get('winRate', 0) >= 70:
                side = 'MUA' if setup['type'] == 'LONG' else 'BÁN'
                entry = round(candles[i]['ema21'], 2)
                sl = round(setup['stopLoss'], 2)
                risk = abs(entry - sl)
                if 2.5 <= risk <= 16.0:
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
                            'side': side, 'product': cqg_sym,
                            'commodity': commodity, 'method': 'M3 (Hybrid: Thuận Sóng M1)', 'result': 'CHƯA KHỚP',
                            'entry_price': entry, 'exit_price': None,
                            'sl_price': sl, 'tp1_price': tp1, 'tp2_price': tp2, 'tp3_price': tp3,
                            'risk_points': round(risk, 2), 'bars_held': 0,
                            'multiplier': MULTIPLIER, 'diff_points': 0.0,
                            'pnl': 0.0, 'win': False, 'tag': 'M1 Trend',
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
                        'product': cqg_sym, 'commodity': commodity, 'method': 'M3 (Hybrid: Thuận Sóng M1)',
                        'result': res, 'entry_price': entry, 'exit_price': exit_p,
                        'sl_price': sl, 'tp1_price': tp1, 'tp2_price': tp2, 'tp3_price': tp3,
                        'risk_points': round(risk, 2), 'bars_held': exit_idx - fill_idx,
                        'multiplier': MULTIPLIER, 'diff_points': diff_pts,
                        'pnl': pnl, 'win': res in ['TP1', 'TP2', 'TP3'], 'tag': 'M1 Trend',
                        'reason': setup.get('reason', ''),
                        'exit_desc': exit_desc
                    })
    return trades


def compute_metrics(trades: list, days_filter: int = None) -> dict:
    """Tính các chỉ số KPI: Tổng PnL, Win Rate, Tổng lệnh, Max Drawdown, ROI trên 10k USD."""
    if not trades:
        return {
            "total_pnl": 0.0, "win_rate": 0.0, "total_trades": 0, "closed_trades": 0,
            "win_trades": 0, "loss_trades": 0, "breakeven_trades": 0, "pending_trades": 0,
            "open_trades": 0,
            "profit_factor": 0.0, "max_drawdown": 0.0, "roi_pct": 0.0, "recommended_capital": 10000,
            "filtered_trades": []
        }
        
    if days_filter is not None:
        all_dates = sorted([t["date"] for t in trades])
        if all_dates:
            last_date = datetime.datetime.strptime(all_dates[-1], "%Y-%m-%d")
            cutoff_date = (last_date - datetime.timedelta(days=days_filter)).strftime("%Y-%m-%d")
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
    win_rate = round((len(win_list) / closed_trades * 100), 1) if closed_trades > 0 else 0.0
    
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
    Phát hiện các điểm vào lệnh tiềm năng trong tương lai (Upcoming Setups / Future Radar)
    dựa trên cấu trúc nến hiện tại (H1 + M5 Realtime) để Trader chuẩn bị lệnh trước.
    """
    radar = []
    commodities = [
        ("ZC", "ZCEZ26", zc_candles),
        ("ZW", "ZWAZ26", zw_candles)
    ]
    
    for comm, prod, candles in commodities:
        if not candles:
            continue
        c_last = candles[-1]
        cur_p = round(c_last["close"], 2)
        cur_time = c_last.get("time", "")
        atr = round(c_last.get("atr", 3.0), 2)
        ema21 = round(c_last.get("ema21", cur_p), 2)
        ema50 = round(c_last.get("ema50", cur_p), 2)
        
        ana = ict_engine.analyze(candles)
        trend = ana.get("trend", "neutral")
        
        # 1. Kịch bản M1: Thuận xu hướng Pullback EMA 21-50
        if trend == "bearish":
            entry = ema21
            sl = round(entry + 1.25 * atr, 2)
            risk = round(sl - entry, 2)
            tp1 = round(entry - 1.0 * risk, 2)
            tp2 = round(entry - 1.5 * risk, 2)
            tp3 = round(entry - 2.0 * risk, 2)
            dist = round(max(0.0, entry - cur_p), 2)
            status = "⚡ SẴN SÀNG (Gần chạm)" if dist <= atr else "⏳ ĐANG CHỜ HỒI"
            radar.append({
                "commodity": comm,
                "product": prod,
                "method": "M1 (Trend Pullback EMA)",
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
                "action_hint": f"Đặt Limit BÁN @ {entry:.2f} (dải EMA 21-50). SL: {sl:.2f}, TP3: {tp3:.2f}",
                "condition": f"Xu hướng H1 đang GIẢM. Chờ giá hồi {dist:.2f} pts về dải EMA21-50 ({min(ema21, ema50):.2f} - {max(ema21, ema50):.2f}).",
                "priority": "Cao" if dist <= atr else "Trung bình"
            })
        elif trend == "bullish":
            entry = ema21
            sl = round(entry - 1.25 * atr, 2)
            risk = round(entry - sl, 2)
            tp1 = round(entry + 1.0 * risk, 2)
            tp2 = round(entry + 1.5 * risk, 2)
            tp3 = round(entry + 2.0 * risk, 2)
            dist = round(max(0.0, cur_p - entry), 2)
            status = "⚡ SẴN SÀNG (Gần chạm)" if dist <= atr else "⏳ ĐANG CHỜ HỒI"
            radar.append({
                "commodity": comm,
                "product": prod,
                "method": "M1 (Trend Pullback EMA)",
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
                "action_hint": f"Đặt Limit MUA @ {entry:.2f} (dải EMA 21-50). SL: {sl:.2f}, TP3: {tp3:.2f}",
                "condition": f"Xu hướng H1 đang TĂNG. Chờ giá hồi {dist:.2f} pts về dải EMA21-50 ({min(ema21, ema50):.2f} - {max(ema21, ema50):.2f}).",
                "priority": "Cao" if dist <= atr else "Trung bình"
            })
            
        # 2. Kịch bản M2: Bắt Đỉnh SMC 5★ - 6★ Zone
        tz_list = [z for z in ana.get("top_zones", []) if z.get("score", 0) >= 5]
        if tz_list:
            tz = tz_list[-1]
            tz_p = round(tz["price"], 2)
            sc = tz.get("score", 5)
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
                "method": f"M2 (SMC {sc}★ Bắt Đỉnh)",
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
                "action_hint": f"Canh nến H1 quét qua {tz_p:.2f} rồi rút râu để BÁN. SL: {sl:.2f}, TP3: {tp3:.2f}",
                "condition": f"Đỉnh SMC {sc}/8★ tại {tz_p:.2f}. " + ", ".join(tz.get("factors", [])[:2]),
                "priority": "Cao" if dist <= atr else "Trung bình"
            })
            
        # 3. Kịch bản M2: Bắt Đáy SMC 5★ - 6★ Zone
        bz_list = [z for z in ana.get("bottom_zones", []) if z.get("score", 0) >= 5]
        if bz_list:
            bz = bz_list[-1]
            bz_p = round(bz["price"], 2)
            sc = bz.get("score", 5)
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
                "method": f"M2 (SMC {sc}★ Bắt Đáy)",
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
                "action_hint": f"Canh nến H1 nhúng qua {bz_p:.2f} rồi rút chân để MUA. SL: {sl:.2f}, TP3: {tp3:.2f}",
                "condition": f"Đáy SMC {sc}/8★ tại {bz_p:.2f}. " + ", ".join(bz.get("factors", [])[:2]),
                "priority": "Cao" if dist <= atr else "Trung bình"
            })

    # Sắp xếp theo mức độ sẵn sàng: Sẵn sàng lên đầu, khoảng cách gần lên trước
    radar = sorted(radar, key=lambda x: (0 if "SẴN SÀNG" in x["status"] else 1, x["distance_pts"]))
    return radar


def run_full_backtest(force_download: bool = False) -> dict:
    """Chạy toàn bộ backtest 90 ngày cho 3 phương pháp trên cả ZC và ZW."""
    print("=" * 60)
    print("  KHỞI ĐỘNG LIVE SIGNAL BACKTEST (3 PHƯƠNG PHÁP - 90 NGÀY)")
    print("=" * 60)
    
    zc_candles = fetch_or_load_90d("ZC", force_download=force_download)
    zw_candles = fetch_or_load_90d("ZW", force_download=force_download)
    
    # ── Phương pháp 1 (ICT Pullback) ──
    print("▶ Chạy Phương pháp 1 (ICT MSS + Pullback EMA)...")
    m1_zc = simulate_method_1(zc_candles, "ZC")
    m1_zw = simulate_method_1(zw_candles, "ZW")
    m1_all = sorted(m1_zc + m1_zw, key=lambda x: x["time"], reverse=True)
    
    # ── Phương pháp 2 (SMC Reversal Zone) ──
    print("▶ Chạy Phương pháp 2 (FVG + Bắt Đáy / Đỉnh SMC Zone)...")
    m2_zc = simulate_method_2(zc_candles, "ZC")
    m2_zw = simulate_method_2(zw_candles, "ZW")
    m2_all = sorted(m2_zc + m2_zw, key=lambda x: x["time"], reverse=True)

    # ── Phương pháp 3 (Hybrid: M1 + M2) ──
    print("▶ Chạy Phương pháp 3 (Chiến Lược Hybrid Kết Hợp M1 + M2)...")
    m3_zc = simulate_method_3_hybrid(zc_candles, "ZC")
    m3_zw = simulate_method_3_hybrid(zw_candles, "ZW")
    m3_all = sorted(m3_zc + m3_zw, key=lambda x: x["time"], reverse=True)
    
    # Tính metrics
    m1_stats_all = compute_metrics(m1_all)
    m1_stats_30d = compute_metrics(m1_all, days_filter=30)
    m1_stats_7d  = compute_metrics(m1_all, days_filter=7)
    
    m2_stats_all = compute_metrics(m2_all)
    m2_stats_30d = compute_metrics(m2_all, days_filter=30)
    m2_stats_7d  = compute_metrics(m2_all, days_filter=7)

    m3_stats_all = compute_metrics(m3_all)
    m3_stats_30d = compute_metrics(m3_all, days_filter=30)
    m3_stats_7d  = compute_metrics(m3_all, days_filter=7)
    
    print("▶ Quét Radar Điểm Vào Lệnh Tương Lai (Upcoming Future Setups)...")
    radar_list = compute_upcoming_radar(zc_candles, zw_candles)
    
    result = {
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "period_days": 90,
        "upcoming_radar": radar_list,
        "method_1": {
            "name": "Phương Pháp 1: ICT MSS + Pullback EMA 21-50",
            "type": "Trend-Following (Thuận xu hướng SMC)",
            "description": "Bắt sóng hồi về dải EMA 21-50 sau khi cấu trúc MSS xác nhận xu hướng.",
            "stats_90d": {k: v for k, v in m1_stats_all.items() if k != "filtered_trades"},
            "stats_30d": {k: v for k, v in m1_stats_30d.items() if k != "filtered_trades"},
            "stats_7d":  {k: v for k, v in m1_stats_7d.items() if k != "filtered_trades"},
            "trades": m1_all
        },
        "method_2": {
            "name": "Phương Pháp 2: FVG + Bắt Đáy / Đỉnh SMC Zone",
            "type": "Contrarian / Reversal (Đảo chiều vùng cực trị)",
            "description": "Bắt đảo chiều tại các vùng thanh khoản cực trị (Quét BSL/SSL Sweep + RSI Phân kỳ + Cản S1/R1 + FVG).",
            "stats_90d": {k: v for k, v in m2_stats_all.items() if k != "filtered_trades"},
            "stats_30d": {k: v for k, v in m2_stats_30d.items() if k != "filtered_trades"},
            "stats_7d":  {k: v for k, v in m2_stats_7d.items() if k != "filtered_trades"},
            "trades": m2_all
        },
        "method_3": {
            "name": "Phương Pháp 3: Chiến Lược Hybrid (M1 + M2 Kết Hợp)",
            "type": "Hybrid Dynamic (Phối hợp Xu hướng & Vùng Cực Trị)",
            "description": "Chỉ bắt đáy/đỉnh khi sóng xả/tăng đã hoàn tất (quét Sweep + cạn kiệt), còn lại đi lệnh thuận sóng M1 khi có MSS xác nhận.",
            "stats_90d": {k: v for k, v in m3_stats_all.items() if k != "filtered_trades"},
            "stats_30d": {k: v for k, v in m3_stats_30d.items() if k != "filtered_trades"},
            "stats_7d":  {k: v for k, v in m3_stats_7d.items() if k != "filtered_trades"},
            "trades": m3_all
        }
    }
    
    BACKTEST_RESULT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(BACKTEST_RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        
    print(f"✅ Đã lưu kết quả Backtest thành công vào {BACKTEST_RESULT_FILE}")
    print(f"   - M1 (30d): Lãi ${m1_stats_30d['total_pnl']:+,.2f} | Win Rate: {m1_stats_30d['win_rate']}% | Lệnh: {m1_stats_30d['total_trades']}")
    print(f"   - M2 (30d): Lãi ${m2_stats_30d['total_pnl']:+,.2f} | Win Rate: {m2_stats_30d['win_rate']}% | Lệnh: {m2_stats_30d['total_trades']}")
    print(f"   - M3 Hybrid (30d): Lãi ${m3_stats_30d['total_pnl']:+,.2f} | Win Rate: {m3_stats_30d['win_rate']}% | Lệnh: {m3_stats_30d['total_trades']}")
    return result


if __name__ == "__main__":
    run_full_backtest(force_download=True)
