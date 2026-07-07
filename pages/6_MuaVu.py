"""
pages/6_MuaVu.py — Phân tích Mùa Vụ 2026 (ZW & ZC)
====================================================
Tổng hợp chiến lược mùa vụ từ Ma Trận Mùa Vụ 2026 và Dự Phóng Lúa Mì 2026.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Mùa Vụ 2026 — CBOT", page_icon="🌾", layout="wide")

DATA_OUTPUT = Path(__file__).parent.parent / "Data" / "output"

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #0f1629; }
[data-testid="stSidebar"] { background: #0d1424 !important; border-right: 1px solid #1e2d45; min-width: 220px !important; max-width: 220px !important; width: 220px !important; }
[data-testid="stSidebarNav"] { display: none !important; }

.card {
    background: #1a2035;
    border: 1px solid #2a3a5c;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 14px;
}
.section-title {
    font-size: 13px; font-weight: 700; color: #94a3b8;
    letter-spacing: 1px; text-transform: uppercase;
    border-bottom: 1px solid #2a3a5c;
    padding-bottom: 8px; margin-bottom: 12px;
}
.metric-box {
    background: #0f1629;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 8px;
    border-left: 3px solid;
}
.scenario-box {
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
    border: 1px solid;
}
.timeline-item {
    display: flex; gap: 12px; margin-bottom: 10px; align-items: flex-start;
}
.timeline-dot {
    width: 10px; height: 10px; border-radius: 50%;
    margin-top: 4px; flex-shrink: 0;
}
.badge {
    display: inline-block;
    font-size: 11px; font-weight: 700;
    padding: 3px 10px; border-radius: 20px;
    margin-bottom: 6px;
}
</style>""", unsafe_allow_html=True)

# ── Sidebar nav ────────────────────────────────────────────────────────────────
st.sidebar.page_link("app.py",              label="🏠 Trang Chủ")
st.sidebar.page_link("pages/1_Overview.py", label="📊 Tổng Quan")
st.sidebar.page_link("pages/2_Profiles.py", label="📈 Hồ Sơ Từng Mã")
st.sidebar.page_link("pages/3_News.py",     label="📰 Báo Cáo USDA & Tin Tức")
st.sidebar.page_link("pages/4_Weather.py",  label="🌤️ Thời Tiết")
st.sidebar.page_link("pages/5_AgriMap.py",  label="🗺️ Bản Đồ Thời Tiết & ENSO")
st.sidebar.page_link("pages/6_MuaVu.py",   label="🌾 Mùa Vụ 2026")

