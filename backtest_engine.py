"""
backtest_engine.py — Mô phỏng Live Signal & Kiểm thử hiệu suất 90 ngày (Backtest Engine)
========================================================================================
Mô phỏng khớp lệnh thực tế chuẩn CQG cho 2 sản phẩm:
  - ZWAZ26 (Lúa Mì CBOT kỳ hạn Dec 2026) — Hệ số nhân 50 ($50/cent)
  - ZCEZ26 (Ngô CBOT kỳ hạn Dec 2026)    — Hệ số nhân 50 ($50/cent)

So sánh 2 phương pháp giao dịch:
  - Phương pháp 1: ICT MSS + Pullback EMA 21-50 (Thuận xu hướng SMC)
  - Phương pháp 2: FVG + Bắt Đáy / Đỉnh SMC Zone (Đảo chiều vùng cực trị 4-5 sao)
"""

import sys
import os
import json
import datetime
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
            # Nếu file được tạo trong vòng 4 tiếng thì tái sử dụng
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
                # Fallback sang file active_H1 hiện có
                fallback_file = DATA_OUTPUT / f"{commodity_code}_active_H1.csv"
                if fallback_file.exists():
                    df = pd.read_csv(fallback_file)

    if df is None or df.empty:
        return []

    # Format sang định dạng cho ict_engine
    df_ict = df.rename(columns={
        "Time": "time", "Open": "open", "High": "high", "Low": "low", "Close": "close",
        "EMA_21": "ema21", "EMA_50": "ema50", "RSI": "rsi", "ATR": "atr",
        "S1": "s1", "S2": "s2", "R1": "r1", "R2": "r2"
    })
    return df_ict.to_dict("records")


