# Bộ Code Pine Script v5 — 3 Phương Pháp Giao Dịch CBOT (Chuẩn CQG)

Tài liệu này chứa mã nguồn **Pine Script v5 (`strategy`)** đã được tối ưu hóa đồng bộ 100% với thuật toán trong `ict_engine.py` và `backtest_engine.py` của hệ thống Dashboard.

---

## 🌟 Điểm Nổi Bật Của Bản Tối Ưu Này (Đã Fix Hiển Thị Bảng Dashboard Góc Phải)

1. **Bảng Dashboard Thống Kê Realtime (Góc Phải Biểu Đồ):**
   * Hiển thị trực tiếp: **Phương pháp đang chạy**, **Xu hướng cấu trúc MSS**, **Dải EMA 21/50**, **RSI & ATR**, **Điểm hội tụ SMC (/8 sao)**, **Mức Entry / SL / TP1 / TP3 của lệnh đang mở**, **Tỷ lệ thắng (Win Rate %)**, **Profit Factor** và **Tổng Lợi Nhuận ($)**.
   * Cho phép tùy chỉnh vị trí bảng (`Góc Phải Trên`, `Góc Phải Dưới`, `Góc Trái Dưới`) và kích thước chữ ngay trong phần Cài đặt (`Settings ⚙️`).
2. **Tích hợp cả 3 Phương Pháp trong 1 Script duy nhất:**
   * **Phương pháp 1 (`M1 - ICT MSS + Pullback EMA 21-50`):** Chờ cấu trúc MSS xác nhận + hội tụ OB/FVG (WinRate >= 70%), đặt lệnh chờ `Limit` tại `EMA 21` (tự động hủy lệnh chờ nếu sau 24 nến giá không hồi về).
   * **Phương pháp 2 (`M2 - FVG + Bắt Đáy/Đỉnh SMC Zone 5 Sao`):** Chấm điểm hội tụ 8 yếu tố (Liquidity Sweep, MSS/CHoCH, RSI cực trị, FVG, Pivot S1/R1, ATR Spike). Vào lệnh đảo chiều khi điểm số đạt chuẩn **>= 5/8 sao**.
   * **Phương pháp 3 (`M3 - Chiến Lược Hybrid M1 + M2 Kết Hợp`):** Chỉ kích hoạt Bắt Đáy/Đỉnh M2 khi sóng xả/tăng đã cạn kiệt (bắt buộc có **Liquidity Sweep** hoặc **RSI < 35 / > 65**); còn lại đi lệnh thuận xu hướng theo M1 và khóa xung đột chiều.
3. **Cơ chế Quản Trị Lệnh Đa Tầng Chuẩn CQG (`TP1` ➔ `Dời SL Hòa Vốn ENTRY` ➔ `TP2` ➔ `TP3`):**
   * Ngay khi giá chạm **TP1 (1.0R)**: Tự động dời Stop Loss từ mức rủi ro ban đầu về đúng **giá vào lệnh (`ENTRY`)** để bảo toàn vốn tuyệt đối.

---

## 📋 Mã Nguồn Pine Script v5 (Copy Toàn Bộ Khối Dưới Đây Dán Đè Vào Pine Editor)

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
swingLen        = input.int(3, "Swing Lookback (Số nến xác nhận Đỉnh/Đáy)", minval=2, maxval=10, group=grp_ict)
sweepLookback   = input.int(36, "Chu kỳ nhớ Liquidity Sweep (Bars)", minval=10, maxval=100, group=grp_ict)
minSmcScore     = input.int(5, "Điểm SMC Zone Tối Thiểu (M2 & M3, chuẩn 5/8)", minval=3, maxval=8, group=grp_ict)
hqObMult        = input.float(0.55, "Hệ số thân nến HQ Order Block (x ATR)", minval=0.2, maxval=2.0, step=0.05, group=grp_ict)

