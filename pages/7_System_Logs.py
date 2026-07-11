import streamlit as st
import json
import os
import datetime
import pandas as pd

# ── CẤU HÌNH TRANG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="System Health & Logs",
    page_icon="favicon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

def sidebar_nav():
    st.sidebar.markdown("""
    <div style='text-align:center; padding:16px 0 8px;'>
        <div style='font-size:24px; font-weight:800; color:#e2e8f0;'>📊 CBOT</div>
        <div style='font-size:11px; color:#64748b; letter-spacing:2px;'>TRADING DASHBOARD</div>
    </div>
    """, unsafe_allow_html=True)
    st.sidebar.markdown("---")
    st.sidebar.page_link("app.py",              label="🏠 Trang Chủ")
    st.sidebar.page_link("pages/1_Overview.py", label="📊 Tổng Quan")
    st.sidebar.page_link("pages/2_Profiles.py", label="📈 Hồ Sơ Từng Mã")
    st.sidebar.page_link("pages/3_News.py",     label="📰 Báo Cáo USDA & Tin Tức")
    st.sidebar.page_link("pages/4_Weather.py",  label="🌤️ Thời Tiết")
    st.sidebar.page_link("pages/5_AgriMap.py",  label="🗺️ Bản Đồ Thời Tiết & ENSO")
    st.sidebar.page_link("pages/6_MuaVu.py",   label="🌾 Mùa Vụ 2026")
    st.sidebar.page_link("pages/7_System_Logs.py", label="⚙️ System Logs")
    st.sidebar.markdown("---")

sidebar_nav()


# ── HÀM TIỆN ÍCH ─────────────────────────────────────────────────────────────
def load_json(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def parse_status_data(data):
    """Gộp trạng thái từ data['modules'] và các key rời rạc trong data_status.json"""
    items = {}
    
    # Quét trong "modules"
    if "modules" in data and isinstance(data["modules"], dict):
        for k, v in data["modules"].items():
            if isinstance(v, dict) and "status" in v:
                items[k] = v
                
    # Quét các key ngoài lề (do data_config.py ghi đè)
    for k, v in data.items():
        if k == "modules" or not isinstance(v, dict):
            continue
        if "status" in v:
            # Nếu trùng, ưu tiên lấy cái có thời gian mới hơn
            if k in items:
                try:
                    t_old = datetime.datetime.strptime(items[k].get("updated_at", ""), "%Y-%m-%d %H:%M:%S")
                    t_new = datetime.datetime.strptime(v.get("updated_at", ""), "%Y-%m-%d %H:%M:%S")
                    if t_new > t_old:
                        items[k] = v
                except:
                    pass
            else:
                items[k] = v
                
    return items

def render_status_table(items, exclude_keys=[]):
    """Render bảng trạng thái với Pandas + st.dataframe hoặc HTML/Markdown"""
    rows = []
    
    # Từ điển ánh xạ tên cho thân thiện
    name_map = {
        "prices": "Giá H1 & Kỹ Thuật",
        "macro": "Vĩ Mô (DXY, Dầu)",
        "usda": "USDA (WASDE & Crop)",
        "export_sales": "Bán Hàng Xuất Khẩu",
        "cot": "Dòng Tiền Đầu Cơ (COT)",
        "weather_short": "Thời Tiết (Ngắn Hạn)",
        "weather_long": "Thời Tiết (Dài Hạn/ENSO)",
        "acreage": "Diện Tích Gieo Trồng",
        "ai_news": "AI Điểm Tin",
        "ai_analysis": "AI Phân Tích Chuyên Sâu",
        "blacksea_news": "Điểm Tin Biển Đen",
        "russian_metrics": "Chỉ Số Lúa Mì Nga",
        "github_sync": "Đồng Bộ GitHub (Sync)"
    }
    
    for k, v in items.items():
        if k in exclude_keys:
            continue
            
        status = v.get("status", "UNKNOWN").upper().strip("[] ")
        detail = v.get("detail", "")
        updated = v.get("updated_at", "")
        
        # Xác định trạng thái Xanh/Đỏ/Vàng
        if status in ["OK", "SUCCESS"]:
            status_html = f"<span style='color: #22c55e; font-weight: bold;'>🟢 {status}</span>"
        elif status in ["ERROR", "FAIL", "TIMEOUT"]:
            status_html = f"<span style='color: #ef4444; font-weight: bold;'>🔴 {status}</span>"
        elif status in ["PARTIAL", "WARN"]:
            status_html = f"<span style='color: #f59e0b; font-weight: bold;'>🟡 {status}</span>"
        elif status in ["SKIPPED"]:
            status_html = f"<span style='color: #94a3b8; font-weight: bold;'>⚪ {status}</span>"
        else:
            status_html = f"<span style='color: #e2e8f0; font-weight: bold;'>{status}</span>"
            
        rows.append({
            "Module": name_map.get(k, k.capitalize()),
            "Key": k,
            "Cập Nhật (Giờ VN)": updated,
            "Trạng Thái": status_html,
            "Chi Tiết": detail
        })
        
    if not rows:
        st.info("Chưa có dữ liệu trạng thái.")
        return
        
    df = pd.DataFrame(rows)
    # Sắp xếp theo tên Module
    df = df.sort_values(by="Module")
    
    # Tạo HTML Table
    html = "<table style='width: 100%; border-collapse: collapse; font-size: 14px;'>"
    html += "<tr style='background-color: #1e293b; border-bottom: 2px solid #334155;'>"
    html += "<th style='padding: 10px; text-align: left;'>Nguồn Dữ Liệu</th>"
    html += "<th style='padding: 10px; text-align: left;'>Lần Chạy Cuối</th>"
    html += "<th style='padding: 10px; text-align: center;'>Trạng Thái</th>"
    html += "<th style='padding: 10px; text-align: left;'>Ghi Chú</th>"
    html += "</tr>"
    
    for _, r in df.iterrows():
        html += f"<tr style='border-bottom: 1px solid #334155;'>"
        html += f"<td style='padding: 10px; font-weight: 600; color: #e2e8f0;'>{r['Module']}<br><span style='font-size:11px; color:#64748b; font-weight:400;'>ID: {r['Key']}</span></td>"
        html += f"<td style='padding: 10px; color: #94a3b8;'>{r['Cập Nhật (Giờ VN)']}</td>"
        html += f"<td style='padding: 10px; text-align: center;'>{r['Trạng Thái']}</td>"
        html += f"<td style='padding: 10px; color: #cbd5e1;'>{r['Chi Tiết']}</td>"
        html += "</tr>"
        
    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)