if st.sidebar.button("🧹 LÀM MỚI TRẠNG THÁI", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_fund():
    p = DATA_OUTPUT / "fundamental_data.json"
    if not p.exists(): return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except: return {}
@st.cache_data(ttl=60)
def load_contracts():
    p = DATA_OUTPUT / "contracts_meta.json"
    if not p.exists(): return {}
    try: return json.loads(p.read_text(encoding="utf-8"))
    except: return {}

@st.cache_data(ttl=60)
def load_status():
    p = DATA_OUTPUT / "data_status.json"
    if not p.exists(): return {}
    try: return json.loads(p.read_text(encoding="utf-8"))
    except: return {}

@st.cache_data(ttl=60)
def load_blacksea():
    p = DATA_OUTPUT / "blacksea_wheat.json"
    if not p.exists(): return {}
    try: return json.loads(p.read_text(encoding="utf-8"))
    except: return {}

fund = load_fund()
meta = load_contracts()
status = load_status()
bs_data = load_blacksea()

usda_up = status.get("modules", {}).get("usda", {}).get("updated_at", "—")
price_up = status.get("modules", {}).get("prices", {}).get("updated_at", "—")
acreage_up = status.get("acreage", {}).get("updated_at", "—")
bs_up = bs_data.get("timestamp", "—")

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='padding: 16px 0 8px;'>
  <div style='font-size:28px; font-weight:800; color:#e2e8f0;'>🌾 Mùa Vụ 2026 — Chiến Lược Dài Hạn</div>
  <div style='font-size:13px; color:#64748b; margin-top:4px;'>
    Tổng hợp từ Ma Trận Mùa Vụ 2026 · Dự Phóng Lúa Mì · Kịch bản El Niño
  </div>
</div>
<hr style='border-color:#2a3a5c; margin-bottom:20px;'>
""", unsafe_allow_html=True)

# ── El Niño Alert Banner ────────────────────────────────────────────────────────
st.markdown("""
<div style='background: linear-gradient(135deg, #7c2d12 0%, #991b1b 100%);
            border: 1px solid #ef4444; border-radius: 12px;
            padding: 14px 20px; margin-bottom: 20px;
            display:flex; align-items:center; gap:14px;'>
  <div style='font-size:32px;'>🌪️</div>
  <div>
    <div style='font-size:14px; font-weight:800; color:#fca5a5;'>CẢNH BÁO: KỊch Bản KHỦNG HOẢNG THỜI TIẾT — EL NIÑO 82%</div>
    <div style='font-size:12px; color:#fecaca; margin-top:3px;'>
      Năm 2026 xác nhận chu kỳ El Niño (82% xác suất). Quy luật giảm giá mùa gặt thông thường SẼ BỊ BẺ GÃY.
      Nhịp giảm sẽ cực nông (rũ bỏ) → Đảo chiều tăng mạnh vào Q4.
      <b>KHÔNG áp dụng tư duy "bán tháo mùa vụ" vào năm 2026.</b>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Main Tabs ──────────────────────────────────────────────────────────────────
tab_zw, tab_zc = st.tabs(["🌾 Lúa Mì (ZW)", "🌽 Ngô (ZC)"])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB LÚA MÌ (ZW)
# ═══════════════════════════════════════════════════════════════════════════════
with tab_zw:
    zw = fund.get("ZW", {})
    zw_meta = meta.get("ZW", {})
    zw_swing_ticker = zw_meta.get("swing", {}).get("ticker", "ZWU26.CBT").replace(".CBT", "")
    zw_dca_ticker   = zw_meta.get("dca", {}).get("ticker", "ZWZ26.CBT").replace(".CBT", "")
    zw_close        = meta.get("ZW", {}).get("liquidity", {}).get("today_close", 601.0)

    col1, col2 = st.columns([1.2, 1], gap="large")

    # ── Cột trái: Thực trạng mùa vụ ──────────────────────────────────────────
    with col1:
        # Block: Trạng thái mùa vụ hiện tại
        st.markdown('<div class="section-title">📋 Trạng Thái Mùa Vụ Hiện Tại (ZW)</div>', unsafe_allow_html=True)

        # Crop quality
        zw_cc   = zw.get("crop_condition", {})
        cc_val  = zw_cc.get("latest", "—") if isinstance(zw_cc, dict) else str(zw_cc)
        # Harvest
        zw_hp   = zw.get("harvest_progress", {})
        hp_val  = zw_hp.get("latest", "—") if isinstance(zw_hp, dict) else str(zw_hp)
        # Planting
        zw_plant = zw.get("us_planting", {})
        plant_val = zw_plant.get("latest", "—") if isinstance(zw_plant, dict) else str(zw_plant)

        # Extract all needed data
        zw_us_stocks  = zw.get("us_ending_stocks", {})
        zw_gl_stocks  = zw.get("global_ending_stocks", {})
        zw_acreage    = zw.get("acreage", {})
        zw_grain_stk  = zw.get("grain_stocks", {})

        def pct_badge(pct):
            """Render badge % change with color."""
            if pct is None: return ""
            clr = "#ef4444" if pct < 0 else "#22c55e"
            arrow = "▼" if pct < 0 else "▲"
            return f"<span style='color:{clr}; font-size:11px; font-weight:700;'>{arrow} {abs(pct):.1f}%</span>"

        zw_us_pct  = zw_us_stocks.get("pct_change", None)
        zw_gl_pct  = zw_gl_stocks.get("pct_change", None)
        zw_ac_pct  = zw_acreage.get("pct_change", None)
        zw_gs_pct  = zw_grain_stk.get("pct_change", None)

        st.markdown(f"""
        <div class='card'>
          <!-- BADGES -->
          <div style='display:flex; gap:10px; flex-wrap:wrap; margin-bottom:14px;'>
            <span class='badge' style='background:#7f1d1d; color:#fca5a5;'>🔴 Lúa Đông: 26% G/E — Cực Xấu</span>
            <span class='badge' style='background:#1c3d5a; color:#93c5fd;'>🌾 Lúa Xuân: 54% G/E — Trung Bình</span>
            <span class='badge' style='background:#1e3a1e; color:#86efac;'>El Niño 82%</span>
            <span class='badge' style='background:#581c87; color:#d8b4fe;'>🇷🇺 Biển Đen: Đáy U-Shape & Bull Trap</span>
          </div>

          <!-- BLOCK I: MUA VU -->
          <div style='font-size:10px; font-weight:700; color:#64748b; letter-spacing:1px; text-transform:uppercase; margin-bottom:8px;'>I. Tình Trạng Mùa Vụ <span style='font-size:9px; color:#94a3b8; font-weight:400; margin-left:6px; font-style:italic; text-transform:none;'>(Cập nhật: {usda_up})</span></div>
          <div style='display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin-bottom:14px;'>
            <div class='metric-box' style='border-color:#ef4444;'>
              <div style='font-size:10px; color:#64748b;'>Chất Lượng (G/E)</div>
              <div style='font-size:14px; font-weight:700; color:#fca5a5;'>{cc_val}</div>
              <div style='font-size:10px; color:#64748b; margin-top:3px;'>Trước: {zw_cc.get('previous','—') if isinstance(zw_cc,dict) else '—'}</div>
            </div>
            <div class='metric-box' style='border-color:#f59e0b;'>
              <div style='font-size:10px; color:#64748b;'>Tiến Độ Thu Hoạch</div>
              <div style='font-size:14px; font-weight:700; color:#fde68a;'>{hp_val}</div>
              <div style='font-size:10px; color:#64748b; margin-top:3px;'>Trước: {zw_hp.get('previous','—') if isinstance(zw_hp,dict) else '—'}</div>
            </div>
            <div class='metric-box' style='border-color:#60a5fa;'>
              <div style='font-size:10px; color:#64748b;'>Tiến Độ Gieo Trồng</div>
              <div style='font-size:14px; font-weight:700; color:#93c5fd;'>{plant_val}</div>
              <div style='font-size:10px; color:#64748b; margin-top:3px;'>Trước: {zw_plant.get('previous','—') if isinstance(zw_plant,dict) else '—'}</div>
            </div>
          </div>

          <!-- BLOCK II: DIEN TICH GIEO TRONG (USDA Acreage 30/06) -->
          <div style='font-size:10px; font-weight:700; color:#64748b; letter-spacing:1px; text-transform:uppercase; margin-bottom:8px;'>II. Diện Tích Gieo Trồng 📊<span style='font-size:9px; color:#f59e0b; font-weight:400; margin-left:6px; text-transform:none;'>BC: {zw_acreage.get('report_date','—')}</span> <span style='font-size:9px; color:#94a3b8; font-weight:400; margin-left:6px; font-style:italic; text-transform:none;'>(Cập nhật: {acreage_up})</span></div>
          <div style='display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin-bottom:14px;'>
            <div class='metric-box' style='border-color:#60a5fa;'>
              <div style='font-size:10px; color:#64748b;'>Hiện Tại (BC mới nhất)</div>
              <div style='font-size:14px; font-weight:700; color:#93c5fd;'>{zw_acreage.get('current','—')}</div>
              <div style='margin-top:4px;'>{pct_badge(zw_ac_pct)} <span style='font-size:10px; color:#64748b;'>vs 2025</span></div>
            </div>
            <div class='metric-box' style='border-color:#475569;'>
              <div style='font-size:10px; color:#64748b;'>Năm Trước (2025)</div>
              <div style='font-size:14px; font-weight:700; color:#94a3b8;'>{zw_acreage.get('previous','—')}</div>
              <div style='font-size:10px; color:#64748b; margin-top:4px;'>{zw_acreage.get('vs_march_est','')}</div>
            </div>
            <div class='metric-box' style='border-color:#f59e0b; background:#1c1800;'>
              <div style='font-size:10px; color:#64748b;'>Chi Tiết</div>
              <div style='font-size:11px; color:#fde68a; line-height:1.6; margin-top:2px;'>
                🔵 Đông: {zw_acreage.get('winter_wheat','—')}<br>
                🟢 Xuân: {zw_acreage.get('spring_wheat','—')}<br>
                🟫 Durum: {zw_acreage.get('durum_wheat','—')}
              </div>
            </div>
          </div>

          <!-- BLOCK III: TON KHO CUOI VU (Ending Stocks WASDE) -->
          <div style='font-size:10px; font-weight:700; color:#64748b; letter-spacing:1px; text-transform:uppercase; margin-bottom:8px;'>III. Tồn Kho Cuối Vụ WASDE <span style='font-size:9px; color:#94a3b8; font-weight:400; margin-left:6px; font-style:italic; text-transform:none;'>(Cập nhật: {usda_up})</span></div>

          <div style='font-size:11px; color:#34d399; font-weight:600; margin-bottom:5px;'>🇺🇸 Tồn Kho Mỹ (US Ending Stocks)</div>
          <div style='display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin-bottom:10px;'>
            <div class='metric-box' style='border-color:#10b981;'>
              <div style='font-size:10px; color:#64748b;'>Hiện Tại (WASDE)</div>
              <div style='font-size:14px; font-weight:700; color:#34d399;'>{zw_us_stocks.get('current','—')}</div>
              <div style='margin-top:4px;'>{pct_badge(zw_us_pct)} <span style='font-size:10px; color:#64748b;'>vs niên vụ trước</span></div>
            </div>
            <div class='metric-box' style='border-color:#0d9488;'>
              <div style='font-size:10px; color:#64748b;'>Dự Báo BC Tiếp</div>
              <div style='font-size:14px; font-weight:700; color:#5eead4;'>{zw_us_stocks.get('forecast_next', zw_us_stocks.get('forecast','—'))}</div>
            </div>
            <div class='metric-box' style='border-color:#475569;'>
              <div style='font-size:10px; color:#64748b;'>Niên Vụ Trước</div>
              <div style='font-size:14px; font-weight:700; color:#94a3b8;'>{zw_us_stocks.get('previous','—')}</div>
            </div>
          </div>

          <div style='font-size:11px; color:#34d399; font-weight:600; margin-bottom:5px;'>🌎 Tồn Kho Thế Giới (Global Stocks)</div>
          <div style='display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin-bottom:14px;'>
            <div class='metric-box' style='border-color:#10b981;'>
              <div style='font-size:10px; color:#64748b;'>Hiện Tại</div>
              <div style='font-size:14px; font-weight:700; color:#34d399;'>{zw_gl_stocks.get('current','—')}</div>
              <div style='margin-top:4px;'>{pct_badge(zw_gl_pct)} <span style='font-size:10px; color:#64748b;'>vs niên vụ trước</span></div>
            </div>
            <div class='metric-box' style='border-color:#0d9488;'>
              <div style='font-size:10px; color:#64748b;'>Dự Báo Tiếp</div>
              <div style='font-size:14px; font-weight:700; color:#5eead4;'>{zw_gl_stocks.get('forecast_next', zw_gl_stocks.get('forecast','—'))}</div>
            </div>
            <div class='metric-box' style='border-color:#475569;'>
              <div style='font-size:10px; color:#64748b;'>Niên Vụ Trước</div>
              <div style='font-size:14px; font-weight:700; color:#94a3b8;'>{zw_gl_stocks.get('previous','—')}</div>
            </div>
          </div>

          <!-- BLOCK IV: GRAIN STOCKS (vat ly) -->
          <div style='font-size:10px; font-weight:700; color:#64748b; letter-spacing:1px; text-transform:uppercase; margin-bottom:8px;'>IV. Tồn Kho Vật Lý (Grain Stocks 01/06) 📊<span style='font-size:9px; color:#f59e0b; font-weight:400; margin-left:6px; text-transform:none;'>BC: {zw_grain_stk.get('report_date','—')}</span> <span style='font-size:9px; color:#94a3b8; font-weight:400; margin-left:6px; font-style:italic; text-transform:none;'>(Cập nhật: {acreage_up})</span></div>
          <div style='display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin-bottom:14px;'>
            <div class='metric-box' style='border-color:#10b981;'>
              <div style='font-size:10px; color:#64748b;'>Hiện Tại</div>
              <div style='font-size:14px; font-weight:700; color:#34d399;'>{zw_grain_stk.get('current','—')}</div>
              <div style='margin-top:4px;'>{pct_badge(zw_gs_pct)} <span style='font-size:10px; color:#64748b;'>vs cùng kỳ 2025</span></div>
            </div>
            <div class='metric-box' style='border-color:#475569;'>
              <div style='font-size:10px; color:#64748b;'>Cùng Kỳ Năm Trước</div>
              <div style='font-size:14px; font-weight:700; color:#94a3b8;'>{zw_grain_stk.get('previous','—')}</div>
            </div>
            <div class='metric-box' style='border-color:#f59e0b; background:#1c1800;'>
              <div style='font-size:10px; color:#64748b;'>Nhận Định</div>
              <div style='font-size:11px; color:#fde68a; line-height:1.6; margin-top:2px;'>{zw_grain_stk.get('note','—')}</div>
            </div>
          </div>

          <!-- BLOCK V: GIA + LICH BC -->
          <div style='font-size:10px; font-weight:700; color:#64748b; letter-spacing:1px; text-transform:uppercase; margin-bottom:8px;'>V. Giá & Lịch Báo Cáo <span style='font-size:9px; color:#94a3b8; font-weight:400; margin-left:6px; font-style:italic; text-transform:none;'>(Cập nhật: {price_up})</span></div>
          <div style='display:grid; grid-template-columns:1fr 1fr; gap:8px;'>
            <div class='metric-box' style='border-color:#60a5fa;'>
              <div style='font-size:10px; color:#64748b;'>Giá Tham Chiếu ({zw_swing_ticker})</div>
              <div style='font-size:14px; font-weight:700; color:#93c5fd;'>{zw_close:.2f} cents</div>
            </div>
            <div class='metric-box' style='border-color:#6366f1;'>
              <div style='font-size:10px; color:#64748b;'>Báo Cáo Tiếp Theo (WASDE)</div>
              <div style='font-size:13px; font-weight:700; color:#a5b4fc;'>{zw_us_stocks.get('next_date','—')}</div>
            </div>
          </div>
          
          <!-- BLOCK RUSSIAN WHEAT -->
          <div style='font-size:10px; font-weight:700; color:#64748b; letter-spacing:1px; text-transform:uppercase; margin-bottom:8px; margin-top:14px;'>VI. Sự Thống Trị Của Nga (Biển Đen) 🇷🇺 <span style='font-size:9px; color:#94a3b8; font-weight:400; margin-left:6px; font-style:italic; text-transform:none;'>(Cập nhật: {bs_up})</span></div>
          <div class='card' style='border-color:#3b0764; background:#1e1b4b; padding:12px; margin-bottom:14px;'>
            <div style='display:flex; gap:8px; margin-bottom:8px;'>
              <div class='metric-box' style='flex:1; border-color:#8b5cf6; background:#2e1065; padding:8px;'>
                <div style='font-size:10px; color:#c4b5fd;'>Tiến Độ Thu Hoạch</div>
                <div style='font-size:14px; font-weight:700; color:#ddd6fe;'>Đạt 3%</div>
                <div style='font-size:10px; color:#a78bfa; margin-top:3px;'>Trễ 1-2 tuần (Khủng hoảng nhiên liệu)</div>
              </div>
              <div class='metric-box' style='flex:1; border-color:#d946ef; background:#4a044e; padding:8px;'>
                <div style='font-size:10px; color:#f5d0fe;'>Sản Lượng Dự Báo</div>
                <div style='font-size:14px; font-weight:700; color:#fdf4ff;'>88.9 Tr. Tấn</div>
                <div style='font-size:10px; color:#e879f9; margin-top:3px;'>(SovEcon) Diện tích gieo: 25.8m ha</div>
              </div>
            </div>
            <div style='font-size:11px; color:#c4b5fd; line-height:1.6;'>
              📌 <b>Áp lực Mùa gặt (Harvest Pressure):</b> Bất chấp Mỹ đang hạn hán, lúa Nga xả hàng ra Biển Đen sẽ ép giá lúa mì Mỹ phải "Price Match" để cạnh tranh xuất khẩu. Tình trạng thiếu hụt dầu diesel đang làm chậm dòng cung ứng, tạo rủi ro suy giảm chất lượng nếu lúa ngâm quá lâu trên đồng.
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Phân tích chu kỳ 10 năm
        st.markdown('<div class="section-title">📊 Phân Tích Chu Kỳ 10 Năm (Cuối T6 → Cuối T8)</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class='card'>
          <div style='margin-bottom:12px;'>
            <div class='scenario-box' style='background:#0f2a1a; border-color:#22c55e;'>
              <div style='font-size:12px; font-weight:700; color:#86efac;'>🟢 Kịch Bản NĂM 2026 — KHỦNG HOẢNG (El Niño / 2018 & 2020)</div>
              <div style='font-size:12px; color:#d1fae5; margin-top:6px; line-height:1.7;'>
                • Diện tích Lúa xuân thấp kỷ lục 56 năm (9.39m) + Nắng nóng thiêu đốt<br>
                • Đầu-Giữa T7: Lúa đông Mỹ gặt (48%-60%) tạo <b>Đáy 1</b><br>
                • Cuối T7: Lúa Nga trễ hẹn đổ ra bến cảng kéo dài vùng đáy <b>(Đáy U-Shape)</b><br>
                • T8: Rũ bỏ cuối cùng (Gặt lúa xuân) tạo <b>Đáy 2 (555-585 cents ZWU26)</b><br>
                • Q4: Thiếu hụt vật chất đẩy giá bùng nổ, nhưng bị "Giảm xóc" bởi mưa Thu gieo vụ mới.
              </div>
            </div>
            <div class='scenario-box' style='background:#1c1a0f; border-color:#64748b;'>
              <div style='font-size:12px; font-weight:700; color:#94a3b8;'>⚪ So Sánh: Kịch Bản DƯ THỪA (2016,2017,2019,2024,2025)</div>
              <div style='font-size:12px; color:#94a3b8; margin-top:6px;'>
                Khi Nga/Mỹ trúng mùa → Giá rơi -7% đến -20% vào tháng 8. <b>KHÔNG áp dụng cho 2026.</b>
              </div>
            </div>
          </div>
          <div style='font-size:12px; color:#94a3b8; background:#0f1629; padding:10px; border-radius:8px;'>
            📌 <b>Năm 2026 tương tự 2020:</b> Đáy tháng 4 → Đáy mùa vụ 1 (22/06) → Đáy mùa vụ 2 (T8) → Sau đó tăng dần
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Cột phải: Chiến lược thực chiến ──────────────────────────────────────
    with col2:
        st.markdown('<div class="section-title">🎯 Lịch Trình Chiến Lược (Timeline)</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class='card'>
          <!-- T7 -->
          <div class='timeline-item'>
            <div class='timeline-dot' style='background:#f59e0b;'></div>
            <div>
              <div style='font-size:12px; font-weight:700; color:#fde68a;'>📅 Đầu đến Giữa Tháng 7 — Rủi Ro Bull Trap</div>
              <div style='font-size:11px; color:#94a3b8; line-height:1.6;'>
                <b>Đầu T7:</b> Mỹ gặt lúa đông kết hợp với Nga mới chớm đưa hàng ra Biển Đen.<br>
                <b>Tâm lý:</b> Trader lao vào mua do hạn hán của Mỹ sẽ dính bẫy (Bull Trap) vì giá CBOT bị Nga đè bẹp.<br>
                ❌ Nghiêm cấm All-in. Vùng 570-585 là rẻ nhưng chỉ giải ngân 20-30% để dò đường.
              </div>
            </div>
          </div>
          <!-- T8 -->
          <div class='timeline-item'>
            <div class='timeline-dot' style='background:#ef4444;'></div>
            <div>
              <div style='font-size:12px; font-weight:700; color:#fca5a5;'>📅 Cuối T7 & Đầu T8 — Điểm Mua Vàng (Golden Zone)</div>
              <div style='font-size:11px; color:#94a3b8; line-height:1.6;'>
                Hội tụ 3 dòng thác nguồn cung: Mỹ dọn xong kho lúa đông + Nga xả lũ mạnh nhất + lúa xuân Mỹ chớm gặt.<br>
                <b style='color:#ef4444;'>Áp lực cực đại = ĐÁY TUYỆT ĐỐI CỦA MÙA VỤ</b><br>
                ✅ Tín hiệu MSS trên H4/D1 vùng 570-585. <b>DỒN HỎA LỰC MUA MẠNH.</b>
              </div>
            </div>
          </div>
          <!-- Q4 -->
          <div class='timeline-item'>
            <div class='timeline-dot' style='background:#22c55e;'></div>
            <div>
              <div style='font-size:12px; font-weight:700; color:#86efac;'>📅 Q4 (Tháng 10→12) — Siêu Sóng Tăng</div>
              <div style='font-size:11px; color:#94a3b8; line-height:1.6;'>
                El Niño tàn phá Úc & Argentina → Siêu bão thiếu hụt.<br>
                Mưa mùa thu Mỹ (T9-T11) làm nắp đập (Cap) ngăn ngáo giá.<br>
                🎯 Target: Bùng nổ vùng <b style='color:#22c55e;'>680–760 cents</b>
              </div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Vùng giá chiến lược
        st.markdown('<div class="section-title">💎 Vùng Giá Chiến Lược (DCA Dài Hạn)</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class='card' style='border-color:#22c55e;'>
          <div style='text-align:center; margin-bottom:12px;'>
            <div style='font-size:11px; color:#64748b;'>MÃ HỢP ĐỒNG ÁP DỤNG</div>
            <div style='font-size:22px; font-weight:800; color:#86efac;'>{zw_dca_ticker}</div>
            <div style='font-size:11px; color:#64748b;'>(Hợp đồng Tháng 12 — Tránh phí đáo hạn)</div>
          </div>
          <div class='metric-box' style='border-color:#22c55e; text-align:center;'>
            <div style='font-size:11px; color:#64748b;'>🎯 VÙNG GOM GOLDEN ZONE</div>
            <div style='font-size:24px; font-weight:800; color:#22c55e;'>570 – 585 cents</div>
            <div style='font-size:11px; color:#86efac;'>Tương đương 555–565 cents {zw_swing_ticker} + Contango 15-25c</div>
          </div>
          <div style='font-size:11px; color:#94a3b8; line-height:1.7; margin-top:10px;'>
            📌 <b>Lý do:</b> Spread Contango giữa ZWZ26 và ZWU26 thường 15–25 cents.<br>
            Gom trên ZWZ26 bảo vệ tránh phí lưu kho (roll cost) và giữ vị thế thoải mái đến Q4.
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Cấu trúc đáy W
        st.markdown('<div class="section-title">📐 Cấu Trúc Đáy Chữ W (Double Bottom)</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class='card'>
          <div style='font-size:11px; color:#94a3b8; line-height:1.8;'>
            <b style='color:#60a5fa;'>Đáy 1 (Hiện tại, Cuối T6):</b> Lúa đông gặt 40% → Risk Premium vẫn còn. Giá neo ~{zw_close:.0f} cents<br>
            <b style='color:#f59e0b;'>Pullback T7:</b> Bull Trap Weather Rally → 620–640 cents<br>
            <b style='color:#ef4444;'>Đáy 2 (Cuối T7 - Đầu T8):</b> Điểm hội tụ nguồn cung (Mỹ lúa đông + Nga xả + lúa xuân) → <b>555–585 cents (Bottom Tuyệt Đối)</b><br>
            <b style='color:#22c55e;'>Bùng nổ Q4:</b> El Niño Nam Bán Cầu → Thiếu cung → 650–700 cents+
          </div>
          <div style='text-align:center; margin-top:12px; font-size:28px; letter-spacing:4px;'>
            📉&nbsp;&nbsp;<span style='color:#f59e0b;'>↗</span>&nbsp;&nbsp;<span style='color:#ef4444;'>↘↘</span>&nbsp;&nbsp;<span style='color:#22c55e;'>↗↗↗</span>
          </div>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB NGÔ (ZC)
# ═══════════════════════════════════════════════════════════════════════════════
with tab_zc:
    zc = fund.get("ZC", {})
    zc_meta = meta.get("ZC", {})
    zc_swing_ticker = zc_meta.get("swing", {}).get("ticker", "ZCU26.CBT").replace(".CBT", "")
    zc_dca_ticker   = zc_meta.get("dca", {}).get("ticker", "ZCZ26.CBT").replace(".CBT", "")
    zc_close        = meta.get("ZC", {}).get("liquidity", {}).get("today_close", 423.75)

    col1, col2 = st.columns([1.2, 1], gap="large")

    with col1:
        st.markdown('<div class="section-title">📋 Trạng Thái Mùa Vụ Hiện Tại (ZC)</div>', unsafe_allow_html=True)

        zc_cc   = zc.get("crop_condition", {})
        cc_val  = zc_cc.get("latest", "—") if isinstance(zc_cc, dict) else str(zc_cc)
        zc_hp   = zc.get("harvest_progress", {})
        hp_val  = zc_hp.get("latest", "—") if isinstance(zc_hp, dict) else str(zc_hp)
        hp_logic = zc_hp.get("logic", "—") if isinstance(zc_hp, dict) else ""
        zc_plant = zc.get("us_planting", {})
        plant_val = zc_plant.get("latest", "—") if isinstance(zc_plant, dict) else str(zc_plant)

        # Extract all needed data
        zc_us_stocks  = zc.get("us_ending_stocks", {})
        zc_gl_stocks  = zc.get("global_ending_stocks", {})
        zc_acreage    = zc.get("acreage", {})
        zc_grain_stk  = zc.get("grain_stocks", {})

        def pct_badge_zc(pct):
            if pct is None: return ""
            clr = "#ef4444" if pct < 0 else "#22c55e"
            arrow = "▼" if pct < 0 else "▲"
            return f"<span style='color:{clr}; font-size:11px; font-weight:700;'>{arrow} {abs(pct):.1f}%</span>"

        zc_us_pct = zc_us_stocks.get("pct_change", None)
        zc_gl_pct = zc_gl_stocks.get("pct_change", None)
        zc_ac_pct = zc_acreage.get("pct_change", None)
        zc_gs_pct = zc_grain_stk.get("pct_change", None)

        st.markdown(f"""
        <div class='card'>
          <!-- BADGES -->
          <div style='display:flex; gap:10px; flex-wrap:wrap; margin-bottom:14px;'>
            <span class='badge' style='background:#1e3a1e; color:#86efac;'>🟢 Chất lượng tốt</span>
            <span class='badge' style='background:#1c3d5a; color:#93c5fd;'>97% đã gieo trồng</span>
            <span class='badge' style='background:#2d1b00; color:#fcd34d;'>Argentina 66% thu hoạch</span>
          </div>

          <!-- BLOCK 1: MUA VU (3 cols) -->
          <div style='font-size:10px; font-weight:700; color:#64748b; letter-spacing:1px; text-transform:uppercase; margin-bottom:8px;'>I. Tình Trạng Mùa Vụ <span style='font-size:9px; color:#94a3b8; font-weight:400; margin-left:6px; font-style:italic; text-transform:none;'>(Cập nhật: {usda_up})</span></div>
          <div style='display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin-bottom:14px;'>
            <div class='metric-box' style='border-color:#22c55e;'>
              <div style='font-size:10px; color:#64748b;'>Chất Lượng (G/E)</div>
              <div style='font-size:14px; font-weight:700; color:#86efac;'>{cc_val}</div>
              <div style='font-size:10px; color:#64748b; margin-top:3px;'>Trước: {zc_cc.get('previous','—') if isinstance(zc_cc,dict) else '—'}</div>
            </div>
            <div class='metric-box' style='border-color:#f59e0b;'>
              <div style='font-size:10px; color:#64748b;'>Tiến Độ Thu Hoạch</div>
              <div style='font-size:14px; font-weight:700; color:#fde68a;'>{hp_val}</div>
              <div style='font-size:10px; color:#64748b; margin-top:3px;'>Trước: {zc_hp.get('previous','—') if isinstance(zc_hp,dict) else '—'}</div>
            </div>
            <div class='metric-box' style='border-color:#60a5fa;'>
              <div style='font-size:10px; color:#64748b;'>Tiến Độ Gieo Trồng Mỹ</div>
              <div style='font-size:14px; font-weight:700; color:#93c5fd;'>{plant_val}</div>
              <div style='font-size:10px; color:#64748b; margin-top:3px;'>Trước: {zc_plant.get('previous','—') if isinstance(zc_plant,dict) else '—'}</div>
            </div>
          </div>

          <!-- BLOCK II: DIEN TICH GIEO TRONG (USDA Acreage 30/06) -->
          <div style='font-size:10px; font-weight:700; color:#64748b; letter-spacing:1px; text-transform:uppercase; margin-bottom:8px;'>II. Diện Tích Gieo Trồng 📊<span style='font-size:9px; color:#f59e0b; font-weight:400; margin-left:6px; text-transform:none;'>BC: {zc_acreage.get('report_date','—')}</span> <span style='font-size:9px; color:#94a3b8; font-weight:400; margin-left:6px; font-style:italic; text-transform:none;'>(Cập nhật: {acreage_up})</span></div>
          <div style='display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin-bottom:14px;'>
            <div class='metric-box' style='border-color:#f59e0b;'>
              <div style='font-size:10px; color:#64748b;'>Hiện Tại (BC mới nhất)</div>
              <div style='font-size:14px; font-weight:700; color:#fde68a;'>{zc_acreage.get('current','—')}</div>
              <div style='margin-top:4px;'>{pct_badge_zc(zc_ac_pct)} <span style='font-size:10px; color:#64748b;'>vs 2025</span></div>
            </div>
            <div class='metric-box' style='border-color:#475569;'>
              <div style='font-size:10px; color:#64748b;'>Năm Trước (2025)</div>
              <div style='font-size:14px; font-weight:700; color:#94a3b8;'>{zc_acreage.get('previous','—')}</div>
              <div style='font-size:10px; color:#64748b; margin-top:4px;'>{zc_acreage.get('vs_march_est','')}</div>
            </div>
            <div class='metric-box' style='border-color:#22c55e; background:#0f1e0f;'>
              <div style='font-size:10px; color:#64748b;'>Nhận Định</div>
              <div style='font-size:11px; color:#86efac; line-height:1.6; margin-top:2px;'>{zc_acreage.get('note','—')}</div>
            </div>
          </div>

          <!-- BLOCK III: TON KHO CUOI VU (Ending Stocks WASDE) -->
          <div style='font-size:10px; font-weight:700; color:#64748b; letter-spacing:1px; text-transform:uppercase; margin-bottom:8px;'>III. Tồn Kho Cuối Vụ WASDE <span style='font-size:9px; color:#94a3b8; font-weight:400; margin-left:6px; font-style:italic; text-transform:none;'>(Cập nhật: {usda_up})</span></div>

          <div style='font-size:11px; color:#34d399; font-weight:600; margin-bottom:5px;'>🇺🇸 Tồn Kho Mỹ</div>
          <div style='display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin-bottom:10px;'>
            <div class='metric-box' style='border-color:#10b981;'>
              <div style='font-size:10px; color:#64748b;'>Hiện Tại (WASDE)</div>
              <div style='font-size:14px; font-weight:700; color:#34d399;'>{zc_us_stocks.get('current','—')}</div>
              <div style='margin-top:4px;'>{pct_badge_zc(zc_us_pct)} <span style='font-size:10px; color:#64748b;'>vs niên vụ trước</span></div>
            </div>
            <div class='metric-box' style='border-color:#0d9488;'>
              <div style='font-size:10px; color:#64748b;'>Dự Báo BC Tiếp</div>
              <div style='font-size:14px; font-weight:700; color:#5eead4;'>{zc_us_stocks.get('forecast_next', zc_us_stocks.get('forecast','—'))}</div>
            </div>
            <div class='metric-box' style='border-color:#475569;'>
              <div style='font-size:10px; color:#64748b;'>Niên Vụ Trước</div>
              <div style='font-size:14px; font-weight:700; color:#94a3b8;'>{zc_us_stocks.get('previous','—')}</div>
            </div>
          </div>

          <div style='font-size:11px; color:#34d399; font-weight:600; margin-bottom:5px;'>🌎 Tồn Kho Thế Giới</div>
          <div style='display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin-bottom:14px;'>
            <div class='metric-box' style='border-color:#10b981;'>
              <div style='font-size:10px; color:#64748b;'>Hiện Tại</div>
              <div style='font-size:14px; font-weight:700; color:#34d399;'>{zc_gl_stocks.get('current','—')}</div>
              <div style='margin-top:4px;'>{pct_badge_zc(zc_gl_pct)} <span style='font-size:10px; color:#64748b;'>vs niên vụ trước</span></div>
            </div>
            <div class='metric-box' style='border-color:#0d9488;'>
              <div style='font-size:10px; color:#64748b;'>Dự Báo Tiếp</div>
              <div style='font-size:14px; font-weight:700; color:#5eead4;'>{zc_gl_stocks.get('forecast_next', zc_gl_stocks.get('forecast','—'))}</div>
            </div>
            <div class='metric-box' style='border-color:#475569;'>
              <div style='font-size:10px; color:#64748b;'>Niên Vụ Trước</div>
              <div style='font-size:14px; font-weight:700; color:#94a3b8;'>{zc_gl_stocks.get('previous','—')}</div>
            </div>
          </div>

          <!-- BLOCK IV: GRAIN STOCKS (vat ly) -->
          <div style='font-size:10px; font-weight:700; color:#64748b; letter-spacing:1px; text-transform:uppercase; margin-bottom:8px;'>IV. Tồn Kho Vật Lý (Grain Stocks 01/06) 📊<span style='font-size:9px; color:#f59e0b; font-weight:400; margin-left:6px; text-transform:none;'>BC: {zc_grain_stk.get('report_date','—')}</span> <span style='font-size:9px; color:#94a3b8; font-weight:400; margin-left:6px; font-style:italic; text-transform:none;'>(Cập nhật: {acreage_up})</span></div>
          <div style='display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin-bottom:14px;'>
            <div class='metric-box' style='border-color:#10b981;'>
              <div style='font-size:10px; color:#64748b;'>Hiện Tại</div>
              <div style='font-size:14px; font-weight:700; color:#34d399;'>{zc_grain_stk.get('current','—')}</div>
              <div style='margin-top:4px;'>{pct_badge_zc(zc_gs_pct)} <span style='font-size:10px; color:#64748b;'>vs cùng kỳ 2025</span></div>
            </div>
            <div class='metric-box' style='border-color:#475569;'>
              <div style='font-size:10px; color:#64748b;'>Cùng Kỳ Năm Trước</div>
              <div style='font-size:14px; font-weight:700; color:#94a3b8;'>{zc_grain_stk.get('previous','—')}</div>
            </div>
            <div class='metric-box' style='border-color:#22c55e; background:#0f1e0f;'>
              <div style='font-size:10px; color:#64748b;'>Nhận Định</div>
              <div style='font-size:11px; color:#86efac; line-height:1.6; margin-top:2px;'>{zc_grain_stk.get('note','—')}</div>
            </div>
          </div>

          <!-- BLOCK V: GIA + LICH BC -->
          <div style='font-size:10px; font-weight:700; color:#64748b; letter-spacing:1px; text-transform:uppercase; margin-bottom:8px;'>V. Giá & Lịch Báo Cáo <span style='font-size:9px; color:#94a3b8; font-weight:400; margin-left:6px; font-style:italic; text-transform:none;'>(Cập nhật: {price_up})</span></div>
          <div style='display:grid; grid-template-columns:1fr 1fr; gap:8px;'>
            <div class='metric-box' style='border-color:#f59e0b;'>
              <div style='font-size:10px; color:#64748b;'>Giá Tham Chiếu ({zc_swing_ticker})</div>
              <div style='font-size:14px; font-weight:700; color:#fde68a;'>{zc_close:.2f} cents</div>
            </div>
            <div class='metric-box' style='border-color:#6366f1;'>
              <div style='font-size:10px; color:#64748b;'>Báo Cáo Tiếp Theo (WASDE)</div>
              <div style='font-size:13px; font-weight:700; color:#a5b4fc;'>{zc_us_stocks.get('next_date','—')}</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)


        # Nhận định thị trường
        st.markdown('<div class="section-title">📊 Phân Tích Mùa Vụ Ngô 2026</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class='card'>
          <div class='scenario-box' style='background:#0f2a1a; border-color:#22c55e; margin-bottom:10px;'>
            <div style='font-size:12px; font-weight:700; color:#86efac;'>✅ Điểm Mạnh: Chất Lượng Vụ Mỹ Tốt</div>
            <div style='font-size:12px; color:#d1fae5; margin-top:6px; line-height:1.7;'>
              • Chất lượng G/E đạt {cc_val} — cao hơn trung bình 5 năm<br>
              • 97% đã nảy mầm — tiến độ nhanh hơn trung bình<br>
              • Argentina đang thu hoạch mạnh 66% (2/3 tiến độ) → áp lực cung tạm thời
            </div>
          </div>
          <div class='scenario-box' style='background:#2d1800; border-color:#f59e0b; margin-bottom:10px;'>
            <div style='font-size:12px; font-weight:700; color:#fcd34d;'>⚠️ Rủi ro: Tháng 7 — Giai Đoạn Pollination</div>
            <div style='font-size:12px; color:#fde68a; margin-top:6px; line-height:1.7;'>
              • Diện tích giảm 3% nhưng Tồn kho nội địa tăng mạnh 14% (WASDE 30/06).<br>
              • El Niño mang nắng nóng đe dọa trực tiếp Midwest (Thụ phấn).<br>
              • Mưa ngập lụt đầu vụ + nắng nóng giữa vụ đè nặng năng suất thực tế.
            </div>
          </div>
          <div class='scenario-box' style='background:#0f1a2d; border-color:#60a5fa;'>
            <div style='font-size:12px; font-weight:700; color:#93c5fd;'>📉 Chu Kỳ Mùa Vụ: Áp Lực Giảm Tháng 8-9</div>
            <div style='font-size:12px; color:#bfdbfe; margin-top:6px; line-height:1.7;'>
              • Ngô Mỹ thường tạo đáy sớm đầu tháng 9 (khi tiến độ gặt ~5-10%)<br>
              • Giá đang giữ vững vùng 440-450 cents bất chấp áp lực → Xác nhận đáy chu kỳ mùa vụ
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Timeline
        st.markdown('<div class="section-title">🎯 Lịch Trình Chiến Lược (ZC)</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class='card'>
          <div class='timeline-item'>
            <div class='timeline-dot' style='background:#ef4444;'></div>
            <div>
              <div style='font-size:12px; font-weight:700; color:#fca5a5;'>📅 Tháng 7 — Nguy Hiểm (Pollination)</div>
              <div style='font-size:11px; color:#94a3b8; line-height:1.6;'>
                Theo dõi nhiệt độ từng ngày vùng Iowa, Illinois.<br>
                Nếu Heatwave → Giá bật tăng mạnh (Weather Rally thật, không phải Trap).
              </div>
            </div>
          </div>
          <div class='timeline-item'>
            <div class='timeline-dot' style='background:#f59e0b;'></div>
            <div>
              <div style='font-size:12px; font-weight:700; color:#fde68a;'>📅 Tháng 8-9 — Áp Lực Thu Hoạch</div>
              <div style='font-size:11px; color:#94a3b8; line-height:1.6;'>
                Argentina + Mỹ thu hoạch đồng loạt → Đáy mùa vụ.<br>
                Đây là cơ hội gom DCA tốt nhất nếu không có Heatwave T7.
              </div>
            </div>
          </div>
          <div class='timeline-item'>
            <div class='timeline-dot' style='background:#22c55e;'></div>
            <div>
              <div style='font-size:12px; font-weight:700; color:#86efac;'>📅 Q4 — Sideways Up (Tăng Dần)</div>
              <div style='font-size:11px; color:#94a3b8; line-height:1.6;'>
                Tồn kho toàn cầu ở mức thấp nhất 12 năm.<br>
                Nhu cầu Trung Quốc & Ethanol duy trì nền tảng giá tốt.
              </div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Vùng giá DCA
        st.markdown('<div class="section-title">💎 Vùng Giá Chiến Lược (DCA Dài Hạn)</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class='card' style='border-color:#f59e0b;'>
          <div style='text-align:center; margin-bottom:12px;'>
            <div style='font-size:11px; color:#64748b;'>MÃ HỢP ĐỒNG ÁP DỤNG</div>
            <div style='font-size:22px; font-weight:800; color:#fde68a;'>{zc_dca_ticker}</div>
            <div style='font-size:11px; color:#64748b;'>(Hợp đồng Tháng 12 — Niên vụ 2026/27)</div>
          </div>
          <div class='metric-box' style='border-color:#f59e0b; text-align:center;'>
            <div style='font-size:11px; color:#64748b;'>🎯 VÙNG GOM DCA TỐI ƯU</div>
            <div style='font-size:24px; font-weight:800; color:#f59e0b;'>436 – 445 cents</div>
            <div style='font-size:11px; color:#fde68a;'>Đáy thu hoạch kỳ vọng, Tháng 8 – đầu T9</div>
          </div>
          <div class='metric-box' style='border-color:#22c55e; text-align:center;'>
            <div style='font-size:11px; color:#64748b;'>📈 XU HƯỚNG CUỐI NĂM</div>
            <div style='font-size:18px; font-weight:700; color:#86efac;'>Sideways Up (Tăng Dần)</div>
            <div style='font-size:11px; color:#86efac;'>Tồn kho thấp 12 năm là nền tảng bền vững</div>
          </div>
          <div style='font-size:11px; color:#94a3b8; line-height:1.7; margin-top:10px;'>
            📌 <b>Điều kiện Entry:</b> Đợi pullback về vùng 436–445 cents + Xác nhận cấu trúc H1 (MSS hoặc FVG) trên khung M15.
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Rủi ro chính
        st.markdown('<div class="section-title">⚠️ Rủi Ro Chính Cần Theo Dõi</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class='card'>
          <div style='font-size:12px; color:#e2e8f0; line-height:2;'>
            🌡️ <b>Nhiệt độ Tháng 7</b> — Pollination Window Iowa/Illinois<br>
            🚢 <b>Xuất Khẩu Tuần</b> — Cạnh tranh từ Brazil/Argentina<br>
            📋 <b>WASDE (10/07)</b> — Tồn kho, diện tích điều chỉnh<br>
            💧 <b>ENSO/La Niña</b> — Tác động mùa vụ Nam Mỹ (Brazil)
          </div>
        </div>
        """, unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center; padding:20px; color:#374151; font-size:11px; margin-top:20px;'>
  📌 Dữ liệu tổng hợp từ Ma Trận Mùa Vụ 2026 · Dự Phóng Chu Kỳ Lúa Mì · fundamental_data.json<br>
  Cập nhật tự động theo dữ liệu thực tế từ USDA và Crop Progress hàng tuần.
</div>
""", unsafe_allow_html=True)