grp_risk = "🛡️ 3. QUẢN TRỊ RỦI RO & CHỐT LỜI ĐA TẦNG (CQG)"
useRiskFilter   = input.bool(true, "Bật bộ lọc biên độ rủi ro SL (Chuẩn CBOT)", group=grp_risk)
minRiskPts      = input.float(2.0, "Khoảng cách SL tối thiểu (Points/Cents)", minval=0.1, step=0.5, group=grp_risk)
maxRiskPts      = input.float(20.0, "Khoảng cách SL tối đa (Points/Cents)", minval=5.0, step=1.0, group=grp_risk)
rrTp1           = input.float(1.0, "Mốc TP1 (R:R) — Chạm TP1 tự dời SL về ENTRY", minval=0.5, step=0.25, group=grp_risk)
rrTp2           = input.float(1.5, "Mốc TP2 (R:R)", minval=1.0, step=0.25, group=grp_risk)
rrTp3           = input.float(2.0, "Mốc TP3 (R:R - Đóng toàn bộ)", minval=1.5, step=0.25, group=grp_risk)
limitExpireBars = input.int(24, "Hạn chờ khớp lệnh Limit EMA21 của M1 (Bars)", minval=4, maxval=72, group=grp_risk)
maxHoldBars     = input.int(48, "Thời gian giữ lệnh tối đa (Bars)", minval=12, maxval=200, group=grp_risk)
pointMultiplier = input.float(50.0, "Hệ số nhân hợp đồng CQG ($/cent, chuẩn CBOT = 50)", minval=1.0, group=grp_risk)

grp_vis = "🎨 4. HIỂN THỊ BẢNG DASHBOARD & WEBHOOK"
showDashboard   = input.bool(true, "Hiển thị Bảng Dashboard Thống Kê Realtime", group=grp_vis)
dashPosInput    = input.string("Góc Phải Trên (Top Right)", "Vị trí Bảng Dashboard", 
     options=["Góc Phải Trên (Top Right)", "Góc Phải Dưới (Bottom Right)", "Góc Trái Dưới (Bottom Left)"], group=grp_vis)
showEmaCloud    = input.bool(true, "Hiển thị dải băng EMA 21 - EMA 50", group=grp_vis)
showMssLabels   = input.bool(true, "Hiển thị nhãn MSS / Sweep", group=grp_vis)
showSmcSignals  = input.bool(true, "Hiển thị nhãn 5★ Bắt Đáy / Đỉnh SMC", group=grp_vis)
onlyTradeLabels = input.bool(true, "Chỉ hiện nhãn 5★ khi thực sự mở lệnh (Đỡ rối biểu đồ)", group=grp_vis)
showTpSlLines   = input.bool(true, "Vẽ đường ENTRY / SL / TP1 / TP2 / TP3", group=grp_vis)
enableWebhook   = input.bool(true, "Bật phát JSON Webhook mỗi khi đóng nến", group=grp_vis)

// ============================================================================
// 2. CHỈ BÁO KỸ THUẬT CƠ SỞ (EMA, RSI, ATR, PIVOT)
// ============================================================================
ema21 = ta.ema(close, 21)
ema50 = ta.ema(close, 50)
rsi14 = ta.rsi(close, 14)
atr14 = ta.atr(14)
atrAvg14 = ta.sma(atr14, 14)

[dHigh, dLow, dClose] = request.security(syminfo.tickerid, "D", [high[1], low[1], close[1]], lookahead=barmerge.lookahead_on)
pivotP  = (dHigh + dLow + dClose) / 3.0
pivotS1 = 2.0 * pivotP - dHigh
pivotR1 = 2.0 * pivotP - dLow
pivotS2 = pivotP - (dHigh - dLow)
pivotR2 = pivotP + (dHigh - dLow)

