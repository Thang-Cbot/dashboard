"""
Script template để bóc tách báo cáo Export Sales (Bán hàng xuất khẩu - Doanh số ròng)
từ file PDF tĩnh của USDA FAS.

Sử dụng thư viện: pdfplumber (pip install pdfplumber)
URL: https://apps.fas.usda.gov/esrqs/StaticReports/CWRCommoditySummary.pdf
"""
import urllib.request
import io
import json

try:
    import pdfplumber
except ImportError:
    print("Vui lòng cài đặt pdfplumber: pip install pdfplumber")
    pdfplumber = None

PDF_URL = "https://apps.fas.usda.gov/esrqs/StaticReports/CWRCommoditySummary.pdf"

def extract_export_sales_from_pdf():
    """
    Tải file PDF báo cáo bán hàng xuất khẩu tuần mới nhất và bóc tách các con số.
    """
    if not pdfplumber:
        return None

    print(f"Đang tải PDF từ {PDF_URL}...")
    req = urllib.request.Request(PDF_URL, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    
    try:
        res = urllib.request.urlopen(req, timeout=30)
        pdf_bytes = res.read()
        print("Tải PDF thành công. Đang bóc tách dữ liệu...")
    except Exception as e:
        print(f"[LỖI] Không thể tải PDF (Có thể do USDA đang chặn/treo máy chủ): {e}")
        return None

    results = {}
    
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            # Quét tất cả các trang để tìm dòng dữ liệu Lúa mì và Ngô
            for page in pdf.pages:
                text = page.extract_text()
                if not text: continue
                
                lines = text.split('\n')
                for line in lines:
                    # Bóc tách Lúa mì (ZW) - Có thể lấy Hard Red Winter hoặc ALL WHEAT
                    if "101 WHEAT - HARD RED WINTER" in line or "ALL WHEAT" in line:
                        print(f"[Phát hiện Lúa mì] {line}")
                        # Logic bóc tách tương lai sẽ parse mảng parts = line.split() 
                        # để lấy cột Net Sales (Doanh số ròng) và Outstanding Sales (Chưa giao).
                        
                    # Bóc tách Ngô (ZC)
                    if "401 CORN - UNMILLED" in line or "CORN - UNMILLED" in line:
                        print(f"[Phát hiện Ngô] {line}")
                        
        print("Bóc tách cấu trúc hoàn tất.")
        return results
    except Exception as e:
        print(f"[LỖI] Xảy ra sự cố khi đọc PDF: {e}")
        return None

if __name__ == "__main__":
    extract_export_sales_from_pdf()
