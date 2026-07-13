"""
pages/3_News.py — Bảng Tin Tức & Cung Cầu
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Báo Cáo USDA & Tin Tức", page_icon="favicon.png", layout="wide")

DATA_OUTPUT = Path(__file__).parent.parent / "Data" / "output"

@st.cache_data(ttl=60)
def load_json(fname):
    p = DATA_OUTPUT / fname
    if not p.exists():
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #0f1629; }
[data-testid="stSidebar"] { background: #0d1424 !important; border-right: 1px solid #1e2d45; min-width: 260px !important; max-width: 260px !important; width: 260px !important; }
[data-testid="stSidebarNav"] { display: none !important; }
.card { background: #1a2035; border: 1px solid #2a3a5c; border-radius: 12px; padding: 16px; margin-bottom: 12px; }
.section-header { font-size:15px; font-weight:800; color:#e2e8f0; margin:20px 0 12px 0; letter-spacing:0.5px; }
table { width:100%; border-collapse:collapse; font-size:13px; }
th { background:#0f1629; color:#94a3b8; padding:10px 12px; text-align:left; font-weight:600;
     font-size:11px; text-transform:uppercase; letter-spacing:0.5px; border-bottom:1px solid #2a3a5c; }
td { padding:10px 12px; color:#cbd5e1; border-bottom:1px solid #1e2d45; vertical-align:top; }
tr:hover td { background:#1e2d45; }
.curr { color:#22c55e; font-weight:700; }
.prev { color:#94a3b8; }
.bull { background:#14532d; color:#4ade80; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:700; }
.bear { background:#7f1d1d; color:#f87171; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:700; }
</style>""", unsafe_allow_html=True)

st.sidebar.page_link("app.py",              label="🏠 Trang Chủ")
st.sidebar.page_link("pages/1_Overview.py", label="📊 Tổng Quan")
st.sidebar.page_link("pages/2_Profiles.py", label="📈 Hồ Sơ Từng Mã")
st.sidebar.page_link("pages/3_News.py",     label="📰 Báo Cáo USDA & Tin Tức")
st.sidebar.page_link("pages/4_Weather.py",  label="🌤️ Thời Tiết")
st.sidebar.page_link("pages/5_AgriMap.py",  label="🗺️ Bản Đồ Thời Tiết & ENSO")
st.sidebar.page_link("pages/6_MuaVu.py",   label="🌾 Mùa Vụ 2026")

st.markdown("## 📰 Báo Cáo USDA & Tin Tức")

tab1, tab2, tab3 = st.tabs(["📊 Số liệu & Báo cáo (USDA)", "⚡ Điểm Tin Nóng (AI)", "🇷🇺 Tình Hình Biển Đen (Nga/EU)"])

