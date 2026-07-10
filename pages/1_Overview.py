"""
pages/1_Overview.py  — Tab Tổng Quan
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
import streamlit as st
from pathlib import Path
from components.alert_panel import render_alert_panel
# Force reload alert panel
from components.charts import render_macro_bar

st.set_page_config(page_title="Tổng Quan — CBOT", page_icon="📊", layout="wide")

DATA_OUTPUT = Path(__file__).parent.parent / "Data" / "output"

# ── CFTC code → commodity code map ─────────────────────────────────────────────
CFTC_TO_CODE = {"002602": "ZC", "001602": "ZW"}

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


def get_cot_by_code(cot_data: dict, code: str) -> dict:
    """Tìm COT entry theo mã ZC/ZW từ cot_data."""
    if not cot_data:
        return {}
    # Thử key trực tiếp trước
    if code in cot_data:
        return cot_data[code]
    # Tìm trong commodities dict (key=cftc_code)
    commodities = cot_data.get("commodities", cot_data)
    for k, v in commodities.items():
        if isinstance(v, dict) and v.get("commodity") == code:
            return v
    return {}


def render_overview():
    # ── CSS ──
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0f1629; }
    [data-testid="stSidebar"] { background: #0d1424 !important; border-right: 1px solid #1e2d45; min-width: 260px !important; max-width: 260px !important; width: 260px !important; }
[data-testid="stSidebarNav"] { display: none !important; }
    .card { background: #1a2035; border: 1px solid #2a3a5c; border-radius: 12px; padding: 16px; margin-bottom: 12px; }
    </style>""", unsafe_allow_html=True)

    # Sidebar nav
    st.sidebar.page_link("app.py",              label="🏠 Trang Chủ")
    st.sidebar.page_link("pages/1_Overview.py", label="📊 Tổng Quan")
    st.sidebar.page_link("pages/2_Profiles.py", label="📈 Hồ Sơ Từng Mã")
    st.sidebar.page_link("pages/3_News.py",     label="📰 Báo Cáo USDA & Tin Tức")
    st.sidebar.page_link("pages/4_Weather.py",  label="🌤️ Thời Tiết")
    st.sidebar.page_link("pages/5_AgriMap.py",  label="🗺️ Bản Đồ Thời Tiết & ENSO")
    st.sidebar.page_link("pages/6_MuaVu.py",   label="🌾 Mùa Vụ 2026")

    st.sidebar.markdown("---")
    if st.sidebar.button("🧠 AI Phân Tích", use_container_width=True):
        with st.sidebar:
            with st.spinner("AI đang phân tích..."):
                import subprocess
                base = Path(__file__).parent.parent
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                # Truyền API key từ Streamlit Secrets vào subprocess (cho môi trường Online)
                try:
                    if "GEMINI_API_KEY" in st.secrets:
                        env["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
                except Exception:
                    pass
                res = subprocess.run(
                    [sys.executable, str(base / "Data" / "ai_analyzer.py")],
                    capture_output=True, text=True, encoding="utf-8", env=env, timeout=60
                )
                if res.returncode == 0 and ("Thành công" in res.stdout or "thành công" in res.stdout or "OK" in res.stdout):
                    st.session_state["ai_msg"] = ("success", "✅ AI đã phân tích xong! Kết quả được cập nhật bên dưới.")
                else:
                    err = res.stdout.strip()[-300:] if res.stdout else res.stderr.strip()[-300:]
                    st.session_state["ai_msg"] = ("error", f"❌ Lỗi phân tích:\n{err}")
                st.cache_data.clear()
                st.rerun()

    # Hiển thị kết quả nút bấm (tồn tại qua rerun)
    if "ai_msg" in st.session_state:
        kind, txt = st.session_state.pop("ai_msg")
        if kind == "success":
            st.sidebar.success(txt)
        else:
            st.sidebar.error(txt)

    fund   = load_json("fundamental_data.json")
    macro  = load_json("macro_data.json")
    cot    = load_json("cot_data.json")
    status = load_json("data_status.json")

    # Header
    last_update = status.get("last_full_update", "—") if status else "—"
    st.markdown(f"""
    <div style='margin-bottom:20px;'>
        <div style='font-size:22px; font-weight:800; color:#e2e8f0;'>📊 Tổng Quan Thị Trường CBOT</div>
        <div style='font-size:12px; color:#64748b;'>Cập nhật: {last_update}</div>
    </div>""", unsafe_allow_html=True)
    
    # ── AI TRADING DESK ──
    ai_path = DATA_OUTPUT / "ai_analysis.json"
    api_key_path = DATA_OUTPUT.parent / "api_key.txt"
    
    st.markdown("""<div class='card' style='border: 1px solid #6366f1; background: linear-gradient(145deg, #1e1b4b, #1a2035);'>
        <div style='display:flex; align-items:center; gap:8px; margin-bottom:12px; border-bottom: 1px solid #3730a3; padding-bottom:8px;'>
            <span style='font-size:20px;'>🧠</span>
            <span style='font-size:14px; font-weight:800; color:#818cf8; letter-spacing:1px; text-transform:uppercase;'>AI Trading Desk</span>
        </div>""", unsafe_allow_html=True)
        
    has_api_key = False
    try:
        if "GEMINI_API_KEY" in st.secrets: has_api_key = True
    except: pass
    if os.environ.get("GEMINI_API_KEY") or api_key_path.exists():
        has_api_key = True

    if not has_api_key:
        st.warning("⚠️ Chưa tìm thấy API Key. Hãy lấy API Key Gemini (miễn phí) và cấu hình trong Streamlit Secrets (Online) hoặc lưu vào file `Data/api_key.txt` (Local) để phân tích tự động.")

    if ai_path.exists():
        try:
            ai_data = json.loads(ai_path.read_text(encoding="utf-8"))
            ai_text = ai_data.get("analysis", "")
            ai_time = ai_data.get("timestamp", "")
            st.markdown(f"<div style='font-size:11px; color:#64748b; margin-bottom:10px;'>Phân tích lúc: {ai_time}</div>", unsafe_allow_html=True)
            st.markdown(ai_text)
        except Exception:
            st.error("Không thể đọc dữ liệu AI.")
    else:
        st.info("Nhấn nút '🧠 AI Phân Tích' ở thanh menu bên trái để tạo nhận định mới nhất.")
            
    st.markdown("</div>", unsafe_allow_html=True)

    # Macro bar — fix: macro dùng key 'pct' không phải 'change_pct'
    if macro:
        cols = st.columns(3)
        for i, (key, label) in enumerate([("brent", "Brent Oil"), ("dxy", "DXY"), ("zw_ref", "ZW Ref")]):
            d = macro.get(key, {})
            if d:
                price = d.get("price", 0)
                pct   = d.get("pct", d.get("change_pct", 0)) or 0
                color = "#22c55e" if pct >= 0 else "#ef4444"
                arrow = "▲" if pct >= 0 else "▼"
                cols[i].markdown(f"""
                <div style='background:#1a2035; border-radius:8px; padding:12px; text-align:center;
                            border:1px solid #2a3a5c;'>
                    <div style='font-size:11px; color:#64748b; font-weight:600;'>{label}</div>
                    <div style='font-size:22px; font-weight:700; color:#e2e8f0;'>{price:.2f}</div>
                    <div style='font-size:13px; color:{color}; font-weight:600;'>{arrow} {abs(pct):.2f}%</div>
                </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Layout: Tóm tắt bên trái + Alert bên phải
    col_main, col_alert = st.columns([2, 1], gap="medium")

    with col_main:
        st.markdown("""<div class='card'>
            <div style='font-size:14px; font-weight:700; color:#94a3b8; letter-spacing:1px;
                        text-transform:uppercase; border-bottom:1px solid #2a3a5c;
                        padding-bottom:8px; margin-bottom:12px;'>
                📰 Tóm Tắt Tin Tức & Vĩ Mô
            </div>""", unsafe_allow_html=True)

        points = []

        # 1. ENSO
        wl_path = DATA_OUTPUT / "weather_long.json"
        if wl_path.exists():
            try:
                wl    = json.loads(wl_path.read_text(encoding="utf-8"))
                enso  = wl.get("enso_status", "Neutral")
                desc  = wl.get("description", "")[:100]
                points.append(f"🌊 <b>ENSO:</b> <span style='color:#60a5fa'>{enso}</span> — {desc}...")
            except Exception:
                pass

        # 2. Xuất khẩu Ngô
        zc_exp = fund.get("ZC", {}).get("exports", {})
        if zc_exp:
            pct = zc_exp.get("pct_change", 0) or 0
            color = "#22c55e" if pct > 0 else "#ef4444"
            points.append(f"🚢 <b>Xuất Khẩu Ngô:</b> {zc_exp.get('latest','N/A')} <span style='color:{color}'>({pct:+.1f}%)</span>")

        # 3. Xuất khẩu Lúa Mì
        zw_exp = fund.get("ZW", {}).get("exports", {})
        if zw_exp:
            pct = zw_exp.get("pct_change", 0) or 0
            color = "#22c55e" if pct > 0 else "#ef4444"
            points.append(f"🚢 <b>Xuất Khẩu Lúa Mì:</b> {zw_exp.get('latest','N/A')} <span style='color:{color}'>({pct:+.1f}%)</span>")

        # 4. Chất lượng Ngô
        zc_cc = fund.get("ZC", {}).get("crop_condition", {})
        if isinstance(zc_cc, dict) and zc_cc.get("latest"):
            points.append(f"🌽 <b>Chất Lượng Ngô (G/E):</b> <span style='color:#34d399'>{zc_cc.get('latest')}</span> · Kỳ trước: {zc_cc.get('previous','—')}")

        # 5. COT ZC
        zc_cot = get_cot_by_code(cot, "ZC")
        if zc_cot:
            net  = zc_cot.get("net_position", 0) or 0
            chg  = zc_cot.get("change", 0) or 0
            quad = zc_cot.get("quadrant", zc_cot.get("quadrant_label", "—"))
            nc   = "#22c55e" if chg > 0 else "#ef4444"
            arrow = "▲" if chg > 0 else "▼"
            points.append(f"📊 <b>COT Ngô (ZC):</b> Net <span style='color:{nc}'>{net:+,} HD</span> ({arrow}{abs(chg):,}) — {quad}")

        # Fallback
        if len(points) < 3:
            points.append("🔄 <b>Hint:</b> Nhấn <b>RUN ALL DATA</b> trên sidebar để nạp dữ liệu mới nhất.")

        for i, pt in enumerate(points[:6], 1):
            st.markdown(f"""
            <div style='padding:8px 12px; border-left:3px solid #334155;
                        background:#0f1629; border-radius:4px; margin-bottom:6px;
                        font-size:13px; color:#cbd5e1; line-height:1.5;'>
                <span style='color:#64748b; font-weight:600; margin-right:6px;'>{i}.</span>{pt}
            </div>""", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Hồ sơ 3 mã
        st.markdown("""<div style='font-size:13px; font-weight:700; color:#94a3b8;
            letter-spacing:1px; text-transform:uppercase; margin:16px 0 8px;'>
            📋 Hồ Sơ Từng Mã</div>""", unsafe_allow_html=True)

        # Đọc contracts_meta để lấy mã hợp đồng
        meta_path = DATA_OUTPUT / "contracts_meta.json"
        meta_data = {}
        if meta_path.exists():
            try:
                meta_data = json.loads(meta_path.read_text(encoding="utf-8"))
            except:
                pass

        cols2 = st.columns(2)
        for col, code, name, emoji, color in [
            (cols2[0], "ZC", "Ngô",        "🌽", "#f59e0b"),
            (cols2[1], "ZW", "Lúa Mì",     "🌾", "#60a5fa"),
        ]:
            d       = fund.get(code, {})
            swing   = d.get("swing_trend", "—")
            hp      = d.get("harvest_progress", {})
            harvest = hp.get("latest", "—") if isinstance(hp, dict) else str(hp)
            
            # Mã hợp đồng
            contract_ticker = meta_data.get(code, {}).get("swing", {}).get("ticker", "")
            contract_display = contract_ticker.replace(".CBT", "") if contract_ticker else code
            
            # Determine direction based on trend
            trend_lower = swing.lower()
            is_short = "giảm" in trend_lower or "bán" in trend_lower or "short" in trend_lower
            prefix = "swing_short" if is_short else "swing_long"
            direction_label = "LỆNH BÁN (SHORT)" if is_short else "LỆNH MUA (LONG)"
            direction_color = "#ef4444" if is_short else "#22c55e"
            
            entry   = d.get(f"{prefix}_entry", "—")
            sl      = d.get(f"{prefix}_sl", "—")

            with col:
                st.markdown(f"""
                <div class='card' style='border-top:3px solid {color};'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <div style='font-size:18px; font-weight:800; color:{color};'>{emoji} {code} <span style='font-size:12px; color:#94a3b8; font-weight:normal;'>({contract_display})</span></div>
                        <div style='font-size:11px; font-weight:bold; background-color:rgba(255,255,255,0.05); padding:2px 8px; border-radius:4px; color:{direction_color};'>{direction_label}</div>
                    </div>
                    <div style='font-size:12px; color:#64748b; margin-bottom:8px;'>{name}</div>
                    <div style='font-size:11px; color:#64748b;'>Xu hướng</div>
                    <div style='font-size:12px; color:#e2e8f0; font-weight:600; margin-bottom:6px;'>{swing[:50] if swing else '—'}</div>
                    <div style='font-size:11px; color:#64748b;'>Thu hoạch</div>
                    <div style='font-size:12px; color:#e2e8f0;'>{harvest}</div>
                    <div style='font-size:11px; color:#64748b; margin-top:6px;'>Entry Zone</div>
                    <div style='font-size:12px; color:{color}; font-weight:600;'>{entry}</div>
                    <div style='font-size:11px; color:#64748b;'>Stop Loss</div>
                    <div style='font-size:12px; color:#ef4444;'>{sl}</div>
                </div>""", unsafe_allow_html=True)

    with col_alert:
        render_alert_panel(st)


render_overview()