# ── GIAO DIỆN CHÍNH ───────────────────────────────────────────────────────────
st.title("⚙️ System Health & Logs")
st.markdown("Kiểm tra trạng thái sức khỏe của Bộ Máy Thu Thập Dữ Liệu và Đồng Bộ Hóa.")

# Đọc file status
DATA_STATUS_PATH = os.path.join(os.path.dirname(__file__), "..", "Data", "output", "data_status.json")
data_json = load_json(DATA_STATUS_PATH)
status_items = parse_status_data(data_json)

# Tạo 2 Tabs
tab1, tab2 = st.tabs(["📊 Tab 1: Thu Thập Dữ Liệu (Local Fetching)", "☁️ Tab 2: Đồng Bộ Lên Mạng (Online Sync)"])

with tab1:
    st.markdown("### 📥 Dữ Liệu Nguồn (Offline Data)")
    st.markdown("""
    Bảng dưới đây hiển thị tình trạng lấy dữ liệu từ các nguồn (USDA, CFTC, Yahoo Finance, Weather...). 
    Nếu có bất kỳ dòng nào **<span style='color:#ef4444'>🔴 ERROR</span>**, nghĩa là dữ liệu đó đang bị **MISS** (thiếu), AI có thể sẽ phân tích sai lệch.
    """, unsafe_allow_html=True)
    
    # Hiển thị tất cả ngoại trừ github_sync
    render_status_table(status_items, exclude_keys=["github_sync"])

with tab2:
    st.markdown("### 📤 Đồng Bộ Mạng (Github Sync)")
    st.markdown("""
    Bảng này theo dõi quá trình máy tính (Local) tự động nén dữ liệu và đẩy lên Cloud (GitHub/Streamlit). 
    Nếu Tab 1 (Dữ liệu) Xanh, nhưng phần Sync này **<span style='color:#ef4444'>🔴 LỖI</span>**, thì trên Web Streamlit sẽ không thấy dữ liệu mới.
    """, unsafe_allow_html=True)
    
    sync_items = {k: v for k, v in status_items.items() if k == "github_sync"}
    
    if not sync_items:
        st.info("Chưa có lịch sử đồng bộ (Có thể Scheduler chưa gọi lệnh Push).")
    else:
        render_status_table(sync_items)
        
    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.markdown("**Cách hoạt động mới:** Hệ thống hiện tại đã kích hoạt *Universal Sync* — ngay sau khi **bất kỳ** lệnh dữ liệu nào ở Tab 1 tải xong thành công, tiến trình Sync ở Tab 2 sẽ tự động chạy trong vòng 1 giây để đảm bảo Local và Online luôn ăn khớp.")