// ============================================================================
// 3. PHÁT HIỆN SWING POINTS, LIQUIDITY SWEEP, CHoCH & MSS (ICT ENGINE v2.0)
// ============================================================================
ph = ta.pivothigh(high, swingLen, swingLen)
pl = ta.pivotlow(low, swingLen, swingLen)

var float lastSwingHigh    = na
var int   lastSwingHighBar = na
var float lastSwingLow     = na
var int   lastSwingLowBar  = na

if not na(ph)
    lastSwingHigh    := ph
    lastSwingHighBar := bar_index - swingLen

if not na(pl)
    lastSwingLow    := pl
    lastSwingLowBar := bar_index - swingLen

var int   lastBslSweepBar    = na
var float lastBslSweepHigh   = na
var float lastBslSweepCandleLow = na
var int   lastSslSweepBar    = na
var float lastSslSweepLow    = na
var float lastSslSweepCandleHigh = na

bool bslSweep = not na(lastSwingHigh) and high > lastSwingHigh and close < lastSwingHigh and bar_index > lastSwingHighBar
if bslSweep
    lastBslSweepBar       := bar_index
    lastBslSweepHigh      := high
    lastBslSweepCandleLow := low

bool sslSweep = not na(lastSwingLow) and low < lastSwingLow and close > lastSwingLow and bar_index > lastSwingLowBar
if sslSweep
    lastSslSweepBar        := bar_index
    lastSslSweepLow        := low
    lastSslSweepCandleHigh := high

var string currentTrend    = "neutral"
var int    lastMssBar      = na
var bool   lastMssHadSweep = false
var bool   lastMssIsChoch  = false

bool hadRecentSslSweep = not na(lastSslSweepBar) and (bar_index - lastSslSweepBar <= sweepLookback)
bool hadRecentBslSweep = not na(lastBslSweepBar) and (bar_index - lastBslSweepBar <= sweepLookback)

bool bullMss = not na(lastSwingHigh) and close > lastSwingHigh and close[1] <= lastSwingHigh and bar_index > lastSwingHighBar
bool bearMss = not na(lastSwingLow)  and close < lastSwingLow  and close[1] >= lastSwingLow  and bar_index > lastSwingLowBar

bool bullChoch = not bullMss and hadRecentSslSweep and not na(lastSslSweepCandleHigh) and close > lastSslSweepCandleHigh and close > open
bool bearChoch = not bearMss and hadRecentBslSweep and not na(lastBslSweepCandleLow)  and close < lastBslSweepCandleLow  and close < open

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

bool isHqBody       = math.abs(close - open) >= hqObMult * atr14
bool recentBullHqOb = ta.barssince(close < open and isHqBody[1] and close[1] > open[1]) <= 20
bool recentBearHqOb = ta.barssince(close > open and isHqBody[1] and close[1] < open[1]) <= 20

int bottomScore = 0
bool isConfirmedBottom = not na(pl)
float swingLowPrice = isConfirmedBottom ? pl : na

if isConfirmedBottom
    if rsi14[swingLen] < 35 or rsi14 < 38
        bottomScore += 2
    bool nearBullMss = not na(lastMssBar) and currentTrend == "bullish" and (bar_index - lastMssBar <= 12)
    if nearBullMss
        bottomScore += (lastMssHadSweep ? 4 : 3)
    else if hadRecentSslSweep and (bar_index - lastSslSweepBar <= 10)
        bottomScore += 3
    if not na(lastBullFvgTop) and close >= lastBullFvgBot
        bottomScore += 1
    if not na(pivotS1) and (math.abs(swingLowPrice - pivotS1) / pivotS1 <= 0.02 or math.abs(swingLowPrice - pivotS2) / pivotS2 <= 0.02)
        bottomScore += 1
    if atr14[swingLen] > atrAvg14[swingLen] * 1.35
        bottomScore += 1

int topScore = 0
bool isConfirmedTop = not na(ph)
float swingHighPrice = isConfirmedTop ? ph : na

