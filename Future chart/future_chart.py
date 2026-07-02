# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
"""
==============================================================================
 PROJECT: FUTURE CHART - Multi-Commodity Engine (ZC, ZW, ZS)
 Version: 2.1.0 | Date: 2026-06-21
 Architecture: 3 Independent Deep-Analysis Engines, same quality as ZW v1.0
==============================================================================
"""

import json, math, random, os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Data", "output")

# ─────────────────────────────────────────────────────────────────────────────
# UTILITY
# ─────────────────────────────────────────────────────────────────────────────
def tick_round(x, tick=0.25):
    return round(x / tick) * tick

from datetime import timedelta
def get_dynamic_dates():
    today = datetime.now()
    if today.weekday() >= 4:
        days_ahead = 7 - today.weekday()
    else:
        days_ahead = -today.weekday()
    monday = today + timedelta(days=days_ahead)
    
    days_map = {}
    ordered_days = []
    for i in range(5):
        d = monday + timedelta(days=i)
        days_map[d.strftime('%d')] = d.strftime('%a %d/%m')
        ordered_days.append(d.strftime('%a %d/%m'))
    
    friday = monday + timedelta(days=4)
    forecast_week = f"{monday.strftime('%B %d')}-{friday.strftime('%d, %Y')}"
    return monday.strftime('%Y-%m-%d'), days_map, ordered_days, forecast_week

GLOBAL_MONDAY_STR, GLOBAL_DAYS_MAP, GLOBAL_ORDERED_DAYS, GLOBAL_FORECAST_WEEK = get_dynamic_dates()

def get_actual_prices(code):
    """Read real H1 closes from CSV, map to 4H session labels used in simulation."""
    import pandas as pd
    sessions_map = [
        ("07-11", range(7, 11)),
        ("11-15", range(11, 15)),
        ("15-19", range(15, 19)),
        ("19-21", range(19, 21)),
        ("21-23", range(21, 23)),
        ("23-01", list(range(23, 24)) + list(range(0, 2))),
    ]
    days_map = GLOBAL_DAYS_MAP

    path = os.path.join(DATA_DIR, f"{code}_active_H1.csv")
    if not os.path.exists(path):
        return []

    df = pd.read_csv(path)
    df['dt'] = pd.to_datetime(df['Time'])
    df = df[df['dt'] >= pd.to_datetime(GLOBAL_MONDAY_STR)].reset_index(drop=True)

    # Build lookup: (day_str, sess_label) -> avg close
    buckets = {}
    for _, row in df.iterrows():
        dt = row['dt']
        h = dt.hour
        day_str = dt.strftime("%d")
        if day_str not in days_map:
            continue
        for sess_label, hrs in sessions_map:
            if h in hrs:
                key = (day_str, sess_label)
                if key not in buckets:
                    buckets[key] = []
                buckets[key].append(float(row['Close']))
                break

    result = []
    for d_str, day_label in days_map.items():
        for sess_label, _ in sessions_map:
            key = (d_str, sess_label)
            if key in buckets:
                avg_close = sum(buckets[key]) / len(buckets[key])
                result.append({
                    "label": f"{day_label.split(' ')[0]} {sess_label}",
                    "price": tick_round(avg_close)
                })
    return result