with tab3:
    st.markdown("<div class='section-header'>🇷🇺 Chiến Lược & Thông Số Mùa Vụ Nga (Golden Zone)</div>", unsafe_allow_html=True)
    
    st.info("""
    **Điểm hội tụ nguồn cung (Cuối Tháng 7 đến Giữa Tháng 8): Khoảnh khắc 3 dòng thác va chạm:**
    + Mỹ dọn xong kho lúa đông.
    + Nga xả lũ mạnh nhất ra Biển Đen.
    + Lúa xuân Mỹ chớm gặt.
    + **TIN NÓNG:** Nga chính thức hạ thuế xuất khẩu lúa mì về 0% từ ngày 15/07.
    
    👉 **KẾT LUẬN:** Sức ép khổng lồ này sẽ ép giá xuống MỨC ĐÁY TUYỆT ĐỐI. Đây chính là "Vùng Vàng" để dồn toàn bộ hỏa lực MUA MẠNH (DCA) khi xuất hiện tín hiệu SMC.
    """)
    
    import pandas as pd
    manual_data = load_json("manual_russian_metrics.json")
    if manual_data and "metrics" in manual_data:
        st.markdown(f"<div style='font-size:12px; color:#64748b; margin-bottom:10px;'>Bảng Thông Số Tĩnh (Cập nhật thủ công): {manual_data.get('updated_at', 'Gần nhất')}</div>", unsafe_allow_html=True)
        df = pd.DataFrame(manual_data["metrics"])
        st.table(df)
        
    st.markdown("<hr style='border-color:#1e2d45; margin:20px 0;'>", unsafe_allow_html=True)
    
    st.markdown("<div class='section-header'>🗞️ AI Quét Tin Tức Tự Động (Biển Đen)</div>", unsafe_allow_html=True)
    if st.button("🔄 CẬP NHẬT TIN BIỂN ĐEN MỚI NHẤT", use_container_width=True, key="update_blacksea"):
        import subprocess
        import os
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        with st.spinner("AI đang quét và tóm tắt tin tức Biển Đen... (Vui lòng đợi 10-15s)"): 
            subprocess.run([sys.executable, str(Path(__file__).parent.parent / "Data" / "fetch_blacksea.py")], env=env)
            st.cache_data.clear()
            st.rerun()

    blacksea_news = load_json("blacksea_wheat.json")
    if blacksea_news:
        st.markdown(f"<div style='font-size:12px; color:#64748b; margin-bottom:10px;'>Cập nhật lần cuối: {blacksea_news.get('timestamp', '—')}</div>", unsafe_allow_html=True)
        news_list = blacksea_news.get("news", [])
        
        import pandas as pd
        def parse_news_date(item):
            s = item.get("source", "").split("-")[0].split("(")[0].strip()
            try: return pd.to_datetime(s)
            except: return pd.to_datetime('1970-01-01')
        news_list = sorted(news_list, key=parse_news_date, reverse=True)
        
        if not news_list:
            st.info("Không có tin tức nào về Biển Đen được tìm thấy.")
        else:
            for item in news_list:
                with st.expander(f"🇷🇺 {item.get('title', 'Tin tức lúa mì Nga mới')}"):
                    for detail in item.get('details', []):
                        st.markdown(f"<div style='font-size:14px; color:#cbd5e1; margin-bottom:6px; line-height:1.6;'>• {detail}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='margin-top:10px; font-size:12px; color:#94a3b8; font-style:italic;'>(Nguồn: {item.get('source', '')}) - <a href='{item.get('link', '#')}' target='_blank' style='color:#38bdf8;'>Đọc chi tiết</a></div>", unsafe_allow_html=True)
    else:
        st.info("Chưa có tin tức lúa mì Biển Đen nào được tóm tắt. Vui lòng nhấn nút Cập nhật phía trên.")

