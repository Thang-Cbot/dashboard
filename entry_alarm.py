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
                    {"text": "🔍 Scan Bot", "callback_data": "scan_market"}
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
                {"text": "🔍 Scan Bot", "callback_data": "scan_market"}
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
        if text.strip() == "/scan" or text.strip() == "Scan Bot":
            trigger = True
            
    elif "callback_query" in update:
        cb = update["callback_query"]
        callback_query_id = cb["id"]
        chat_id = cb["message"]["chat"]["id"]
        if cb.get("data") == "scan_market":
            trigger = True
            try:
                # Phản hồi ngay để mất biểu tượng loading trên nút
                token = "8723627742:AAEpZFbfd8RSOGi9jxoh2tKQ8TdFViXivc0"
                requests.post(f"https://api.telegram.org/bot{token}/answerCallbackQuery", json={
                    "callback_query_id": callback_query_id,
                    "text": "Đang quét dữ liệu thị trường..."
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
            send_single_message(chat_id, "⏳ Đang bắt đầu quét dữ liệu thị trường CBOT mới nhất từ Yahoo Finance...")
            any_signal = run_analysis()
            if not any_signal:
                # Không có tín hiệu mới => gửi lại tín hiệu cũ gần nhất
                last_signals = load_last_signals()
                if last_signals:
                    header = "📭 <b>Chưa có tín hiệu mới.</b> Dưới đây là các tín hiệu gần nhất:\n\n"
                    combined = header
                    for code, sig_data in last_signals.items():
                        ts = sig_data.get('timestamp', 'N/A')
                        old_msg = sig_data.get('msg', '')
                        combined += f"🕐 <i>Tín hiệu lúc: {ts}</i>\n{old_msg}\n{'─'*30}\n"
                    send_single_message(chat_id, combined)
                else:
                    send_single_message(chat_id, "📭 <b>Kết quả quét:</b> Hiện tại thị trường không phát hiện tín hiệu MSS hoặc Bắt đáy/đỉnh đạt chuẩn trên ZC, ZW, ZS. Chưa có tín hiệu nào được lưu trước đó.")
        except Exception as e:
            send_single_message(chat_id, f"❌ Có lỗi xảy ra khi quét: {e}")
        finally:
            with scan_lock:
                is_scanning = False

def poll_telegram_updates():
    offset = 0
    token = "8723627742:AAEpZFbfd8RSOGi9jxoh2tKQ8TdFViXivc0"
    print("Đang khởi chạy Polling Telegram nhận tương tác nút nhấn...")
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
                        # Xử lý update trong một thread riêng để không block việc polling
                        t = threading.Thread(target=handle_telegram_update, args=(update,))
                        t.start()
            else:
                time.sleep(5)
        except Exception as e:
            print(f"Lỗi polling Telegram: {e}")
            time.sleep(5)

def is_cbot_open():
    """Sử dụng pandas_market_calendars (CMEGlobex_Grains) để tự động check ngày nghỉ lễ và giờ đóng/mở cửa"""
    try:
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        today = now_utc.date()
        
        # Gọi lịch của nhóm Nông sản CBOT
        cbot_cal = mcal.get_calendar('CMEGlobex_Grains')
        
        # Lấy lịch trong cửa sổ 3 ngày (Hôm qua, Hôm nay, Ngày mai) để cover toàn bộ session qua đêm
        start_date = today - datetime.timedelta(days=1)
        end_date = today + datetime.timedelta(days=1)
        
        schedule = cbot_cal.schedule(start_date=start_date, end_date=end_date)
        
        if schedule.empty:
            return False # Nghỉ lễ hoặc cuối tuần
            
        for _, row in schedule.iterrows():
            market_open = row['market_open']
            market_close = row['market_close']
            break_start = row.get('break_start')
            break_end = row.get('break_end')
            
            # Kiểm tra UTC Now có nằm trong 1 phiên hợp lệ hay không
            if market_open <= now_utc <= market_close:
                # Nếu đang nằm trong khung giờ nghỉ trưa (Clearing Break)
                if pd.notna(break_start) and pd.notna(break_end):
                    if break_start <= now_utc <= break_end:
                        return False # Đang nghỉ giữa phiên
                return True # Đang mở cửa giao dịch
                
        return False
    except Exception as e:
        print(f"Lỗi khi check lịch giao dịch: {e}")
        return True # Fallback để vẫn quét nếu lỗi thư viện

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
    """Chạy script cập nhật dữ liệu và kiểm tra MSS trên H1. Trả về True nếu có bất kỳ tín hiệu nào được phát hiện."""
    print(f"\n--- [{datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime('%Y-%m-%d %H:%M:%S')}] BẮT ĐẦU QUÉT THỊ TRƯỜNG ---")
    
    # 1. Chạy cập nhật dữ liệu
    try:
        print("Đang tải dữ liệu H1 mới nhất...")
        subprocess.run(["python", "update_active_data.py"], check=True)
    except Exception as e:
        print(f"Lỗi khi chạy update_active_data.py: {e}")
        return False

    # 2. Đọc DCA data và Active data từ v3_state_snapshot.json
    dca_data = {}
    active_data = {}
    if os.path.exists('v3_state_snapshot.json'):
        try:
            with open('v3_state_snapshot.json', 'r', encoding='utf-8') as f:
                snapshot = json.load(f)
                commodities = snapshot.get('commodities', {})
                for code, data in commodities.items():
                    if 'dca' in data:
                        dca_data[code] = data['dca']
                    if 'active' in data:
                        active_data[code] = data['active']
        except Exception as e:
            print(f"Lỗi đọc DCA/Active data: {e}")

    # 3. Đọc file CSV và tìm kiếm MSS, Bắt đáy/đỉnh
    codes = {"ZW": "Lúa Mì", "ZC": "Ngô", "ZS": "Đậu Tương"}
    any_signal_sent = False
    
    for code, name in codes.items():
        file_path = _data_path(f"{code}_active_H1.csv")
        if not os.path.exists(file_path):
            continue
            
        try:
            df = pd.read_csv(file_path)
            if len(df) < 50:
                continue
                
            # Đổi tên cột cho phù hợp với ict_engine
            df_ict = df.rename(columns={
                'Time': 'time', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close',
                'EMA_21': 'ema21', 'EMA_50': 'ema50', 'RSI': 'rsi', 'ATR': 'atr',
                'S1': 's1', 'S2': 's2', 'R1': 'r1', 'R2': 'r2'
            })
            candles = df_ict.to_dict('records')
            
            # Phân tích ICT
            analysis = ict_engine.analyze(candles)
            setup = analysis.get('setup')
            bottom_zones = analysis.get('bottom_zones', [])
            top_zones = analysis.get('top_zones', [])
            
            last_candle = candles[-1]
            close = last_candle['close']
            
            msg = ""
            
            # Lấy mã Hợp đồng Active (vd: ZCN26)
            contract_code = code
            if code in active_data and 'contract' in active_data[code]:
                contract_code = active_data[code]['contract']
                
            # Kiểm tra MSS (Win Rate >= 65%)
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
            
            # Kiểm tra Bắt đáy (>= 4 sao / 5 điểm)
            last_bz = bottom_zones[-1] if bottom_zones else None
            if last_bz and last_bz['index'] >= len(candles) - 3 and last_bz['score'] >= 5:
                msg += (
                    f"🚀 <b>TÍN HIỆU BẮT ĐÁY (4 SAO HIGH)</b> 🚀\n"
                    f"Đáy tiềm năng xuất hiện tại: {last_bz['price']:.2f}\n"
                    f"Điểm số ICT: {last_bz['score']}/8 (Rất mạnh)\n"
                    f"Các yếu tố: {', '.join(last_bz['factors'])}\n\n"
                )
                
            # Kiểm tra Bắt đỉnh (>= 4 sao / 5 điểm)
            last_tz = top_zones[-1] if top_zones else None
            if last_tz and last_tz['index'] >= len(candles) - 3 and last_tz['score'] >= 5:
                msg += (
                    f"☄️ <b>TÍN HIỆU BẮT ĐỈNH (4 SAO HIGH)</b> ☄️\n"
                    f"Đỉnh tiềm năng xuất hiện tại: {last_tz['price']:.2f}\n"
                    f"Điểm số ICT: {last_tz['score']}/8 (Rất mạnh)\n"
                    f"Các yếu tố: {', '.join(last_tz['factors'])}\n\n"
                )
                
            # Đính kèm DCA
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
                # Tránh gửi lặp lại tín hiệu giống hệt hoặc chưa thay đổi nhiều so với lần quét trước
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
                    print(f"{code}: Tín hiệu giống lần quét trước (cùng loại, chênh lệch Entry < 2 giá). Bỏ qua gửi Telegram để tránh spam.")
                else:
                    print(f"Phát hiện tín hiệu trên {code}! Đang gửi Telegram...")
                    send_telegram_message(msg)
                    any_signal_sent = True
                    # Lưu lại tín hiệu vừa phát hiện
                    ts = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%H:%M %d/%m/%Y")
                    save_last_signal(code, msg, ts, setup)
            else:
                print(f"{code}: Không có tín hiệu MSS hoặc Bắt đáy/đỉnh đạt chuẩn.")
                
        except Exception as e:
            print(f"Lỗi khi phân tích {code}: {e}")
            
    if any_signal_sent:
        print("Cập nhật lại HTML Dashboard sau khi có tín hiệu...")
        try:
            subprocess.run([sys.executable, "gen_dashboard.py"], cwd=os.path.dirname(__file__), check=False)
        except Exception as e:
            print(f"Lỗi update HTML: {e}")
            
    return any_signal_sent

def main():
    # Khởi động luồng Polling Telegram
    polling_thread = threading.Thread(target=poll_telegram_updates, daemon=True)
    polling_thread.start()
    
    # Gửi tin nhắn test lúc khởi động để đảm bảo Bot hoạt động
    send_telegram_message("✅ <b>Hệ thống CBOT Entry Alarm đã kích hoạt!</b>\nBot sẽ tự động quét tín hiệu MSS (H1) mỗi khi đóng nến 1 giờ trong khung thời gian giao dịch của CBOT.")
    print("Bot đang chạy ngầm... Nhấn Ctrl+C để dừng.")
    
    last_run_hour = -1
    
    while True:
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))
        
        # Chỉ quét nếu thị trường đang mở cửa
        if is_cbot_open():
            if now.minute == 16 and now.hour != last_run_hour:
                if now.second < 1:
                    time.sleep(1) # Chờ đúng 1 giây để nến đóng cửa hoàn toàn
                run_analysis()
                
                # TỰ ĐỘNG HÓA V2: Chạy lệnh xuất Báo cáo và HTML Dashboard
                print(f"[{now.strftime('%H:%M:%S')}] Đang tự động xuất Báo cáo V3 và Dashboard HTML...")
                try:
                    # KHÔNG CẦN CHẠY DATA UPDATE NỮA VÌ DATA SCHEDULER ĐÃ CHẠY LÚC PHÚT 15
                    subprocess.run([sys.executable, "run_pro_plus.py"], cwd=os.path.dirname(__file__), check=False)
                    subprocess.run([sys.executable, "gen_dashboard.py"], cwd=os.path.dirname(__file__), check=False)
                    print(f"[{now.strftime('%H:%M:%S')}] Đã cập nhật Dashboard HTML thành công!")
                except Exception as e:
                    print(f"Lỗi khi cập nhật Dashboard: {e}")
                
                last_run_hour = now.hour
        else:
            # Thông báo ngủ đông nếu là phút đầu tiên của giờ đang đóng cửa
            if now.minute == 15 and now.hour != last_run_hour:
                print(f"[{now.strftime('%H:%M:%S')}] Thị trường CBOT đang đóng cửa. Bot ngủ đông...")
                last_run_hour = now.hour
                
        # Nghỉ 30 giây trước khi lặp lại để giảm tải CPU
        # Nếu sắp đến phút 16, ngủ ngắn hơn để không bỏ lỡ giây đầu tiên
        if now.minute == 15 and now.second >= 30:
            time.sleep(60 - now.second)
        else:
            time.sleep(30)

if __name__ == "__main__":
    main()
