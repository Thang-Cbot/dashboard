import streamlit as st
import json
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="CBOT - Lúa Mì Nga", page_icon="🇷🇺", layout="wide")

def load_json(filename):
    filepath = Path(__file__).parent.parent / "Data" / filename
    if filepath.exists():
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

st.title("🇷🇺 THE RUSSIAN FACTOR - LÚA MÌ BIỂN ĐEN")
st.markdown("""
Khu vực hiển thị các số liệu mùa vụ Nga mới nhất (SovEcon/IKAR) và Cấu trúc Điểm hội tụ nguồn cung 2026.
""")

st.markdown("---")
st.subheader("💡 CHIẾN LƯỢC MÙA VỤ 2026 (GOLDEN ZONE)")
st.info("""
**Điểm hội tụ nguồn cung (Cuối Tháng 7 đến Giữa Tháng 8):** 
Khoảnh khắc 3 dòng thác va chạm: Mỹ dọn xong kho lúa đông + Nga xả lũ mạnh nhất ra Biển Đen + lúa xuân Mỹ chớm gặt. Sức ép này ép giá xuống MỨC ĐÁY TUYỆT ĐỐI.

👉 **Đây chính là "Vùng Vàng" để dồn toàn bộ hỏa lực MUA MẠNH (DCA) khi xuất hiện tín hiệu SMC.**
""")

st.markdown("---")
st.subheader("📊 THÔNG SỐ MÙA VỤ TĨNH (CẬP NHẬT THỦ CÔNG)")

data = load_json("manual_russian_metrics.json")
if data and "metrics" in data:
    st.markdown(f"<div style='font-size:13px; color:#64748b; margin-bottom:15px;'>Cập nhật lần cuối: {data.get('updated_at', 'Gần nhất')}</div>", unsafe_allow_html=True)
    
    # Chuyển list dict thành DataFrame để hiển thị bảng
    df = pd.DataFrame(data["metrics"])
    st.table(df)
else:
    st.warning("Chưa tìm thấy file Data/manual_russian_metrics.json.")
