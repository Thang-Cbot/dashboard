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
    Phương pháp 1: Scalp / Intraday (Thuận Xu Hướng EMA 21-50 • Mục tiêu $200 USD)
    - Chỉ vào lệnh trong giờ giao dịch chính trong ngày (14:00 - 22:00 VN).
    - Không treo hay giữ lệnh qua đêm (tối đa 9 nến H1 trong phiên).
    - Mục tiêu lợi nhuận chuẩn: $200 USD / giao dịch (TP1 = +4.0 pts, TP2 = +4.5 pts, TP3 = +5.0 pts).
    """
    trades = []
    pos_end_idx = 0
    
    tp1_pts = 4.0   # $200 USD
    tp2_pts = 4.5   # $225 USD
    tp3_pts = 5.0   # $250 USD
    be_trigger = 2.6 if commodity == "ZW" else 2.4
    
    for i in range(50, len(candles) - 5):
        if i < pos_end_idx:
            continue
        c = candles[i]
        atr = max(1.2, c.get("atr", 2.0))
        if commodity == "ZC" and atr < 1.35:
            continue
        if commodity == "ZW" and atr < 2.0:
            continue
            
        # Chỉ vào lệnh trong giờ giao dịch sôi động trong ngày (14:00 - 22:00 VN)
        hour_vn = int(c["time"][11:13])
        if not (14 <= hour_vn <= 22):
            continue
            
        ema21 = c["ema21"]
        ema50 = c["ema50"]
        ema21_prev = candles[i-3]["ema21"]
        ema50_prev = candles[i-5]["ema50"]
        rsi = c.get("rsi", 50.0)
        
        side = None
        pullback_offset = 0.45 * atr if commodity == "ZW" else 0.40 * atr
        reason_str = ""
        
        # MUA INTRADAY: EMA21 > EMA50, cả 2 cùng dốc lên, nến đóng cửa xanh trên EMA21
        if ema21 > ema50 and ema21 > ema21_prev and ema50 >= ema50_prev and c["close"] > ema21 and c["close"] > c["open"]:
            if c["low"] <= ema21 + 0.45 * atr and 48 <= rsi <= 66:
                if (c["close"] - c["low"]) >= 0.55 * (c["high"] - c["low"] + 0.01):
                    side = "MUA"
                    entry = round(max(ema21 - 0.1 * atr, c["close"] - pullback_offset), 2)
                    sl_dist = min(5.0 if commodity == "ZW" else 4.2, max(3.6, round(1.8 * atr, 2)))
                    sl = round(entry - sl_dist, 2)
                    reason_str = f"Scalp Intraday Thuận Xu Hướng TĂNG: EMA21 ({ema21:.2f}) > EMA50 ({ema50:.2f}), nến rút chân đồng thuận động lượng (RSI {rsi:.1f})."
        # BÁN INTRADAY: EMA21 < EMA50, cả 2 cùng dốc xuống, nến đóng cửa đỏ dưới EMA21
        elif ema21 < ema50 and ema21 < ema21_prev and ema50 <= ema50_prev and c["close"] < ema21 and c["close"] < c["open"]:
            if c["high"] >= ema21 - 0.45 * atr and 34 <= rsi <= 52:
                if (c["high"] - c["close"]) >= 0.55 * (c["high"] - c["low"] + 0.01):
                    side = "BÁN"
                    entry = round(min(ema21 + 0.1 * atr, c["close"] + pullback_offset), 2)
                    sl_dist = min(5.0 if commodity == "ZW" else 4.2, max(3.6, round(1.8 * atr, 2)))
                    sl = round(entry + sl_dist, 2)
                    reason_str = f"Scalp Intraday Thuận Xu Hướng GIẢM: EMA21 ({ema21:.2f}) < EMA50 ({ema50:.2f}), nến rút râu trên đồng thuận áp lực bán (RSI {rsi:.1f})."
                
        if not side:
            continue
            
        risk = round(abs(entry - sl), 2)
        if side == "MUA":
            tp1 = round(entry + tp1_pts, 2)
            tp2 = round(entry + tp2_pts, 2)
            tp3 = round(entry + tp3_pts, 2)
        else:
            tp1 = round(entry - tp1_pts, 2)
            tp2 = round(entry - tp2_pts, 2)
            tp3 = round(entry - tp3_pts, 2)
            
        # Chờ khớp trong tối đa 4 giờ trong phiên (nếu không khớp thì hủy ngay trong ngày)
        filled = False
        fill_idx = 0
        for j in range(i + 1, min(i + 5, len(candles))):
            if side == "MUA" and candles[j]["low"] <= entry:
                if candles[j]["open"] > sl:
                    filled = True; fill_idx = j; break
            elif side == "BÁN" and candles[j]["high"] >= entry:
                if candles[j]["open"] < sl:
                    filled = True; fill_idx = j; break
                    
        if not filled:
            continue
            
        # Quản lý lệnh trong ngày (tối đa 9 nến H1, tuyệt đối không giữ qua đêm)
        max_hold = 9
        end_bar = min(fill_idx + max_hold, len(candles))
        res = "ENTRY"
        exit_p = entry
        pnl = 0.0
        hit_be = False
        hit_tp1_time = None
        exit_idx = end_bar - 1
        exit_time = candles[exit_idx]["time"]
        exit_desc = ""
        
        for k in range(fill_idx, end_bar):
            ck = candles[k]
            cur_sl = entry if hit_be else sl
            
            if k == fill_idx:
                if side == "MUA":
                    if ck["close"] >= tp1 or ck["high"] >= tp1 + 0.5:
                        res = "TP1"; exit_p = tp1; pnl = round(tp1_pts * MULTIPLIER, 2)
                        hit_tp1_time = ck["time"]; exit_idx = k; exit_time = ck["time"]; pos_end_idx = k + 2
                        exit_desc = f"Đạt mục tiêu lợi nhuận Scalp trong ngày TP1 ({tp1} • +$200 USD) ngay sau khi khớp lệnh."
                        break
                    elif ck["low"] <= sl and ck["close"] < entry:
                        res = "SL"; exit_p = sl; pnl = round((sl - entry) * MULTIPLIER, 2)
                        exit_idx = k; exit_time = ck["time"]; pos_end_idx = k + 3
                        exit_desc = f"Giá chạm mức cắt lỗ Intraday SL ({sl}) — Lỗ {abs(sl - entry):.2f} pts."
                        break
                    elif ck["close"] >= entry + be_trigger:
                        hit_be = True; hit_tp1_time = ck["time"]
                else:
                    if ck["close"] <= tp1 or ck["low"] <= tp1 - 0.5:
                        res = "TP1"; exit_p = tp1; pnl = round(tp1_pts * MULTIPLIER, 2)
                        hit_tp1_time = ck["time"]; exit_idx = k; exit_time = ck["time"]; pos_end_idx = k + 2
                        exit_desc = f"Đạt mục tiêu lợi nhuận Scalp trong ngày TP1 ({tp1} • +$200 USD) ngay sau khi khớp lệnh."
                        break
                    elif ck["high"] >= sl and ck["close"] > entry:
                        res = "SL"; exit_p = sl; pnl = round((entry - sl) * MULTIPLIER, 2)
                        exit_idx = k; exit_time = ck["time"]; pos_end_idx = k + 3
                        exit_desc = f"Giá chạm mức cắt lỗ Intraday SL ({sl}) — Lỗ {abs(entry - sl):.2f} pts."
                        break
                    elif ck["close"] <= entry - be_trigger:
                        hit_be = True; hit_tp1_time = ck["time"]
                continue
                
            if side == "MUA":
                if ck["high"] >= tp1:
                    if ck["high"] >= tp3 and ck["close"] >= tp2:
                        res = "TP3"; exit_p = tp3
                    elif ck["high"] >= tp2 and ck["close"] >= tp1:
                        res = "TP2"; exit_p = tp2
                    else:
                        res = "TP1"; exit_p = tp1
                    pnl = round((exit_p - entry) * MULTIPLIER, 2)
                    if not hit_tp1_time: hit_tp1_time = ck["time"]
                    exit_idx = k; exit_time = ck["time"]; pos_end_idx = k + 2
                    exit_desc = f"Chốt lời Scalp Intraday thành công tại {res} ({exit_p}) — Lãi +${pnl:,.0f} USD trong phiên, không giữ qua đêm."
                    break
                if ck["low"] <= cur_sl:
                    if hit_be:
                        res = "ENTRY"; exit_p = entry; pnl = 0.0
                        exit_desc = f"Lệnh đã lãi trên +${be_trigger*50:.0f} và dời SL về hòa vốn {entry}. Giá quay đầu chạm SL hòa vốn (Bảo toàn vốn $0)."
                    else:
                        res = "SL"; exit_p = sl; pnl = round((sl - entry) * MULTIPLIER, 2)
                        exit_desc = f"Giá chạm mức cắt lỗ Intraday SL ({sl}) — Lỗ {abs(sl - entry):.2f} pts."
                    exit_idx = k; exit_time = ck["time"]; pos_end_idx = k + 3; break
                if ck["high"] >= entry + be_trigger and not hit_be:
                    hit_be = True; hit_tp1_time = ck["time"]
            else:
                if ck["low"] <= tp1:
                    if ck["low"] <= tp3 and ck["close"] <= tp2:
                        res = "TP3"; exit_p = tp3
                    elif ck["low"] <= tp2 and ck["close"] <= tp1:
                        res = "TP2"; exit_p = tp2
                    else:
                        res = "TP1"; exit_p = tp1
                    pnl = round((entry - exit_p) * MULTIPLIER, 2)
                    if not hit_tp1_time: hit_tp1_time = ck["time"]
                    exit_idx = k; exit_time = ck["time"]; pos_end_idx = k + 2
                    exit_desc = f"Chốt lời Scalp Intraday thành công tại {res} ({exit_p}) — Lãi +${pnl:,.0f} USD trong phiên, không giữ qua đêm."
                    break
                if ck["high"] >= cur_sl:
                    if hit_be:
                        res = "ENTRY"; exit_p = entry; pnl = 0.0
                        exit_desc = f"Lệnh đã lãi trên +${be_trigger*50:.0f} và dời SL về hòa vốn {entry}. Giá quay đầu chạm SL hòa vốn (Bảo toàn vốn $0)."
                    else:
                        res = "SL"; exit_p = sl; pnl = round((entry - sl) * MULTIPLIER, 2)
                        exit_desc = f"Giá chạm mức cắt lỗ Intraday SL ({sl}) — Lỗ {abs(entry - sl):.2f} pts."
                    exit_idx = k; exit_time = ck["time"]; pos_end_idx = k + 3; break
                if ck["low"] <= entry - be_trigger and not hit_be:
                    hit_be = True; hit_tp1_time = ck["time"]
        else:
            exit_idx = end_bar - 1
            ck = candles[exit_idx]
            exit_time = ck["time"]
            is_currently_open = (end_bar == len(candles) and (end_bar - 1 - fill_idx < max_hold))
            if is_currently_open:
                res = "ĐANG MỞ"
                exit_p = round(candles[-1]["close"], 2)
                cur_diff = (exit_p - entry) if side == "MUA" else (entry - exit_p)
                pnl = round(cur_diff * MULTIPLIER, 2)
                exit_time = "Đang chạy..."
                exit_desc = f"Vị thế Scalp Intraday đang hoạt động ở nến mới nhất ({candles[-1]['time']}). Giá hiện tại: {exit_p}. {'Đã dời SL về hòa vốn ' + str(entry) if hit_be else 'SL đang đặt tại ' + str(sl)}."
            else:
                exit_p = round(ck["close"], 2)
                diff = (exit_p - entry) if side == "MUA" else (entry - exit_p)
                if hit_be and diff <= 0:
                    res = "ENTRY"; exit_p = entry; pnl = 0.0
                    exit_desc = "Kết thúc phiên giao dịch trong ngày (9 giờ): Đóng lệnh tại mức bảo vệ hòa vốn ($0), không giữ qua đêm."
                elif diff >= 2.5:
                    res = "TP1"; pnl = round(diff * MULTIPLIER, 2)
                    exit_desc = f"Kết thúc phiên giao dịch trong ngày: Tất toán vị thế chốt lãi Intraday +${pnl:,.0f} USD ({diff:+.2f} pts), không giữ qua đêm."
                elif diff <= -2.5:
                    res = "SL"; pnl = round(diff * MULTIPLIER, 2)
                    exit_desc = f"Kết thúc phiên giao dịch trong ngày: Đóng vị thế Intraday theo quy tắc không giữ lệnh qua đêm ({diff:+.2f} pts)."
                else:
                    res = "ENTRY"; exit_p = entry; pnl = 0.0
                    exit_desc = "Kết thúc phiên giao dịch trong ngày quanh vùng giá vào: Tất toán hòa vốn ($0), tuyệt đối không giữ lệnh qua đêm."
            pos_end_idx = end_bar
            
        diff_pts = round(pnl / MULTIPLIER, 2) if res != "ENTRY" else 0.0
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
            "method": "M1 (Scalp / Intraday • Mục Tiêu $200)",
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
            "tag": "M1 Scalp",
            "reason": reason_str,
            "exit_desc": exit_desc
        })
        
    return trades


def simulate_method_2(candles: list, commodity: str) -> list:
    """
    Phương pháp 2: Swing Đỉnh / Đáy Gần Nhất (Mục tiêu lợi nhuận $400 - $500 USD)
    - Giao dịch tại cấu trúc Đỉnh / Đáy gần nhất (SMC Zone >= 5 sao hoặc Swing High/Low 20 nến đồng thuận xu hướng).
    - Mục tiêu lợi nhuận: $400 - $500 USD / giao dịch (TP1 = +8.0 pts, TP2 = +9.0 pts, TP3 = +10.0 pts).
    - Lệnh có thể treo và giữ vài ngày (tối đa 120 nến H1 ~ 5 ngày giao dịch) để đảm bảo đạt mục tiêu sóng Swing.
    """
    trades = []
    pos_end_idx = 0
    
    tp1_pts = 8.0   # $400 USD
    tp2_pts = 9.0   # $450 USD
    tp3_pts = 10.0  # $500 USD
    be_trigger = 5.0 if commodity == "ZW" else 4.5
    
    ana = ict_engine.analyze(candles)
    bzs = {b["index"]: b for b in ana.get("bottom_zones", []) if b["score"] >= 5}
    tzs = {t["index"]: t for t in ana.get("top_zones", []) if t["score"] >= 5}
    
    for i in range(50, len(candles) - 5):
        if i < pos_end_idx:
            continue
        c = candles[i]
        atr = max(1.3, c.get("atr", 2.2))
        if commodity == "ZC" and atr < 1.55:
            continue
        if commodity == "ZW" and atr < 2.2:
            continue
            
        ema21 = c["ema21"]
        ema50 = c["ema50"]
        ema21_prev = candles[i-3]["ema21"]
        ema50_prev = candles[i-5]["ema50"]
        rsi = c.get("rsi", 50.0)
        
        recent_20 = candles[max(0, i-20):i]
        low_20 = min(x["low"] for x in recent_20)
        high_20 = max(x["high"] for x in recent_20)
        
        side = None
        swing_ref = 0.0
        tag_str = "M2 Swing"
        reason_str = ""
        
        # 1. MUA TẠI ĐÁY SWING GẦN NHẤT:
        bz = bzs.get(i - 3)
        if bz and c["close"] > ema21 and ema21 >= ema50 - 0.4 * atr and c["close"] > c["open"] and c["low"] >= bz["price"] - 0.2 * atr:
            side = "MUA"
            swing_ref = bz["price"]
            tag_str = "M2 Swing Đáy"
            reason_str = f"Swing Đáy Gần Nhất ({swing_ref:.2f}) đạt chuẩn SMC {bz['score']}/8★: " + ", ".join(bz.get("factors", [])[:2])
        elif ema21 > ema50 and ema21 > ema21_prev and ema50 >= ema50_prev and c["close"] > ema21 and c["close"] > c["open"]:
            if c["low"] <= ema21 + 0.35 * atr and c["low"] >= low_20 and 45 <= rsi <= 65:
                if (c["close"] - c["low"]) >= 0.55 * (c["high"] - c["low"] + 0.01):
                    side = "MUA"
                    swing_ref = min(c["low"], ema50)
                    tag_str = "M2 Swing Đáy"
                    reason_str = f"Swing Đáy Gần Nhất ({swing_ref:.2f}): Tạo đáy cao hơn (Higher Low) trên cụm 20 nến & EMA50 ({ema50:.2f}), mục tiêu sóng Swing $400-$500."
                
        # 2. BÁN TẠI ĐỈNH SWING GẦN NHẤT:
        tz = tzs.get(i - 3)
        if not side:
            if tz and c["close"] < ema21 and ema21 <= ema50 + 0.4 * atr and c["close"] < c["open"] and c["high"] <= tz["price"] + 0.2 * atr:
                side = "BÁN"
                swing_ref = tz["price"]
                tag_str = "M2 Swing Đỉnh"
                reason_str = f"Swing Đỉnh Gần Nhất ({swing_ref:.2f}) đạt chuẩn SMC {tz['score']}/8★: " + ", ".join(tz.get("factors", [])[:2])
            elif ema21 < ema50 and ema21 < ema21_prev and ema50 <= ema50_prev and c["close"] < ema21 and c["close"] < c["open"]:
                if c["high"] >= ema21 - 0.35 * atr and c["high"] <= high_20 and 35 <= rsi <= 55:
                    if (c["high"] - c["close"]) >= 0.55 * (c["high"] - c["low"] + 0.01):
                        side = "BÁN"
                        swing_ref = max(c["high"], ema50)
                        tag_str = "M2 Swing Đỉnh"
                        reason_str = f"Swing Đỉnh Gần Nhất ({swing_ref:.2f}): Tạo đỉnh thấp hơn (Lower High) dưới cụm 20 nến & EMA50 ({ema50:.2f}), mục tiêu sóng Swing $400-$500."
                    
        if not side:
            continue
            
        pullback_offset = 0.60 * atr if commodity == "ZW" else 0.65 * atr
        if side == "MUA":
            entry = round(max(swing_ref + 0.2 * atr, c["close"] - pullback_offset), 2)
            sl_dist = min(9.2 if commodity == "ZW" else 7.5, max(6.2, round(2.6 * atr, 2)))
            sl = round(entry - sl_dist, 2)
            tp1 = round(entry + tp1_pts, 2)
            tp2 = round(entry + tp2_pts, 2)
            tp3 = round(entry + tp3_pts, 2)
        else:
            entry = round(min(swing_ref - 0.2 * atr, c["close"] + pullback_offset), 2)
            sl_dist = min(9.2 if commodity == "ZW" else 7.5, max(6.2, round(2.6 * atr, 2)))
            sl = round(entry + sl_dist, 2)
            tp1 = round(entry - tp1_pts, 2)
            tp2 = round(entry - tp2_pts, 2)
            tp3 = round(entry - tp3_pts, 2)
            
        risk = round(abs(entry - sl), 2)
        filled = False
        fill_idx = 0
        for j in range(i + 1, min(i + 13, len(candles))):
            if side == "MUA" and candles[j]["low"] <= entry:
                if candles[j]["open"] > sl:
                    filled = True; fill_idx = j; break
            elif side == "BÁN" and candles[j]["high"] >= entry:
                if candles[j]["open"] < sl:
                    filled = True; fill_idx = j; break
                    
        if not filled:
            continue
            
        max_hold = 120 # Giữ lệnh tối đa 5 ngày (120 nến H1) để đạt mục tiêu $400-$500
        end_bar = min(fill_idx + max_hold, len(candles))
        res = "ENTRY"
        exit_p = entry
        pnl = 0.0
        hit_be = False
        hit_tp1_time = None
        exit_idx = end_bar - 1
        exit_time = candles[exit_idx]["time"]
        exit_desc = ""
        
        for k in range(fill_idx, end_bar):
            ck = candles[k]
            cur_sl = entry if hit_be else sl
            
            if k == fill_idx:
                if side == "MUA":
                    if ck["close"] >= tp1:
                        res = "TP1"; exit_p = tp1; pnl = round(tp1_pts * MULTIPLIER, 2)
                        hit_tp1_time = ck["time"]; exit_idx = k; exit_time = ck["time"]; pos_end_idx = k + 4
                        exit_desc = f"Giá bật mạnh từ vùng Đáy Swing đạt ngay mục tiêu TP1 ({tp1} • +$400 USD)."
                        break
                    elif ck["low"] <= sl and ck["close"] < entry:
                        res = "SL"; exit_p = sl; pnl = round((sl - entry) * MULTIPLIER, 2)
                        exit_idx = k; exit_time = ck["time"]; pos_end_idx = k + 6
                        exit_desc = f"Giá phá vỡ cấu trúc Đáy Swing chạm SL ({sl}) — Lỗ {abs(sl - entry):.2f} pts."
                        break
                    elif ck["close"] >= entry + be_trigger:
                        hit_be = True; hit_tp1_time = ck["time"]
                else:
                    if ck["close"] <= tp1:
                        res = "TP1"; exit_p = tp1; pnl = round(tp1_pts * MULTIPLIER, 2)
                        hit_tp1_time = ck["time"]; exit_idx = k; exit_time = ck["time"]; pos_end_idx = k + 4
                        exit_desc = f"Giá giảm mạnh từ vùng Đỉnh Swing đạt ngay mục tiêu TP1 ({tp1} • +$400 USD)."
                        break
                    elif ck["high"] >= sl and ck["close"] > entry:
                        res = "SL"; exit_p = sl; pnl = round((entry - sl) * MULTIPLIER, 2)
                        exit_idx = k; exit_time = ck["time"]; pos_end_idx = k + 6
                        exit_desc = f"Giá phá vỡ cấu trúc Đỉnh Swing chạm SL ({sl}) — Lỗ {abs(entry - sl):.2f} pts."
                        break
                    elif ck["close"] <= entry - be_trigger:
                        hit_be = True; hit_tp1_time = ck["time"]
                continue
                
            if side == "MUA":
                if ck["high"] >= tp1:
                    if ck["high"] >= tp3 and ck["close"] >= tp2:
                        res = "TP3"; exit_p = tp3
                    elif ck["high"] >= tp2 and ck["close"] >= tp1:
                        res = "TP2"; exit_p = tp2
                    else:
                        res = "TP1"; exit_p = tp1
                    pnl = round((exit_p - entry) * MULTIPLIER, 2)
                    if not hit_tp1_time: hit_tp1_time = ck["time"]
                    exit_idx = k; exit_time = ck["time"]; pos_end_idx = k + 4
                    exit_desc = f"Sóng Swing Đáy hoàn tất mục tiêu tại {res} ({exit_p}) — Chốt lời +${pnl:,.0f} USD."
                    break
                if ck["low"] <= cur_sl:
                    if hit_be:
                        res = "ENTRY"; exit_p = entry; pnl = 0.0
                        exit_desc = f"Lệnh Swing đã lãi trên +${be_trigger*50:.0f} và dời SL về hòa vốn {entry}. Giá hồi chạm SL hòa vốn ($0)."
                    else:
                        res = "SL"; exit_p = sl; pnl = round((sl - entry) * MULTIPLIER, 2)
                        exit_desc = f"Giá chạm mức cắt lỗ cấu trúc Swing SL ({sl}) — Lỗ {abs(sl - entry):.2f} pts."
                    exit_idx = k; exit_time = ck["time"]; pos_end_idx = k + 6; break
                if ck["high"] >= entry + be_trigger and not hit_be:
                    hit_be = True; hit_tp1_time = ck["time"]
            else:
                if ck["low"] <= tp1:
                    if ck["low"] <= tp3 and ck["close"] <= tp2:
                        res = "TP3"; exit_p = tp3
                    elif ck["low"] <= tp2 and ck["close"] <= tp1:
                        res = "TP2"; exit_p = tp2
                    else:
                        res = "TP1"; exit_p = tp1
                    pnl = round((entry - exit_p) * MULTIPLIER, 2)
                    if not hit_tp1_time: hit_tp1_time = ck["time"]
                    exit_idx = k; exit_time = ck["time"]; pos_end_idx = k + 4
                    exit_desc = f"Sóng Swing Đỉnh hoàn tất mục tiêu tại {res} ({exit_p}) — Chốt lời +${pnl:,.0f} USD."
                    break
                if ck["high"] >= cur_sl:
                    if hit_be:
                        res = "ENTRY"; exit_p = entry; pnl = 0.0
                        exit_desc = f"Lệnh Swing đã lãi trên +${be_trigger*50:.0f} và dời SL về hòa vốn {entry}. Giá hồi chạm SL hòa vốn ($0)."
                    else:
                        res = "SL"; exit_p = sl; pnl = round((entry - sl) * MULTIPLIER, 2)
                        exit_desc = f"Giá chạm mức cắt lỗ cấu trúc Swing SL ({sl}) — Lỗ {abs(entry - sl):.2f} pts."
                    exit_idx = k; exit_time = ck["time"]; pos_end_idx = k + 6; break
                if ck["low"] <= entry - be_trigger and not hit_be:
                    hit_be = True; hit_tp1_time = ck["time"]
        else:
            exit_idx = end_bar - 1
            ck = candles[exit_idx]
            exit_time = ck["time"]
            is_currently_open = (end_bar == len(candles) and (end_bar - 1 - fill_idx < max_hold))
            if is_currently_open:
                res = "ĐANG MỞ"
                exit_p = round(candles[-1]["close"], 2)
                cur_diff = (exit_p - entry) if side == "MUA" else (entry - exit_p)
                pnl = round(cur_diff * MULTIPLIER, 2)
                exit_time = "Đang chạy..."
                exit_desc = f"Vị thế Swing Đỉnh/Đáy đang được giữ qua ngày ({candles[-1]['time']}) hướng tới mục tiêu $400-$500. Giá hiện tại: {exit_p}. {'Đã dời SL về hòa vốn ' + str(entry) if hit_be else 'SL đang đặt tại ' + str(sl)}."
            else:
                exit_p = round(ck["close"], 2)
                diff = (exit_p - entry) if side == "MUA" else (entry - exit_p)
                if hit_be and diff <= 0:
                    res = "ENTRY"; exit_p = entry; pnl = 0.0
                    exit_desc = "Hết chu kỳ giữ lệnh Swing 5 ngày (120 giờ): Đóng lệnh bảo toàn vốn ($0)."
                elif diff >= 6.5:
                    res = "TP1"; pnl = round(diff * MULTIPLIER, 2)
                    exit_desc = f"Hết chu kỳ giữ lệnh Swing 5 ngày: Chốt lời sóng Swing +${pnl:,.0f} USD ({diff:+.2f} pts)."
                elif diff <= -4.0:
                    res = "SL"; pnl = round(diff * MULTIPLIER, 2)
                    exit_desc = f"Hết chu kỳ giữ lệnh Swing 5 ngày: Tất toán vị thế ({diff:+.2f} pts)."
                else:
                    res = "ENTRY"; exit_p = entry; pnl = 0.0
                    exit_desc = "Hết chu kỳ giữ lệnh Swing 5 ngày quanh vùng hòa vốn ($0)."
            pos_end_idx = end_bar
            
        diff_pts = round(pnl / MULTIPLIER, 2) if res != "ENTRY" else 0.0
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
            "method": "M2 (Swing Đỉnh/Đáy • Mục Tiêu $400-$500)",
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
            "tag": tag_str,
            "reason": reason_str,
            "exit_desc": exit_desc
        })
        
    return trades


def simulate_method_3_hybrid(candles: list, commodity: str) -> list:
    """
    Phương pháp 3: Chiến Lược Hybrid (Kết Hợp Scalp Intraday $200 + Swing Đỉnh/Đáy $400-$500)
    Quy tắc phối hợp:
      1. ƯU TIÊN 1 — Sóng Lớn Swing ($400 - $500 USD, giữ vài ngày):
         Khi xuất hiện cấu trúc Đỉnh/Đáy gần nhất (SMC Zone >= 5 sao hoặc Swing High/Low 20 nến khi ATR đủ rộng).
      2. ƯU TIÊN 2 — Lệnh Ngắn Scalp / Intraday ($200 USD, đóng trong ngày):
         Khi thị trường đi giữa sóng trong giờ giao dịch chính (14:00 - 22:00 VN), đánh lệnh ngắn ăn $200 và tuyệt đối không giữ qua đêm.
    """
    trades = []
    pos_end_idx = 0
    
    ana = ict_engine.analyze(candles)
    bzs = {b["index"]: b for b in ana.get("bottom_zones", []) if b["score"] >= 5}
    tzs = {t["index"]: t for t in ana.get("top_zones", []) if t["score"] >= 5}
    
    for i in range(50, len(candles) - 5):
        if i < pos_end_idx:
            continue
        c = candles[i]
        atr = max(1.2, c.get("atr", 2.0))
        if commodity == "ZC" and atr < 1.40:
            continue
        if commodity == "ZW" and atr < 2.05:
            continue
            
        ema21 = c["ema21"]
        ema50 = c["ema50"]
        ema21_prev = candles[i-3]["ema21"]
        ema50_prev = candles[i-5]["ema50"]
        rsi = c.get("rsi", 50.0)
        hour_vn = int(c["time"][11:13])
        
        recent_20 = candles[max(0, i-20):i]
        low_20 = min(x["low"] for x in recent_20)
        high_20 = max(x["high"] for x in recent_20)
        
        mode = None # "SWING" or "SCALP"
        side = None
        swing_ref = 0.0
        tag = ""
        reason_str = ""
        
        # ƯU TIÊN 1: Tín hiệu SWING Đỉnh/Đáy Gần Nhất ($400 - $500) khi biên độ ATR đủ lớn hoặc có SMC Zone 5★
        is_swing_vol = (commodity == "ZW" and atr >= 2.4) or (commodity == "ZC" and atr >= 1.65)
        bz = bzs.get(i - 3)
        tz = tzs.get(i - 3)
        
        if bz and c["close"] > ema21 and ema21 >= ema50 - 0.4 * atr and c["close"] > c["open"] and c["low"] >= bz["price"] - 0.2 * atr:
            mode = "SWING"; side = "MUA"; swing_ref = bz["price"]; tag = "M3 Bắt Đáy"
            reason_str = f"[Hybrid Swing $400-$500] Bắt Đáy SMC {bz['score']}/8★ ({swing_ref:.2f}): " + ", ".join(bz.get("factors", [])[:2])
        elif tz and c["close"] < ema21 and ema21 <= ema50 + 0.4 * atr and c["close"] < c["open"] and c["high"] <= tz["price"] + 0.2 * atr:
            mode = "SWING"; side = "BÁN"; swing_ref = tz["price"]; tag = "M3 Bắt Đỉnh"
            reason_str = f"[Hybrid Swing $400-$500] Bắt Đỉnh SMC {tz['score']}/8★ ({swing_ref:.2f}): " + ", ".join(tz.get("factors", [])[:2])
        elif is_swing_vol:
            if ema21 > ema50 and ema21 > ema21_prev and ema50 >= ema50_prev and c["close"] > ema21 and c["close"] > c["open"]:
                if c["low"] <= ema21 + 0.3 * atr and c["low"] >= low_20 and 46 <= rsi <= 64:
                    if (c["close"] - c["low"]) >= 0.60 * (c["high"] - c["low"] + 0.01):
                        mode = "SWING"; side = "MUA"; swing_ref = min(c["low"], ema50); tag = "M3 Swing"
                        reason_str = f"[Hybrid Swing $400-$500] Đáy Gần Nhất ({swing_ref:.2f}) đồng thuận xu hướng tăng mạnh (ATR {atr:.2f})."
            elif ema21 < ema50 and ema21 < ema21_prev and ema50 <= ema50_prev and c["close"] < ema21 and c["close"] < c["open"]:
                if c["high"] >= ema21 - 0.3 * atr and c["high"] <= high_20 and 36 <= rsi <= 54:
                    if (c["high"] - c["close"]) >= 0.60 * (c["high"] - c["low"] + 0.01):
                        mode = "SWING"; side = "BÁN"; swing_ref = max(c["high"], ema50); tag = "M3 Swing"
                        reason_str = f"[Hybrid Swing $400-$500] Đỉnh Gần Nhất ({swing_ref:.2f}) đồng thuận xu hướng giảm mạnh (ATR {atr:.2f})."
                        
        # ƯU TIÊN 2: Nếu không phải pha Swing lớn -> Đánh SCALP INTRADAY ($200) trong phiên (14h - 22h)
        if not mode and (14 <= hour_vn <= 22):
            if ema21 > ema50 and ema21 > ema21_prev and ema50 >= ema50_prev and c["close"] > ema21 and c["close"] > c["open"]:
                if c["low"] <= ema21 + 0.45 * atr and 48 <= rsi <= 66:
                    if (c["close"] - c["low"]) >= 0.55 * (c["high"] - c["low"] + 0.01):
                        mode = "SCALP"; side = "MUA"; tag = "M3 Scalp"
                        reason_str = f"[Hybrid Scalp Intraday $200] Thuận sóng tăng EMA21 ({ema21:.2f}) > EMA50 ({ema50:.2f}) trong phiên, không giữ qua đêm."
            elif ema21 < ema50 and ema21 < ema21_prev and ema50 <= ema50_prev and c["close"] < ema21 and c["close"] < c["open"]:
                if c["high"] >= ema21 - 0.45 * atr and 34 <= rsi <= 52:
                    if (c["high"] - c["close"]) >= 0.55 * (c["high"] - c["low"] + 0.01):
                        mode = "SCALP"; side = "BÁN"; tag = "M3 Scalp"
                        reason_str = f"[Hybrid Scalp Intraday $200] Thuận sóng giảm EMA21 ({ema21:.2f}) < EMA50 ({ema50:.2f}) trong phiên, không giữ qua đêm."
                        
        if not mode or not side:
            continue
            
        if mode == "SWING":
            tp1_pts, tp2_pts, tp3_pts = 8.0, 9.0, 10.0 # $400 - $500 USD
            be_trigger = 5.0 if commodity == "ZW" else 4.5
            pullback_offset = 0.60 * atr if commodity == "ZW" else 0.65 * atr
            if side == "MUA":
                entry = round(max(swing_ref + 0.2 * atr, c["close"] - pullback_offset), 2)
                sl_dist = min(9.2 if commodity == "ZW" else 7.5, max(6.2, round(2.6 * atr, 2)))
                sl = round(entry - sl_dist, 2)
            else:
                entry = round(min(swing_ref - 0.2 * atr, c["close"] + pullback_offset), 2)
                sl_dist = min(9.2 if commodity == "ZW" else 7.5, max(6.2, round(2.6 * atr, 2)))
                sl = round(entry + sl_dist, 2)
            wait_bars = 12
            max_hold = 120
            method_lbl = "M3 (Hybrid: Swing $400-$500)"
        else: # SCALP INTRADAY ($200)
            tp1_pts, tp2_pts, tp3_pts = 4.0, 4.5, 5.0  # $200 - $250 USD
            be_trigger = 2.6 if commodity == "ZW" else 2.4
            pullback_offset = 0.45 * atr if commodity == "ZW" else 0.40 * atr
            if side == "MUA":
                entry = round(max(ema21 - 0.1 * atr, c["close"] - pullback_offset), 2)
                sl_dist = min(5.0 if commodity == "ZW" else 4.2, max(3.6, round(1.8 * atr, 2)))
                sl = round(entry - sl_dist, 2)
            else:
                entry = round(min(ema21 + 0.1 * atr, c["close"] + pullback_offset), 2)
                sl_dist = min(5.0 if commodity == "ZW" else 4.2, max(3.6, round(1.8 * atr, 2)))
                sl = round(entry + sl_dist, 2)
            wait_bars = 4
            max_hold = 9
            method_lbl = "M3 (Hybrid: Scalp $200)"
            
        risk = round(abs(entry - sl), 2)
        if side == "MUA":
            tp1 = round(entry + tp1_pts, 2); tp2 = round(entry + tp2_pts, 2); tp3 = round(entry + tp3_pts, 2)
        else:
            tp1 = round(entry - tp1_pts, 2); tp2 = round(entry - tp2_pts, 2); tp3 = round(entry - tp3_pts, 2)
            
        filled = False
        fill_idx = 0
        for j in range(i + 1, min(i + 1 + wait_bars, len(candles))):
            if side == "MUA" and candles[j]["low"] <= entry:
                if candles[j]["open"] > sl:
                    filled = True; fill_idx = j; break
            elif side == "BÁN" and candles[j]["high"] >= entry:
                if candles[j]["open"] < sl:
                    filled = True; fill_idx = j; break
                    
        if not filled:
            continue
            
        end_bar = min(fill_idx + max_hold, len(candles))
        res = "ENTRY"; exit_p = entry; pnl = 0.0; hit_be = False
        hit_tp1_time = None
        exit_idx = end_bar - 1
        exit_time = candles[exit_idx]["time"]
        exit_desc = ""
        
        for k in range(fill_idx, end_bar):
            ck = candles[k]
            cur_sl = entry if hit_be else sl
            
            if k == fill_idx:
                if side == "MUA":
                    if ck["close"] >= tp1:
                        res = "TP1"; exit_p = tp1; pnl = round(tp1_pts * MULTIPLIER, 2)
                        hit_tp1_time = ck["time"]; exit_idx = k; exit_time = ck["time"]; pos_end_idx = k + 3
                        exit_desc = f"Đạt ngay mục tiêu chốt lời {mode} TP1 ({tp1} • +${pnl:,.0f} USD)."
                        break
                    elif ck["low"] <= sl and ck["close"] < entry:
                        res = "SL"; exit_p = sl; pnl = round((sl - entry) * MULTIPLIER, 2)
                        exit_idx = k; exit_time = ck["time"]; pos_end_idx = k + 4
                        exit_desc = f"Giá chạm mức cắt lỗ SL ({sl}) — Lỗ {abs(sl - entry):.2f} pts."
                        break
                    elif ck["close"] >= entry + be_trigger:
                        hit_be = True; hit_tp1_time = ck["time"]
                else:
                    if ck["close"] <= tp1:
                        res = "TP1"; exit_p = tp1; pnl = round(tp1_pts * MULTIPLIER, 2)
                        hit_tp1_time = ck["time"]; exit_idx = k; exit_time = ck["time"]; pos_end_idx = k + 3
                        exit_desc = f"Đạt ngay mục tiêu chốt lời {mode} TP1 ({tp1} • +${pnl:,.0f} USD)."
                        break
                    elif ck["high"] >= sl and ck["close"] > entry:
                        res = "SL"; exit_p = sl; pnl = round((entry - sl) * MULTIPLIER, 2)
                        exit_idx = k; exit_time = ck["time"]; pos_end_idx = k + 4
                        exit_desc = f"Giá chạm mức cắt lỗ SL ({sl}) — Lỗ {abs(entry - sl):.2f} pts."
                        break
                    elif ck["close"] <= entry - be_trigger:
                        hit_be = True; hit_tp1_time = ck["time"]
                continue
                
            if side == "MUA":
                if ck["high"] >= tp1:
                    if ck["high"] >= tp3 and ck["close"] >= tp2: res = "TP3"; exit_p = tp3
                    elif ck["high"] >= tp2 and ck["close"] >= tp1: res = "TP2"; exit_p = tp2
                    else: res = "TP1"; exit_p = tp1
                    pnl = round((exit_p - entry) * MULTIPLIER, 2)
                    if not hit_tp1_time: hit_tp1_time = ck["time"]
                    exit_idx = k; exit_time = ck["time"]; pos_end_idx = k + 3
                    exit_desc = f"Chốt lời {mode} thành công tại {res} ({exit_p}) — Lãi +${pnl:,.0f} USD."
                    break
                if ck["low"] <= cur_sl:
                    if hit_be:
                        res = "ENTRY"; exit_p = entry; pnl = 0.0
                        exit_desc = f"Lệnh đã kích hoạt bảo vệ vốn (+${be_trigger*50:.0f}) và dời SL về {entry}. Giá hồi chạm SL hòa vốn ($0)."
                    else:
                        res = "SL"; exit_p = sl; pnl = round((sl - entry) * MULTIPLIER, 2)
                        exit_desc = f"Giá chạm mức cắt lỗ SL ({sl}) — Lỗ {abs(sl - entry):.2f} pts."
                    exit_idx = k; exit_time = ck["time"]; pos_end_idx = k + 4; break
                if ck["high"] >= entry + be_trigger and not hit_be:
                    hit_be = True; hit_tp1_time = ck["time"]
            else:
                if ck["low"] <= tp1:
                    if ck["low"] <= tp3 and ck["close"] <= tp2: res = "TP3"; exit_p = tp3
                    elif ck["low"] <= tp2 and ck["close"] <= tp1: res = "TP2"; exit_p = tp2
                    else: res = "TP1"; exit_p = tp1
                    pnl = round((entry - exit_p) * MULTIPLIER, 2)
                    if not hit_tp1_time: hit_tp1_time = ck["time"]
                    exit_idx = k; exit_time = ck["time"]; pos_end_idx = k + 3
                    exit_desc = f"Chốt lời {mode} thành công tại {res} ({exit_p}) — Lãi +${pnl:,.0f} USD."
                    break
                if ck["high"] >= cur_sl:
                    if hit_be:
                        res = "ENTRY"; exit_p = entry; pnl = 0.0
                        exit_desc = f"Lệnh đã kích hoạt bảo vệ vốn (+${be_trigger*50:.0f}) và dời SL về {entry}. Giá hồi chạm SL hòa vốn ($0)."
                    else:
                        res = "SL"; exit_p = sl; pnl = round((entry - sl) * MULTIPLIER, 2)
                        exit_desc = f"Giá chạm mức cắt lỗ SL ({sl}) — Lỗ {abs(entry - sl):.2f} pts."
                    exit_idx = k; exit_time = ck["time"]; pos_end_idx = k + 4; break
                if ck["low"] <= entry - be_trigger and not hit_be:
                    hit_be = True; hit_tp1_time = ck["time"]
        else:
            exit_idx = end_bar - 1
            ck = candles[exit_idx]
            exit_time = ck["time"]
            is_currently_open = (end_bar == len(candles) and (end_bar - 1 - fill_idx < max_hold))
            if is_currently_open:
                res = "ĐANG MỞ"
                exit_p = round(candles[-1]["close"], 2)
                cur_diff = (exit_p - entry) if side == "MUA" else (entry - exit_p)
                pnl = round(cur_diff * MULTIPLIER, 2)
                exit_time = "Đang chạy..."
                exit_desc = f"Vị thế Hybrid ({mode}) đang hoạt động ở nến mới nhất ({candles[-1]['time']}). Giá hiện tại: {exit_p}. {'Đã dời SL về hòa vốn ' + str(entry) if hit_be else 'SL đang đặt tại ' + str(sl)}."
            else:
                exit_p = round(ck["close"], 2)
                diff = (exit_p - entry) if side == "MUA" else (entry - exit_p)
                win_cut = 6.5 if mode == "SWING" else 2.5
                loss_cut = -4.0 if mode == "SWING" else -2.5
                if hit_be and diff <= 0:
                    res = "ENTRY"; exit_p = entry; pnl = 0.0
                    exit_desc = f"Hết thời gian giữ lệnh {mode}: Đóng lệnh bảo toàn vốn ($0)."
                elif diff >= win_cut:
                    res = "TP1"; pnl = round(diff * MULTIPLIER, 2)
                    exit_desc = f"Hết thời gian giữ lệnh {mode}: Chốt lời +${pnl:,.0f} USD ({diff:+.2f} pts)."
                elif diff <= loss_cut:
                    res = "SL"; pnl = round(diff * MULTIPLIER, 2)
                    exit_desc = f"Hết thời gian giữ lệnh {mode}: Tất toán vị thế ({diff:+.2f} pts)."
                else:
                    res = "ENTRY"; exit_p = entry; pnl = 0.0
                    exit_desc = f"Hết thời gian giữ lệnh {mode} quanh vùng hòa vốn ($0)."
            pos_end_idx = end_bar
            
        diff_pts = round(pnl / MULTIPLIER, 2) if res != "ENTRY" else 0.0
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
            "method": method_lbl,
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
            "tag": tag,
            "reason": reason_str,
            "exit_desc": exit_desc
        })
    return trades


def compute_metrics(trades: list, days_filter = None) -> dict:
    """Tính các chỉ số KPI: Tổng PnL, Win Rate, Tỷ lệ đạt TP1/Dời BE, Tổng lệnh, Max Drawdown, ROI trên 10k USD."""
    if not trades:
        return {
            "total_pnl": 0.0, "win_rate": 0.0, "tp1_reach_rate": 0.0, "tp1_reach_trades": 0,
            "total_trades": 0, "closed_trades": 0,
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
    
    # Tỷ lệ lệnh đạt mốc TP1 / kích hoạt dời SL về Hòa vốn (Đánh giá chất lượng điểm Entry):
    # Bao gồm tất cả lệnh Thắng (TP1/TP2/TP3) + các lệnh Hòa vốn/Đang mở đã từng chạm mốc kích hoạt BE (hit_tp1_time)
    tp1_reach_list = [
        t for t in filtered
        if t["result"] in ["TP1", "TP2", "TP3"] or bool(t.get("hit_tp1_time")) or (t["result"] == "ENTRY" and "dời SL về" in str(t.get("exit_desc", "")))
    ]
    tp1_reach_trades = len(tp1_reach_list)
    tp1_reach_rate = round((tp1_reach_trades / closed_trades * 100), 1) if closed_trades > 0 else 0.0
    
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
        "tp1_reach_rate": tp1_reach_rate,
        "tp1_reach_trades": tp1_reach_trades,
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
    RADAR ĐIỂM VÀO LỆNH TƯƠNG LAI (UPCOMING SETUPS) - 3 PHƯƠNG PHÁP MỚI:
      - M1 (Scalp / Intraday): Đánh trong phiên (14h-22h), không giữ qua đêm, mục tiêu $200 USD (+4.0 pts).
      - M2 (Swing Đỉnh / Đáy Gần Nhất): Đón tại Đỉnh/Đáy gần nhất (SMC Zone >= 5★), giữ vài ngày, mục tiêu $400-$500 USD (+8.0 - +10.0 pts).
      - M3 (Chiến Lược Hybrid): Phối hợp linh hoạt theo trạng thái thị trường (Ưu tiên Swing $400-$500 khi gặp Đỉnh/Đáy; đánh Scalp $200 khi giữa sóng).
      - Con trỏ Giá M5 Realtime: Chỉ dùng đo khoảng cách thực chiến (Live Distance) và cập nhật trạng thái Sẵn sàng / Chờ hồi.
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
        h1_time = str(c_last.get("time", ""))
        h1_close = round(float(c_last["close"]), 2)
        atr = round(float(c_last.get("atr", 3.0)), 2)
        rsi = round(float(c_last.get("rsi", 50.0)), 1)
        ema21 = round(float(c_last.get("ema21", h1_close)), 2)
        ema50 = round(float(c_last.get("ema50", h1_close)), 2)
        
        ana = ict_engine.analyze(candles)
        trend = ana.get("trend", "neutral")
        
        # Con trỏ giá M5 Realtime
        m5_live = tv_webhook_client.get_latest_m5_price(comm)
        cur_p = round(float(m5_live["close"]), 2) if m5_live and m5_live.get("close") else h1_close
        m5_high = round(float(m5_live["high"]), 2) if m5_live and m5_live.get("high") else cur_p
        m5_low = round(float(m5_live["low"]), 2) if m5_live and m5_live.get("low") else cur_p
        
        recent_20 = candles[max(0, len(candles)-20):]
        low_20 = min(x["low"] for x in recent_20)
        high_20 = max(x["high"] for x in recent_20)

        # ── 1. KỊCH BẢN M1: SCALP / INTRADAY ($200 USD • KHÔNG GIỮ QUA ĐÊM) ────────
        pullback_offset_m1 = 0.45 * atr if comm == "ZW" else 0.40 * atr
        sl_dist_m1 = min(5.0 if comm == "ZW" else 4.2, max(3.6, round(1.8 * atr, 2)))
        
        if ema21 <= ema50 or trend == "bearish":
            m1_side = "BÁN"
            m1_entry = round(min(ema21 + 0.1 * atr, h1_close + pullback_offset_m1), 2)
            m1_sl = round(m1_entry + sl_dist_m1, 2)
            m1_risk = round(m1_sl - m1_entry, 2)
            m1_tp1 = round(m1_entry - 4.0, 2)   # +$200 USD
            m1_tp2 = round(m1_entry - 4.5, 2)   # +$225 USD
            m1_tp3 = round(m1_entry - 5.0, 2)   # +$250 USD
            m1_cond = f"[M1 Scalp Intraday] Thuận xu hướng GIẢM (EMA21 {ema21:.2f} <= EMA50 {ema50:.2f}, RSI {rsi:.1f}). Đánh ngắn trong phiên (14h-22h) mục tiêu $200 USD, không giữ qua đêm."
            m1_hint = f"[Scalp Intraday — Không giữ qua đêm] Đặt Limit BÁN @ {m1_entry:.2f}. Mục tiêu chốt lời: TP1 {m1_tp1:.2f} (+$200) -> TP3 {m1_tp3:.2f} (+$250). SL: {m1_sl:.2f}. Dời BE khi lãi đạt +$125."
        else:
            m1_side = "MUA"
            m1_entry = round(max(ema21 - 0.1 * atr, h1_close - pullback_offset_m1), 2)
            m1_sl = round(m1_entry - sl_dist_m1, 2)
            m1_risk = round(m1_entry - m1_sl, 2)
            m1_tp1 = round(m1_entry + 4.0, 2)   # +$200 USD
            m1_tp2 = round(m1_entry + 4.5, 2)   # +$225 USD
            m1_tp3 = round(m1_entry + 5.0, 2)   # +$250 USD
            m1_cond = f"[M1 Scalp Intraday] Thuận xu hướng TĂNG (EMA21 {ema21:.2f} > EMA50 {ema50:.2f}, RSI {rsi:.1f}). Đánh ngắn trong phiên (14h-22h) mục tiêu $200 USD, không giữ qua đêm."
            m1_hint = f"[Scalp Intraday — Không giữ qua đêm] Đặt Limit MUA @ {m1_entry:.2f}. Mục tiêu chốt lời: TP1 {m1_tp1:.2f} (+$200) -> TP3 {m1_tp3:.2f} (+$250). SL: {m1_sl:.2f}. Dời BE khi lãi đạt +$125."
            
        m1_dist = round(abs(cur_p - m1_entry), 2)
        m1_touched = (m5_low <= m1_entry <= m5_high)
        m1_status = f"⚡ SẴN SÀNG ({m1_dist:.2f} pts)" if (m1_touched or m1_dist <= 0.8 * atr) else f"⏳ ĐANG CHỜ HỒI ({m1_dist:.2f} pts)"
        
        radar.append({
            "commodity": comm,
            "product": prod,
            "method": "M1 (Scalp Intraday • Mục Tiêu $200)",
            "side": m1_side,
            "current_price": cur_p,
            "entry_target": m1_entry,
            "distance_pts": m1_dist,
            "sl_price": m1_sl,
            "tp1_price": m1_tp1,
            "tp2_price": m1_tp2,
            "tp3_price": m1_tp3,
            "risk_pts": m1_risk,
            "risk_usd": round(m1_risk * MULTIPLIER, 2),
            "rr": f"1 : {round(4.0/max(0.1, m1_risk), 1)}",
            "status": m1_status,
            "structure_time": h1_time,
            "latest_h1_time": h1_time,
            "m3_confluence": False,
            "action_hint": m1_hint,
            "condition": m1_cond,
            "priority": "Cao" if m1_dist <= atr else "Trung bình"
        })

        # ── 2. KỊCH BẢN M2: SWING ĐỈNH / ĐÁY GẦN NHẤT ($400 - $500 USD • GIỮ VÀI NGÀY) ─
        min_opposing_dist = 7.0 if comm == "ZW" else 4.0
        valid_tzs = [z for z in ana.get("top_zones", []) if z.get("score", 0) >= 5 and z.get("price", 0) >= cur_p - 0.3 * atr]
        valid_bzs = [z for z in ana.get("bottom_zones", []) if z.get("score", 0) >= 5 and z.get("price", 0) <= cur_p + 0.3 * atr]

        chosen_tz = valid_tzs[-1] if valid_tzs else None
        chosen_bz = valid_bzs[-1] if valid_bzs else None

        if chosen_tz and chosen_bz:
            if (chosen_tz["price"] - chosen_bz["price"]) < min_opposing_dist:
                if trend == "bearish":
                    chosen_bz = None
                else:
                    chosen_tz = None

        sl_dist_m2 = min(9.2 if comm == "ZW" else 7.5, max(6.2, round(2.6 * atr, 2)))
        pullback_offset_m2 = 0.60 * atr if comm == "ZW" else 0.65 * atr

        if chosen_tz:
            m2_side = "BÁN"
            m2_entry = round(chosen_tz["price"], 2)
            m2_sc = chosen_tz.get("score", 5)
            m2_idx = chosen_tz.get("index", len(candles) - 1)
            m2_time = str(candles[m2_idx].get("time", h1_time)) if 0 <= m2_idx < len(candles) else h1_time
            m2_sl = round(m2_entry + sl_dist_m2, 2)
            m2_risk = round(m2_sl - m2_entry, 2)
            m2_tp1 = round(m2_entry - 8.0, 2)   # +$400 USD
            m2_tp2 = round(m2_entry - 9.0, 2)   # +$450 USD
            m2_tp3 = round(m2_entry - 10.0, 2)  # +$500 USD
            m2_name = f"M2 (Swing Đỉnh Gần Nhất {m2_sc}★ • $400-$500)"
            m2_cond = f"[M2 Swing Đỉnh {m2_sc}/8★] Vùng Đỉnh gần nhất tại {m2_entry:.2f}. " + ", ".join(chosen_tz.get("factors", [])[:2])
            m2_hint = f"[Swing Đỉnh Gần Nhất — Giữ vài ngày] Đỉnh cố định tại {m2_entry:.2f}. Canh BÁN giữ lệnh vài ngày hướng tới mục tiêu lớn: TP1 {m2_tp1:.2f} (+$400) -> TP3 {m2_tp3:.2f} (+$500). SL: {m2_sl:.2f}. Dời BE khi lãi đạt +$250."
        elif chosen_bz:
            m2_side = "MUA"
            m2_entry = round(chosen_bz["price"], 2)
            m2_sc = chosen_bz.get("score", 5)
            m2_idx = chosen_bz.get("index", len(candles) - 1)
            m2_time = str(candles[m2_idx].get("time", h1_time)) if 0 <= m2_idx < len(candles) else h1_time
            m2_sl = round(m2_entry - sl_dist_m2, 2)
            m2_risk = round(m2_entry - m2_sl, 2)
            m2_tp1 = round(m2_entry + 8.0, 2)   # +$400 USD
            m2_tp2 = round(m2_entry + 9.0, 2)   # +$450 USD
            m2_tp3 = round(m2_entry + 10.0, 2)  # +$500 USD
            m2_name = f"M2 (Swing Đáy Gần Nhất {m2_sc}★ • $400-$500)"
            m2_cond = f"[M2 Swing Đáy {m2_sc}/8★] Vùng Đáy gần nhất tại {m2_entry:.2f}. " + ", ".join(chosen_bz.get("factors", [])[:2])
            m2_hint = f"[Swing Đáy Gần Nhất — Giữ vài ngày] Đáy cố định tại {m2_entry:.2f}. Canh MUA giữ lệnh vài ngày hướng tới mục tiêu lớn: TP1 {m2_tp1:.2f} (+$400) -> TP3 {m2_tp3:.2f} (+$500). SL: {m2_sl:.2f}. Dời BE khi lãi đạt +$250."
        else:
            # Fallback lấy Swing High / Low 20 nến gần nhất
            if trend == "bearish":
                m2_side = "BÁN"
                m2_entry = round(min(high_20 - 0.2 * atr, h1_close + pullback_offset_m2), 2)
                m2_time = h1_time
                m2_sl = round(m2_entry + sl_dist_m2, 2)
                m2_risk = round(m2_sl - m2_entry, 2)
                m2_tp1 = round(m2_entry - 8.0, 2)
                m2_tp2 = round(m2_entry - 9.0, 2)
                m2_tp3 = round(m2_entry - 10.0, 2)
                m2_name = "M2 (Swing Đỉnh 20 Nến • $400-$500)"
                m2_cond = f"[M2 Swing Đỉnh 20 nến] Vùng Đỉnh gần nhất tại {high_20:.2f}. Sóng giảm trung hạn, giữ lệnh vài ngày mục tiêu $400-$500."
                m2_hint = f"[Swing Đỉnh — Giữ vài ngày] Canh BÁN tại {m2_entry:.2f}. TP1: {m2_tp1:.2f} (+$400), TP3: {m2_tp3:.2f} (+$500). SL: {m2_sl:.2f}."
            else:
                m2_side = "MUA"
                m2_entry = round(max(low_20 + 0.2 * atr, h1_close - pullback_offset_m2), 2)
                m2_time = h1_time
                m2_sl = round(m2_entry - sl_dist_m2, 2)
                m2_risk = round(m2_entry - m2_sl, 2)
                m2_tp1 = round(m2_entry + 8.0, 2)
                m2_tp2 = round(m2_entry + 9.0, 2)
                m2_tp3 = round(m2_entry + 10.0, 2)
                m2_name = "M2 (Swing Đáy 20 Nến • $400-$500)"
                m2_cond = f"[M2 Swing Đáy 20 nến] Vùng Đáy gần nhất tại {low_20:.2f}. Sóng tăng trung hạn, giữ lệnh vài ngày mục tiêu $400-$500."
                m2_hint = f"[Swing Đáy — Giữ vài ngày] Canh MUA tại {m2_entry:.2f}. TP1: {m2_tp1:.2f} (+$400), TP3: {m2_tp3:.2f} (+$500). SL: {m2_sl:.2f}."

        m2_dist = round(abs(cur_p - m2_entry), 2)
        m2_status = f"⚡ SẴN SÀNG ({m2_dist:.2f} pts)" if m2_dist <= atr else f"🔍 THEO DÕI VÙNG SWING ({m2_dist:.2f} pts)"

        radar.append({
            "commodity": comm,
            "product": prod,
            "method": m2_name,
            "side": m2_side,
            "current_price": cur_p,
            "entry_target": m2_entry,
            "distance_pts": m2_dist,
            "sl_price": m2_sl,
            "tp1_price": m2_tp1,
            "tp2_price": m2_tp2,
            "tp3_price": m2_tp3,
            "risk_pts": m2_risk,
            "risk_usd": round(m2_risk * MULTIPLIER, 2),
            "rr": f"1 : {round(10.0/max(0.1, m2_risk), 1)}",
            "status": m2_status,
            "structure_time": m2_time,
            "latest_h1_time": h1_time,
            "m3_confluence": True,
            "action_hint": m2_hint,
            "condition": m2_cond,
            "priority": "Cao" if m2_dist <= atr else "Trung bình"
        })

        # ── 3. KỊCH BẢN M3: CHIẾN LƯỢC HYBRID (PHỐI HỢP SCALP $200 + SWING $400-$500) ─
        is_swing_vol = (comm == "ZW" and atr >= 2.4) or (comm == "ZC" and atr >= 1.65)
        has_strong_smc = bool(chosen_tz or chosen_bz)
        
        if has_strong_smc or is_swing_vol:
            # M3 ưu tiên đi lệnh Swing $400-$500 khi gặp vùng Đỉnh/Đáy hoặc biên độ rộng
            m3_side = m2_side
            m3_entry = m2_entry
            m3_sl = m2_sl
            m3_risk = m2_risk
            m3_tp1 = m2_tp1
            m3_tp2 = m2_tp2
            m3_tp3 = m2_tp3
            m3_dist = m2_dist
            m3_method = "M3 (Hybrid: Swing $400-$500)"
            m3_cond = f"[M3 Hybrid • Chế độ Swing] Biên độ ATR ({atr:.2f}) đủ lớn để ăn sóng dài $400-$500. Ưu tiên đón tại Đỉnh/Đáy gần nhất, giữ lệnh vài ngày."
            m3_hint = f"[Hybrid Swing — Giữ vài ngày] Đặt Limit {m3_side} @ {m3_entry:.2f}. Mục tiêu: TP1 {m3_tp1:.2f} (+$400) -> TP3 {m3_tp3:.2f} (+$500). SL: {m3_sl:.2f}."
            m3_status = m2_status
        else:
            # M3 đi lệnh Scalp Intraday $200 khi sóng đi giữa chu kỳ
            m3_side = m1_side
            m3_entry = m1_entry
            m3_sl = m1_sl
            m3_risk = m1_risk
            m3_tp1 = m1_tp1
            m3_tp2 = m1_tp2
            m3_tp3 = m1_tp3
            m3_dist = m1_dist
            m3_method = "M3 (Hybrid: Scalp $200)"
            m3_cond = f"[M3 Hybrid • Chế độ Scalp] Thị trường vận động giữa chu kỳ sóng. Kích hoạt lệnh Scalp Intraday chốt nhanh $200 USD trong phiên, không giữ qua đêm."
            m3_hint = f"[Hybrid Scalp — Trong ngày] Đặt Limit {m3_side} @ {m3_entry:.2f}. Mục tiêu: TP1 {m3_tp1:.2f} (+$200) -> TP3 {m3_tp3:.2f} (+$250). SL: {m3_sl:.2f}."
            m3_status = m1_status

        radar.append({
            "commodity": comm,
            "product": prod,
            "method": m3_method,
            "side": m3_side,
            "current_price": cur_p,
            "entry_target": m3_entry,
            "distance_pts": m3_dist,
            "sl_price": m3_sl,
            "tp1_price": m3_tp1,
            "tp2_price": m3_tp2,
            "tp3_price": m3_tp3,
            "risk_pts": m3_risk,
            "risk_usd": round(m3_risk * MULTIPLIER, 2),
            "rr": f"1 : {round((10.0 if 'Swing' in m3_method else 4.0)/max(0.1, m3_risk), 1)}",
            "status": m3_status,
            "structure_time": h1_time,
            "latest_h1_time": h1_time,
            "m3_confluence": True,
            "action_hint": m3_hint,
            "condition": m3_cond,
            "priority": "Cao" if m3_dist <= atr else "Trung bình"
        })

    # Sắp xếp theo mức độ sẵn sàng: Sẵn sàng lên đầu, khoảng cách gần lên trước
    radar = sorted(radar, key=lambda x: (0 if "SẴN SÀNG" in x["status"] else 1, x["distance_pts"]))
    return radar


def run_full_backtest(force_download: bool = False) -> dict:
    """Chạy toàn bộ backtest toàn bộ lịch sử nến H1 cho 3 phương pháp trên cả ZC và ZW."""
    print("=" * 60)
    print("  KHỞI ĐỘNG LIVE SIGNAL BACKTEST (3 PHƯƠNG PHÁP - TOÀN BỘ LỊCH SỬ & YTD)")
    print("=" * 60)
    
    zc_candles = fetch_or_load_candles("ZC", force_download=force_download)
    zw_candles = fetch_or_load_candles("ZW", force_download=force_download)
    
    # ── Phương pháp 1 (Scalp / Intraday $200 USD - Đánh trong ngày, không giữ qua đêm) ──
    print("▶ Chạy Phương pháp 1 (Scalp / Intraday • Mục tiêu $200 USD)...")
    m1_zc = apply_m5_live_status_to_trades(simulate_method_1(zc_candles, "ZC"), "ZC")
    m1_zw = apply_m5_live_status_to_trades(simulate_method_1(zw_candles, "ZW"), "ZW")
    m1_all = sorted(m1_zc + m1_zw, key=lambda x: x["time"], reverse=True)
    
    # ── Phương pháp 2 (Swing Đỉnh / Đáy Gần Nhất $400-$500 USD - Giữ lệnh vài ngày) ──
    print("▶ Chạy Phương pháp 2 (Swing Đỉnh / Đáy Gần Nhất • Mục tiêu $400-$500 USD)...")
    m2_zc = apply_m5_live_status_to_trades(simulate_method_2(zc_candles, "ZC"), "ZC")
    m2_zw = apply_m5_live_status_to_trades(simulate_method_2(zw_candles, "ZW"), "ZW")
    m2_all = sorted(m2_zc + m2_zw, key=lambda x: x["time"], reverse=True)

    # ── Phương pháp 3 (Hybrid: Phối hợp Scalp $200 + Swing $400-$500) ──
    print("▶ Chạy Phương pháp 3 (Chiến Lược Hybrid Kết Hợp Scalp $200 + Swing $400-$500)...")
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
            "name": "Phương Pháp 1: Scalp / Intraday (Mục Tiêu $200 USD)",
            "type": "Scalp / Intraday (Đánh trong ngày • Không giữ qua đêm)",
            "description": "Giao dịch ngắn hạn thuận xu hướng EMA 21-50 trong giờ sôi động (14h-22h), chốt lời nhanh $200 USD/giao dịch và tất toán trong ngày.",
            "stats_all":  {k: v for k, v in m1_stats_all.items() if k != "filtered_trades"},
            "stats_ytd":  {k: v for k, v in m1_stats_ytd.items() if k != "filtered_trades"},
            "stats_365d": {k: v for k, v in m1_stats_365d.items() if k != "filtered_trades"},
            "stats_90d":  {k: v for k, v in m1_stats_90d.items() if k != "filtered_trades"},
            "stats_30d":  {k: v for k, v in m1_stats_30d.items() if k != "filtered_trades"},
            "stats_7d":   {k: v for k, v in m1_stats_7d.items() if k != "filtered_trades"},
            "trades": m1_all
        },
        "method_2": {
            "name": "Phương Pháp 2: Swing Đỉnh / Đáy Gần Nhất ($400 - $500 USD)",
            "type": "Swing Trading (Giữ lệnh vài ngày • Ăn sóng lớn)",
            "description": "Đón sóng tại cấu trúc Đỉnh / Đáy gần nhất (SMC Zone >= 5 sao & Higher Low / Lower High), treo giữ lệnh vài ngày để đạt mục tiêu $400 - $500 USD.",
            "stats_all":  {k: v for k, v in m2_stats_all.items() if k != "filtered_trades"},
            "stats_ytd":  {k: v for k, v in m2_stats_ytd.items() if k != "filtered_trades"},
            "stats_365d": {k: v for k, v in m2_stats_365d.items() if k != "filtered_trades"},
            "stats_90d":  {k: v for k, v in m2_stats_90d.items() if k != "filtered_trades"},
            "stats_30d":  {k: v for k, v in m2_stats_30d.items() if k != "filtered_trades"},
            "stats_7d":   {k: v for k, v in m2_stats_7d.items() if k != "filtered_trades"},
            "trades": m2_all
        },
        "method_3": {
            "name": "Phương Pháp 3: Chiến Lược Hybrid (Scalp $200 + Swing $400-$500)",
            "type": "Hybrid Synergy (Kết hợp Lệnh Ngắn Trong Ngày & Sóng Lớn Swing)",
            "description": "Ưu tiên bắt sóng lớn Swing ($400-$500, giữ vài ngày) tại Đỉnh/Đáy gần nhất khi biên độ rộng, đồng thời đánh lệnh ngắn Scalp ($200, đóng trong ngày) khi sóng đi giữa chu kỳ.",
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
