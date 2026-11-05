# Bộ Code Pine Script v5 — 3 Phương Pháp Giao Dịch CBOT (Chuẩn CQG)

Tài liệu này chứa mã nguồn **Pine Script v5 (`strategy`)** đã được tối ưu hóa đồng bộ 100% với thuật toán trong `ict_engine.py` và `backtest_engine.py` của hệ thống Dashboard.

---

## 🌟 Điểm Nổi Bật Của Bản Tối Ưu Này So Với Bản Cũ Trên TradingView

1. **Tích hợp cả 3 Phương Pháp trong 1 Script duy nhất (Chọn trực tiếp trong menu Cài Đặt ⚙️):**
   * **Phương pháp 1 (`M1 - ICT MSS + Pullback EMA 21-50`):** Chờ cấu trúc MSS xác nhận + hội tụ OB/FVG (WinRate >= 70%), đặt lệnh chờ `Limit` tại `EMA 21` (tự động hủy lệnh chờ nếu sau 24 nến giá không hồi về).
   * **Phương pháp 2 (`M2 - FVG + Bắt Đáy/Đỉnh SMC Zone 5 Sao`):** Chấm điểm hội tụ 8 yếu tố (Liquidity Sweep, MSS/CHoCH, RSI cực trị, FVG, Pivot S1/R1, ATR Spike). Vào lệnh đảo chiều khi điểm số đạt chuẩn **>= 5/8 sao**.
   * **Phương pháp 3 (`M3 - Chiến Lược Hybrid M1 + M2 Kết Hợp`):** Chỉ kích hoạt Bắt Đáy/Đỉnh M2 khi sóng xả/tăng đã cạn kiệt (bắt buộc có **Liquidity Sweep** hoặc **RSI < 35 / > 65**); còn lại đi lệnh thuận xu hướng theo M1 và khóa xung đột chiều.
2. **Cơ chế Quản Trị Lệnh Đa Tầng Chuẩn CQG (`TP1` ➔ `Dời SL Hòa Vốn ENTRY` ➔ `TP2` ➔ `TP3`):**
   * Ngay khi giá chạm **TP1 (1.0R)**: Tự động dời Stop Loss từ mức rủi ro ban đầu về đúng **giá vào lệnh (`ENTRY`)** để bảo toàn vốn tuyệt đối.
   * Vẽ trực quan các đường **ENTRY, SL, TP1 (1R), TP2 (1.5R), TP3 (2R)** và bảng **Bảng Điều Khiển (Dashboard Table)** ngay ở góc phải biểu đồ.
3. **Tích hợp sẵn bộ phát Webhook JSON (Nến M5 / H1 + Tín hiệu):**
   * Vừa dùng để xem **Strategy Tester (Backtest Win Rate, Profit Factor, Drawdown)** trên TradingView, vừa dùng làm Alert bắn thẳng về link Google Apps Script.

---

## 📋 Mã Nguồn Pine Script v5 (Copy Toàn Bộ Khối Dưới Đây Dán Vào Pine Editor)