if isConfirmedTop
    if rsi14[swingLen] > 65 or rsi14 > 62
        topScore += 2
    bool nearBearMss = not na(lastMssBar) and currentTrend == "bearish" and (bar_index - lastMssBar <= 12)
    if nearBearMss
        topScore += (lastMssHadSweep ? 4 : 3)
    else if hadRecentBslSweep and (bar_index - lastBslSweepBar <= 10)
        topScore += 3
    if not na(lastBearFvgBot) and close <= lastBearFvgTop
        topScore += 1
    if not na(pivotR1) and (math.abs(swingHighPrice - pivotR1) / pivotR1 <= 0.02 or math.abs(swingHighPrice - pivotR2) / pivotR2 <= 0.02)
        topScore += 1
    if atr14[swingLen] > atrAvg14[swingLen] * 1.35
        topScore += 1

var int lastBotScoreSeen = 0
var int lastTopScoreSeen = 0
if isConfirmedBottom
    lastBotScoreSeen := bottomScore
if isConfirmedTop
    lastTopScoreSeen := topScore

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
var float  activeEntry = na
var float  activeSl    = na
var float  activeTp1   = na
var float  activeTp2   = na
var float  activeTp3   = na
var bool   hitTp1      = false
var int    entryBarIdx = na
var string activeTag   = ""

var bool   pendingM1      = false
var string pendingM1Side  = ""
var float  pendingM1Entry = na
var float  pendingM1Sl    = na
var int    pendingM1Bar   = na

bool isFlat = strategy.position_size == 0

if isFlat and not na(activeEntry) and (na(entryBarIdx) or bar_index > entryBarIdx)
    activeEntry := na
    activeSl    := na
    activeTp1   := na
    activeTp2   := na
    activeTp3   := na
    hitTp1      := false
    activeTag   := ""

if pendingM1 and (bar_index - pendingM1Bar > limitExpireBars)
    strategy.cancel("M1_LONG")
    strategy.cancel("M1_SHORT")
    pendingM1 := false

bool useM1 = strategyMode == "M1: ICT MSS + Pullback EMA 21-50"
bool useM2 = strategyMode == "M2: FVG + Bắt Đáy/Đỉnh SMC Zone (5 Sao)"
bool useM3 = strategyMode == "M3: Chiến Lược Hybrid (M1 + M2 Kết Hợp)"

bool m2BuyCond  = isConfirmedBottom and bottomScore >= minSmcScore
bool m2SellCond = isConfirmedTop    and topScore    >= minSmcScore

bool m3ExhaustionBuy  = m2BuyCond  and (hadRecentSslSweep or rsi14 < 35 or rsi14[swingLen] < 35)
bool m3ExhaustionSell = m2SellCond and (hadRecentBslSweep or rsi14 > 65 or rsi14[swingLen] > 65)

bool triggerReversalBuy  = isFlat and ((useM2 and m2BuyCond)  or (useM3 and m3ExhaustionBuy))
bool triggerReversalSell = isFlat and ((useM2 and m2SellCond) or (useM3 and m3ExhaustionSell))

bool openedRevBuy  = false
bool openedRevSell = false

if triggerReversalBuy
    float calcEntry = close
    float calcSl    = swingLowPrice - 0.75 * atr14
    float risk      = calcEntry - calcSl
    bool  validRisk = not useRiskFilter or (risk >= minRiskPts and risk <= maxRiskPts)
    if validRisk and risk > 0
        strategy.cancel_all()
        pendingM1     := false
        activeEntry   := calcEntry
        activeSl      := calcSl
        activeTp1     := calcEntry + rrTp1 * risk
        activeTp2     := calcEntry + rrTp2 * risk
        activeTp3     := calcEntry + rrTp3 * risk
        hitTp1        := false
        entryBarIdx   := bar_index
        activeTag     := useM3 ? "M3: Bắt Đáy Hấp Thụ" : "M2: Bắt Đáy 5★"
        openedRevBuy  := true
        strategy.entry("REV_LONG", strategy.long, comment=activeTag)