def simulate_method_1(candles: list, commodity: str) -> list:
    """
    Phương pháp 1: ICT MSS + Pullback EMA 21-50 (Trend-Following)
    Quy tắc:
      - Quét tín hiệu khi xu hướng MSS xác nhận và setup winRate >= 70%.
      - Đặt lệnh chờ Limit tại EMA21.
      - Hạn chờ khớp: 24 bars (24 giờ).
      - TP1 = 1.0R (Dời SL về hòa vốn ENTRY).
      - TP2 = 1.5R.
      - TP3 = 2.0R.
      - SL = initial StopLoss.
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
        
        # Chỉ nhận setup chất lượng cao (winRate >= 70%)
        if setup and setup.get("winRate", 0) >= 70:
            side = "MUA" if setup["type"] == "LONG" else "BÁN"
            entry = round(candles[i]["ema21"], 2)
            sl = round(setup["stopLoss"], 2)
            risk = abs(entry - sl)
            
            # Lọc nhiễu: risk tối thiểu 2.5 cent và tối đa 16 cent
            if risk < 2.5 or risk > 16.0:
                continue
                
            tp1 = round(entry + (1.0 * risk if side == "MUA" else -1.0 * risk), 2)
            tp2 = round(entry + (1.5 * risk if side == "MUA" else -1.5 * risk), 2)
            tp3 = round(entry + (2.0 * risk if side == "MUA" else -2.0 * risk), 2)
            
            # 1. Kiểm tra khớp lệnh trong 24 giờ tiếp theo
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
                    "side": side,
                    "product": cqg_sym,
                    "commodity": commodity,
                    "method": "M1 (ICT MSS + EMA Pullback)",
                    "result": "CHƯA KHỚP",
                    "entry_price": entry,
                    "exit_price": None,
                    "multiplier": MULTIPLIER,
                    "diff_points": 0.0,
                    "pnl": 0.0,
                    "win": False,
                    "reason": setup.get("reason", "")
                })
                pos_end_idx = i + 12
                continue
                
            # 2. Lệnh đã khớp -> Theo dõi nến tiếp theo (tối đa 48 bars)
            res = "ENTRY"
            exit_p = entry
            pnl = 0.0
            hit_tp1 = False
            hit_tp2 = False
            end_bar = min(fill_idx + 48, len(candles))
            
            for k in range(fill_idx, end_bar):
                ck = candles[k]
                cur_sl = entry if hit_tp1 else sl
                
                if side == "MUA":
                    if ck["low"] <= cur_sl:
                        if hit_tp1:
                            res = "ENTRY"; exit_p = entry; pnl = 0.0
                        else:
                            res = "SL"; exit_p = sl; pnl = round((sl - entry) * MULTIPLIER, 2)
                        pos_end_idx = k + 6
                        break
                    if ck["high"] >= tp3:
                        res = "TP3"; exit_p = tp3; pnl = round((tp3 - entry) * MULTIPLIER, 2)
                        pos_end_idx = k + 6
                        break
                    elif ck["high"] >= tp2:
                        hit_tp2 = True; hit_tp1 = True
                    elif ck["high"] >= tp1:
                        hit_tp1 = True
                else: # BÁN
                    if ck["high"] >= cur_sl:
                        if hit_tp1:
                            res = "ENTRY"; exit_p = entry; pnl = 0.0
                        else:
                            res = "SL"; exit_p = sl; pnl = round((entry - sl) * MULTIPLIER, 2)
                        pos_end_idx = k + 6
                        break
                    if ck["low"] <= tp3:
                        res = "TP3"; exit_p = tp3; pnl = round((entry - tp3) * MULTIPLIER, 2)
                        pos_end_idx = k + 6
                        break
                    elif ck["low"] <= tp2:
                        hit_tp2 = True; hit_tp1 = True
                    elif ck["low"] <= tp1:
                        hit_tp1 = True
            else:
                if hit_tp2:
                    res = "TP2"; exit_p = tp2; pnl = round(abs(tp2 - entry) * MULTIPLIER, 2)
                elif hit_tp1:
                    res = "TP1"; exit_p = tp1; pnl = round(abs(tp1 - entry) * MULTIPLIER, 2)
                else:
                    res = "ENTRY"; exit_p = entry; pnl = 0.0
                pos_end_idx = end_bar
                
            diff_pts = round(abs(exit_p - entry) if res != "SL" else -abs(exit_p - entry), 2)
            trades.append({
                "date": candles[fill_idx]["time"][:10],
                "time": candles[fill_idx]["time"],
                "side": side,
                "product": cqg_sym,
                "commodity": commodity,
                "method": "M1 (ICT MSS + EMA Pullback)",
                "result": res,
                "entry_price": entry,
                "exit_price": exit_p,
                "multiplier": MULTIPLIER,
                "diff_points": diff_pts,
                "pnl": pnl,
                "win": res in ["TP1", "TP2", "TP3"],
                "reason": setup.get("reason", "")
            })
            
    return trades


def simulate_method_2(candles: list, commodity: str) -> list:
    """
    Phương pháp 2: FVG + Bắt Đáy / Đỉnh SMC Zone (Contrarian Reversal)
    Quy tắc:
      - Quét cụm đáy/đỉnh có điểm số ICT Zone >= 5 (RSI quá bán/quá mua + Sweep BSL/SSL + Cản S/R + FVG).
      - Vào lệnh tại nến xác nhận tạo đáy/đỉnh.
      - SL đặt ngoài râu nến Swing + 0.75 ATR buffer.
      - TP1 = 1.0R (Dời SL về hòa vốn), TP2 = 1.5R, TP3 = 2.0R.
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
        end_bar = min(idx + 4 + 48, len(candles))
        
        for k in range(idx + 4, end_bar):
            ck = candles[k]
            cur_sl = entry if hit_tp1 else sl
            
            if side == "MUA":
                if ck["low"] <= cur_sl:
                    if hit_tp1:
                        res = "ENTRY"; exit_p = entry; pnl = 0.0
                    else:
                        res = "SL"; exit_p = sl; pnl = round((sl - entry) * MULTIPLIER, 2)
                    pos_end_idx = k + 6; break
                if ck["high"] >= tp3:
                    res = "TP3"; exit_p = tp3; pnl = round((tp3 - entry) * MULTIPLIER, 2)
                    pos_end_idx = k + 6; break
                elif ck["high"] >= tp2:
                    hit_tp2 = True; hit_tp1 = True
                elif ck["high"] >= tp1:
                    hit_tp1 = True
            else: # BÁN
                if ck["high"] >= cur_sl:
                    if hit_tp1:
                        res = "ENTRY"; exit_p = entry; pnl = 0.0
                    else:
                        res = "SL"; exit_p = sl; pnl = round((entry - sl) * MULTIPLIER, 2)
                    pos_end_idx = k + 6; break
                if ck["low"] <= tp3:
                    res = "TP3"; exit_p = tp3; pnl = round((entry - tp3) * MULTIPLIER, 2)
                    pos_end_idx = k + 6; break
                elif ck["low"] <= tp2:
                    hit_tp2 = True; hit_tp1 = True
                elif ck["low"] <= tp1:
                    hit_tp1 = True
        else:
            if hit_tp2:
                res = "TP2"; exit_p = tp2; pnl = round(abs(tp2 - entry) * MULTIPLIER, 2)
            elif hit_tp1:
                res = "TP1"; exit_p = tp1; pnl = round(abs(tp1 - entry) * MULTIPLIER, 2)
            else:
                res = "ENTRY"; exit_p = entry; pnl = 0.0
            pos_end_idx = end_bar
            
        diff_pts = round(abs(exit_p - entry) if res != "SL" else -abs(exit_p - entry), 2)
        trades.append({
            "date": entry_c["time"][:10],
            "time": entry_c["time"],
            "side": side,
            "product": cqg_sym,
            "commodity": commodity,
            "method": "M2 (SMC Zone 5-Sao Reversal)",
            "result": res,
            "entry_price": entry,
            "exit_price": exit_p,
            "multiplier": MULTIPLIER,
            "diff_points": diff_pts,
            "pnl": pnl,
            "win": res in ["TP1", "TP2", "TP3"],
            "reason": f"SMC Zone {score}/8: " + ", ".join(factors[:2])
        })
        
    return trades