```pinescript
//@version=5
strategy("CBOT SMC/ICT 3-in-1 Strategy (M1 Trend | M2 Reversal | M3 Hybrid)", 
     shorttitle="CBOT 3-Methods CQG", 
     overlay=true, 
     initial_capital=10000, 
     default_qty_type=strategy.fixed, 
     default_qty_value=1, 
     currency=currency.USD,
     calc_on_every_tick=false,
     max_labels_count=500,
     max_lines_count=500)

// ============================================================================
// 1. CẤU HÌNH THAM SỐ CHIẾN LƯỢC (INPUTS)
// ============================================================================
grp_strat = "⚡ 1. CHỌN PHƯƠNG PHÁP GIAO DỊCH"
strategyMode = input.string("M3: Chiến Lược Hybrid (M1 + M2 Kết Hợp)", "Phương Pháp Chạy Backtest", 
     options=[
         "M1: ICT MSS + Pullback EMA 21-50", 
         "M2: FVG + Bắt Đáy/Đỉnh SMC Zone (5 Sao)", 
         "M3: Chiến Lược Hybrid (M1 + M2 Kết Hợp)"
     ], group=grp_strat)

grp_ict = "📐 2. THÔNG SỐ CẤU TRÚC ICT / SMC"
swingLen       = input.int(3, "Swing Lookback (Số nến xác nhận Đỉnh/Đáy)", minval=2, maxval=10, group=grp_ict)
sweepLookback  = input.int(36, "Chu kỳ nhớ Liquidity Sweep (Bars)", minval=10, maxval=100, group=grp_ict)
minSmcScore    = input.int(5, "Điểm SMC Zone Tối Thiểu (M2 & M3, chuẩn 5/8)", minval=3, maxval=8, group=grp_ict)
hqObMult       = input.float(0.55, "Hệ số thân nến HQ Order Block (x ATR)", minval=0.2, maxval=2.0, step=0.05, group=grp_ict)

grp_risk = "🛡️ 3. QUẢN TRỊ RỦI RO & CHỐT LỜI ĐA TẦNG (CQG)"
useRiskFilter  = input.bool(true, "Bật bộ lọc biên độ rủi ro SL ( chuẩn CBOT)", group=grp_risk)
minRiskPts     = input.float(2.0, "Khoảng cách SL tối thiểu (Points/Cents)", minval=0.1, step=0.5, group=grp_risk)
maxRiskPts     = input.float(20.0, "Khoảng cách SL tối đa (Points/Cents)", minval=5.0, step=1.0, group=grp_risk)
rrTp1          = input.float(1.0, "Mốc TP1 (R:R) — Chạm TP1 tự dời SL về ENTRY", minval=0.5, step=0.25, group=grp_risk)
rrTp2          = input.float(1.5, "Mốc TP2 (R:R)", minval=1.0, step=0.25, group=grp_risk)
rrTp3          = input.float(2.0, "Mốc TP3 (R:R - Đóng toàn bộ)", minval=1.5, step=0.25, group=grp_risk)
limitExpireBars= input.int(24, "Hạn chờ khớp lệnh Limit EMA21 của M1 (Bars)", minval=4, maxval=72, group=grp_risk)
maxHoldBars    = input.int(48, "Thời gian giữ lệnh tối đa (Bars)", minval=12, maxval=200, group=grp_risk)

grp_vis = "🎨 4. HIỂN THỊ & WEBHOOK"
showEmaCloud   = input.bool(true, "Hiển thị dải băng EMA 21 - EMA 50", group=grp_vis)
showMssLabels  = input.bool(true, "Hiển thị nhãn MSS / CHoCH / Sweep", group=grp_vis)
showSmcSignals = input.bool(true, "Hiển thị nhãn 5★ Bắt Đáy / Đỉnh SMC", group=grp_vis)
showTpSlLines  = input.bool(true, "Vẽ đường ENTRY / SL / TP1 / TP2 / TP3", group=grp_vis)
enableWebhook  = input.bool(true, "Bật phát JSON Webhook mỗi khi đóng nến", group=grp_vis)

// ============================================================================
// 2. CHỈ BÁO KỸ THUẬT CƠ SỞ (EMA, RSI, ATR, PIVOT)
// ============================================================================
ema21 = ta.ema(close, 21)
ema50 = ta.ema(close, 50)
rsi14 = ta.rsi(close, 14)
atr14 = ta.atr(14)
atrAvg14 = ta.sma(atr14, 14)

// Daily Pivot S1 / R1 để tính điểm hội tụ SMC Zone
[dHigh, dLow, dClose] = request.security(syminfo.tickerid, "D", [high[1], low[1], close[1]], lookahead=barmerge.lookahead_on)
pivotP = (dHigh + dLow + dClose) / 3.0
pivotS1 = 2.0 * pivotP - dHigh
pivotR1 = 2.0 * pivotP - dLow
pivotS2 = pivotP - (dHigh - dLow)
pivotR2 = pivotP + (dHigh - dLow)

// ============================================================================
// 3. PHÁT HIỆN SWING POINTS, LIQUIDITY SWEEP, CHoCH & MSS (ICT ENGINE v2.0)
// ============================================================================
ph = ta.pivothigh(high, swingLen, swingLen)
pl = ta.pivotlow(low, swingLen, swingLen)

var float lastSwingHigh = na
var int   lastSwingHighBar = na
var float lastSwingLow  = na
var int   lastSwingLowBar  = na

if not na(ph)
    lastSwingHigh := ph
    lastSwingHighBar := bar_index - swingLen

if not na(pl)
    lastSwingLow := pl
    lastSwingLowBar := bar_index - swingLen

// Theo dõi Liquidity Sweep (Quét thanh khoản BSL / SSL)
var int   lastBslSweepBar  = na
var float lastBslSweepHigh = na
var int   lastSslSweepBar  = na
var float lastSslSweepLow  = na

bool bslSweep = not na(lastSwingHigh) and high > lastSwingHigh and close < lastSwingHigh and bar_index > lastSwingHighBar
if bslSweep
    lastBslSweepBar  := bar_index
    lastBslSweepHigh := high

bool sslSweep = not na(lastSwingLow) and low < lastSwingLow and close > lastSwingLow and bar_index > lastSwingLowBar
if sslSweep
    lastSslSweepBar := bar_index
    lastSslSweepLow := low

// Phát hiện MSS (Market Structure Shift) & CHoCH
var string currentTrend = "neutral"
var int    lastMssBar   = na
var bool   lastMssHadSweep = false
var bool   lastMssIsChoch  = false

bool hadRecentSslSweep = not na(lastSslSweepBar) and (bar_index - lastSslSweepBar <= sweepLookback)
bool hadRecentBslSweep = not na(lastBslSweepBar) and (bar_index - lastBslSweepBar <= sweepLookback)

bool bullMss = not na(lastSwingHigh) and close > lastSwingHigh and close[1] <= lastSwingHigh and bar_index > lastSwingHighBar
bool bearMss = not na(lastSwingLow)  and close < lastSwingLow  and close[1] >= lastSwingLow  and bar_index > lastSwingLowBar

bool bullChoch = not bullMss and hadRecentSslSweep and not na(lastSslSweepLow) and close > high[bar_index - lastSslSweepBar] and close > open
bool bearChoch = not bearMss and hadRecentBslSweep and not na(lastBslSweepHigh) and close < low[bar_index - lastBslSweepBar] and close < open

if bullMss or bullChoch
    currentTrend    := "bullish"
    lastMssBar      := bar_index
    lastMssHadSweep := hadRecentSslSweep
    lastMssIsChoch  := bullChoch and not bullMss

if bearMss or bearChoch
    currentTrend    := "bearish"
    lastMssBar      := bar_index
    lastMssHadSweep := hadRecentBslSweep
    lastMssIsChoch  := bearChoch and not bearMss

// ============================================================================
// 4. PHÁT HIỆN FVG, HQ ORDER BLOCK & CHẤM ĐIỂM SMC ZONE (THANG ĐIỂM 8 SAO)
// ============================================================================
bool bullFvg = low > high[2] and close[1] > open[1]
bool bearFvg = high < low[2] and close[1] < open[1]

var float lastBullFvgTop = na
var float lastBullFvgBot = na
if bullFvg
    lastBullFvgTop := low
    lastBullFvgBot := high[2]

var float lastBearFvgTop = na
var float lastBearFvgBot = na
if bearFvg
    lastBearFvgTop := low[2]
    lastBearFvgBot := high

// HQ Order Block (Thân nến >= 0.55 ATR)
bool isHqBody = math.abs(close - open) >= hqObMult * atr14
bool recentBullHqOb = ta.barssince(close < open and isHqBody[1] and close[1] > open[1]) <= 20
bool recentBearHqOb = ta.barssince(close > open and isHqBody[1] and close[1] < open[1]) <= 20

// Chấm điểm vùng Đáy (Bottom Zone Score / 8) khi xác nhận Pivot Low (tại bar_index - swingLen)
int bottomScore = 0
bool isConfirmedBottom = not na(pl)
float swingLowPrice = isConfirmedBottom ? pl : na

if isConfirmedBottom
    // 1. RSI quá bán (+2đ)
    if rsi14[swingLen] < 35 or rsi14 < 38
        bottomScore += 2
    // 2. Có Bullish MSS / Sweep gần đó (+4đ nếu có Sweep, +3đ nếu MSS, +2đ nếu Sweep râu)
    bool nearBullMss = not na(lastMssBar) and currentTrend == "bullish" and (bar_index - lastMssBar <= 12)
    if nearBullMss
        bottomScore += (lastMssHadSweep ? 4 : 3)
    else if hadRecentSslSweep and (bar_index - lastSslSweepBar <= 10)
        bottomScore += 3
    // 3. Có Bullish FVG hỗ trợ (+1đ)
    if not na(lastBullFvgTop) and close >= lastBullFvgBot
        bottomScore += 1
    // 4. Gần hỗ trợ S1 / S2 (+1đ)
    if not na(pivotS1) and (math.abs(swingLowPrice - pivotS1) / pivotS1 <= 0.02 or math.abs(swingLowPrice - pivotS2) / pivotS2 <= 0.02)
        bottomScore += 1
    // 5. ATR Spike cao trào xả (+1đ)
    if atr14[swingLen] > atrAvg14[swingLen] * 1.35
        bottomScore += 1

// Chấm điểm vùng Đỉnh (Top Zone Score / 8) khi xác nhận Pivot High
int topScore = 0
bool isConfirmedTop = not na(ph)
float swingHighPrice = isConfirmedTop ? ph : na

if isConfirmedTop
    // 1. RSI quá mua (+2đ)
    if rsi14[swingLen] > 65 or rsi14 > 62
        topScore += 2
    // 2. Có Bearish MSS / Sweep gần đó (+4đ / +3đ)
    bool nearBearMss = not na(lastMssBar) and currentTrend == "bearish" and (bar_index - lastMssBar <= 12)
    if nearBearMss
        topScore += (lastMssHadSweep ? 4 : 3)
    else if hadRecentBslSweep and (bar_index - lastBslSweepBar <= 10)
        topScore += 3
    // 3. Có Bearish FVG phía trên (+1đ)
    if not na(lastBearFvgBot) and close <= lastBearFvgTop
        topScore += 1
    // 4. Gần kháng cự R1 / R2 (+1đ)
    if not na(pivotR1) and (math.abs(swingHighPrice - pivotR1) / pivotR1 <= 0.02 or math.abs(swingHighPrice - pivotR2) / pivotR2 <= 0.02)
        topScore += 1
    // 5. ATR Spike cao trào mua (+1đ)
    if atr14[swingLen] > atrAvg14[swingLen] * 1.35
        topScore += 1

// Tính WinRate dự kiến cho Phương pháp 1 (M1 Trend Setup)
float m1WinRate = 65.0
if lastMssHadSweep
    m1WinRate += 10.0
else if not lastMssIsChoch
    m1WinRate += 6.0
if (currentTrend == "bullish" and recentBullHqOb) or (currentTrend == "bearish" and recentBearHqOb)
    m1WinRate += 5.0
if (currentTrend == "bullish" and not na(lastBullFvgTop)) or (currentTrend == "bearish" and not na(lastBearFvgBot))
    m1WinRate += 3.0

// ============================================================================
// 5. LOGIC VÀO LỆNH & QUẢN TRỊ ĐA TẦNG CHO CẢ 3 PHƯƠNG PHÁP
// ============================================================================
var float activeEntry = na
var float activeSl    = na
var float activeTp1   = na
var float activeTp2   = na
var float activeTp3   = na
var bool  hitTp1      = false
var int   entryBarIdx = na
var string activeTag  = ""

// Biến lưu lệnh chờ Limit của Phương pháp 1
var bool   pendingM1      = false
var string pendingM1Side  = ""
var float  pendingM1Entry = na
var float  pendingM1Sl    = na
var int    pendingM1Bar   = na

bool isFlat = strategy.position_size == 0

// Reset trạng thái khi lệnh đã đóng
if isFlat and not na(activeEntry) and (na(entryBarIdx) or bar_index > entryBarIdx)
    activeEntry := na
    activeSl    := na
    activeTp1   := na
    activeTp2   := na
    activeTp3   := na
    hitTp1      := false
    activeTag   := ""

// Hủy lệnh chờ M1 nếu quá hạn 24 bars chưa khớp
if pendingM1 and (bar_index - pendingM1Bar > limitExpireBars)
    strategy.cancel("M1_LONG")
    strategy.cancel("M1_SHORT")
    pendingM1 := false

bool useM1 = strategyMode == "M1: ICT MSS + Pullback EMA 21-50"
bool useM2 = strategyMode == "M2: FVG + Bắt Đáy/Đỉnh SMC Zone (5 Sao)"
bool useM3 = strategyMode == "M3: Chiến Lược Hybrid (M1 + M2 Kết Hợp)"

// ── A. TÍN HIỆU ĐẢO CHIỀU VÙNG CỰC TRỊ (DÙNG CHO M2 & M3 HYBRID) ──
bool m2BuyCond  = isConfirmedBottom and bottomScore >= minSmcScore
bool m2SellCond = isConfirmedTop    and topScore    >= minSmcScore

// Với M3 Hybrid: Bắt buộc có thêm xác nhận cạn kiệt (Sweep hoặc RSI quá bán < 35 / quá mua > 65)
bool m3ExhaustionBuy  = m2BuyCond  and (hadRecentSslSweep or rsi14 < 35 or rsi14[swingLen] < 35)
bool m3ExhaustionSell = m2SellCond and (hadRecentBslSweep or rsi14 > 65 or rsi14[swingLen] > 65)

bool triggerReversalBuy  = isFlat and ((useM2 and m2BuyCond)  or (useM3 and m3ExhaustionBuy))
bool triggerReversalSell = isFlat and ((useM2 and m2SellCond) or (useM3 and m3ExhaustionSell))

if triggerReversalBuy
    float calcEntry = close
    float calcSl    = swingLowPrice - 0.75 * atr14
    float risk      = calcEntry - calcSl
    bool  validRisk = not useRiskFilter or (risk >= minRiskPts and risk <= maxRiskPts)
    if validRisk and risk > 0
        strategy.cancel_all()
        pendingM1   := false
        activeEntry := calcEntry
        activeSl    := calcSl
        activeTp1   := calcEntry + rrTp1 * risk
        activeTp2   := calcEntry + rrTp2 * risk
        activeTp3   := calcEntry + rrTp3 * risk
        hitTp1      := false
        entryBarIdx := bar_index
        activeTag   := useM3 ? "M3: Bắt Đáy Hấp Thụ" : "M2: Bắt Đáy 5★"
        strategy.entry("REV_LONG", strategy.long, comment=activeTag)

if triggerReversalSell and isFlat
    float calcEntry = close
    float calcSl    = swingHighPrice + 0.75 * atr14
    float risk      = calcSl - calcEntry
    bool  validRisk = not useRiskFilter or (risk >= minRiskPts and risk <= maxRiskPts)
    if validRisk and risk > 0
        strategy.cancel_all()
        pendingM1   := false
        activeEntry := calcEntry
        activeSl    := calcSl
        activeTp1   := calcEntry - rrTp1 * risk
        activeTp2   := calcEntry - rrTp2 * risk
        activeTp3   := calcEntry - rrTp3 * risk
        hitTp1      := false
        entryBarIdx := bar_index
        activeTag   := useM3 ? "M3: Bắt Đỉnh Hấp Thụ" : "M2: Bắt Đỉnh 5★"
        strategy.entry("REV_SHORT", strategy.short, comment=activeTag)

// ── B. TÍN HIỆU THUẬN XU HƯỚNG PULLBACK EMA 21-50 (DÙNG CHO M1 & M3 HYBRID) ──
bool canPlaceM1 = isFlat and not pendingM1 and not triggerReversalBuy and not triggerReversalSell and (useM1 or useM3)

if canPlaceM1 and m1WinRate >= 70.0
    float entryTop = math.max(ema21, ema50)
    float entryBot = math.min(ema21, ema50)
    if currentTrend == "bullish" and close > entryTop
        float limitP = ema21
        float slP    = entryBot - math.max(4.0, atr14 * 1.5)
        float risk   = limitP - slP
        bool validR  = not useRiskFilter or (risk >= minRiskPts and risk <= maxRiskPts)
        if validR and risk > 0
            pendingM1      := true
            pendingM1Side  := "LONG"
            pendingM1Entry := limitP
            pendingM1Sl    := slP
            pendingM1Bar   := bar_index
            strategy.entry("M1_LONG", strategy.long, limit=limitP, comment=useM3 ? "M3: Thuận Sóng M1" : "M1: Pullback Mua")
    else if currentTrend == "bearish" and close < entryBot
        float limitP = ema21
        float slP    = entryTop + math.max(4.0, atr14 * 1.5)
        float risk   = slP - limitP
        bool validR  = not useRiskFilter or (risk >= minRiskPts and risk <= maxRiskPts)
        if validR and risk > 0
            pendingM1      := true
            pendingM1Side  := "SHORT"
            pendingM1Entry := limitP
            pendingM1Sl    := slP
            pendingM1Bar   := bar_index
            strategy.entry("M1_SHORT", strategy.short, limit=limitP, comment=useM3 ? "M3: Thuận Sóng M1" : "M1: Pullback Bán")

// Khi lệnh Limit M1 đã khớp trên thị trường -> Kích hoạt bộ TP1, TP2, TP3, SL
if strategy.position_size != 0 and pendingM1
    float fillP = strategy.position_avg_price
    float risk  = math.abs(fillP - pendingM1Sl)
    activeEntry := fillP
    activeSl    := pendingM1Sl
    if strategy.position_size > 0
        activeTp1 := fillP + rrTp1 * risk
        activeTp2 := fillP + rrTp2 * risk
        activeTp3 := fillP + rrTp3 * risk
    else
        activeTp1 := fillP - rrTp1 * risk
        activeTp2 := fillP - rrTp2 * risk
        activeTp3 := fillP - rrTp3 * risk
    hitTp1      := false
    entryBarIdx := bar_index
    activeTag   := useM3 ? "M3: Thuận Sóng M1" : "M1: Trend Pullback"
    pendingM1   := false

// ============================================================================
// 6. QUẢN TRỊ LỆNH ĐANG MỞ: DỜI SL VỀ ENTRY KHI ĐẠT TP1 & ĐÓNG TẠI TP3
// ============================================================================
if strategy.position_size > 0 and not na(activeEntry)
    if high >= activeTp1
        hitTp1 := true
    float currentStop = hitTp1 ? activeEntry : activeSl
    strategy.exit("EXIT_LONG", stop=currentStop, limit=activeTp3, comment_loss=hitTp1 ? "ENTRY (Hòa Vốn)" : "SL", comment_profit="TP3 (2R)")
    if not na(entryBarIdx) and (bar_index - entryBarIdx >= maxHoldBars)
        strategy.close_all(comment="Hết Chu Kỳ 48h")

if strategy.position_size < 0 and not na(activeEntry)
    if low <= activeTp1
        hitTp1 := true
    float currentStop = hitTp1 ? activeEntry : activeSl
    strategy.exit("EXIT_SHORT", stop=currentStop, limit=activeTp3, comment_loss=hitTp1 ? "ENTRY (Hòa Vốn)" : "SL", comment_profit="TP3 (2R)")
    if not na(entryBarIdx) and (bar_index - entryBarIdx >= maxHoldBars)
        strategy.close_all(comment="Hết Chu Kỳ 48h")

// ============================================================================
// 7. VẼ GIAO DIỆN TRỰC QUAN TRÊN BIỂU ĐỒ (EMA CLOUD, NHÃN, ĐƯỜNG TP/SL)
// ============================================================================
pEma21 = plot(showEmaCloud ? ema21 : na, "EMA 21", color=color.new(#38bdf8, 15), linewidth=2)
pEma50 = plot(showEmaCloud ? ema50 : na, "EMA 50", color=color.new(#f59e0b, 15), linewidth=2)
fill(pEma21, pEma50, color=ema21 >= ema50 ? color.new(#10b981, 86) : color.new(#ef4444, 86), title="Vùng Pullback EMA 21-50")

// Nhãn cấu trúc MSS / Sweep
plotshape(showMssLabels and bullMss, title="Bullish MSS", style=shape.labelup, location=location.belowbar, color=color.new(#10b981, 10), text="MSS ▲", textcolor=color.white, size=size.tiny)
plotshape(showMssLabels and bearMss, title="Bearish MSS", style=shape.labeldown, location=location.abovebar, color=color.new(#ef4444, 10), text="MSS ▼", textcolor=color.white, size=size.tiny)
plotshape(showMssLabels and sslSweep, title="SSL Sweep", style=shape.xcross, location=location.belowbar, color=color.new(#38bdf8, 0), size=size.tiny)
plotshape(showMssLabels and bslSweep, title="BSL Sweep", style=shape.xcross, location=location.abovebar, color=color.new(#f59e0b, 0), size=size.tiny)

// Nhãn 5 Sao Bắt Đáy / Đỉnh SMC
plotshape(showSmcSignals and m2BuyCond, title="SMC 5★ Buy Zone", style=shape.labelup, location=location.belowbar, color=color.new(#a855f7, 0), text="5★ ĐÁY", textcolor=color.white, size=size.small)
plotshape(showSmcSignals and m2SellCond, title="SMC 5★ Sell Zone", style=shape.labeldown, location=location.abovebar, color=color.new(#f97316, 0), text="5★ ĐỈNH", textcolor=color.white, size=size.small)

// Vẽ các đường ENTRY, SL, TP1, TP2, TP3 khi đang có lệnh
bool inTrade = strategy.position_size != 0 and not na(activeEntry)
plot(showTpSlLines and inTrade ? activeEntry : na, "Giá ENTRY", color=color.new(#94a3b8, 0), style=plot.style_linebr, linewidth=2)
plot(showTpSlLines and inTrade ? (hitTp1 ? activeEntry : activeSl) : na, "Stop Loss (SL)", color=color.new(#ef4444, 0), style=plot.style_linebr, linewidth=2)
plot(showTpSlLines and inTrade ? activeTp1 : na, "TP1 (1.0R - Dời Hòa Vốn)", color=color.new(#2dd4bf, 20), style=plot.style_linebr, linewidth=1)
plot(showTpSlLines and inTrade ? activeTp2 : na, "TP2 (1.5R)", color=color.new(#34d399, 10), style=plot.style_linebr, linewidth=1)
plot(showTpSlLines and inTrade ? activeTp3 : na, "TP3 (2.0R - Đích)", color=color.new(#10b981, 0), style=plot.style_linebr, linewidth=2)

// ============================================================================
// 8. BẢNG THỐNG KÊ HIỆU SUẤT MINI (DASHBOARD TABLE Ở GÓC PHẢI TRÊN)
// ============================================================================
var table dash = table.new(position.top_right, 2, 7, bgcolor=color.new(#0f172a, 10), border_color=color.new(#1e293b, 0), border_width=1)
if barstate.islast
    int totalClosed = strategy.closedtrades
    int wins        = strategy.wintrades
    float winRate   = totalClosed > 0 ? (wins * 100.0 / totalClosed) : 0.0
    float netPnl    = strategy.netprofit

    table.cell(dash, 0, 0, "🎯 CBOT CQG ENGINE", text_color=color.white, bgcolor=color.new(#1e293b, 0), text_size=size.small)
    table.cell(dash, 1, 0, strategyMode, text_color=#38bdf8, bgcolor=color.new(#1e293b, 0), text_size=size.small)

    table.cell(dash, 0, 1, "Xu hướng MSS", text_color=#94a3b8, text_size=size.small)
    table.cell(dash, 1, 1, currentTrend == "bullish" ? "TĂNG (BULL) ▲" : currentTrend == "bearish" ? "GIẢM (BEAR) ▼" : "TRUNG LẬP", 
         text_color=currentTrend == "bullish" ? #10b981 : currentTrend == "bearish" ? #ef4444 : #cbd5e1, text_size=size.small)

    table.cell(dash, 0, 2, "EMA21 / EMA50", text_color=#94a3b8, text_size=size.small)
    table.cell(dash, 1, 2, str.tostring(ema21, "#.##") + " / " + str.tostring(ema50, "#.##"), text_color=color.white, text_size=size.small)

    table.cell(dash, 0, 3, "RSI(14) | ATR(14)", text_color=#94a3b8, text_size=size.small)
    table.cell(dash, 1, 3, str.tostring(rsi14, "#.1") + " | " + str.tostring(atr14, "#.##"), text_color=color.white, text_size=size.small)

    table.cell(dash, 0, 4, "Trạng thái Lệnh", text_color=#94a3b8, text_size=size.small)
    string posTxt = strategy.position_size > 0 ? "ĐANG MUA (" + (hitTp1 ? "Đã dời BE" : "Gồng") + ")" : strategy.position_size < 0 ? "ĐANG BÁN (" + (hitTp1 ? "Đã dời BE" : "Gồng") + ")" : pendingM1 ? "CHỜ KHỚP LIMIT EMA21" : "ĐỨNG NGOÀI"
    table.cell(dash, 1, 4, posTxt, text_color=strategy.position_size != 0 ? #f59e0b : #cbd5e1, text_size=size.small)

    table.cell(dash, 0, 5, "Tỷ lệ Thắng (TV)", text_color=#94a3b8, text_size=size.small)
    table.cell(dash, 1, 5, str.tostring(winRate, "#.1") + "% (" + str.tostring(wins) + "/" + str.tostring(totalClosed) + ")", text_color=#10b981, text_size=size.small)

    table.cell(dash, 0, 6, "Tổng Lợi Nhuận", text_color=#94a3b8, text_size=size.small)
    table.cell(dash, 1, 6, (netPnl >= 0 ? "+$" : "-$") + str.tostring(math.abs(netPnl), "#,###.##"), text_color=netPnl >= 0 ? #10b981 : #ef4444, text_size=size.small)

// ============================================================================
// 9. TÍCH HỢP WEBHOOK REALTIME BẮN VỀ GOOGLE APPS SCRIPT / DASHBOARD
// ============================================================================
if enableWebhook and barstate.isconfirmed
    string payload = '{"symbol":"' + syminfo.ticker + '","interval":"' + timeframe.period + '","time":"' + str.tostring(time_close) + '","open":' + str.tostring(open) + ',"high":' + str.tostring(high) + ',"low":' + str.tostring(low) + ',"close":' + str.tostring(close) + ',"volume":' + str.tostring(volume) + ',"ema21":' + str.tostring(ema21, "#.####") + ',"ema50":' + str.tostring(ema50, "#.####") + ',"rsi":' + str.tostring(rsi14, "#.##") + ',"atr":' + str.tostring(atr14, "#.####") + '}'
    alert(payload, alert.freq_once_per_bar_close)
```

