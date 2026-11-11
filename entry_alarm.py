import time
import datetime
import subprocess
import os
import sys
import pandas as pd
import requests
import pandas_market_calendars as mcal
import pytz
import json
import ict_engine
import threading
import backtest_engine

# ── Data Project Integration ──────────────────────────────────────────────────
_DATA_DIR = os.path.join(os.path.dirname(__file__), 'Data')
sys.path.insert(0, _DATA_DIR)
try:
    from data_config import OUTPUT_DIR as _DATA_OUTPUT_DIR
    _USE_DATA_PROJECT = True
except ImportError:
    _DATA_OUTPUT_DIR = None
    _USE_DATA_PROJECT = False

def _data_path(filename: str) -> str:
    """Trả về đường dẫn đến file trong Data/output/ nếu có sẵn."""
    if _USE_DATA_PROJECT and _DATA_OUTPUT_DIR is not None:
        return os.path.join(str(_DATA_OUTPUT_DIR), filename)
    return filename

# Cấu hình Bot Telegram
TELEGRAM_CONFIGS = [
    {"token": "8723627742:AAEpZFbfd8RSOGi9jxoh2tKQ8TdFViXivc0", "chat_id": "5294991069"},
    {"token": "8723627742:AAEpZFbfd8RSOGi9jxoh2tKQ8TdFViXivc0", "chat_id": "-1003920117828"},  # Group: Cbot Thắng
]

# Tạm ngưng hệ thống CBOT ENTRY ALARM cũ theo yêu cầu, chuyển sang CBOT RADAR
ENABLE_LEGACY_ENTRY_ALARM = False
ENABLE_CBOT_RADAR = False  # Đã tắt hoàn toàn việc gửi tin nhắn CBOT RADAR qua Telegram theo yêu cầu

# Trạng thái quét thủ công để tránh xung đột
is_scanning = False
scan_lock = threading.Lock()

# File lưu tín hiệu cuối cùng — đọc từ Data/output/
LAST_SIGNAL_FILE = _data_path("last_signals.json")

