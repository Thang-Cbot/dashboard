import os
import sys
import subprocess
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.parse
import webbrowser

class CBOTHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        # Xu ly request tu nut "Scan Data"
        if self.path == '/run-scan':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            try:
                base = os.path.dirname(os.path.abspath(__file__))

                # Bước 1: Cập nhật dữ liệu thị trường thực tế
                print("\n[SERVER] Bước 1/4 — Quét dữ liệu thị trường...")
                r1 = subprocess.run([sys.executable, os.path.join(base, "Data", "run_data_update.py")],
                                    capture_output=True, text=True)
                if r1.returncode != 0:
                    raise Exception(f"run_data_update failed: {r1.stderr[-500:]}")

                # Bước 2: Chạy Future Chart Engine
                print("[SERVER] Bước 2/4 — Chạy Future Chart Engine...")
                fc_path = os.path.join(base, "Future chart", "future_chart.py")
                r2 = subprocess.run([sys.executable, fc_path],
                                    capture_output=True, text=True)
                if r2.returncode != 0:
                    raise Exception(f"future_chart failed: {r2.stderr[-500:]}")

                # Bước 3: Phân tích kỹ thuật & Báo cáo
                print("[SERVER] Bước 3/4 — Phân tích kỹ thuật & Báo cáo...")
                r3 = subprocess.run([sys.executable, os.path.join(base, "run_pro_plus.py")],
                                    capture_output=True, text=True)
                if r3.returncode != 0:
                    raise Exception(f"run_pro_plus failed: {r3.stderr[-500:]}")

                # Bước 4: Tạo Dashboard HTML
                print("[SERVER] Bước 4/4 — Tạo Dashboard HTML...")
                r4 = subprocess.run([sys.executable, os.path.join(base, "gen_dashboard.py")],
                                    capture_output=True, text=True)
                if r4.returncode != 0:
                    raise Exception(f"gen_dashboard failed: {r4.stderr[-500:]}")

                print("[SERVER] ✅ Hoàn tất toàn bộ 4 bước!")
                self.wfile.write(b'{"status": "success", "message": "Cap nhat thanh cong 4 buoc!"}')
            except Exception as e:
                print(f"[SERVER] ❌ Lỗi: {e}")
                msg = str(e).replace('"', "'").encode('utf-8', errors='replace')
                self.wfile.write(b'{"status": "error", "message": "' + msg + b"'" + b'}')
            return
            
        self.send_response(404)
        self.end_headers()

    def do_GET(self):
        # Neu truy cap goc, chuyen huong vao CBOT_Dashboard.html
        if self.path == '/':
            self.path = '/CBOT_Dashboard.html'
        return SimpleHTTPRequestHandler.do_GET(self)

def run_server():
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass

    # Chuyen thu muc lam viec ve dung thu muc cua server.py
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    port = 8080
    server_address = ('', port)
    httpd = HTTPServer(server_address, CBOTHandler)
    
    print(f"\n=========================================")
    print(f"[+] CBOT LOCAL SERVER DANG CHAY TAI CONG {port}")
    print(f"=========================================")
    print(f"Hay mo trinh duyet truy cap: http://localhost:{port}")
    print(f"Nhan Ctrl+C de tat server.")
    print(f"=========================================\n")
    
    # Tu dong mo trinh duyet
    def open_browser():
        webbrowser.open(f'http://localhost:{port}/CBOT_Dashboard.html')
    
    threading.Timer(1.0, open_browser).start()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nDang tat Server...")
        httpd.server_close()

if __name__ == '__main__':
    run_server()