# ─────────────────────────────────────────────────────────────────────────────
# BASE ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def get_latest_close(code):
    import pandas as pd
    path = os.path.join(DATA_DIR, f"{code}_active_H1.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    if not df.empty:
        return float(df.iloc[-1]['Close'])
    return None

class BaseFutureEngine:
    def __init__(self, code, anchor, atr_h1, rsi, ema21, ema50, s1, s2, r1, r2):
        self.code = code
        # Dynamic Anchor
        latest = get_latest_close(code)
        if latest is not None:
            self.anchor = latest
        else:
            self.anchor = anchor
            
        self.atr_h1 = atr_h1
        self.atr_4h = atr_h1 * 4.0  # Increased volatility
        self.rsi = rsi
        self.ema21 = ema21
        self.ema50 = ema50
        self.s1 = s1; self.s2 = s2; self.r1 = r1; self.r2 = r2
        self.candles = []
        self.composite_bias = 0.0
        self.candles = []
        self.composite_bias = 0.0

    def _gen_candle(self, price, move, day, sess, vol=1.0, shock=0.0):
        if "Mon " in day: day = GLOBAL_ORDERED_DAYS[0]
        elif "Tue " in day: day = GLOBAL_ORDERED_DAYS[1]
        elif "Wed " in day: day = GLOBAL_ORDERED_DAYS[2]
        elif "Thu " in day: day = GLOBAL_ORDERED_DAYS[3]
        elif "Fri " in day: day = GLOBAL_ORDERED_DAYS[4]
        atr = self.atr_4h * vol
        close = price + move + shock
        if move >= 0:
            high = max(price, close) + abs(atr * random.uniform(0.3, 0.7))
            low  = min(price, close) - abs(atr * random.uniform(0.4, 0.9))
        else:
            high = max(price, close) + abs(atr * random.uniform(0.4, 0.9))
            low  = min(price, close) - abs(atr * random.uniform(0.3, 0.7))
        return {
            "day": day, "session": sess,
            "open":  tick_round(price), "high": tick_round(high),
            "low":   tick_round(low),   "close": tick_round(close),
            "net_change": tick_round(close - price),
            "bias": "🟢 BULL" if close >= price else "🔴 BEAR",
        }

    def _log(self, c):
        arrow = "↑" if c["net_change"] >= 0 else "↓"
        print(f"  {c['day']:12} │ {c['session']:16} │ O:{c['open']:7.2f} H:{c['high']:7.2f} "
              f"L:{c['low']:7.2f} C:{c['close']:7.2f} │ {arrow}{abs(c['net_change']):.2f} │ {c['bias']}")

    def get_daily_summary(self):
        days = {}
        for c in self.candles:
            d = c["day"]
            if d not in days:
                days[d] = {"open": c["open"], "high": c["high"], "low": c["low"],
                           "close": c["close"], "scenario": c.get("scenario", ""), "logic": c.get("logic", "")}
            days[d]["high"]  = max(days[d]["high"], c["high"])
            days[d]["low"]   = min(days[d]["low"],  c["low"])
            days[d]["close"] = c["close"]
            if c.get("scenario"): days[d]["scenario"] = c["scenario"]
            if c.get("logic"):    days[d]["logic"]    = c["logic"]
        return days

    def export(self, scores, key_levels, key_events, scenarios_text, action_plan):
        actual = get_actual_prices(self.code)
        daily = self.get_daily_summary()
        return {
            "meta": {
                "symbol": self.code,
                "contract": f"{self.code}U26 (September 2026)",
                "anchor_price": self.anchor,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "forecast_week": GLOBAL_FORECAST_WEEK,
                "composite_bias": round(self.composite_bias, 2),
                "detailed_scores": scores,
                "key_levels": key_levels,
                "key_events": key_events,
                "action_plan": action_plan,
            },
            "actual_data": actual,
            "candles_4h": self.candles,
            "daily_summary": {
                day: {k: round(v, 2) if isinstance(v, float) else v
                      for k, v in data.items()}
                for day, data in daily.items()
            },
            "week_forecast": {
                "open": round(self.candles[0]["open"], 2),
                "close": round(self.candles[-1]["close"], 2),
                "high": round(max(c["high"] for c in self.candles), 2),
                "low":  round(min(c["low"]  for c in self.candles), 2),
                "net_change": round(self.candles[-1]["close"] - self.anchor, 2),
                "direction": "BULLISH" if self.candles[-1]["close"] > self.anchor else "BEARISH",
            },
            "scenarios_text": scenarios_text,
        }


# ─────────────────────────────────────────────────────────────────────────────
# ZW ENGINE (original masterpiece, fully preserved)
# ─────────────────────────────────────────────────────────────────────────────
class ZWEngine(BaseFutureEngine):
    """
    ZW Wheat Engine — Tuần 22-27/06/2026
    ════════════════════════════════════════════════════════════
    DỮ LIỆU THỰC TẾ (Crop Progress ngày 15/06/2026):
    • Lúa mì mùa đông G/E: chỉ 27% — mức CỰC THẤP lịch sử (thấp nhất kể từ 2002)
    • Harvest tiến độ: đang thu hoạch tại TX/OK/KS nhưng chất lượng kém
    • Spring Wheat (Minnesota): G/E ~52%, đang phát triển bình thường
    • Thị trường toàn cầu: Nga + EU nguồn cung vẫn cạnh tranh giá

    YẾU TỐ MÙA VỤ TUẦN NÀY:
    • Thu hoạch lúa mì mùa đông Kansas/Oklahoma đang diễn ra
    • Chất lượng Protein cực thấp → premium Hard Red Winter tăng
    • Australia vẫn trong mùa gieo hạt (Jun-Jul) — ảnh hưởng cung Q4 2026
    • Nga đang gặp hạn hán cục bộ tại Krasnodar region

    ENSO/KHÍ HẬU:
    • El Niño đã bắt đầu hình thành (xác nhận tháng 6/2026)
    • Lịch sử El Niño: thường gây khô hạn tại Great Plains (US) → bullish ZW
    • Australia: El Niño gây hạn hán → giảm crop Q4 2026

    ANCHOR PRICE: Lấy động từ giá đóng cửa H1 cuối cùng của CSV
    """
    def __init__(self):
        super().__init__(
            code="ZW", anchor=594.25, atr_h1=3.54, rsi=42.0,
            ema21=597.00, ema50=598.15, s1=591.25, s2=587.75, r1=596.00, r2=700.00
        )
        self.scores = {
            "V3_Technical":  +0.8,   # RSI thoát vùng oversold, đà phục hồi hình thành
            "V4_Structure":  +1.0,   # Higher low structure đang xây dựng
            "ICT_Profile":   +1.2,   # Judas Swing đã hoàn thành tuần trước, giá sẵn sàng bứt phá
            "Seasonality":   +1.2,   # Jun-Jul: Harvest stress + El Niño Great Plains → bullish mạnh
            "Macro_DXY":    +0.2,   # DXY ổn định, không cản trở xuất khẩu
            "Macro_Brent":  -0.8,   # Dầu thấp giảm logistics premium, nhưng tác động yếu
            "COT_Report":   +0.8,   # Managed Money short-covering mạnh → momentum tăng
            "Fundamentals": +1.5,   # G/E 27% (cực thấp lịch sử) + El Niño Australia + Nga khô hạn
        }
        self.composite_bias = sum(self.scores.values())
        random.seed(42)

    def build(self):
        p = self.anchor
        print(f"\n{'='*70}")
        print(f"  [ZW] FUTURE CHART ENGINE - WHEAT (ZWU26)")
        print(f"  [PIN] Anchor: {self.anchor} | Bias: {self.composite_bias:+.2f}")
        print(f"{'='*70}")
        print("\n  [CANDLE] ZW 4H CANDLE SEQUENCE:")
        print("  " + "─"*66)

        # MONDAY — USDA Crop Progress + Hấp Thụ Short-Covering
        for sess, move, vol, shock in [
            ("Asia 07-11",    -0.75, 1.1,  0.0),   # Asia mở yếu — chờ USDA tối
            ("Asia 11-15",    -0.50, 1.0,  0.0),   # Giằng co
            ("London 15-19",  +1.75, 1.4, +0.25),  # MATIF Paris tăng theo tin thu hoạch kém chất lượng
            ("Pre-NY 19-21",  +1.25, 1.3,  0.0),   # Pre-market bullish
            ("NY Open 21-23", +3.00, 1.8, +1.50),  # USDA Crop Progress G/E vẫn 27% → shock mua mạnh
            ("NY Close 23-01",+1.25, 1.2,  0.0),   # Duy trì đà sau USDA
        ]:
            c = self._gen_candle(p, move, "Mon ", sess, vol, shock)
            if sess == "Asia 07-11": c["scenario"] = "USDA Crop Progress + Hấp Thụ Short-Covering"; c["logic"] = "USDA Crop Progress: G/E lúa mì duy trì 27%. LƯU Ý: Đà tăng tuần qua đã xả bớt phần lớn vị thế Short của Quỹ. Không nên kỳ vọng một cú Squeeze sốc mới, thị trường sẽ tăng chậm lại hoặc có nhịp Pullback chốt lời."
            self.candles.append(c); p = c["close"]; self._log(c)

        # TUESDAY — El Niño Update + Australia Planting Concern
        for sess, move, vol, shock in [
            ("Asia 07-11",    +1.75, 1.5,  0.0),   # Asia gap up theo USDA đêm qua
            ("Asia 11-15",    -1.00, 1.2,  0.0),   # Profit-taking Asia
            ("London 15-19",  +1.50, 1.5, +0.75),  # Australia planting concern + El Niño tin tức
            ("Pre-NY 19-21",  +0.75, 1.1,  0.0),   # Ổn định trước NY
            ("NY Open 21-23", +1.50, 1.4, +0.50),  # Short-covering wave thứ 2
            ("NY Close 23-01",+0.25, 1.0,  0.0),
        ]:
            c = self._gen_candle(p, move, "Tue ", sess, vol, shock)
            if sess == "Asia 07-11": c["scenario"] = "El Niño + Australia Planting Risk"; c["logic"] = "El Niño xác nhận tháng 6/2026 → dự báo hạn hán tại Australia mùa gieo hạt Jul-Sep. Lịch sử: El Niño + Australia hạn hán = giảm 15-20% sản lượng lúa mì Australia. Đây là yếu tố cung dài hạn cực kỳ bullish cho ZW Q4 2026."
            self.candles.append(c); p = c["close"]; self._log(c)

        # WEDNESDAY — Nga hạn hán + mid-week consolidation
        for sess, move, vol, shock in [
            ("Asia 07-11",    +0.50, 1.0,  0.0),   # Giữ đà tăng
            ("Asia 11-15",    -0.75, 1.1,  0.0),   # Nga phủ nhận tin hạn hán → sell-off nhẹ
            ("London 15-19",  +1.25, 1.3, +0.50),  # Báo cáo Nga khô hạn Krasnodar được xác nhận
            ("Pre-NY 19-21",  +0.50, 1.0,  0.0),   # Ổn định
            ("NY Open 21-23", -1.00, 1.3, -0.50),  # Fund profit-taking — không có data mới
            ("NY Close 23-01",+0.50, 1.0,  0.0),   # Mua lại cuối phiên
        ]:
            c = self._gen_candle(p, move, "Wed ", sess, vol, shock)
            if sess == "Asia 07-11": c["scenario"] = "Nga Khô Hạn + Consolidation"; c["logic"] = "Báo cáo vệ tinh xác nhận hạn hán cục bộ tại Krasnodar/Rostov (Nga) — khu vực sản xuất lúa mì chất lượng cao. Nga vẫn là nguồn cung lớn nhất thế giới, bất kỳ giảm sản lượng nào cũng tác động mạnh đến giá. Thị trường consolidate chờ Export Sales thứ Năm."
            self.candles.append(c); p = c["close"]; self._log(c)

        # THURSDAY — Export Sales Weekly + Egypt/Asia tender (QUAN TRỌNG)
        for sess, move, vol, shock in [
            ("Asia 07-11",    -0.25, 0.9,  0.0),   # Chờ Export Sales
            ("Asia 11-15",    +0.50, 1.0,  0.0),   # Tin Egypt cân nhắc mua ZW Mỹ
            ("London 15-19",  +0.75, 1.2,  0.0),   # MATIF London tích cực
            ("Pre-NY 19-21",  +0.50, 1.1,  0.0),   # Pre-positioning trước Export Sales
            ("NY Open 21-23", +2.50, 1.6, +1.00),  # Export Sales tốt: Egypt + Philippines mua Mỹ
            ("NY Close 23-01",+0.75, 1.0,  0.0),   # Duy trì đà tăng
        ]:
            c = self._gen_candle(p, move, "Thu ", sess, vol, shock)
            if sess == "Asia 07-11": c["scenario"] = "Export Sales + Egypt Tender - QUAN TRỌNG"; c["logic"] = "Export Sales lúa mì tuần 23-27/06: Kỳ vọng Egypt, Philippines và Bangladesh quay lại mua lúa mì Mỹ khi giá HRW cạnh tranh hơn so với Nga (Nga vừa tăng thuế xuất khẩu). Data ~20:30 ICT là catalyst lớn nhất tuần. G/E 27% đảm bảo supply tight dài hạn."
            self.candles.append(c); p = c["close"]; self._log(c)

        # FRIDAY — Đóng vị thế + Quarterly Options Expiry
        for sess, move, vol, shock in [
            ("Asia 07-11",    -0.75, 0.9,  0.0),   # Profit-taking sau tuần tăng mạnh
            ("Asia 11-15",    -1.00, 0.9,  0.0),   # Fund đóng Long một phần
            ("London 15-19",  +0.75, 1.1,  0.0),   # Mua lại quanh vùng hỗ trợ
            ("Pre-NY 19-21",  -0.25, 0.9,  0.0),   # Cẩn thận trước Options Expiry
            ("NY Open 21-23", +1.25, 1.3, +0.50),  # Options Expiry tạo volatility
            ("NY Close 23-01",-0.75, 0.9,  0.0),   # Đóng tuần, Long còn ít
        ]:
            c = self._gen_candle(p, move, "Fri ", sess, vol, shock)
            if sess == "Asia 07-11": c["scenario"] = "Quarterly Options Expiry — Chốt tuần"; c["logic"] = "Quarterly options expiry tạo biến động xung quanh các mức strike lớn (~610¢, ~620¢). Fund đóng một phần Long để book profit. Nhưng nền tảng cơ bản vẫn bullish: G/E 27%, El Niño Australia, Nga khô hạn — dự kiến tuần tiếp theo tiếp tục tăng."
            self.candles.append(c); p = c["close"]; self._log(c)

        return self.export(
            scores=self.scores,
            key_levels={"support_ob": 600.00, "ote_low": 605.00, "mss_trigger": 615.00,
                        "ema21": self.ema21, "ema50": self.ema50, "week_target": 630.00, "r2": 650.0},
            key_events={
                "Mon Jun 22": "USDA Crop Progress (G/E Lúa Mì mùa đông 27%) + Export Inspection - BIẾN ĐỘNG CAO",
                "Tue Jun 23": "El Niño Update + Australia Planting Concern + MATIF Settlement",
                "Wed Jun 24": "Nga Khô Hạn Krasnodar — Báo cáo Vệ tinh xác nhận - TRUNG BÌNH",
                "Thu Jun 25": "Export Sales Weekly (~20:30 ICT): Egypt/Philippines/Bangladesh tender - QUAN TRỌNG",
                "Fri Jun 26": "Quarterly Options Expiry — Đóng vị thế cuối tuần",
            },
            scenarios_text="""
  ════════════════════════════════════════════════════════════
  DỮ LIỆU THỰC TẾ LÀM CƠ SỞ PHÂN TÍCH:
  • USDA Crop Progress (15/06/2026): G/E Lúa mì mùa đông = 27% (thấp nhất từ 2002)
  • El Niño xác nhận tháng 6/2026 → hạn hán Australia Jul-Sep = cung ZW Q4 2026 giảm
  • Nga: Hạn hán cục bộ vùng Krasnodar/Rostov đe dọa chất lượng lúa mì HRW
  • Spring Wheat (Minnesota): G/E 52% — bình thường, không đáng lo
  ════════════════════════════════════════════════════════════

  PHASE 1 — THỨ 2 (USDA Crop Progress + Hấp Thụ Short-Covering):
  G/E Lúa mì tiếp tục ở 27% — thấp nhất lịch sử 20 năm qua.
  Chất lượng protein HRW Kansas kém → người dùng phải trả premium cao hơn.
  Export Inspection xác nhận đơn mua đang quay lại từ Egypt, Philippines.

  PHASE 2 — THỨ 3 (El Niño + Australia Planting Risk):
  El Niño 2026 được xác nhận — lịch sử cho thấy Australia mất 15-20% sản lượng.
  MATIF Paris settlement kéo ZW CBOT tăng theo. Short-covering tiếp diễn mạnh.

  PHASE 3 — THỨ 4 (Nga Khô Hạn Confirmation):
  Báo cáo vệ tinh xác nhận hạn hán Krasnodar → Nga có thể giảm xuất khẩu H2 2026.
  Đây là yếu tố cực kỳ bullish vì Nga chiếm ~20% xuất khẩu lúa mì thế giới.

  PHASE 4-5 — THỨ 5/6 (Export Sales + Options Expiry):
  Export Sales là catalyst quyết định: Egypt/Philippines quay lại mua Mỹ do giá cạnh tranh.
  Quarterly options expiry tạo biến động mạnh nhưng trend tăng vẫn được duy trì.""",
            action_plan="ZW MIXED/BULLISH NHẸ tuần 22-26/06. Đã qua giai đoạn Short-Squeeze dễ nhất (tuần trước). Tuyệt đối không FOMO Long đuổi. Chờ giá Pullback rõ rệt về S1 (600-605¢) mới giải ngân. Đề phòng phe Short đã cắt lỗ xong và bắt đầu chốt lời Long ngắn hạn."
        )


# ─────────────────────────────────────────────────────────────────────────────
# ZC ENGINE (Corn — Ethanol Demand + Crop Progress + Midwest Weather)
# ─────────────────────────────────────────────────────────────────────────────
class ZCEngine(BaseFutureEngine):
    """
    ZC Corn Engine — Tuần 22-26/06/2026
    ════════════════════════════════════════════════════════════
    DỮ LIỆU THỰC TẾ (Crop Progress ngày 15/06/2026):
    • Ngô G/E: 68% (tăng từ 67% tuần trước) — TÍCH CỰC
    • Ngô đã mọc: 94% (vượt 5 năm bình quân 1 điểm)
    • Giai đoạn mùa vụ: Đang chuẩn bị Silking (thụ phấn)
    • Silking thường bắt đầu cuối tháng 6 / đầu tháng 7 tại Iowa/Illinois

    YẾU TỐ MÙA VỤ TUẦN NÀY — CRITICAL:
    • Tuần 22-26/06 là ĐỈNH POLLINATION RISK WINDOW cho vùng Iowa/Illinois
    • Nhiệt độ >35°C trong 5-7 ngày liên tục CÓ THỂ phá hủy khả năng thụ phấn
    • Lịch sử: Mỗi sự kiện Heat Stress Pollination nghiêm trọng = +15-30¢/bu premium
    • Nếu G/E tuần này giảm → market sẽ phản ứng rất mạnh (tăng mạnh)

    ENSO/KHÍ HẬU:
    • El Niño mới bắt đầu → thường mang lại MƯA cho Midwest summer
    • Tuy nhiên El Niño đầu mùa tháng 6 chưa có tác động rõ đến Midwest
    • Weather model: nửa July mới rõ ràng hơn → UNCERTAINTY cao = premium

    ETHANOL:
    • EIA Ethanol Production thứ Tư: kỳ vọng ~1.04-1.06 triệu thùng/ngày
    • Pha trộn Ethanol với xăng vẫn ổn định, Blending Mandate RVO duy trì

    ANCHOR PRICE: Lấy động từ giá đóng cửa H1 cuối cùng của CSV
    """
    def __init__(self):
        super().__init__(
            code="ZC", anchor=421.0, atr_h1=1.44, rsi=55.78,
            ema21=420.43, ema50=421.11, s1=418.75, s2=414.50, r1=422.00, r2=491.25
        )
        self.scores = {
            "V3_Technical":  +0.3,   # RSI phục hồi từ vùng 45, cấu trúc đang cải thiện
            "V4_Structure":  +0.3,   # Giá đang test breakout khỏi range 418-422
            "ICT_Profile":   +0.5,   # FVG hỗ trợ, có thể có Judas Swing trước khi tăng
            "Seasonality":   +1.8,   # ⭐ PEAK POLLINATION RISK WINDOW — yếu tố mùa vụ lớn nhất năm
            "Macro_DXY":    +0.2,   # DXY ổn định, hỗ trợ xuất khẩu
            "Macro_Brent":  -0.6,   # Dầu thấp giảm Ethanol margin nhẹ
            "COT_Report":   +0.5,   # Managed Money short-covering tích cực
            "Fundamentals": +0.6,   # G/E 68% tốt nhưng Pollination Risk tạo uncertainty premium
        }
        self.composite_bias = sum(self.scores.values())
        random.seed(77)

    def build(self):
        p = self.anchor
        print(f"\n{'='*70}")
        print(f"  [ZC] FUTURE CHART ENGINE - CORN (ZCU26)")
        print(f"  [PIN] Anchor: {self.anchor} | Bias: {self.composite_bias:+.2f}")
        print(f"{'='*70}")
        print("\n  [CANDLE] ZC 4H CANDLE SEQUENCE:")
        print("  " + "─"*66)

        # MONDAY — USDA Crop Progress Ngô + Bắt đầu Silking Window
        for sess, move, vol, shock in [
            ("Asia 07-11",    +0.20, 1.0,  0.0),   # Asia tích cực, chờ USDA tối
            ("Asia 11-15",    -0.40, 0.9,  0.0),   # Giằng co
            ("London 15-19",  +0.50, 1.1, +0.20),  # ZW tăng kéo ZC theo (nông sản đồng thuận)
            ("Pre-NY 19-21",  +0.80, 1.2,  0.0),   # Pollination risk premium build-up trước USDA
            ("NY Open 21-23", +1.50, 1.5, +0.80),  # USDA Crop Progress G/E 68% duy trì + Silking bắt đầu
            ("NY Close 23-01",+0.30, 0.9,  0.0),   # Giữ đà
        ]:
            c = self._gen_candle(p, move, "Mon ", sess, vol, shock)
            if sess == "Asia 07-11": c["scenario"] = "USDA G/E 68% + Silking Window Bắt Đầu"; c["logic"] = "USDA Crop Progress: G/E Ngô 68% (ổn định). QUAN TRỌNG HƠN: Silking (thụ phấn) bắt đầu tại Iowa/Illinois — đây là giai đoạn NHẠY CẢM NHẤT với nhiệt độ. Mỗi ngày >35°C trong tuần này có thể phá hủy 2-5% năng suất. Pollination Risk Premium được xây dựng từ phiên NY."
            self.candles.append(c); p = c["close"]; self._log(c)

        # TUESDAY — Phản ứng thị trường sau USDA Ngô
        for sess, move, vol, shock in [
            ("Asia 07-11",    +0.80, 1.3,  0.0),   # Tiêu hóa tin USDA
            ("Asia 11-15",    -0.50, 1.1,  0.0),   # Fund bán vào rally
            ("London 15-19",  +0.60, 1.2,  0.0),
            ("Pre-NY 19-21",  +0.40, 1.0,  0.0),
            ("NY Open 21-23", +0.70, 1.3, +0.20),  # Momentum tiếp diễn
            ("NY Close 23-01",+0.10, 0.9,  0.0),
        ]:
            c = self._gen_candle(p, move, "Tue ", sess, vol, shock)
            if sess == "Asia 07-11": c["scenario"] = "Phản ứng USDA Ngô"; c["logic"] = "Thị trường tiêu hóa USDA Crop Progress. Pollination Risk Premium duy trì lực mua. Giá kiểm tra vùng R1 422.00."
            self.candles.append(c); p = c["close"]; self._log(c)

        # WEDNESDAY — EIA Ethanol + 7-Day Weather Forecast Update (CAO VOL)
        for sess, move, vol, shock in [
            ("Asia 07-11",    -0.50, 1.0,  0.0),   # Profit-taking nhẹ
            ("Asia 11-15",    -0.30, 1.0,  0.0),
            ("London 15-19",  +0.60, 1.2,  0.0),   # Weather model mới công bố
            ("Pre-NY 19-21",  +1.20, 1.5, +0.80),  # EIA Ethanol tốt + Weather cực đoan dự báo
            ("NY Open 21-23", +1.00, 1.6, +0.50),  # Reaction EIA + Weather spike
            ("NY Close 23-01",-0.50, 1.0,  0.0),
        ]:
            c = self._gen_candle(p, move, "Wed ", sess, vol, shock)
            if sess == "Asia 07-11": c["scenario"] = "EIA Ethanol + 7-Day Heat Forecast Update"; c["logic"] = "EIA Ethanol Production (thứ 4): Kỳ vọng ~1.05 triệu thùng/ngày (tốt hơn 1.04 tuần trước). QUAN TRỌNG HƠN: 7-Day weather model GFS/Euro cập nhật — nếu dự báo nhiệt độ >35°C tại Iowa trong 5-7 ngày tới trong giai đoạn Silking peak → Pollination Risk Premium tăng đột biến 5-10¢. Đây là phiên biến động nhất tuần cho ZC."
            self.candles.append(c); p = c["close"]; self._log(c)

        # THURSDAY — Export Sales Weekly Ngô (~20:30 ICT) - TRUNG BÌNH
        for sess, move, vol, shock in [
            ("Asia 07-11",    -0.30, 0.9,  0.0),
            ("Asia 11-15",    +0.20, 1.0,  0.0),
            ("London 15-19",  +0.40, 1.1,  0.0),
            ("Pre-NY 19-21",  +0.30, 1.0,  0.0),
            ("NY Open 21-23", +0.50, 1.2, +0.20),  # Export Sales ngô trung bình
            ("NY Close 23-01",+0.10, 0.9,  0.0),
        ]:
            c = self._gen_candle(p, move, "Thu ", sess, vol, shock)
            if sess == "Asia 07-11": c["scenario"] = "Export Sales Weekly - Trung Bình"; c["logic"] = "Export Sales ngô tuần này ổn định. Brazil vẫn cạnh tranh nhưng Pollination Risk Premium hỗ trợ floor giá. Thị trường chờ xác nhận từ weather model."
            self.candles.append(c); p = c["close"]; self._log(c)

        # FRIDAY — Đóng vị thế cuối tuần + theo dõi thời tiết Midwest
        for sess, move, vol, shock in [
            ("Asia 07-11",    -0.30, 0.8,  0.0),
            ("Asia 11-15",    -0.20, 0.8,  0.0),
            ("London 15-19",  +0.30, 0.9,  0.0),
            ("Pre-NY 19-21",  -0.10, 0.8,  0.0),
            ("NY Open 21-23", +0.40, 1.0,  0.0),
            ("NY Close 23-01",-0.30, 0.8,  0.0),
        ]:
            c = self._gen_candle(p, move, "Fri ", sess, vol, shock)
            if sess == "Asia 07-11": c["scenario"] = "Đóng vị thế cuối tuần"; c["logic"] = "Ngô không có catalyst mới cuối tuần. Giá dao động hẹp. Weather outlook tuần tới sẽ quyết định hướng đi tiếp theo của Pollination Risk Premium."
            self.candles.append(c); p = c["close"]; self._log(c)

        return self.export(
            scores=self.scores,
            key_levels={"s1": self.s1, "s2": self.s2, "r1": self.r1, "r2": self.r2,
                        "ema21": self.ema21, "ema50": self.ema50, "pollination_r1": 430.0, "heat_target": 440.0},
            key_events={
                "Mon Jun 22": "USDA Crop Progress (G/E Ngô 68% → Silking bắt đầu) - BIẾN ĐỘNG CAO",
                "Tue Jun 23": "Phản ứng USDA + Argentina Corn Harvest Final Report - TRUNG BÌNH",
                "Wed Jun 24": "EIA Ethanol Production + 7-Day Heat Weather Update - BIẾN ĐỘNG CAO",
                "Thu Jun 25": "Export Sales Weekly (Corn) + Pollination Status Update - TRUNG BÌNH",
                "Fri Jun 26": "Đóng vị thế cuối tuần + Weekly Weather Model Update",
            },
            scenarios_text="""
  ════════════════════════════════════════════════════════════
  DỮ LIỆU THỰC TẾ LÀM CƠ SỞ PHÂN TÍCH:
  • USDA Crop Progress (15/06/2026): G/E Ngô = 68% (tốt, tăng từ 67%)
  • Ngô mọc: 94% (trên bình quân 5 năm)
  • Giai đoạn mùa vụ: Silking (thụ phấn) bắt đầu Iowa/Illinois từ tuần này
  • El Niño 2026: Uncertainty về thời tiết tháng 7 → premium speculation
  ════════════════════════════════════════════════════════════

  PHASE 1 — THỨ 2 (USDA + Silking Window Khai Mạc):
  G/E 68% tốt nhưng Silking bắt đầu = giai đoạn nhạy cảm nhất với nhiệt.
  Pollination Risk Premium bắt đầu xây dựng từ phiên NY. Catalyst tuần này.

  PHASE 2 — THỨ 3 (Phản ứng + Argentina Final):
  Thị trường tiêu hóa USDA. Argentina hoàn tất thu hoạch ngô — cung dồi dào.
  Hai lực kéo đối nghịch → giá giằng co nhưng Pollination premium là yếu tố chủ đạo.

  PHASE 3 — THỨ 4 (EIA Ethanol + HEAT FORECAST — Vol Cao Nhất Tuần):
  EIA Ethanol tích cực hỗ trợ cầu nội địa. Weather model GFS/Euro cập nhật —
  nếu dự báo 35°C+ tại Iowa trong peak Silking = spike 5-10¢ ngay lập tức.

  PHASE 4-5 — THỨ 5/6 (Export Sales + Cuối Tuần):
  Export Sales phản ánh nhu cầu thực. Argentina cạnh tranh nhưng không phá được
  Pollination premium. Đóng tuần trong biên độ hẹp, chờ G/E tuần tới.""",
            action_plan="ZC BULLISH BIAS nhờ Pollination Risk Premium. Long tại S1 418.75 khi pullback. THEO DÕI: Weather model Midwest hàng ngày + G/E thứ 2 tới. Target: 430-435¢ nếu heat stress xác nhận. EIA Ethanol thứ 4 là phiên vol cao nhất."
        )


# ─────────────────────────────────────────────────────────────────────────────
# ZS ENGINE (Soybean — China Demand + La Niña Brazil + NOPA Crush)
# ─────────────────────────────────────────────────────────────────────────────
class ZSEngine(BaseFutureEngine):
    """
    ZS Soybean Engine — Tuần 22-26/06/2026
    ════════════════════════════════════════════════════════════
    DỮ LIỆU THỰC TẾ (Crop Progress ngày 15/06/2026):
    • Đậu tương G/E: 66% (ổn định, phù hợp kỳ vọng)
    • Đậu tương gieo trồng: 95% hoàn thành (tốt hơn lịch sử)
    • Giai đoạn mùa vụ: Cây đang phát triển lá, chưa đến Pod-setting
    • Pod-setting thường bắt đầu đầu tháng 8 — chưa phải risk factor lớn

    YẾU TỐ CƠ BẢN TUẦN NÀY:
    • Brazil: Xuất khẩu tháng 6/2026 đang ở mức ký lục → ÁP LỰC BÁN liên tục
    • Trung Quốc: Nhập khẩu đậu tương vẫn mạnh (tồn kho heo cần bổ sung)
    • NOPA Crush: Số liệu tháng 5 đã công bố — tháng 6 chờ báo cáo cuối tháng
    • Argentina: Hoàn tất thu hoạch, đang cắt soybean meal exports

    ĐIỂM THEN CHỐT — EL NIÑO:
    • El Niño 2026: TỐT cho đậu tương Mỹ mùa hè (mang mưa Midwest)
    • Nhưng XẤU cho Brazil vụ safrinha (2027 supply) — DCA long opportunity
    • Giá đậu tương US được hưởng lợi từ El Niño lần sau (Brazil giảm sản lượng)

    ANCHOR PRICE: Lấy động từ giá đóng cửa H1 cuối cùng của CSV
    """
    def __init__(self):
        super().__init__(
            code="ZS", anchor=1133.5, atr_h1=3.00, rsi=45.26,
            ema21=1130.27, ema50=1132.07, s1=1127.75, s2=1121.75, r1=1135.75, r2=1214.00
        )
        self.scores = {
            "V3_Technical":  -0.3,   # RSI đang hồi phục từ vùng 40, cấu trúc trung tính
            "V4_Structure":  -0.3,   # Giá dao động quanh EMA50, chưa có hướng rõ
            "ICT_Profile":   +0.5,   # FVG hỗ trợ, khả năng Judas Swing trước rally
            "Seasonality":   +0.5,   # Jun: El Niño tốt cho đậu Mỹ (mưa Midwest), nhưng Brazil supply lớn
            "Macro_DXY":    +0.3,   # DXY trung tính, không hỗ trợ đặc biệt
            "Macro_Brent":  -0.5,   # Dầu thấp giảm Biodiesel demand
            "COT_Report":   -0.3,   # Managed Money đang bắt đầu cover short nhẹ
            "Fundamentals": +0.7,   # Trung Quốc mua ổn định vs Brazil supply dồi dào = MIXED
        }
        self.composite_bias = sum(self.scores.values())
        random.seed(55)

    def build(self):
        p = self.anchor
        print(f"\n{'='*70}")
        print(f"  [ZS] FUTURE CHART ENGINE - SOYBEAN (ZSU26)")
        print(f"  [PIN] Anchor: {self.anchor} | Bias: {self.composite_bias:+.2f}")
        print(f"{'='*70}")
        print("\n  [CANDLE] ZS 4H CANDLE SEQUENCE:")
        print("  " + "─"*66)

        # MONDAY — Brazil Kỷ Lục Xuất Khẩu vs China Mua Ổn Định
        for sess, move, vol, shock in [
            ("Asia 07-11",    -1.50, 1.2, -0.50),  # Brazil xuất khẩu kỷ lục tháng 6 → sell-off mở đầu
            ("Asia 11-15",    -0.80, 1.0,  0.0),   # Tiếp tục áp lực
            ("London 15-19",  +0.80, 1.1,  0.0),   # Phục hồi nhẹ
            ("Pre-NY 19-21",  +1.50, 1.3, +0.50),  # China buying news tái xuất hiện
            ("NY Open 21-23", +2.00, 1.5, +1.00),  # USDA G/E 66% + China order xác nhận
            ("NY Close 23-01",+0.00, 0.9,  0.0),   # Giằng co, đóng phiên flat
        ]:
            c = self._gen_candle(p, move, "Mon ", sess, vol, shock)
            if sess == "Asia 07-11": c["scenario"] = "Brazil Xuất Khẩu Kỷ Lục vs China Buying"; c["logic"] = "Brazil xuất khẩu đậu tương tháng 6/2026 đạt kỷ lục mới (>10 triệu tấn/tháng) — áp lực bán lớn đầu tuần. Nhưng Trung Quốc vẫn duy trì mua đều để bổ sung tồn kho heo. USDA Crop Progress ZS G/E 66% ổn định + China order mới tạo rally phiên NY. Kết quả: tug-of-war không có người thắng rõ ràng."
            self.candles.append(c); p = c["close"]; self._log(c)

        # TUESDAY — Phản ứng thị trường + China demand sentiment
        for sess, move, vol, shock in [
            ("Asia 07-11",    +0.60, 1.2,  0.0),   # Tiêu hóa tin China
            ("Asia 11-15",    -0.80, 1.1,  0.0),   # Brazil trader bán hedge
            ("London 15-19",  +0.50, 1.0,  0.0),
            ("Pre-NY 19-21",  +0.80, 1.2,  0.0),   # Sentiment tích cực tiếp diễn
            ("NY Open 21-23", +1.00, 1.3, +0.30),  # Momentum China buying
            ("NY Close 23-01",-0.20, 1.0,  0.0),
        ]:
            c = self._gen_candle(p, move, "Tue ", sess, vol, shock)
            if sess == "Asia 07-11": c["scenario"] = "China Demand Sentiment"; c["logic"] = "Thị trường tiêu hóa tin China mua hàng. Sentiment tích cực duy trì. Brazil trader hedge bán tạo pullback nhỏ giữa phiên."
            self.candles.append(c); p = c["close"]; self._log(c)

        # WEDNESDAY — Giằng co Brazil supply vs China demand
        for sess, move, vol, shock in [
            ("Asia 07-11",    -1.20, 1.1,  0.0),   # Brazil hedge selling
            ("Asia 11-15",    -0.80, 1.0,  0.0),
            ("London 15-19",  -0.50, 1.0,  0.0),
            ("Pre-NY 19-21",  +0.60, 1.1,  0.0),   # China buyer dip-buying
            ("NY Open 21-23", -0.80, 1.3, -0.30),  # Fund bán vào rally - net bearish
            ("NY Close 23-01",-0.40, 0.9,  0.0),
        ]:
            c = self._gen_candle(p, move, "Wed ", sess, vol, shock)
            if sess == "Asia 07-11": c["scenario"] = "Brazil Supply Pressure"; c["logic"] = "Brazil hedge selling tiếp tục đè nặng lên ZS. Nhà xuất khẩu Brazil bán aggressively vào mọi rally. China buyer hỗ trợ nhưng không đủ bù Brazil."
            self.candles.append(c); p = c["close"]; self._log(c)

        # THURSDAY — Export Sales Soybeans QUAN TRỌNG (~20:30 ICT)
        for sess, move, vol, shock in [
            ("Asia 07-11",    -0.30, 0.9,  0.0),
            ("Asia 11-15",    +0.50, 1.0,  0.0),   # Tin China tiếp tục mua
            ("London 15-19",  +0.80, 1.1,  0.0),
            ("Pre-NY 19-21",  +0.50, 1.0,  0.0),
            ("NY Open 21-23", +1.50, 1.3, +0.50),  # Export Sales Đậu tương tốt hơn kỳ vọng
            ("NY Close 23-01",+0.20, 0.9,  0.0),
        ]:
            c = self._gen_candle(p, move, "Thu ", sess, vol, shock)
            if sess == "Asia 07-11": c["scenario"] = "Export Sales Soybeans - QUAN TRỌNG"; c["logic"] = "Export Sales Đậu tương tuần 23-27/06: Trung Quốc là người mua chính. Kỳ vọng >700k tấn sẽ là catalyst bullish mạnh. Data ~20:30 ICT."
            self.candles.append(c); p = c["close"]; self._log(c)

        # FRIDAY — Đóng vị thế cuối tuần + ZS mixed bias
        for sess, move, vol, shock in [
            ("Asia 07-11",    -0.60, 0.9,  0.0),
            ("Asia 11-15",    -0.40, 0.8,  0.0),
            ("London 15-19",  +0.30, 0.9,  0.0),
            ("Pre-NY 19-21",  -0.30, 0.8,  0.0),
            ("NY Open 21-23", +0.50, 1.0,  0.0),
            ("NY Close 23-01",-0.60, 0.8,  0.0),   # Đóng Long trước cuối tuần
        ]:
            c = self._gen_candle(p, move, "Fri ", sess, vol, shock)
            if sess == "Asia 07-11": c["scenario"] = "Đóng vị thế cuối tuần"; c["logic"] = "ZS mixed bias: China demand bullish vs Brazil supply bearish. Trader rút Long trước cuối tuần. Giá dao động hẹp quanh EMA50."
            self.candles.append(c); p = c["close"]; self._log(c)

        return self.export(
            scores=self.scores,
            key_levels={"s1": self.s1, "s2": self.s2, "r1": self.r1, "r2": self.r2,
                        "ema21": self.ema21, "ema50": self.ema50, "brazil_pressure_lvl": 1120.0},
            key_events={
                "Mon Jun 22": "USDA Crop Progress (G/E Đậu Tương 66%) + Brazil Export Volume Monthly Record",
                "Tue Jun 23": "China GACC Import Data + Argentina Soybean Meal Export Report",
                "Wed Jun 24": "Mid-week: Brazil vs China tug-of-war — theo dõi sát",
                "Thu Jun 25": "Export Sales Weekly (Soybeans) — Kỳ vọng >700k tấn - QUAN TRỌNG",
                "Fri Jun 26": "Đóng vị thế cuối tuần + El Niño Brazil safrinha outlook 2027",
            },
            scenarios_text="""
  ════════════════════════════════════════════════════════════
  DỮ LIỆU THỰC TẾ LÀM CƠ SỞ PHÂN TÍCH:
  • USDA Crop Progress (15/06/2026): G/E Đậu tương = 66% (ổn định)
  • Gieo trồng: 95% hoàn thành (tốt)
  • Brazil: Xuất khẩu tháng 6 kỷ lục >10 triệu tấn → ÁP LỰC BÁN CÓ CẤU TRÚC
  • Trung Quốc: Duy trì nhập khẩu để bổ sung tồn kho heo (heo hơi tăng giá)
  • El Niño 2026: Tốt cho ZS Mỹ mùa hè, xấu cho Brazil vụ 2027 → DCA opportunity
  ════════════════════════════════════════════════════════════

  PHASE 1 — THỨ 2 (Brazil Kỷ Lục vs China Mua):
  Brazil xuất khẩu kỷ lục tháng 6 → áp lực bán đầu tuần. China mua đều đặn hỗ trợ.
  Kết quả: giằng co, giá trong biên độ 1120-1135. Không có hướng rõ ràng.

  PHASE 2 — THỨ 3 (China GACC Data + Argentina Meal):
  Số liệu nhập khẩu của Trung Quốc (GACC) nếu tốt → sẽ kích hoạt rally ngắn hạn.
  Argentina xuất khẩu Soybean Meal xong → giảm cạnh tranh với ZS Mỹ.

  PHASE 3 — THỨ 4 (Brazil vs China — Mid-week Showdown):
  Brazil tiếp tục bán hedge. Thị trường kiểm tra lại S1 1127.75.
  Đây là cơ hội mua DCA nếu giá test S1 và không break down.

  PHASE 4-5 — THỨ 5/6 (Export Sales Quyết Định + Cuối Tuần):
  >700k tấn = bullish breakout khỏi range, target R1 1135.75+
  <600k tấn = tiếp tục range-bound, chờ tuần sau.
  El Niño 2027 outlook Brazil = DCA long opportunity dài hạn.""",
            action_plan="ZS MIXED BIAS — Brazil supply vs China demand là cuộc chiến chủ đạo. LONG chỉ khi: (1) Export Sales >700k tấn THỨ NĂM hoặc (2) China thông báo mua lớn đột xuất và giá break R1 1135.75. DCA Long dài hạn tại S2 1121.75 là cơ hội tốt vì El Niño 2026 sẽ giảm sản lượng Brazil vụ 2027."
        )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*70)
    print("  🚀 MULTI-COMMODITY FUTURE CHART ENGINE v2.0 (ZC, ZW, ZS)")
    print("="*70)

    all_data = {}

    for EngineClass in [ZCEngine, ZWEngine, ZSEngine]:
        engine = EngineClass()
        data = engine.build()
        all_data[engine.code] = data

        daily = data["daily_summary"]
        print(f"\n  [{engine.code}] WEEKLY SUMMARY:")
        print(f"  {'Day':<14} | {'Open':>7} | {'High':>7} | {'Low':>7} | {'Close':>7} | {'Change':>8} | Kịch bản")
        print("  " + "="*90)
        prev = engine.anchor
        for day, d in daily.items():
            chg = d['close'] - prev
            print(f"  {day:<14} | {d['open']:>7.2f} | {d['high']:>7.2f} | {d['low']:>7.2f} | {d['close']:>7.2f} | {chg:>+8.2f} | {d.get('scenario','')}")
            prev = d['close']

    base_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(base_dir, "future_chart_data.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*70}")
    print(f"  [OK] Data exported to: {out_path}")
    print(f"  [OK] Run future_chart_html.py to generate interactive chart")
    print(f"{'='*70}\n")
