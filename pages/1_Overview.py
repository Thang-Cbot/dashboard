"""
pages/1_Overview.py — TRUNG TÂM TÁC CHIẾN RUN TIN TỨC (CẤU TRÚC 6 PHẦN CHUẨN MỰC)
=================================================================================
- Bảng Phân Tích 5 Phần Đầu (Phần 1 -> Phần 5, tích hợp AgWeb Market Analysis ở Phần 5)
  -> Chốt Xu Hướng Trong Ngày cho từng mã W (Lúa mì) và C (Ngô).
- Phần 6 (Nằm riêng biệt cuối cùng): Chiến Lược Tác Chiến Trong Ngày (Nhận định đúc kết & Phương án hành động).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import re
import json
import html
import subprocess
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="RUN TIN TỨC 6 Phần — CBOT", page_icon="favicon.png", layout="wide")

DATA_OUTPUT = Path(__file__).parent.parent / "Data" / "output"


def render_html(raw_html: str):
    """Loại bỏ khoảng trắng đầu dòng để Markdown của Streamlit không biến HTML thành code block."""
    cleaned = "\n".join(line.lstrip() for line in raw_html.splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)


@st.fragment(run_every="30s")
def check_trigger_update():
    _trigger_file = DATA_OUTPUT / ".streamlit_trigger"
    _current_mtime = _trigger_file.stat().st_mtime if _trigger_file.exists() else 0
    if "last_trigger_mtime" not in st.session_state:
        st.session_state["last_trigger_mtime"] = _current_mtime

    if _current_mtime > st.session_state["last_trigger_mtime"]:
        st.session_state["last_trigger_mtime"] = _current_mtime
        st.cache_data.clear()
        st.rerun()


check_trigger_update()


@st.cache_data(ttl=30)
def load_json(fname):
    p = DATA_OUTPUT / fname
    if not p.exists():
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def get_cot_by_code(cot_data: dict, code: str) -> dict:
    if not cot_data:
        return {}
    if code in cot_data:
        return cot_data[code]
    commodities = cot_data.get("commodities", cot_data)
    for k, v in commodities.items():
        if isinstance(v, dict) and v.get("commodity") == code:
            return v
    return {}


def get_badge_style(badge_text: str) -> tuple:
    txt = (badge_text or "").upper()
    if any(k in txt for k in ["BULLISH", "HỒI PHỤC", "TĂNG", "HỖ TRỢ", "CORRECTION", "TẠO ĐÁY", "CẠN CUNG"]):
        return ("rgba(34, 197, 94, 0.15)", "#4ade80", "1px solid rgba(34, 197, 94, 0.4)")
    if any(k in txt for k in ["BEARISH", "ÁP LỰC GIẢM", "RỦI RO", "TIÊU CỰC"]):
        return ("rgba(239, 68, 68, 0.15)", "#f87171", "1px solid rgba(239, 68, 68, 0.4)")
    return ("rgba(245, 158, 11, 0.15)", "#fbbf24", "1px solid rgba(245, 158, 11, 0.4)")


def get_default_structured_report():
    """Bản dữ liệu chuẩn 6 phần mặc định."""
    return {
        "header_context": {
            "report_time": "2026-10-23 (Cấu trúc 6 Phần Chuẩn Mực)",
            "zw_price_str": "627.5 ¢/bu (Fair Value gốc: 670c)",
            "zc_price_str": "459.25 ¢/bu (Fair Value gốc: 480c)",
            "cot_summary": "ZW Net Est: -44,042 HĐ | ZC Net Est: +227,932 HĐ",
            "macro_summary": "DXY: 101.80 | Brent: 108.99$",
        },
        "table_parts": [
            {
                "part_num": "PHẦN 1",
                "part_title": "Phiên Đêm, Cấu Trúc Giá (VSA/Wyckoff) & Vị Thế COT",
                "core_content": "• <b>Lúa mì (ZWZ26):</b> Chốt phiên đêm tại 624.6c sau khi kiểm định đáy 2 tại <b>621.4c</b> với khối lượng bán cạn kiệt 85% (~2.000 HĐ so với 13.113 HĐ phiên Selling Climax). Mở phiên sáng bật lên vùng 628–630c và nén biên độ hẹp hấp thụ cung.<br>• <b>Vị thế COT:</b> Quỹ Managed Money đang ôm lượng Net Short quá tải <b>~43.000 - 44.000 HĐ</b> ở ZW.<br>• <b>Đối chiếu Fair Value:</b> ZW đang chiết khấu sâu hơn 40c so với trục gốc 670c; ZC giao dịch sát sàn chi phí sản xuất 455–460c.",
                "zw_impact": "Đã cạn kiệt nguồn cung bán tháo (Seller Exhaustion) tại đáy đôi 621.0 - 621.4. Phe Mua đang hấp thụ lực cung quanh 628-630.",
                "zw_badge": "TẠO ĐÁY ĐÔI / HỒI PHỤC KỸ THUẬT",
                "zc_impact": "Đà giảm thanh lý Long đang suy yếu dần khi giá tiệm cận vùng giá thành sản xuất của nông dân Mỹ.",
                "zc_badge": "DÒ ĐÁY NGẮN HẠN",
            },
            {
                "part_num": "PHẦN 2",
                "part_title": "Cung Cầu Thực Tế, Báo Cáo USDA & Cạnh Tranh Quốc Tế",
                "core_content": "• <b>USDA Weekly Export Sales:</b> Lúa mì chỉ đạt <b>239.627 tấn (~240k tấn)</b> — mức thấp nhất 6 tuần (giảm 25% so với mức 319k tuần trước). Tuy nhiên, tin xấu ra nhưng giá không thủng đáy 621c → <b>Đã Priced-in 100%</b>.<br>• <b>Cạnh tranh quốc tế:</b> Nga vẫn đẩy hàng giá rẻ 267–268 USD/tấn FOB qua các cảng Baltic, nhưng hạn ngạch xuất khẩu mùa đông từ tháng 11 sẽ bắt đầu siết lại.",
                "zw_impact": "Tin xuất khẩu xấu nhất đã được hấp thụ hoàn toàn mà không làm gãy cấu trúc đáy.",
                "zw_badge": "TRUNG TÍNH (ĐÃ PRICED-IN 100%)",
                "zc_impact": "Doanh số xuất khẩu Ngô đạt hơn 1.52 triệu tấn cùng nhu cầu Ethanol nội địa giữ trụ đỡ tốt.",
                "zc_badge": "HỖ TRỢ CẦU NỘI ĐỊA & XK",
            },
            {
                "part_num": "PHẦN 3",
                "part_title": "Địa Chính Trị Biển Đen & Vĩ Mô Liên Thị Trường",
                "core_content": "• <b>Đàm phán 3 bên (10/11):</b> Cố vấn Kremlin Yuri Ushakov xác nhận cuộc gặp từ 10/11 chỉ ở <b>cấp độ chuyên viên kỹ thuật (Technical level)</b> sau Bầu cử Mỹ (03/11), bác bỏ đề xuất ngừng bắn Oslo. Hòa bình chính thức còn rất xa vời.<br>• <b>Liên thị trường:</b> Giá năng lượng duy trì cao hỗ trợ chi phí đầu vào nông sản và nhiên liệu sinh học.",
                "zw_impact": "Thị trường nhận ra đàm phán 10/11 chỉ là thăm dò kỹ thuật, giúp phí rủi ro chiến tranh (War Premium) không bị bóc tách thêm.",
                "zw_badge": "HỖ TRỢ TÂM LÝ / SHORT-COVERING",
                "zc_impact": "Giá năng lượng neo cao củng cố biên lợi nhuận sản xuất cồn Ethanol tại Mỹ.",
                "zc_badge": "HỖ TRỢ TỪ NĂNG LƯỢNG",
            },
            {
                "part_num": "PHẦN 4",
                "part_title": "Thời Tiết (NOAA / Jim Roemer) & Mùa Vụ 2 Bán Cầu",
                "core_content": "• <b>Bắc Bán Cầu (Mỹ):</b> Mưa rào nhẹ tại Kansas & Oklahoma hỗ trợ lúa mì vụ Đông mới gieo nảy mầm; thời tiết khô ráo tại Corn Belt đẩy tiến độ thu hoạch Ngô vượt ngưỡng 65–70%.<br>• <b>Nam Bán Cầu & ENSO:</b> Úc và Argentina bước vào mùa thu hoạch tháng 11 tạo áp lực cung ngắn hạn; nhưng <b>Super El Niño (xác suất 83%)</b> đe dọa mùa đông 2026/27.",
                "zw_impact": "Gieo trồng Mỹ thuận lợi và hàng Nam Bán Cầu sắp ra kìm hãm đà tăng nóng, nhưng El Niño bảo kê xu hướng 2027.",
                "zw_badge": "GIẰNG CO NGẮN / BULLISH 2027",
                "zc_impact": "Thu hoạch vượt 65-70% đồng nghĩa áp lực xả hàng trực tiếp từ nông dân (Harvest Pressure) đang chạm đỉnh và sắp hạ nhiệt.",
                "zc_badge": "SẮP THOÁT ÁP LỰC MÙA GẶT",
            },
            {
                "part_num": "PHẦN 5",
                "part_title": "Chuyên Mục AgWeb Market Analysis (Góc Nhìn Chuyên Gia Mỹ)",
                "core_content": "• <b>Mark Schultz (North Star Commodity) & Michelle Rook (AgWeb):</b> Nhận định trong bài <i>'Corn and Wheat Look for Lows'</i> rằng cả Lúa mì và Ngô đều đã rơi vào trạng thái <b>Cực Kỳ Quá Bán (Extremely Oversold)</b> và đến lúc phải có nhịp hồi phục kỹ thuật (Due for a technical correction).<br>• <b>Sam Hudson & DuWayne Bosse:</b> Áp lực bán của quỹ và nông dân sẽ chững lại khi thu hoạch đạt 60–70%, nông dân bắt đầu cất hàng vào kho Silo.",
                "zw_impact": "Xác nhận vùng giá hiện tại đang trong pha dò đáy và xây nền (Looking for Lows), rủi ro bán đuổi cực cao.",
                "zw_badge": "QUÁ BÁN - CHỜ BẬT HỒI (CORRECTION)",
                "zc_impact": "Đang thiết lập đáy mùa vụ thu hoạch (Seasonal Harvest Low) khi nông dân chuẩn bị đóng kho ngừng bán rẻ.",
                "zc_badge": "THIẾT LẬP ĐÁY MÙA VỤ (HARVEST LOW)",
            },
        ],
        "daily_trend_conclusion": {
            "summary_label": "Tổng hợp trọng số từ 5 Phần phân tích trên cho phiên giao dịch hôm nay:",
            "zw_trend_title": "HỒI PHỤC KỸ THUẬT / SHORT-COVERING CUỐI TUẦN",
            "zw_range": "Biên độ dự kiến: 624.5 – 636.0 ¢/bu (ZWZ26)",
            "zw_rationale": "Đáy đôi 621.0 - 621.4 đã hấp thụ trọn vẹn tin xấu USDA 240k tấn; quỹ ôm -43k HĐ Net Short có xu hướng mua cover hạ tải trước kỳ nghỉ cuối tuần.",
            "zc_trend_title": "TÍCH LŨY XÂY NỀN ĐÁY MÙA VỤ (SIDEWAY-TO-UP)",
            "zc_range": "Biên độ dự kiến: 456.0 – 468.0 ¢/bu (ZCZ26)",
            "zc_rationale": "Áp lực bán thu hoạch của nông dân Mỹ đạt đỉnh quanh mốc 65-70% diện tích, cầu xuất khẩu và Ethanol đỡ giá tại vùng sàn chi phí 455-460c.",
        },
        "part6_strategy": {
            "executive_verdict": "Đúc kết từ 5 phần phân tích trên: Thị trường Lúa mì (W) và Ngô (C) đều đã đi vào vùng quá bán sâu và phản ánh xong các tin tức bất lợi ngắn hạn (báo cáo xuất khẩu 240k tấn, áp lực thu hoạch Mỹ, và tin đồn đàm phán kỹ thuật 10/11). Sự kiện giá kiểm định mốc 621.4c với khối lượng sụt giảm 85% cùng nhận định 'Looking for Lows' từ các chuyên gia AgWeb khẳng định lực bán tháo cưỡng bức từ phe Long đã cạn kiệt (như Charlie Sernatinger - Marex đã chỉ ra). Tuy nhiên, do chưa có chất xúc tác thời tiết mới nên nhịp tăng hiện tại chủ yếu đến từ hoạt động mua đóng vị thế (Short-Covering) của khối quỹ đang cầm -43k HĐ Net Short. Chiến lược tối ưu là đứng ở vị thế chủ động với 100% tiền mặt, chỉ bắn tỉa ngắn hạn ở kỳ gần (Z) khi có nhịp nhúng retest và kiên nhẫn chờ gom dài hạn kỳ xa (H) sau khi qua giai đoạn ép Spread Rollover.",
            "golden_rules": [
                "Tâm thế Vua Tiền Mặt (100% Cash > $21.500 USD): Đã chốt bảo toàn vốn + lãi nhẹ vị thế ZWH27 tại 643+, tuyệt đối không chịu áp lực tâm lý và không bị bào mòn bởi hiện tượng thu hẹp chênh lệch giá (Contango Spread Compression: Mua kỳ gần Z, Bán kỳ xa H).",
                "Cấm kỵ tuyệt đối: KHÔNG SHORT chặn đầu ở vùng 628 – 631 khi thị trường vừa xác lập đáy đôi cạn cung và các quỹ chuẩn bị bước vào nhịp Weekend Short-Covering; đồng thời KHÔNG FOMO mua đuổi ngay dưới cản khi chưa có nến bứt phá.",
                "Phân tách rõ 2 nhiệm vụ: Đánh lướt sóng ngắn hạn chỉ dùng HĐ Tháng 12 (ZWZ26) để hưởng trọn biên độ nhạy; Gom trung-dài hạn cho năm 2027 (ZWH27 / ZCH27) phải kiên nhẫn đợi vùng chiết khấu sâu 61x (với Z26) hoặc sau khi bão thông tin đàm phán 10/11 và Rollover đi qua.",
            ],
            "zw_tactical": {
                "intraday_contract": "ZWZ26 (HĐ Tháng 12/2026)",
                "intraday_plan": "• Kịch bản 1 (Pullback - Ưu tiên): Chờ nhịp nhúng kiểm định lại vùng hỗ trợ cân bằng 624.5 – 626.0 ¢/bu với volume thấp và nến M15 rút chân → Vào Sniper Long 1 lot. Cắt lỗ (SL): 620.5c | Chốt lời (TP): 633.0 – 636.5c.\n• Kịch bản 2 (Breakout): Nếu phiên Âu/Mỹ nổ volume đóng nến H1 dứt khoát trên 632.0c → Canh nhịp backtest 631.0 – 631.5c để mua lướt lên 636.5 – 638.5c (chốt gọn trong ngày).",
                "support_zone": "624.5 – 626.0c (Hỗ trợ gần) | 621.0 – 621.4c (Đáy kép thép)",
                "resistance_zone": "630.6 – 632.0c (Cản gần) | 636.0 – 638.5c (Mục tiêu Short-covering)",
                "macro_dca_contract": "ZWH27 (HĐ Tháng 03/2027)",
                "macro_dca_plan": "Tạm đứng ngoài quan sát sau khi đã thoát thành công ở 643+. Chờ đợt ép Spread Rollover đầu tháng 11 và nhiễu tin đàm phán 10/11 đẩy giá về vùng chiết khấu mục tiêu (tương ứng Z26 về 61x hoặc H27 về 628.0 – 635.0c) mới kích hoạt gom lại đón sóng mùa đông & Super El Niño 2027.",
            },
            "zc_tactical": {
                "intraday_contract": "ZCZ26 (HĐ Tháng 12/2026)",
                "intraday_plan": "Theo dõi phản ứng tạo nền quanh vùng 456.0 – 460.0 ¢/bu. Chỉ giải ngân lướt sóng khi xuất hiện cấu trúc đảo chiều MSS trên khung M15/H1 vượt lại mốc 462.5c, mục tiêu hướng về 468.0 – 472.0c.",
                "support_zone": "455.0 – 459.0c (Vùng sàn giá thành sản xuất Mỹ)",
                "resistance_zone": "465.0 – 472.0c (Kháng cự ngắn hạn)",
                "macro_dca_contract": "ZCZ26 / ZCH27 (Đón đáy mùa gặt)",
                "macro_dca_plan": "Đưa vào tầm ngắm thu gom tích lũy tại vùng 455.0 – 465.0 ¢/bu khi tiến độ thu hoạch Mỹ vượt 70% và nông dân đóng kho Silo ngừng xả hàng giao ngay (theo đúng tín hiệu từ AgWeb Market Analysis).",
            },
        },
    }


def render_overview():
    render_html("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0f1629; }
    [data-testid="stSidebar"] { background: #0d1424 !important; border-right: 1px solid #1e2d45; min-width: 260px !important; max-width: 260px !important; width: 260px !important; }
    [data-testid="stSidebarNav"] { display: none !important; }
    .card { background: #1a2035; border: 1px solid #2a3a5c; border-radius: 12px; padding: 16px; margin-bottom: 14px; }
    .run-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        background: #131b2e;
        border: 1px solid #2a3a5c;
        border-radius: 12px;
        overflow: hidden;
        margin-bottom: 20px;
    }
    .run-table th {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        color: #f8fafc;
        font-size: 13px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        padding: 14px 16px;
        border-bottom: 2px solid #334155;
        border-right: 1px solid #1e293b;
        text-align: left;
    }
    .run-table td {
        padding: 14px 16px;
        border-bottom: 1px solid #1e293b;
        border-right: 1px solid #1e293b;
        color: #cbd5e1;
        font-size: 13.5px;
        line-height: 1.6;
        vertical-align: top;
    }
    .run-table tr:hover td {
        background: rgba(30, 41, 59, 0.45);
    }
    .part-badge {
        display: inline-block;
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: #ffffff;
        font-size: 11px;
        font-weight: 800;
        padding: 3px 9px;
        border-radius: 6px;
        margin-bottom: 6px;
        letter-spacing: 0.5px;
    }
    .part-badge-agweb {
        display: inline-block;
        background: linear-gradient(135deg, #d97706 0%, #b45309 100%);
        color: #ffffff;
        font-size: 11px;
        font-weight: 800;
        padding: 3px 9px;
        border-radius: 6px;
        margin-bottom: 6px;
        letter-spacing: 0.5px;
    }
    .part6-container {
        background: linear-gradient(145deg, #111827 0%, #1a2238 100%);
        border: 2px solid #3b82f6;
        border-radius: 14px;
        padding: 22px;
        margin-top: 10px;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px -10px rgba(59, 130, 246, 0.25);
    }
    </style>
    """)

    # Sidebar nav
    st.sidebar.page_link("app.py",                   label="🏠 Trang Chủ")
    st.sidebar.page_link("pages/1_Overview.py", label="⚡ Tổng Quan (RUN TIN TỨC)")
    st.sidebar.page_link("pages/2_Profiles.py",      label="📈 Hồ Sơ Từng Mã")
    st.sidebar.page_link("pages/3_News.py",          label="📰 Báo Cáo USDA & Tin Tức")
    st.sidebar.page_link("pages/4_Weather_Map.py",   label="🌤️ Thời Tiết & Bản Đồ")
    st.sidebar.page_link("pages/5_Macro_Matrix.py",  label="🧠 Ma Trận Vĩ Mô (Brain)")
    st.sidebar.page_link("pages/6_MuaVu.py",         label="🌾 Mùa Vụ")
    st.sidebar.page_link("pages/7_System_Logs.py",   label="⚙️ System Logs")

    st.sidebar.markdown("---")

    def trigger_run_tin_tuc():
        with st.spinner("⚡ Đang quét AgWeb Market Analysis & chạy RUN TIN TỨC 6 Phần..."):
            base = Path(__file__).parent.parent
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            try:
                if "GEMINI_API_KEY" in st.secrets:
                    env["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
            except Exception:
                pass
            res = subprocess.run(
                [sys.executable, str(base / "Data" / "ai_analyzer.py")],
                capture_output=True, text=True, encoding="utf-8", env=env, timeout=110
            )
            if res.returncode == 0 and ("OK" in res.stdout or "hoàn tất" in res.stdout or "thành công" in res.stdout):
                st.session_state["ai_msg"] = ("success", "✅ Đã cập nhật RUN TIN TỨC 6 Phần & AgWeb mới nhất!")
            else:
                err = res.stdout.strip()[-300:] if res.stdout else res.stderr.strip()[-300:]
                st.session_state["ai_msg"] = ("error", f"❌ Lỗi cập nhật:\n{err}")
            st.cache_data.clear()
            st.rerun()

    if st.sidebar.button("⚡ CHẠY RUN TIN TỨC (AI)", use_container_width=True):
        trigger_run_tin_tuc()

    if "ai_msg" in st.session_state:
        kind, txt = st.session_state.pop("ai_msg")
        if kind == "success":
            st.toast(txt, icon="✅")
            st.sidebar.success(txt)
        else:
            st.sidebar.error(txt)

    # Load live JSON data
    macro   = load_json("macro_data.json")
    cot     = load_json("cot_data.json")
    meta    = load_json("contracts_meta.json")
    ai_raw  = load_json("ai_analysis.json")

    structured = ai_raw.get("structured") if isinstance(ai_raw, dict) else None
    if not structured or "table_parts" not in structured:
        structured = get_default_structured_report()

    agweb_articles = ai_raw.get("agweb_articles", []) if isinstance(ai_raw, dict) else []
    report_ts = ai_raw.get("timestamp", structured.get("header_context", {}).get("report_time", "—"))

    # ── TOP HEADER & ACTION BAR ──
    col_title, col_btn = st.columns([3.5, 1.2])
    with col_title:
        render_html(f"""
        <div style='margin-bottom:12px;'>
            <div style='display:flex; align-items:center; gap:10px;'>
                <span style='font-size:28px;'>⚡</span>
                <div>
                    <div style='font-size:22px; font-weight:800; color:#f8fafc; letter-spacing:0.3px;'>
                        RUN TIN TỨC — BẢNG PHÂN TÍCH 5 PHẦN & CHIẾN LƯỢC TÁC CHIẾN (PHẦN 6)
                    </div>
                    <div style='font-size:12px; color:#94a3b8;'>
                        Chuẩn hóa 6 Phần | Tích hợp <a href='https://www.agweb.com/markets/market-analysis' target='_blank' style='color:#fbbf24; text-decoration:none; font-weight:600;'>AgWeb Market Analysis ↗</a> | Cập nhật lần cuối: <b>{report_ts}</b>
                    </div>
                </div>
            </div>
        </div>
        """)
    with col_btn:
        render_html("<div style='height:6px;'></div>")
        if st.button("🔄 CẬP NHẬT RUN TIN TỨC MỚI NHẤT", use_container_width=True):
            trigger_run_tin_tuc()

    # ── LIVE METRICS STRIP (ZW, ZC, COT, MACRO) ──
    zw_close = meta.get("ZW", {}).get("liquidity", {}).get("today_close") or macro.get("zw_ref", {}).get("price", 627.5)
    zw_prev  = meta.get("ZW", {}).get("liquidity", {}).get("prev_close") or macro.get("zw_ref", {}).get("prev", 624.75)
    zw_diff  = (zw_close - zw_prev) if isinstance(zw_close, (int, float)) and isinstance(zw_prev, (int, float)) else 0

    zc_close = meta.get("ZC", {}).get("liquidity", {}).get("today_close") or macro.get("zc_ref", {}).get("price", 459.25)
    zc_prev  = meta.get("ZC", {}).get("liquidity", {}).get("prev_close") or macro.get("zc_ref", {}).get("prev", 460.5)
    zc_diff  = (zc_close - zc_prev) if isinstance(zc_close, (int, float)) and isinstance(zc_prev, (int, float)) else 0

    cot_zw = get_cot_by_code(cot, "ZW")
    cot_zc = get_cot_by_code(cot, "ZC")
    zw_net_est = cot_zw.get("net_estimated", cot_zw.get("net_position", -44042))
    zc_net_est = cot_zc.get("net_estimated", cot_zc.get("net_position", 227932))

    dxy_val   = macro.get("dxy", {}).get("price", 101.80)
    dxy_pct   = macro.get("dxy", {}).get("pct", 0.0)
    brent_val = macro.get("brent", {}).get("price", 108.99)

    m1, m2, m3, m4 = st.columns(4, gap="small")
    with m1:
        c_zw = "#4ade80" if zw_diff >= 0 else "#f87171"
        arr_zw = "▲" if zw_diff >= 0 else "▼"
        render_html(f"""
        <div style='background:#161f33; border:1px solid #2a3a5c; border-left:4px solid #3b82f6; border-radius:10px; padding:10px 14px;'>
            <div style='font-size:11px; color:#94a3b8; font-weight:700;'>🌾 LÚA MÌ (ZWZ26) vs FAIR VALUE 670c</div>
            <div style='display:flex; justify-content:space-between; align-items:baseline; margin-top:4px;'>
                <span style='font-size:20px; font-weight:800; color:#f8fafc;'>{zw_close} ¢/bu</span>
                <span style='font-size:12px; font-weight:700; color:{c_zw};'>{arr_zw} {zw_diff:+.2f}c</span>
            </div>
        </div>""")
    with m2:
        c_zc = "#4ade80" if zc_diff >= 0 else "#f87171"
        arr_zc = "▲" if zc_diff >= 0 else "▼"
        render_html(f"""
        <div style='background:#161f33; border:1px solid #2a3a5c; border-left:4px solid #f59e0b; border-radius:10px; padding:10px 14px;'>
            <div style='font-size:11px; color:#94a3b8; font-weight:700;'>🌽 NGÔ (ZCZ26) vs FAIR VALUE 480c</div>
            <div style='display:flex; justify-content:space-between; align-items:baseline; margin-top:4px;'>
                <span style='font-size:20px; font-weight:800; color:#f8fafc;'>{zc_close} ¢/bu</span>
                <span style='font-size:12px; font-weight:700; color:{c_zc};'>{arr_zc} {zc_diff:+.2f}c</span>
            </div>
        </div>""")
    with m3:
        render_html(f"""
        <div style='background:#161f33; border:1px solid #2a3a5c; border-left:4px solid #a855f7; border-radius:10px; padding:10px 14px;'>
            <div style='font-size:11px; color:#94a3b8; font-weight:700;'>🏦 VỊ THẾ QUỸ COT (NET ESTIMATED)</div>
            <div style='display:flex; justify-content:space-between; align-items:baseline; margin-top:4px;'>
                <span style='font-size:13px; font-weight:700; color:#f87171;'>ZW: {zw_net_est:+,.0f} HĐ</span>
                <span style='font-size:13px; font-weight:700; color:#fbbf24;'>ZC: {zc_net_est:+,.0f} HĐ</span>
            </div>
        </div>""")
    with m4:
        render_html(f"""
        <div style='background:#161f33; border:1px solid #2a3a5c; border-left:4px solid #10b981; border-radius:10px; padding:10px 14px;'>
            <div style='font-size:11px; color:#94a3b8; font-weight:700;'>🌐 VĨ MÔ LIÊN THỊ TRƯỜNG (DXY & DẦU)</div>
            <div style='display:flex; justify-content:space-between; align-items:baseline; margin-top:4px;'>
                <span style='font-size:13px; font-weight:700; color:#e2e8f0;'>DXY: {dxy_val:.2f} ({dxy_pct:+.2f}%)</span>
                <span style='font-size:13px; font-weight:700; color:#e2e8f0;'>Brent: ${brent_val:.2f}</span>
            </div>
        </div>""")

    render_html("<div style='height:14px;'></div>")

    # ══════════════════════════════════════════════════════════════════════════
    # KHU VỰC 1: BẢNG PHÂN TÍCH 5 PHẦN & ĐỊNH HƯỚNG XU HƯỚNG TRONG NGÀY
    # ══════════════════════════════════════════════════════════════════════════
    render_html("""
    <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>
        <div style='font-size:16px; font-weight:800; color:#e2e8f0; text-transform:uppercase; letter-spacing:0.6px;'>
            📋 BẢNG PHÂN TÍCH 5 PHẦN & ĐỊNH HƯỚNG XU HƯỚNG TRONG NGÀY (PHẦN 1 ➔ PHẦN 5)
        </div>
        <div style='font-size:12px; color:#64748b;'>
            Đối chiếu đa tầng ➔ Chốt xu hướng độc lập cho từng mã W & C
        </div>
    </div>
    """)

    table_parts = structured.get("table_parts", [])
    conclusion  = structured.get("daily_trend_conclusion", {})

    rows_html = ""
    for part in table_parts:
        p_num   = part.get("part_num", "")
        p_title = part.get("part_title", "")
        p_core  = part.get("core_content", "")
        zw_imp  = part.get("zw_impact", "")
        zw_bdg  = part.get("zw_badge", "NEUTRAL")
        zc_imp  = part.get("zc_impact", "")
        zc_bdg  = part.get("zc_badge", "NEUTRAL")

        is_agweb = "PHẦN 5" in p_num.upper() or "AGWEB" in p_title.upper()
        badge_cls = "part-badge-agweb" if is_agweb else "part-badge"
        row_bg = "background: rgba(217, 119, 6, 0.06);" if is_agweb else ""

        zw_bg, zw_col, zw_bdr = get_badge_style(zw_bdg)
        zc_bg, zc_col, zc_bdr = get_badge_style(zc_bdg)

        agweb_link_html = ""
        if is_agweb:
            agweb_link_html = (
                "<div style='margin-top:6px;'>"
                "<a href='https://www.agweb.com/markets/market-analysis' target='_blank' "
                "style='font-size:11px; color:#fbbf24; text-decoration:underline; font-weight:600;'>"
                "🔗 Mở AgWeb Market Analysis ↗</a></div>"
            )

        rows_html += f"""
<tr style="{row_bg}">
<td style="width:18%; font-weight:700; color:#f1f5f9;">
<span class="{badge_cls}">{p_num}</span>
<div style="font-size:13.5px; font-weight:700; color:#e2e8f0; line-height:1.35;">{p_title}</div>
{agweb_link_html}
</td>
<td style="width:40%;">{p_core}</td>
<td style="width:21%;">
<div style="display:inline-block; background:{zw_bg}; color:{zw_col}; border:{zw_bdr}; font-size:11px; font-weight:800; padding:3px 8px; border-radius:6px; margin-bottom:6px;">🌾 {zw_bdg}</div>
<div style="font-size:13px; color:#cbd5e1;">{zw_imp}</div>
</td>
<td style="width:21%;">
<div style="display:inline-block; background:{zc_bg}; color:{zc_col}; border:{zc_bdr}; font-size:11px; font-weight:800; padding:3px 8px; border-radius:6px; margin-bottom:6px;">🌽 {zc_bdg}</div>
<div style="font-size:13px; color:#cbd5e1;">{zc_imp}</div>
</td>
</tr>
"""

    sum_label  = conclusion.get("summary_label", "Tổng hợp trọng số từ 5 Phần trên cho phiên giao dịch hôm nay:")
    zw_t_title = conclusion.get("zw_trend_title", "—")
    zw_t_range = conclusion.get("zw_range", "—")
    zw_t_rat   = conclusion.get("zw_rationale", "")
    zc_t_title = conclusion.get("zc_trend_title", "—")
    zc_t_range = conclusion.get("zc_range", "—")
    zc_t_rat   = conclusion.get("zc_rationale", "")

    rows_html += f"""
<tr style="background: linear-gradient(135deg, #1e1b4b 0%, #172554 100%); border-top: 2px solid #3b82f6;">
<td style="font-weight:800; color:#fbbf24; font-size:13.5px;">🎯 KẾT LUẬN XU HƯỚNG TRONG NGÀY</td>
<td style="font-weight:600; color:#e2e8f0; font-size:13.5px;">
{sum_label}
<div style="font-size:12px; color:#93c5fd; margin-top:4px;">(Làm cơ sở trực tiếp để lập Phương Án Tác Chiến tại <b>PHẦN 6</b> bên dưới)</div>
</td>
<td style="background: rgba(37, 99, 235, 0.15);">
<div style="font-size:13px; font-weight:800; color:#60a5fa; margin-bottom:4px;">🌾 XU HƯỚNG W: {zw_t_title}</div>
<div style="font-size:12px; font-weight:700; color:#fbbf24; margin-bottom:4px;">📌 {zw_t_range}</div>
<div style="font-size:12px; color:#cbd5e1;">{zw_t_rat}</div>
</td>
<td style="background: rgba(245, 158, 11, 0.12);">
<div style="font-size:13px; font-weight:800; color:#fbbf24; margin-bottom:4px;">🌽 XU HƯỚNG C: {zc_t_title}</div>
<div style="font-size:12px; font-weight:700; color:#4ade80; margin-bottom:4px;">📌 {zc_t_range}</div>
<div style="font-size:12px; color:#cbd5e1;">{zc_t_rat}</div>
</td>
</tr>
"""

    full_table_html = f"""
<table class="run-table">
<thead>
<tr>
<th style="width:18%;">PHẦN PHÂN TÍCH</th>
<th style="width:40%;">NỘI DUNG CỐT LÕI & ĐỘ THẨM THẤU (PRICED-IN)</th>
<th style="width:21%;">TÁC ĐỘNG & XU HƯỚNG MÃ W (LÚA MÌ)</th>
<th style="width:21%;">TÁC ĐỘNG & XU HƯỚNG MÃ C (NGÔ)</th>
</tr>
</thead>
<tbody>
{rows_html}
</tbody>
</table>
"""
    render_html(full_table_html)

    # ══════════════════════════════════════════════════════════════════════════
    # KHU VỰC 2 (RIÊNG BIỆT CUỐI CÙNG): PHẦN 6 — CHIẾN LƯỢC TÁC CHIẾN TRONG NGÀY
    # ══════════════════════════════════════════════════════════════════════════
    p6 = structured.get("part6_strategy", {})
    verdict = p6.get("executive_verdict", "")
    rules   = p6.get("golden_rules", [])
    zw_tac  = p6.get("zw_tactical", {})
    zc_tac  = p6.get("zc_tactical", {})

    rules_html = "".join(
        [
            f"<div style='padding:6px 10px; margin-bottom:6px; background:rgba(15, 23, 42, 0.75); "
            f"border-left:3px solid #fbbf24; border-radius:4px; font-size:13px; color:#e2e8f0;'>"
            f"<b>⚠️ Nguyên tắc {idx}:</b> {r}</div>"
            for idx, r in enumerate(rules, 1)
        ]
    )

    render_html(f"""
    <div class="part6-container">
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #334155; padding-bottom:12px; margin-bottom:16px;">
            <div style="display:flex; align-items:center; gap:10px;">
                <span style="background:linear-gradient(135deg, #2563eb, #1d4ed8); color:white; font-weight:800; font-size:13px; padding:5px 12px; border-radius:8px; letter-spacing:0.8px;">
                    PHẦN 6 (CUỐI CÙNG)
                </span>
                <span style="font-size:19px; font-weight:800; color:#f8fafc; letter-spacing:0.4px;">
                    ⚔️ CHIẾN LƯỢC TÁC CHIẾN TRONG NGÀY (NHẬN ĐỊNH ĐÚC KẾT TỐI HẬU)
                </span>
            </div>
            <span style="font-size:12px; color:#93c5fd; font-weight:600;">
                Đúc kết từ 5 Phần Phân Tích ➔ Hành Động Thực Chiến
            </span>
        </div>
        <div style="background:rgba(30, 41, 59, 0.7); border:1px solid #334155; border-radius:10px; padding:14px 16px; margin-bottom:16px;">
            <div style="font-size:12px; font-weight:800; color:#60a5fa; text-transform:uppercase; letter-spacing:0.6px; margin-bottom:6px;">
                🧠 NHẬN ĐỊNH TỔNG KẾT TỪ 5 PHẦN TRÊN:
            </div>
            <div style="font-size:14px; color:#f1f5f9; line-height:1.65;">
                {verdict}
            </div>
        </div>
        <div style="margin-bottom:16px;">
            <div style="font-size:12px; font-weight:800; color:#fbbf24; text-transform:uppercase; letter-spacing:0.6px; margin-bottom:8px;">
                🛡️ KỶ LUẬT & NGUYÊN TẮC VÀNG HÔM NAY:
            </div>
            {rules_html}
        </div>
    </div>
    """)

    # Hai cột Phương án tác chiến cụ thể cho W và C
    col_w, col_c = st.columns(2, gap="medium")

    with col_w:
        zw_intra_plan = (zw_tac.get("intraday_plan", "—") or "—").replace("\n", "<br>")
        zw_dca_plan   = (zw_tac.get("macro_dca_plan", "—") or "—").replace("\n", "<br>")
        render_html(f"""
        <div class="card" style="border-top:4px solid #3b82f6; background:#151e32;">
            <div style="font-size:16px; font-weight:800; color:#60a5fa; margin-bottom:12px; border-bottom:1px solid #2a3a5c; padding-bottom:8px;">
                🌾 PHƯƠNG ÁN TÁC CHIẾN MÃ W — LÚA MÌ (CBOT WHEAT)
            </div>
            <div style="background:#0f1629; border:1px solid #1e293b; border-radius:8px; padding:12px; margin-bottom:10px;">
                <div style="font-size:12px; font-weight:800; color:#38bdf8; margin-bottom:6px;">
                    🎯 MŨI 1 — BẮN TỈA NGẮN HẠN INTRADAY ({zw_tac.get('intraday_contract', 'ZWZ26')})
                </div>
                <div style="font-size:13px; color:#e2e8f0; line-height:1.6; margin-bottom:8px;">
                    {zw_intra_plan}
                </div>
                <div style="display:flex; justify-content:space-between; font-size:12px; border-top:1px dashed #334155; padding-top:8px;">
                    <span style="color:#4ade80;"><b>🟢 Hỗ trợ:</b> {zw_tac.get('support_zone', '—')}</span>
                    <span style="color:#f87171;"><b>🔴 Kháng cự:</b> {zw_tac.get('resistance_zone', '—')}</span>
                </div>
            </div>
            <div style="background:#0f1629; border:1px solid #1e293b; border-radius:8px; padding:12px;">
                <div style="font-size:12px; font-weight:800; color:#a855f7; margin-bottom:6px;">
                    🏛️ MŨI 2 — THU GOM CHIẾN LƯỢC DÀI HẠN ({zw_tac.get('macro_dca_contract', 'ZWH27')})
                </div>
                <div style="font-size:13px; color:#cbd5e1; line-height:1.6;">
                    {zw_dca_plan}
                </div>
            </div>
        </div>
        """)

    with col_c:
        zc_intra_plan = (zc_tac.get("intraday_plan", "—") or "—").replace("\n", "<br>")
        zc_dca_plan   = (zc_tac.get("macro_dca_plan", "—") or "—").replace("\n", "<br>")
        render_html(f"""
        <div class="card" style="border-top:4px solid #f59e0b; background:#151e32;">
            <div style="font-size:16px; font-weight:800; color:#fbbf24; margin-bottom:12px; border-bottom:1px solid #2a3a5c; padding-bottom:8px;">
                🌽 PHƯƠNG ÁN TÁC CHIẾN MÃ C — NGÔ (CBOT CORN)
            </div>
            <div style="background:#0f1629; border:1px solid #1e293b; border-radius:8px; padding:12px; margin-bottom:10px;">
                <div style="font-size:12px; font-weight:800; color:#fbbf24; margin-bottom:6px;">
                    🎯 MŨI 1 — GIAO DỊCH NGẮN HẠN INTRADAY ({zc_tac.get('intraday_contract', 'ZCZ26')})
                </div>
                <div style="font-size:13px; color:#e2e8f0; line-height:1.6; margin-bottom:8px;">
                    {zc_intra_plan}
                </div>
                <div style="display:flex; justify-content:space-between; font-size:12px; border-top:1px dashed #334155; padding-top:8px;">
                    <span style="color:#4ade80;"><b>🟢 Hỗ trợ:</b> {zc_tac.get('support_zone', '—')}</span>
                    <span style="color:#f87171;"><b>🔴 Kháng cự:</b> {zc_tac.get('resistance_zone', '—')}</span>
                </div>
            </div>
            <div style="background:#0f1629; border:1px solid #1e293b; border-radius:8px; padding:12px;">
                <div style="font-size:12px; font-weight:800; color:#34d399; margin-bottom:6px;">
                    🏛️ MŨI 2 — THU GOM ĐÁY MÙA VỤ ({zc_tac.get('macro_dca_contract', 'ZCZ26 / ZCH27')})
                </div>
                <div style="font-size:13px; color:#cbd5e1; line-height:1.6;">
                    {zc_dca_plan}
                </div>
            </div>
        </div>
        """)

    # ── DANH SÁCH BÀI VIẾT GỐC AGWEB MARKET ANALYSIS ──
    with st.expander("📰 Xem danh sách các bài phân tích gốc vừa quét từ chuyên mục AgWeb Market Analysis", expanded=False):
        if agweb_articles:
            for item in agweb_articles:
                t = html.escape(item.get("title", ""))
                s = html.escape(item.get("summary", ""))
                d = html.escape(item.get("pub_date", ""))
                l = item.get("link", "https://www.agweb.com/markets/market-analysis")
                render_html(f"""
                <div style='padding:10px 14px; background:#131b2e; border:1px solid #2a3a5c; border-left:3px solid #f59e0b; border-radius:8px; margin-bottom:8px;'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <a href='{l}' target='_blank' style='font-size:14px; font-weight:700; color:#fbbf24; text-decoration:none;'>{t} ↗</a>
                        <span style='font-size:11px; color:#64748b;'>{d}</span>
                    </div>
                    <div style='font-size:12.5px; color:#cbd5e1; margin-top:4px;'>{s}</div>
                </div>
                """)
        else:
            st.info("Nhấn nút '🔄 CẬP NHẬT RUN TIN TỨC MỚI NHẤT' ở góc trên bên phải để quét trực tiếp các bài viết mới nhất từ AgWeb Market Analysis.")


render_overview()