def compute_metrics(trades: list, days_filter: int = None) -> dict:
    """Tính các chỉ số KPI: Tổng PnL, Win Rate, Tổng lệnh, Max Drawdown, ROI trên 10k USD."""
    if not trades:
        return {
            "total_pnl": 0.0, "win_rate": 0.0, "total_trades": 0,
            "win_trades": 0, "loss_trades": 0, "breakeven_trades": 0, "pending_trades": 0,
            "profit_factor": 0.0, "max_drawdown": 0.0, "roi_pct": 0.0, "recommended_capital": 10000
        }
        
    # Lọc theo số ngày gần nhất
    if days_filter is not None:
        # Lấy ngày cuối cùng trong tập dữ liệu
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
        "profit_factor": profit_factor,
        "max_drawdown": round(max_dd, 2),
        "roi_pct": roi_pct,
        "recommended_capital": 10000,
        "filtered_trades": filtered
    }


def run_full_backtest(force_download: bool = False) -> dict:
    """Chạy toàn bộ backtest 90 ngày cho 2 phương pháp trên cả ZC và ZW."""
    print("=" * 60)
    print("  KHỞI ĐỘNG LIVE SIGNAL BACKTEST (90 NGÀY)")
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
    
    # Tính metrics
    m1_stats_all = compute_metrics(m1_all)
    m1_stats_30d = compute_metrics(m1_all, days_filter=30)
    m1_stats_7d  = compute_metrics(m1_all, days_filter=7)
    
    m2_stats_all = compute_metrics(m2_all)
    m2_stats_30d = compute_metrics(m2_all, days_filter=30)
    m2_stats_7d  = compute_metrics(m2_all, days_filter=7)
    
    result = {
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "period_days": 90,
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
        }
    }
    
    BACKTEST_RESULT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(BACKTEST_RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        
    print(f"✅ Đã lưu kết quả Backtest thành công vào {BACKTEST_RESULT_FILE}")
    print(f"   - M1 (30d): Lãi ${m1_stats_30d['total_pnl']:+,.2f} | Win Rate: {m1_stats_30d['win_rate']}% | Lệnh: {m1_stats_30d['total_trades']}")
    print(f"   - M2 (30d): Lãi ${m2_stats_30d['total_pnl']:+,.2f} | Win Rate: {m2_stats_30d['win_rate']}% | Lệnh: {m2_stats_30d['total_trades']}")
    return result


if __name__ == "__main__":
    run_full_backtest(force_download=True)