def save_last_signal(code, msg, timestamp, setup=None):
    """Lưu tín hiệu mới nhất theo mã hàng hóa"""
    data = {}
    if os.path.exists(LAST_SIGNAL_FILE):
        try:
            with open(LAST_SIGNAL_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            pass
            
    signal_data = {"msg": msg, "timestamp": timestamp}
    if setup:
        signal_data['setup_type'] = setup.get('type')
        signal_data['setup_entry_range'] = setup.get('entryRange')
        
    data[code] = signal_data
    try:
        with open(LAST_SIGNAL_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Lỗi lưu tín hiệu: {e}")

def load_last_signals():
    """Đọc tất cả tín hiệu cuối cùng đã lưu"""
    if not os.path.exists(LAST_SIGNAL_FILE):
        return {}
    try:
        with open(LAST_SIGNAL_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def send_telegram_message(text):
    """Gửi tin nhắn cảnh báo qua Telegram đến toàn bộ các kênh đã cấu hình"""
    for config in TELEGRAM_CONFIGS:
        token = config["token"]
        chat_id = config["chat_id"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": {
                "inline_keyboard": [[
                    {"text": "🔍 Quét CBOT RADAR", "callback_data": "scan_market"}
                ]]
            }
        }
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                print(f"[{datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime('%H:%M:%S')}] Đã gửi cảnh báo Telegram tới {chat_id} thành công.")
            else:
                print(f"Lỗi gửi Telegram tới {chat_id}: {response.text}")
        except Exception as e:
            print(f"Lỗi kết nối API Telegram ({chat_id}): {e}")

def send_single_message(chat_id, text):
    """Gửi tin nhắn đơn tới 1 chat_id cụ thể (Dùng cho tương tác nút nhấn)"""
    token = "8723627742:AAEpZFbfd8RSOGi9jxoh2tKQ8TdFViXivc0"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [[
                {"text": "🔍 Quét CBOT RADAR", "callback_data": "scan_market"}
            ]]
        }
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Lỗi gửi tin nhắn đơn tới {chat_id}: {e}")

def handle_telegram_update(update):
    global is_scanning
    chat_id = None
    callback_query_id = None
    trigger = False
    
    if "message" in update:
        message = update["message"]
        text = message.get("text", "")
        chat_id = message["chat"]["id"]
        if text.strip() in ("/scan", "Scan Bot", "/radar"):
            trigger = True
            
    elif "callback_query" in update:
        cb = update["callback_query"]
        callback_query_id = cb["id"]
        chat_id = cb["message"]["chat"]["id"]
        if cb.get("data") == "scan_market":
            trigger = True
            try:
                token = "8723627742:AAEpZFbfd8RSOGi9jxoh2tKQ8TdFViXivc0"
                requests.post(f"https://api.telegram.org/bot{token}/answerCallbackQuery", json={
                    "callback_query_id": callback_query_id,
                    "text": "Đang quét CBOT RADAR..."
                })
            except:
                pass
                
    if trigger and chat_id:
        with scan_lock:
            if is_scanning:
                send_single_message(chat_id, "⚠️ Hệ thống đang bận thực hiện một lượt quét khác. Vui lòng thử lại sau.")
                return
            is_scanning = True
            
        try:
            if not ENABLE_CBOT_RADAR:
                send_single_message(chat_id, "ℹ️ Hệ thống CBOT RADAR đã tạm ngưng gửi cảnh báo qua Telegram theo yêu cầu.")
                return
            send_single_message(chat_id, "⏳ Đang quét dữ liệu CBOT RADAR mới nhất...")
            backtest_engine.scan_and_send_cbot_radar_telegram(force_test_nearest=True, target_chat_id=str(chat_id))
        except Exception as e:
            send_single_message(chat_id, f"❌ Có lỗi xảy ra khi quét CBOT RADAR: {e}")
        finally:
            with scan_lock:
                is_scanning = False

def poll_telegram_updates():
    token = "8723627742:AAEpZFbfd8RSOGi9jxoh2tKQ8TdFViXivc0"
    print("Đang khởi chạy Polling Telegram nhận tương tác nút nhấn...")

    offset = -1
    try:
        url = f"https://api.telegram.org/bot{token}/getUpdates"
        r = requests.get(url, params={"limit": 100, "timeout": 3}, timeout=8)
        if r.status_code == 200 and r.json().get("ok"):
            results = r.json().get("result", [])
            if results:
                offset = results[-1]["update_id"] + 1
                print(f"[Polling] Bỏ qua {len(results)} updates cũ. Offset mới: {offset}")
            else:
                offset = 0
                print("[Polling] Không có updates cũ. Bắt đầu từ offset=0")
    except Exception as e:
        offset = 0
        print(f"[Polling] Lỗi lấy offset ban đầu: {e}. Dùng offset=0")

    while True:
        try:
            url = f"https://api.telegram.org/bot{token}/getUpdates"
            params = {"offset": offset, "timeout": 20}
            response = requests.get(url, params=params, timeout=25)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    for update in data.get("result", []):
                        offset = update["update_id"] + 1
                        print(f"[Polling] Nhận update_id={update['update_id']} | keys={list(update.keys())}")
                        t = threading.Thread(target=handle_telegram_update, args=(update,))
                        t.start()
            else:
                print(f"[Polling] HTTP {response.status_code}. Thử lại sau 5s...")
                time.sleep(5)
        except Exception as e:
            print(f"[Polling] Lỗi kết nối: {e}. Thử lại sau 5s...")
            time.sleep(5)


def is_cbot_open():
    """Sử dụng pandas_market_calendars (CMEGlobex_Grains) để tự động check ngày nghỉ lễ và giờ đóng/mở cửa"""
    try:
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        today = now_utc.date()
        cbot_cal = mcal.get_calendar('CMEGlobex_Grains')
        start_date = today - datetime.timedelta(days=1)
        end_date = today + datetime.timedelta(days=1)
        schedule = cbot_cal.schedule(start_date=start_date, end_date=end_date)
        
        if schedule.empty:
            return False
            
        for _, row in schedule.iterrows():
            market_open = row['market_open']
            market_close = row['market_close']
            break_start = row.get('break_start')
            break_end = row.get('break_end')
            
            if market_open <= now_utc <= market_close:
                if pd.notna(break_start) and pd.notna(break_end):
                    if break_start <= now_utc <= break_end:
                        return False
                return True
                
        return False
    except Exception as e:
        print(f"Lỗi khi check lịch giao dịch: {e}")
        return True

def extract_avg_entry(entry_range_str):
    if not entry_range_str: return 0.0
    try:
        parts = entry_range_str.split('-')
        if len(parts) == 2:
            return (float(parts[0].strip()) + float(parts[1].strip())) / 2.0
    except:
        pass
    return 0.0

def run_analysis():
    """Chạy quét CBOT RADAR mới (Tạm ngưng hệ thống CBOT ENTRY ALARM cũ khi ENABLE_LEGACY_ENTRY_ALARM = False)."""
    if not ENABLE_CBOT_RADAR:
        print("[CBOT RADAR] Đã tạm ngưng gửi cảnh báo qua Telegram theo yêu cầu.")
        return False
    if not ENABLE_LEGACY_ENTRY_ALARM:
        return backtest_engine.scan_and_send_cbot_radar_telegram(force_test_nearest=False)

    print(f"\n--- [{datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime('%Y-%m-%d %H:%M:%S')}] BẮT ĐẦU QUÉT THỊ TRƯỜNG ---")
    dca_data = {}
    active_data = {}
    snapshot_path = os.path.join('Data', 'output', 'v3_state_snapshot.json')
    if os.path.exists(snapshot_path):
        try:
            with open(snapshot_path, 'r', encoding='utf-8') as f:
                snapshot = json.load(f)
                commodities = snapshot.get('commodities', {})
                for code, data in commodities.items():
                    if 'dca' in data:
                        dca_data[code] = data['dca']
                    if 'active' in data:
                        active_data[code] = data['active']
        except Exception as e:
            print(f"Lỗi đọc DCA/Active data: {e}")

    codes = {"ZW": "Lúa Mì", "ZC": "Ngô"}
    any_signal_sent = False
    
    for code, name in codes.items():
        file_path = _data_path(f"{code}_active_H1.csv")
        if not os.path.exists(file_path):
            continue
            
        try:
            df = pd.read_csv(file_path)
            if len(df) < 50:
                continue
                
            df_ict = df.rename(columns={
                'Time': 'time', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close',
                'EMA_21': 'ema21', 'EMA_50': 'ema50', 'RSI': 'rsi', 'ATR': 'atr',
                'S1': 's1', 'S2': 's2', 'R1': 'r1', 'R2': 'r2'
            })
            candles = df_ict.to_dict('records')
            
            analysis = ict_engine.analyze(candles)
            setup = analysis.get('setup')
            bottom_zones = analysis.get('bottom_zones', [])
            top_zones = analysis.get('top_zones', [])
            
            last_candle = candles[-1]
            close = last_candle['close']
            msg = ""
            contract_code = code
            if code in active_data and 'contract' in active_data[code]:
                contract_code = active_data[code]['contract']
                
            if setup and setup['winRate'] >= 65:
                signal_icon = "🟢" if setup['type'] == "LONG" else "🔴"
                msg += (
                    f"🚨 <b>CBOT ENTRY ALARM (ICT MSS - {contract_code})</b> 🚨\n"
                    f"🌾 Mã: <b>{name}</b> | Giá H1: {close:.2f}\n"
                    f"📈 Tín hiệu: <b>{signal_icon} {setup['type']} MSS (Win Rate: {setup['winRate']}%)</b>\n"
                    f"🎯 Vùng Entry: <b>{setup['entryRange']}</b>\n"
                    f"🛑 Stoploss: {setup['stopLoss']:.2f} | 💵 Take Profit: {setup['takeProfit']:.2f}\n"
                    f"🧠 Lý do: {setup['reason']}\n\n"
                )
            
            last_bz = bottom_zones[-1] if bottom_zones else None
            if last_bz and last_bz['index'] >= len(candles) - 3 and last_bz['score'] >= 5:
                msg += (
                    f"🚀 <b>TÍN HIỆU BẮT ĐÁY (4 SAO HIGH)</b> 🚀\n"
                    f"Đáy tiềm năng xuất hiện tại: {last_bz['price']:.2f}\n"
                    f"Điểm số ICT: {last_bz['score']}/8 (Rất mạnh)\n"
                    f"Các yếu tố: {', '.join(last_bz['factors'])}\n\n"
                )
                
            last_tz = top_zones[-1] if top_zones else None
            if last_tz and last_tz['index'] >= len(candles) - 3 and last_tz['score'] >= 5:
                msg += (
                    f"☄️ <b>TÍN HIỆU BẮT ĐỈNH (4 SAO HIGH)</b> ☄️\n"
                    f"Đỉnh tiềm năng xuất hiện tại: {last_tz['price']:.2f}\n"
                    f"Điểm số ICT: {last_tz['score']}/8 (Rất mạnh)\n"
                    f"Các yếu tố: {', '.join(last_tz['factors'])}\n\n"
                )
                
            if code in dca_data and msg != "":
                dca = dca_data[code]
                s2 = dca.get('s2', 0)
                atr = dca.get('atr', 0)
                dca_entry_bottom = s2 - 4.0 * atr
                msg += (
                    f"💎 <b>VÙNG GOM DCA DÀI HẠN ({dca.get('contract', 'Mùa vụ')})</b> 💎\n"
                    f"Vùng chờ mua an toàn: <b>{dca_entry_bottom:.2f} - {s2:.2f}</b>\n"
                )
            
            if msg:
                last_signals = load_last_signals()
                is_duplicate = False
                if code in last_signals:
                    old_sig = last_signals[code]
                    if setup and old_sig.get('setup_type') == setup.get('type'):
                        old_entry = extract_avg_entry(old_sig.get('setup_entry_range', ''))
                        new_entry = extract_avg_entry(setup.get('entryRange', ''))
                        if old_entry > 0 and new_entry > 0 and abs(new_entry - old_entry) < 2.0:
                            is_duplicate = True
                            
                if is_duplicate:
                    print(f"{code}: Tín hiệu giống lần quét trước. Bỏ qua gửi Telegram.")
                else:
                    print(f"Phát hiện tín hiệu trên {code}! Đang gửi Telegram...")
                    send_telegram_message(msg)
                    any_signal_sent = True
                    ts = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%H:%M %d/%m/%Y")
                    save_last_signal(code, msg, ts, setup)
            else:
                print(f"{code}: Không có tín hiệu MSS hoặc Bắt đáy/đỉnh đạt chuẩn.")
                
        except Exception as e:
            print(f"Lỗi khi phân tích {code}: {e}")
            
    return any_signal_sent

def main():
    polling_thread = threading.Thread(target=poll_telegram_updates, daemon=True)
    polling_thread.start()
    
    print("CBOT RADAR Bot đang chạy ngầm (Đã tạm ngưng CBOT ENTRY ALARM cũ)... Nhấn Ctrl+C để dừng.")
    
    try:
        while True:
            if ENABLE_CBOT_RADAR and is_cbot_open():
                try:
                    backtest_engine.scan_and_send_cbot_radar_telegram(force_test_nearest=False)
                except Exception as e:
                    print(f"[CBOT RADAR] Lỗi quét định kỳ: {e}")
            time.sleep(300)
    except KeyboardInterrupt:
        print("Đã dừng Bot.")

if __name__ == "__main__":
    main()