with tab2:
    st.markdown("<div class='section-header'>⚡ AI Tóm Tắt Tin Tức Thị Trường (Yahoo RSS)</div>", unsafe_allow_html=True)
    if st.button("🔄 CẬP NHẬT TIN TỨC MỚI NHẤT (AI)", use_container_width=True):
        import subprocess
        import os
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        with st.spinner("AI đang quét và tóm tắt tin tức... (Vui lòng đợi 10-15s)"): 
            subprocess.run([sys.executable, str(Path(__file__).parent.parent / "Data" / "fetch_news.py")], env=env)
            st.cache_data.clear()
            st.rerun()

    ai_news = load_json("ai_news.json")
    if ai_news:
        st.markdown(f"<div style='font-size:12px; color:#64748b; margin-bottom:10px;'>Cập nhật lần cuối: {ai_news.get('timestamp', '—')}</div>", unsafe_allow_html=True)
        news_list = ai_news.get("news", [])
        
        import pandas as pd
        def parse_news_date_ai(item):
            s = item.get("source", "").split("-")[0].split("(")[0].strip()
            try: return pd.to_datetime(s)
            except: return pd.to_datetime('1970-01-01')
        news_list = sorted(news_list, key=parse_news_date_ai, reverse=True)
        
        if not news_list:
            # Hỗ trợ dữ liệu cũ
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            for bullet in ai_news.get("bullets", []):
                st.markdown(f"<div style='font-size:14px; color:#e2e8f0; margin-bottom:8px; line-height:1.6;'><b>{bullet}</b></div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            # Giao diện Drop Down mới
            for item in news_list:
                with st.expander(f"🔹 {item.get('title', 'Tin tức mới')}"):
                    for detail in item.get('details', []):
                        st.markdown(f"<div style='font-size:14px; color:#cbd5e1; margin-bottom:6px; line-height:1.6;'>• {detail}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='margin-top:10px; font-size:12px; color:#94a3b8; font-style:italic;'>(Nguồn: {item.get('source', '')}) - <a href='{item.get('link', '#')}' target='_blank' style='color:#38bdf8;'>Đọc chi tiết</a></div>", unsafe_allow_html=True)
    else:
        st.info("Chưa có tin tức nào được tóm tắt. Vui lòng nhấn nút Cập nhật phía trên.")

with tab1:

    fund = load_json("fundamental_data.json")
    acreage_data = load_json("acreage_data.json")

    # ── HEADER + NÚT CẬP NHẬT ──────────────────────────────────────────────────
    hdr_col, btn_col = st.columns([3, 1.2])
    with hdr_col:
        st.markdown("<div style='font-size:16px; font-weight:800; color:#e2e8f0; margin-top:16px;'>📊 Số liệu & Báo cáo (USDA)</div>", unsafe_allow_html=True)
    with btn_col:
        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Cập Nhật Báo Cáo Mới Nhất", use_container_width=True, key="refresh_usda_tab"):
            import subprocess
            msgs = []
            placeholders = st.empty()
            with st.spinner("⏳ Đang quét dữ liệu USDA, Export Sales, Acreage và COT..."):
                scripts = [
                    ("Export Sales",   str(Path(__file__).parent.parent / "Data" / "reports" / "export_sales.py")),
                    ("Acreage",        str(Path(__file__).parent.parent / "Data" / "reports" / "fetch_acreage.py")),
                    ("USDA/WASDE",     str(Path(__file__).parent.parent / "Data" / "fetch_usda.py")),
                    ("COT",            str(Path(__file__).parent.parent / "Data" / "price" / "cot.py")),
                ]
                for name, script in scripts:
                    try:
                        import os
                        env = os.environ.copy()
                        env["PYTHONIOENCODING"] = "utf-8"
                        result = subprocess.run(
                            [sys.executable, script],
                            capture_output=True, text=True, encoding="utf-8", env=env, timeout=60
                        )
                        if result.returncode == 0:
                            msgs.append(("✅", name, "Thành công"))
                        else:
                            err = result.stderr.strip()[-120:] if result.stderr else "Lỗi không xác định"
                            msgs.append(("⚠️", name, err))
                    except subprocess.TimeoutExpired:
                        msgs.append(("⏱️", name, "Timeout (>60s)"))
                    except Exception as e:
                        msgs.append(("❌", name, str(e)[:100]))
                st.cache_data.clear()
            # Lưu vào session_state để hiển thị sau khi load lại
            st.session_state["usda_update_msgs"] = msgs

    # Hiển thị kết quả cập nhật (tồn tại qua các lần render)
    if "usda_update_msgs" in st.session_state and st.session_state["usda_update_msgs"]:
        msgs = st.session_state["usda_update_msgs"]
        rows_html = ""
        for icon, name, msg in msgs:
            bg    = "#14532d" if icon == "✅" else "#7f1d1d" if icon in ("⚠️", "❌") else "#1e293b"
            color = "#4ade80" if icon == "✅" else "#f87171" if icon in ("⚠️", "❌") else "#94a3b8"
            rows_html += (
                f"<div style='display:flex; align-items:center; gap:10px; padding:6px 10px; "
                f"border-radius:6px; margin-bottom:4px; background:{bg};'>"
                f"<span style='font-size:16px;'>{icon}</span>"
                f"<span style='color:#e2e8f0; font-size:13px; font-weight:600; min-width:110px;'>{name}</span>"
                f"<span style='color:{color}; font-size:12px;'>{msg}</span>"
                f"</div>"
            )

        all_ok = all(i == "✅" for i, _, _ in msgs)
        summary_color = "#22c55e" if all_ok else "#f59e0b"
        summary_text = "Tất cả báo cáo đã được cập nhật thành công!" if all_ok else "Một số báo cáo gặp lỗi, kiểm tra chi tiết bên dưới."
        st.markdown(f"""
        <div style='background:#1a2035; border:1px solid #2a3a5c; border-radius:10px; padding:14px 16px; margin:8px 0 12px 0;'>
            <div style='font-size:13px; font-weight:700; color:{summary_color}; margin-bottom:10px;'>
                📋 Kết quả cập nhật — <span style='font-weight:400;'>{summary_text}</span>
            </div>
            {rows_html}
        </div>""", unsafe_allow_html=True)
        col_reload, col_clear = st.columns([1, 1])
        with col_reload:
            if st.button("🔃 Tải lại trang để xem dữ liệu mới", use_container_width=True, key="reload_after_update"):
                st.session_state.pop("usda_update_msgs", None)
                st.rerun()
        with col_clear:
            if st.button("✖ Đóng thông báo", use_container_width=True, key="close_update_msgs"):
                st.session_state.pop("usda_update_msgs", None)
                st.rerun()

    st.markdown("<hr style='border-color:#1e2d45; margin:8px 0 16px 0;'>", unsafe_allow_html=True)

    # ── BÁN HÀNG XUẤT KHẨU (Export Sales - Thứ 5, từ PDF USDA) ─────────────────
    zc_sales = fund.get("ZC", {}).get("export_sales_weekly", {}) if fund else {}
    sales_ts = zc_sales.get("latest_date", "—") if isinstance(zc_sales, dict) else "—"
    sales_ts_html = f"<span style='font-size:11px; color:#f59e0b; font-weight:400; font-style:italic; float:right; margin-top:4px;'>(Dữ liệu: {sales_ts})</span>"
    st.markdown(f"""
    <div style='background:linear-gradient(90deg,#1a2035,#1e2a1e); border:1px solid #2d5a27; border-radius:10px; padding:10px 16px; margin:0 0 12px 0; display:flex; align-items:center; justify-content:space-between;'>
        <span style='font-size:15px; font-weight:800; color:#4ade80; letter-spacing:0.5px;'>📋 BÁN HÀNG Xuất Khẩu (Export Sales) — <span style='font-size:12px; color:#86efac; font-weight:500;'>Báo cáo Thứ 5 hàng tuần</span></span>
        {sales_ts_html}
    </div>""", unsafe_allow_html=True)


    if fund:
        cols2 = st.columns(2)
        for i, (code, name, emoji) in enumerate([("ZC", "Ngô", "🌽"), ("ZW", "Lúa Mì", "🌾")]):
            d = fund.get(code, {}).get("export_sales_weekly", {})
            with cols2[i]:
                net_sales = d.get("latest_net_sales", "N/A") if d else "N/A"
                prev_sales = d.get("previous_net_sales", "N/A") if d else "N/A"
                shipments = d.get("latest_shipments", "N/A") if d else "N/A"
                outstanding = d.get("outstanding_sales", "N/A") if d else "N/A"
                pct = d.get("pct_change", 0) if d else 0
                logic = d.get("logic", "") if d else ""
                week_end = d.get("week_ending", "—") if d else "—"
                next_rpt = d.get("next_report", "—") if d else "—"
                note = d.get("note", "") if d else ""
                
                is_na = "N/A" in net_sales
                
                bias = "bull" if pct > 5 else ("bear" if pct < -5 else "")
                badge = f'<span class="{bias}">' + ("▲ BULL" if bias == "bull" else "▼ BEAR" if bias == "bear" else "—") + '</span>' if bias else "—"
                
                st.markdown(f"""
                <div class='card' style='border-color:#2d5a27;'>
                    <div style='font-size:14px; font-weight:700; color:#e2e8f0; margin-bottom:10px;'>{emoji} {name}</div>
                    <div style='display:flex; justify-content:space-between; margin-bottom:6px;'>
                        <span style='color:#94a3b8; font-size:12px;'>Kỳ trước: {prev_sales}</span>
                        <span style='color:{"#64748b" if is_na else "#22c55e"}; font-weight:700; font-size:13px;'>{net_sales}</span>
                    </div>
                    <div style='margin-bottom:8px; border-bottom:1px solid #1e2d45; padding-bottom:8px;'>
                        {badge} &nbsp; {f'<span style="color:#22c55e;">+{pct:.2f}%</span>' if pct > 0 else f'<span style="color:#ef4444;">{pct:.2f}%</span>' if pct < 0 else '<span style="color:#94a3b8;">0.0%</span>'}
                    </div>
                    <div style='display:flex; justify-content:space-between; margin-bottom:6px; padding-bottom:6px;'>
                        <span style='color:#94a3b8; font-size:12px;'>🚢 Shipments (Giao trong tuần)</span>
                        <span style='color:#cbd5e1; font-size:13px;'>{shipments}</span>
                    </div>
                    <div style='display:flex; justify-content:space-between; margin-bottom:8px; border-bottom:1px solid #1e2d45; padding-bottom:6px;'>
                        <span style='color:#94a3b8; font-size:12px;'>📊 Outstanding (Tồn đơn)</span>
                        <span style='color:#cbd5e1; font-size:13px;'>{outstanding}</span>
                    </div>
                    <div style='font-size:11px; color:#64748b; margin-top:8px; margin-bottom:8px;'>
                        {logic[:150]}...
                    </div>
                    <div style='font-size:10px; color:#475569; border-top:1px solid #1e2d45; padding-top:6px;'>
                        📅 Kỳ báo cáo: <b style='color:#64748b;'>{week_end}</b> &nbsp;|&nbsp; Kế tiếp: <b style='color:#f59e0b;'>{next_rpt}</b>
                    </div>
                </div>""", unsafe_allow_html=True)

    # ── GIAO HÀNG XUẤT KHẨU (Export Inspections - Thứ 2) ────────────────────────
    zc_exp = fund.get("ZC", {}).get("exports", {}) if fund else {}
    ts = zc_exp.get("latest_date", "—") if isinstance(zc_exp, dict) else "—"
    ts_html = f"<span style='font-size:11px; color:#38bdf8; font-weight:400; font-style:italic; float:right; margin-top:4px;'>(Dữ liệu: {ts})</span>"
    st.markdown(f"""
    <div style='background:linear-gradient(90deg,#1a2035,#1a2535); border:1px solid #1e4a7a; border-radius:10px; padding:10px 16px; margin:20px 0 12px 0; display:flex; align-items:center; justify-content:space-between;'>
        <span style='font-size:15px; font-weight:800; color:#38bdf8; letter-spacing:0.5px;'>🚢 GIAO HÀNG Xuất Khẩu (Export Inspections) — <span style='font-size:12px; color:#7dd3fc; font-weight:500;'>Báo cáo Thứ 2 hàng tuần</span></span>
        {ts_html}
    </div>""", unsafe_allow_html=True)

    if fund:
        cols2 = st.columns(2)
        for i, (code, name) in enumerate([("ZC", "🌽 Ngô"), ("ZW", "🌾 Lúa Mì")]):
            d = fund.get(code, {}).get("exports", {})
            with cols2[i]:
                if d:
                    curr = d.get("latest", "N/A")
                    prev = d.get("previous", "N/A")
                    pct = d.get("pct_change", 0) or 0
                    logic = d.get("logic", "")
                    bias = "bull" if pct > 5 else ("bear" if pct < -5 else "")
                    badge = f'<span class="{bias}">' + ("▲ BULL" if bias == "bull" else "▼ BEAR" if bias == "bear" else "—") + '</span>' if bias else "—"
                    st.markdown(f"""
                    <div class='card' style='border-color:#1e4a7a;'>
                    <div style='font-size:14px; font-weight:700; color:#e2e8f0;'>{name}</div>
                    <div style='display:flex; justify-content:space-between; margin-top:8px;'>
                        <span class='prev'>Kỳ trước: {prev}</span>
                        <span class='curr'>{curr}</span>
                    </div>
                    <div style='margin-top:8px;'>{badge} &nbsp; {f'<span style="color:#22c55e;">+{pct:.1f}%</span>' if pct > 0 else f'<span style="color:#ef4444;">{pct:.1f}%</span>'}</div>
                    <div style='font-size:11px; color:#64748b; margin-top:8px;'>{logic[:100]}...</div>
                    </div>""", unsafe_allow_html=True)


    # ── USDA Cung Cầu ──────────────────────────────────────────────────────────────
    zc_cp = fund.get("ZC", {}).get("harvest_progress", {}) if fund else {}
    cp_ts = zc_cp.get("latest_date", "—") if isinstance(zc_cp, dict) else "—"
    cp_html = f"<span style='font-size:11px; color:#94a3b8; font-weight:400; font-style:italic; float:right; margin-top:4px;'>(Dữ liệu: {cp_ts})</span>"
    st.markdown(f"<div class='section-header'>📊 Cung Cầu Mùa Vụ (USDA Crop Progress) {cp_html}</div>", unsafe_allow_html=True)

    USDA_METRICS = [
        ("us_planting", "Tiến độ gieo trồng"),
        ("harvest_progress", "Tiến độ thu hoạch"),
        ("crop_condition", "Chất lượng (Good/Exc)"),
    ]

    import re
    def apply_delta(p_str, c_str):
        if c_str == "—" or not p_str or not c_str:
            return c_str
        prev_nums = [int(m) for m in re.findall(r'(\d+)%', p_str)]
        def replacer(match):
            curr_val = int(match.group(1))
            if prev_nums:
                prev_val = prev_nums.pop(0)
                delta = curr_val - prev_val
                if delta > 0:
                    return f"{curr_val}% <span style='color:#22c55e; font-size:11px; font-weight:700;'>(+{delta}%)</span>"
                elif delta < 0:
                    return f"{curr_val}% <span style='color:#ef4444; font-size:11px; font-weight:700;'>({delta}%)</span>"
                else:
                    return f"{curr_val}% <span style='color:#94a3b8; font-size:11px; font-weight:700;'>(0%)</span>"
            return f"{curr_val}%"
        return re.sub(r'(\d+)%', replacer, c_str)

    if fund:
        cols2 = st.columns(2)
        for i, (code, name, emoji) in enumerate([("ZC", "Ngô", "🌽"), ("ZW", "Lúa Mì", "🌾")]):
            d = fund.get(code, {})
            with cols2[i]:
                html_content = f"<div class='card'>\n<div style='font-weight:700; color:#e2e8f0; margin-bottom:12px; font-size:14px;'>{emoji} {name}</div>\n"
                for metric_key, metric_label in USDA_METRICS:
                    meta = d.get(metric_key, {})
                    if not meta: continue
                    curr_str = str(meta.get("latest", "—"))
                    prev_str = str(meta.get("previous", "—"))
                    
                    curr_parts = [p.strip() for p in curr_str.split(",")]
                    prev_parts = [p.strip() for p in prev_str.split(",")]
                    
                    if code == "ZW" and len(prev_parts) == 2 and ("đông" in prev_parts[0].lower() or "xuân" in prev_parts[1].lower()):
                        if len(curr_parts) == 1:
                            curr_lower = curr_str.lower()
                            c1, c2 = "—", "—"
                            if "đông" in curr_lower and "xuân" not in curr_lower:
                                c1 = curr_str
                            elif "xuân" in curr_lower and "đông" not in curr_lower:
                                c2 = curr_str
                            else:
                                c1 = curr_str
                            
                            c1_html = apply_delta(prev_parts[0], c1)
                            c2_html = apply_delta(prev_parts[1], c2)
                            lines_html = (f"<div><span class='prev'>{prev_parts[0]}</span> ➔ <span class='curr'>{c1_html}</span></div>"
                                          f"<div><span class='prev'>{prev_parts[1]}</span> ➔ <span class='curr'>{c2_html}</span></div>")
                        else:
                            c_parts = curr_parts[:]
                            while len(c_parts) < 2: c_parts.append("—")
                            lines_html = "".join([f"<div><span class='prev'>{p}</span> ➔ <span class='curr'>{apply_delta(p, c)}</span></div>" for p, c in zip(prev_parts, c_parts)])
                    elif len(prev_parts) > 1:
                        c_parts = curr_parts[:]
                        while len(c_parts) < len(prev_parts): c_parts.append("—")
                        lines_html = "".join([f"<div><span class='prev'>{p}</span> ➔ <span class='curr'>{apply_delta(p, c)}</span></div>" for p, c in zip(prev_parts, c_parts)])
                    else:
                        c_html = apply_delta(prev_str, curr_str)
                        lines_html = f"<div><span class='prev'>{prev_str}</span> ➔ <span class='curr'>{c_html}</span></div>"
                        
                    curr_dt = meta.get("latest_date", "")
                    html_content += f"""<div style='display:flex; justify-content:space-between; margin-bottom:8px; border-bottom:1px solid #1e2d45; padding-bottom:6px;'>
<span style='color:#cbd5e1; font-size:13px; margin-top:2px;'>{metric_label}</span>
<div style='text-align:right;'>
<div style='font-size:13px; line-height:1.4;'>{lines_html}</div>
<div style='font-size:10px; color:#475569;'>{curr_dt}</div>
</div>
</div>"""
                html_content += "</div>"
                st.markdown(html_content, unsafe_allow_html=True)


    # ── WASDE Tồn Kho ──────────────────────────────────────────────────────────────
    wasde_month = fund.get("ZC", {}).get("wasde", {}).get("month", "—") if fund else "—"
    wasde_html = f"<span style='font-size:11px; color:#94a3b8; font-weight:400; font-style:italic; float:right; margin-top:4px;'>(Kỳ báo cáo: {wasde_month} 2026)</span>"
    st.markdown(f"<div class='section-header'>🏛️ WASDE — Tồn Kho & Cân Đối Cung Cầu {wasde_html}</div>", unsafe_allow_html=True)

    if fund:
        cols2 = st.columns(2)
        for i, (code, name, emoji) in enumerate([("ZC", "Ngô", "🌽"), ("ZW", "Lúa Mì", "🌾")]):
            d = fund.get(code, {})
            with cols2[i]:
                html_content = f"<div class='card'>\n<div style='font-weight:700; color:#e2e8f0; margin-bottom:12px; font-size:14px;'>{emoji} {name}</div>\n"
                for metric_key, metric_label in [("us_ending_stocks", "Tồn Kho Mỹ"), ("global_ending_stocks", "Tồn Kho TG")]:
                    meta = d.get(metric_key, {})
                    if not meta: continue
                    curr = str(meta.get("current", meta.get("latest", "—")))
                    prev = str(meta.get("previous", "—"))
                    
                    import re
                    def get_first_num(s):
                        m = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)', s)
                        if m:
                            try: return float(m.group(1).replace(',', ''))
                            except: pass
                        return None
                    
                    p_val = get_first_num(prev)
                    c_val = get_first_num(curr)
                    delta_html = ""
                    if p_val is not None and c_val is not None and p_val != 0:
                        pct = (c_val - p_val) / p_val * 100
                        if pct > 0:
                            delta_html = f" <span style='color:#22c55e; font-size:11px; font-weight:700;'>(+{pct:.1f}%)</span>"
                        elif pct < 0:
                            delta_html = f" <span style='color:#ef4444; font-size:11px; font-weight:700;'>({pct:.1f}%)</span>"
                        else:
                            delta_html = f" <span style='color:#94a3b8; font-size:11px; font-weight:700;'>(0.0%)</span>"
                            
                    html_content += f"""<div style='display:flex; justify-content:space-between; margin-bottom:8px; border-bottom:1px solid #1e2d45; padding-bottom:6px;'>
<span style='color:#cbd5e1; font-size:13px;'>{metric_label}</span>
<div style='text-align:right;'>
<div style='font-size:13px;'><span class='prev'>{prev}</span> ➔ <span class='curr'>{curr}{delta_html}</span></div>
</div>
</div>"""
                html_content += "</div>"
                st.markdown(html_content, unsafe_allow_html=True)

    # ── Diện Tích Gieo Trồng (Acreage) ─────────────────────────────────────────────
    if acreage_data:
        st.markdown(f"<div class='section-header'>🌱 Diện Tích Gieo Trồng (NASS Planted Acreage)</div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style='font-size:12px; color:#64748b; margin-bottom:10px;'>
            Nguồn: <b style='color:#e2e8f0;'>USDA NASS</b> | Cập nhật: {acreage_data.get('fetched_at', '—')}
        </div>""", unsafe_allow_html=True)

        import plotly.graph_objects as go
    
        commodities = acreage_data.get("commodities", {})
        if commodities:
            # 1. Summary Cards
            cols3 = st.columns(3)
            for i, sym in enumerate(["ZC", "ZS", "ZW"]):
                if sym in commodities:
                    d = commodities[sym]
                    with cols3[i]:
                        st.markdown(f"""
                        <div class='card' style='text-align:center;'>
                            <div style='font-weight:700; color:#94a3b8; font-size:13px;'>{d.get('name')}</div>
                            <div style='font-size:24px; font-weight:800; color:#e2e8f0; margin:4px 0;'>{d.get('latest_planted_mln_acres', 0):.1f}<span style='font-size:14px; color:#64748b;'>M ac</span></div>
                            <div style='font-size:12px; color:{"#4ade80" if d.get('yoy_delta_mln_acres',0) < 0 else ("#f87171" if d.get('yoy_delta_mln_acres',0) > 0 else "#94a3b8")};'>
                                {d.get('yoy_direction')} {abs(d.get('yoy_delta_mln_acres', 0)):.1f}M ({d.get('yoy_pct', 0):+.1f}%)
                            </div>
                            <div style='font-size:11px; margin-top:8px; padding-top:8px; border-top:1px solid #1e2d45;'>
                                {d.get('signal')}
                            </div>
                        </div>""", unsafe_allow_html=True)

            # 2. History Chart
            fig = go.Figure()
            colors = {"ZC": "#facc15", "ZW": "#d97706", "ZS": "#4ade80"}
            for sym in ["ZC", "ZS", "ZW"]:
                if sym in commodities:
                    d = commodities[sym]
                    hist = d.get("history", [])
                    if hist:
                        x = [h["year"] for h in hist]
                        y = [h["planted_mln_acres"] for h in hist]
                        fig.add_trace(go.Scatter(
                            x=x, y=y, mode="lines+markers", name=d.get("name"),
                            line=dict(color=colors[sym], width=2),
                            marker=dict(size=6)
                        ))
        
            fig.update_layout(
                title="Biểu Đồ Lịch Sử Diện Tích Gieo Trồng (2015-Nay)",
                title_font=dict(size=14, color="#e2e8f0"),
                paper_bgcolor="#1a2035", plot_bgcolor="#1a2035",
                font=dict(color="#cbd5e1"),
                xaxis=dict(showgrid=False, linecolor="#334155"),
                yaxis=dict(title="Triệu Mẫu Anh (M acres)", gridcolor="#1e2d45"),
                margin=dict(l=40, r=20, t=40, b=20),
                height=300,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # 3. Lịch báo cáo sắp tới
        next_rep = acreage_data.get("next_report")
        if next_rep:
            st.markdown(f"""
            <div class='card' style='background:rgba(59,130,246,0.1); border-color:#3b82f6;'>
                <div style='font-size:13px; color:#93c5fd; font-weight:700;'>📅 BÁO CÁO SẮP TỚI: {next_rep.get('name')}</div>
                <div style='font-size:15px; color:#e2e8f0; font-weight:700; margin:4px 0;'>Thời gian: {next_rep.get('publish_vn')}</div>
                <div style='font-size:13px; color:#cbd5e1;'>{next_rep.get('description')}</div>
                <div style='font-size:13px; color:#f87171; font-weight:600; margin-top:4px;'>⚠️ {next_rep.get('impact')}</div>
            </div>""", unsafe_allow_html=True)
