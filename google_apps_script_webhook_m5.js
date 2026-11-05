/**
 * ============================================================================
 * GOOGLE APPS SCRIPT — TRẠM NHẬN & PHÂN PHỐI NẾN M5 REALTIME TỪ TRADINGVIEW
 * ============================================================================
 * Hướng dẫn cài đặt (Chỉ làm 1 lần trên https://script.google.com):
 *   1. Mở https://script.google.com -> Bấm "Dự án mới" (New Project).
 *   2. Xóa toàn bộ code mặc định trong file Code.gs, dán toàn bộ code này vào.
 *   3. Bấm "Triển khai" (Deploy) -> "Tùy chọn triển khai mới" (New deployment).
 *   4. Chọn loại: "Ứng dụng web" (Web app):
 *      - Thực thi dưới dạng (Execute as): "Tôi" (Me)
 *      - Ai có quyền truy cập (Who has access): "Bất kỳ ai" (Anyone)
 *   5. Bấm "Triển khai" (Deploy) -> Copy đường link Web App URL:
 *      (Dạng: https://script.google.com/macros/s/AKfycb.../exec)
 *   6. Dán đường link này vào:
 *      - Ô "Webhook URL" khi tạo Alert trên TradingView (khung 5 phút - M5).
 *      - Ô "Cấu hình Link Google Webhook" trên trang Live Signal của Dashboard.
 * ============================================================================
 */

function normalizeSymbol(ticker) {
  var s = String(ticker || "").toUpperCase().trim();
  if (s.indexOf("ZW") === 0 || s.indexOf("WHEAT") !== -1) return "ZW";
  if (s.indexOf("ZC") === 0 || s.indexOf("CORN") !== -1) return "ZC";
  if (s.indexOf("ZS") === 0 || s.indexOf("SOY") !== -1) return "ZS";
  return s;
}

/**
 * 1. Nhận Webhook POST từ TradingView mỗi khi đóng nến M5 (5 phút)
 */
function doPost(e) {
  try {
    var rawBody = e.postData ? e.postData.contents : "{}";
    var payload = JSON.parse(rawBody);

    var ticker = payload.symbol || payload.ticker || "ZW";
    var sym = normalizeSymbol(ticker);

    var closePrice = parseFloat(payload.close || payload.price || 0);
    var openPrice  = parseFloat(payload.open  || closePrice);
    var highPrice  = parseFloat(payload.high  || closePrice);
    var lowPrice   = parseFloat(payload.low   || closePrice);
    var volume     = parseFloat(payload.volume || 0);
    var barTime    = payload.time || new Date().toISOString();
    var hourPrefix = String(barTime).substring(0, 13); // YYYY-MM-DDTHH

    var m5Candle = {
      symbol: sym,
      contract: ticker,
      interval: payload.interval || "M5",
      time: barTime,
      received_at: new Date().toISOString(),
      open: openPrice,
      high: highPrice,
      low: lowPrice,
      close: closePrice,
      volume: volume,
      ema21: payload.ema21 ? parseFloat(payload.ema21) : null,
      ema50: payload.ema50 ? parseFloat(payload.ema50) : null,
      rsi: payload.rsi ? parseFloat(payload.rsi) : null,
      atr: payload.atr ? parseFloat(payload.atr) : null
    };

    var props = PropertiesService.getScriptProperties();
    var storeRaw = props.getProperty("CBOT_M5_STORE");
    var store = storeRaw ? JSON.parse(storeRaw) : { status: "ok", symbols: {} };

    if (!store.symbols[sym]) {
      store.symbols[sym] = {
        latest_m5: null,
        forming_h1: null,
        history_m5: []
      };
    }

    var symObj = store.symbols[sym];
    symObj.latest_m5 = m5Candle;

    // Lưu lịch sử 36 nến M5 gần nhất (tương đương 3 giờ giao dịch)
    symObj.history_m5.push(m5Candle);
    if (symObj.history_m5.length > 36) {
      symObj.history_m5 = symObj.history_m5.slice(symObj.history_m5.length - 36);
    }

    // Tự động tổng hợp các nến M5 cùng giờ thành cây nến H1 đang chạy (Forming H1)
    var prevH1 = symObj.forming_h1;
    if (!prevH1 || String(prevH1.hour_prefix) !== hourPrefix) {
      symObj.forming_h1 = {
        hour_prefix: hourPrefix,
        time: hourPrefix.replace("T", " ") + ":00:00",
        open: openPrice,
        high: highPrice,
        low: lowPrice,
        close: closePrice,
        volume: volume,
        m5_count: 1
      };
    } else {
      prevH1.high = Math.max(prevH1.high, highPrice);
      prevH1.low = Math.min(prevH1.low, lowPrice);
      prevH1.close = closePrice;
      prevH1.volume = (prevH1.volume || 0) + volume;
      prevH1.m5_count = (prevH1.m5_count || 1) + 1;
      symObj.forming_h1 = prevH1;
    }

    store.updated_at = new Date().toISOString();
    props.setProperty("CBOT_M5_STORE", JSON.stringify(store));

    return ContentService.createTextOutput(JSON.stringify({
      status: "ok",
      symbol: sym,
      close: closePrice,
      forming_h1: symObj.forming_h1
    })).setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      message: err.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * 2. Trả dữ liệu JSON khi trang Online (thang-cbot.streamlit.app) hoặc Localhost gọi GET
 */
function doGet(e) {
  var props = PropertiesService.getScriptProperties();
  var storeRaw = props.getProperty("CBOT_M5_STORE");
  var data = storeRaw ? JSON.parse(storeRaw) : {
    status: "ok",
    updated_at: null,
    symbols: {}
  };
  return ContentService.createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}