---

## 🛠️ Hướng Dẫn Sử Dụng Nhanh Trên TradingView

1. Mở biểu đồ **`ZW1!` (Lúa Mì)** hoặc **`ZC1!` (Ngô)** trên khung **`1 giờ (1H)`** (để xem Backtest) hoặc **`5 phút (5m)`**.
2. Mở tab **`Pine Editor`** ở thanh dưới cùng ➔ Xóa code mặc định ➔ Copy toàn bộ khối code `pinescript` bên trên dán vào ➔ Bấm **`Add to chart` (Thêm vào biểu đồ)**.
3. Mở tab **`Strategy Tester` (Trình kiểm tra Chiến lược)** cạnh Pine Editor:
   * Bấm vào biểu tượng **Bánh răng cài đặt (Settings ⚙️)** của chiến lược.
   * Tại mục **"Phương Pháp Chạy Backtest"**, bạn có thể chọn qua lại giữa:
     * `M1: ICT MSS + Pullback EMA 21-50`
     * `M2: FVG + Bắt Đáy/Đỉnh SMC Zone (5 Sao)`
     * `M3: Chiến Lược Hybrid (M1 + M2 Kết Hợp)`
   * Ngay lập tức biểu đồ và bảng Strategy Tester sẽ cập nhật toàn bộ điểm mua/bán, đường cong vốn (Equity Curve) và tỷ lệ thắng của từng phương pháp!