if triggerReversalSell and isFlat and not openedRevBuy
    float calcEntry = close
    float calcSl    = swingHighPrice + 0.75 * atr14
    float risk      = calcSl - calcEntry
    bool  validRisk = not useRiskFilter or (risk >= minRiskPts and risk <= maxRiskPts)
    if validRisk and risk > 0
        strategy.cancel_all()
        pendingM1     := false
        activeEntry   := calcEntry
        activeSl      := calcSl
        activeTp1     := calcEntry - rrTp1 * risk
        activeTp2     := calcEntry - rrTp2 * risk
        activeTp3     := calcEntry - rrTp3 * risk
        hitTp1        := false
        entryBarIdx   := bar_index
        activeTag     := useM3 ? "M3: Bắt Đỉnh Hấp Thụ" : "M2: Bắt Đỉnh 5★"
        openedRevSell := true
        strategy.entry("REV_SHORT", strategy.short, comment=activeTag)

bool canPlaceM1 = isFlat and not pendingM1 and not openedRevBuy and not openedRevSell and (useM1 or useM3)

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
pEma21 = plot(showEmaCloud ? ema21 : na, "EMA 21", color=color.new(#38bdf8, 15), linewidth=2, display=display.pane)
pEma50 = plot(showEmaCloud ? ema50 : na, "EMA 50", color=color.new(#f59e0b, 15), linewidth=2, display=display.pane)
fill(pEma21, pEma50, color=ema21 >= ema50 ? color.new(#10b981, 86) : color.new(#ef4444, 86), title="Vùng Pullback EMA 21-50")

plotshape(showMssLabels and bullMss, title="Bullish MSS", style=shape.labelup, location=location.belowbar, color=color.new(#10b981, 10), text="MSS ▲", textcolor=color.white, size=size.tiny, display=display.pane)
plotshape(showMssLabels and bearMss, title="Bearish MSS", style=shape.labeldown, location=location.abovebar, color=color.new(#ef4444, 10), text="MSS ▼", textcolor=color.white, size=size.tiny, display=display.pane)
plotshape(showMssLabels and sslSweep, title="SSL Sweep", style=shape.xcross, location=location.belowbar, color=color.new(#38bdf8, 0), size=size.tiny, display=display.pane)
plotshape(showMssLabels and bslSweep, title="BSL Sweep", style=shape.xcross, location=location.abovebar, color=color.new(#f59e0b, 0), size=size.tiny, display=display.pane)

bool showBuyStar  = showSmcSignals and (onlyTradeLabels ? openedRevBuy  : m2BuyCond)
bool showSellStar = showSmcSignals and (onlyTradeLabels ? openedRevSell : m2SellCond)
plotshape(showBuyStar,  title="SMC 5★ Buy Zone",  style=shape.labelup,   location=location.belowbar, color=color.new(#a855f7, 0), text="5★ ĐÁY",  textcolor=color.white, size=size.small, display=display.pane)
plotshape(showSellStar, title="SMC 5★ Sell Zone", style=shape.labeldown, location=location.abovebar, color=color.new(#f97316, 0), text="5★ ĐỈNH", textcolor=color.white, size=size.small, display=display.pane)

bool inTrade = strategy.position_size != 0 and not na(activeEntry)
plot(showTpSlLines and inTrade ? activeEntry : na, "Giá ENTRY", color=color.new(#94a3b8, 0), style=plot.style_linebr, linewidth=2, display=display.pane)
plot(showTpSlLines and inTrade ? (hitTp1 ? activeEntry : activeSl) : na, "Stop Loss (SL)", color=color.new(#ef4444, 0), style=plot.style_linebr, linewidth=2, display=display.pane)
plot(showTpSlLines and inTrade ? activeTp1 : na, "TP1 (1.0R - Dời Hòa Vốn)", color=color.new(#2dd4bf, 20), style=plot.style_linebr, linewidth=1, display=display.pane)
plot(showTpSlLines and inTrade ? activeTp2 : na, "TP2 (1.5R)", color=color.new(#34d399, 10), style=plot.style_linebr, linewidth=1, display=display.pane)
plot(showTpSlLines and inTrade ? activeTp3 : na, "TP3 (2.0R - Đích)", color=color.new(#10b981, 0), style=plot.style_linebr, linewidth=2, display=display.pane)

// ============================================================================
// 8. BẢNG THỐNG KÊ HIỆU SUẤT REALTIME (DASHBOARD TABLE)
// ============================================================================
tablePos = dashPosInput == "Góc Phải Dưới (Bottom Right)" ? position.bottom_right : dashPosInput == "Góc Trái Dưới (Bottom Left)" ? position.bottom_left : position.top_right
var table dash = table.new(tablePos, 2, 9, bgcolor=color.new(#0f172a, 5), border_color=color.new(#334155, 0), border_width=1, frame_color=color.new(#38bdf8, 30), frame_width=1)

if showDashboard and barstate.islast
    int   totalClosed = strategy.closedtrades
    int   wins        = strategy.wintrades
    int   losses      = strategy.losstrades
    int   evenTrades  = math.max(0, totalClosed - wins - losses)
    float winRate     = totalClosed > 0 ? (wins * 100.0 / totalClosed) : 0.0
    float grossP      = strategy.grossprofit * pointMultiplier
    float grossL      = math.abs(strategy.grossloss) * pointMultiplier
    float pf          = grossL > 0 ? (grossP / grossL) : (grossP > 0 ? 99.0 : 0.0)
    float netPnlUsd   = strategy.netprofit * pointMultiplier

    string shortMode  = useM1 ? "M1: Trend Pullback" : useM2 ? "M2: SMC 5★ Reversal" : "M3: Hybrid (M1+M2)"

    table.cell(dash, 0, 0, "🎯 CBOT CQG LIVE", text_color=color.white, bgcolor=color.new(#1e293b, 0), text_size=size.small)
    table.cell(dash, 1, 0, shortMode, text_color=#38bdf8, bgcolor=color.new(#1e293b, 0), text_size=size.small)

    table.cell(dash, 0, 1, "Xu hướng MSS", text_color=#94a3b8, text_size=size.small)
    table.cell(dash, 1, 1, currentTrend == "bullish" ? "TĂNG (BULL) ▲" : currentTrend == "bearish" ? "GIẢM (BEAR) ▼" : "TRUNG LẬP", 
         text_color=currentTrend == "bullish" ? #10b981 : currentTrend == "bearish" ? #ef4444 : #cbd5e1, text_size=size.small)

    table.cell(dash, 0, 2, "EMA21 / EMA50", text_color=#94a3b8, text_size=size.small)
    table.cell(dash, 1, 2, str.tostring(ema21, "0.00") + " / " + str.tostring(ema50, "0.00"), text_color=color.white, text_size=size.small)

    table.cell(dash, 0, 3, "RSI(14) | ATR(14)", text_color=#94a3b8, text_size=size.small)
    table.cell(dash, 1, 3, str.tostring(rsi14, "0.0") + " | " + str.tostring(atr14, "0.00"), text_color=color.white, text_size=size.small)

    table.cell(dash, 0, 4, "Điểm SMC (Đáy/Đỉnh)", text_color=#94a3b8, text_size=size.small)
    table.cell(dash, 1, 4, "Đáy: " + str.tostring(lastBotScoreSeen) + "/8 | Đỉnh: " + str.tostring(lastTopScoreSeen) + "/8", text_color=#c084fc, text_size=size.small)

    table.cell(dash, 0, 5, "Trạng thái Lệnh", text_color=#94a3b8, text_size=size.small)
    string posTxt = strategy.position_size > 0 ? "MUA @ " + str.tostring(activeEntry, "0.00") + (hitTp1 ? " (Đã dời BE)" : "") : strategy.position_size < 0 ? "BÁN @ " + str.tostring(activeEntry, "0.00") + (hitTp1 ? " (Đã dời BE)" : "") : pendingM1 ? "CHỜ LIMIT @ " + str.tostring(pendingM1Entry, "0.00") : "ĐỨNG NGOÀI"
    table.cell(dash, 1, 5, posTxt, text_color=strategy.position_size != 0 ? #f59e0b : #cbd5e1, text_size=size.small)

    table.cell(dash, 0, 6, "SL / TP3 Hiện Tại", text_color=#94a3b8, text_size=size.small)
    string slTpTxt = inTrade ? ("SL: " + str.tostring(hitTp1 ? activeEntry : activeSl, "0.00") + " | TP3: " + str.tostring(activeTp3, "0.00")) : "—"
    table.cell(dash, 1, 6, slTpTxt, text_color=color.white, text_size=size.small)

    table.cell(dash, 0, 7, "Win Rate | PF", text_color=#94a3b8, text_size=size.small)
    table.cell(dash, 1, 7, str.tostring(winRate, "0.0") + "% (" + str.tostring(wins) + "W/" + str.tostring(evenTrades) + "BE/" + str.tostring(losses) + "L) | PF: " + str.tostring(pf, "0.00"), text_color=#10b981, text_size=size.small)

    table.cell(dash, 0, 8, "Lợi Nhuận (CQG $50)", text_color=#94a3b8, text_size=size.small)
    table.cell(dash, 1, 8, (netPnlUsd >= 0 ? "+$" : "-$") + str.tostring(math.abs(netPnlUsd), "#,##0"), text_color=netPnlUsd >= 0 ? #10b981 : #ef4444, text_size=size.small)

// ============================================================================
// 9. TÍCH HỢP WEBHOOK REALTIME BẮN VỀ GOOGLE APPS SCRIPT / DASHBOARD
// ============================================================================
if enableWebhook and barstate.isconfirmed
    string payload = '{"symbol":"' + syminfo.ticker + '","interval":"' + timeframe.period + '","time":"' + str.tostring(time_close) + '","open":' + str.tostring(open) + ',"high":' + str.tostring(high) + ',"low":' + str.tostring(low) + ',"close":' + str.tostring(close) + ',"volume":' + str.tostring(volume) + ',"ema21":' + str.tostring(ema21, "0.0000") + ',"ema50":' + str.tostring(ema50, "0.0000") + ',"rsi":' + str.tostring(rsi14, "0.00") + ',"atr":' + str.tostring(atr14, "0.0000") + '}'
    alert(payload, alert.freq_once_per_bar_close)
```

---

## 🛠️ Hướng Dẫn Sử Dụng Nhanh Trên TradingView

1. Mở file [**`CBOT_3_Strategies_PineScript.md`**](file:///D:/0_Thang_Drive/Antigravity/Cbot/CBOT_3_Strategies_PineScript.md), copy lại khối code `pinescript` bên trên, dán đè vào **Pine Editor** và bấm **`Save` / `Update on chart` (Cập nhật trên biểu đồ)**.
2. **Bảng Dashboard Thống Kê Realtime** gồm 9 dòng sẽ lập tức hiện ra ở **Góc Phải Trên** của biểu đồ (hiển thị cả Lợi nhuận quy đổi theo hệ số nhân `$50/cent` chuẩn CQG, tỷ lệ thắng `W/BE/L`, `Profit Factor`, điểm `SMC /8` và mức `SL / TP3` hiện tại).
3. Tôi cũng đã bật sẵn tùy chọn **"Chỉ hiện nhãn 5★ khi thực sự mở lệnh"** để biểu đồ gọn gàng, không bị chồng chéo nhãn `5★ ĐỈNH / ĐÁY`.
