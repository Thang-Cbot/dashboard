import os
import datetime
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.section import WD_ORIENT
from export_to_word import parse_markdown_to_doc

def run_export():
    # Colors
    PRIMARY_COLOR = RGBColor(0x1B, 0x36, 0x5D)  # Premium Dark Blue (#1B365D)
    SECONDARY_COLOR = RGBColor(0x5C, 0x76, 0x8D) # Slate Gray (#5C768D)
    HIGHLIGHT_COLOR = RGBColor(0xD9, 0x77, 0x06) # Warm Amber (#D97706)

    # Text of the report
    wasde_md = """# BÁO CÁO PHÂN TÍCH CHUYÊN ĐỀ: BÁO CÁO WASDE & XU HƯỚNG GIÁ NGÔ, LÚA MÌ

Báo cáo WASDE (Ước tính Cung - Cầu Nông nghiệp Thế giới) tháng 6/2026 sẽ được Bộ Nông nghiệp Hoa Kỳ (USDA) công bố vào **Thứ Năm, ngày 11/06/2026 lúc 12:00 PM giờ Mỹ (tức khoảng 23:00 giờ Việt Nam)**.

Dưới đây là tổng hợp dữ liệu báo cáo WASDE tháng 5/2026 (trước đó), các số liệu dự báo (kỳ vọng thị trường) cho báo cáo ngày mai và nhận định xu hướng giá chi tiết đối với Ngô và Lúa mì.

---

## I. Dữ liệu WASDE Kỳ trước (Tháng 5/2026) vs Kỳ vọng Báo cáo Ngày mai (Tháng 6/2026)

Vì báo cáo tháng 6 diễn ra khi vụ mới (2026/27) chỉ mới bắt đầu gieo trồng và thu hoạch sớm, USDA thường có xu hướng "chờ đợi và quan sát" (wait and see) trước khi có dữ liệu chính xác hơn từ báo cáo Diện tích gieo trồng (Acreage) công bố vào ngày 30/06. Do đó, các nhà phân tích dự báo sẽ có ít điều chỉnh lớn về sản lượng, trọng tâm sẽ là điều chỉnh nhẹ tồn kho cũ chuyển sang kỳ mới.

### 1. Tồn kho cuối kỳ của Mỹ (US Ending Stocks)
*Đơn vị: Tỷ bushels*

| Nông sản | WASDE Kỳ trước (Tháng 5) | Dự báo Báo cáo Ngày mai (Tháng 6) | Đánh giá xu hướng thay đổi |
| :--- | :---: | :---: | :--- |
| **Ngô (Corn)** | **1.957** | **1.947** | Dự kiến thắt chặt hơn (Giảm ~10 triệu bushels) |
| **Lúa mì (Wheat)** | **0.762** (762M) | **0.765** (765M) | Dự kiến tăng nhẹ so với mức dự báo cực thấp của tháng 5 |
| **Đậu tương (Soy)** | **0.310** (310M) | **0.312** (312M) | Dự kiến đi ngang hoặc tăng nhẹ không đáng kể |

### 2. Tồn kho cuối kỳ Thế giới (Global Ending Stocks)
*Đơn vị: Triệu tấn (MMT)*

| Nông sản | WASDE Kỳ trước (Tháng 5) | Dự báo Báo cáo Ngày mai (Tháng 6) | Đánh giá xu hướng thay đổi |
| :--- | :---: | :---: | :--- |
| **Ngô (Corn)** | **277.54** | **278.51** | Tăng nhẹ do nguồn cung Nam Mỹ được điều chỉnh tăng |
| **Lúa mì (Wheat)** | **275.04** | **274.66** | Tiếp tục giảm nhẹ, thắt chặt năm thứ 4 liên tiếp |

---

## II. Nhận định Xu hướng Giá Ngô (CBOT: ZC)

### 1. Các yếu tố tác động chính:
*   **Tiến độ gieo trồng tốt kìm hãm ngắn hạn:** Tiến độ gieo trồng ngô của Mỹ đạt **93%** (vượt trung bình 5 năm là 89%), chất lượng đầu mùa đạt **67% G/E** khá tích cực. Điều này tạo áp lực nguồn cung ngắn hạn, hạn chế đà tăng sốc của giá ngô trong tuần này.
*   **Thời tiết khô hạn đe dọa nảy mầm:** Vùng rìa phía Bắc (Minnesota, Dakotas) đang có thời tiết khô hạn cục bộ làm chậm tiến độ nảy mầm của cây non.
*   **Rủi ro từ Nam Mỹ:** Thị trường đang theo dõi sát sao liệu USDA có hạ dự báo sản lượng ngô vụ 2 (Safrinha) của Brazil do khô hạn tại các bang phía Nam hay không. Ngược lại, sản lượng của Argentina có thể được nâng nhẹ.

### 2. Nhận định xu hướng giá Ngô:
*   **Ngắn hạn (Intraday):** Giá ngô dự kiến sẽ dao động trong biên độ tích lũy từ **420.00 – 438.00 cents**. Do áp lực tiến độ gieo trồng nhanh của Mỹ, giá khó bứt phá mạnh trước giờ báo cáo WASDE.
*   **Trung và dài hạn (Mùa vụ):** Vẫn duy trì xu hướng **Tăng (Bullish)**. Nếu báo cáo ngày mai xác nhận tồn kho niên vụ mới của Mỹ giảm xuống dưới 1.95 tỷ bushels như kỳ vọng, đây sẽ là bệ đỡ vững chắc cho giá. Chiến thuật phù hợp là **Canh mua khi điều chỉnh (Long on dip)** quanh vùng hỗ trợ kỹ thuật hoặc gom dài hạn (DCA) cho các hợp đồng tháng 9/tháng 12 đón đầu chu kỳ thời tiết nắng nóng La Niña vào tháng 7.

---

## III. Nhận định Xu hướng Giá Lúa mì (CBOT: ZW)

### 1. Các yếu tố tác động chính:
*   **Thiệt hại sản lượng nghiêm trọng:** Xếp hạng chất lượng lúa mì đông của Mỹ đang ở mức cực kỳ thấp: Chỉ **26% đạt Good/Excellent** trong khi có tới **44% ở mức Poor/Very Poor** do hạn hán kéo dài ở vành đai Southern Plains (Kansas, Oklahoma).
*   **Thiếu hụt nguồn cung toàn cầu:** Úc dự báo sụt giảm sản lượng lên tới 41% (xuống còn 21.3 triệu tấn), khu vực Biển Đen (Nga/Ukraine) và EU chịu sương giá muộn làm giảm năng suất xuất khẩu.
*   **Áp lực mùa gặt ngắn hạn:** Lúa mì đông Mỹ đã bắt đầu thu hoạch (đạt 5%), tạo ra áp lực bán phòng vệ (hedging pressure) tạm thời từ nông dân, làm kìm hãm đà tăng trong ngắn hạn.

### 2. Nhận định xu hướng giá Lúa mì:
*   **Ngắn hạn (Intraday):** Giá lúa mì đang chịu áp lực kỹ thuật ngắn hạn khi kiểm định lại các vùng hỗ trợ thấp quanh **580.00 – 605.00 cents**. Báo cáo WASDE ngày mai có thể gây ra những biến động 2 chiều mạnh (co giật) khi số liệu sản lượng thực tế từ các bang của Mỹ được cập nhật.
*   **Trung và dài hạn (Mùa vụ):** Xu hướng **Tăng (Bullish) rất mạnh**. Tồn kho cuối kỳ giảm liên tục 4 năm và tình trạng mất mùa diện rộng của lúa mì chất lượng cao (lúa mì đông đỏ cứng) là yếu tố cốt lõi đẩy giá lúa mì lên cao vào nửa cuối năm 2026. Mọi nhịp giảm điều chỉnh do áp lực thu hoạch ngắn hạn là cơ hội tuyệt vời để thực hiện chiến lược **Mua gom tích lũy (Accumulative Long)** cho các hợp đồng kỳ hạn xa (tháng 9 và tháng 12).
"""

    doc = Document()
    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)
        section.orientation = WD_ORIENT.LANDSCAPE
        section.page_width = Inches(11.0)
        section.page_height = Inches(8.5)

    style_normal = doc.styles['Normal']
    font = style_normal.font
    font.name = 'Arial'
    font.size = Pt(11)
    font.color.rgb = RGBColor(0x33, 0x33, 0x33)

    parse_markdown_to_doc(doc, wasde_md, PRIMARY_COLOR, SECONDARY_COLOR, HIGHLIGHT_COLOR)

    out_dir = "Daily Reports"
    os.makedirs(out_dir, exist_ok=True)
    filename = os.path.join(out_dir, "10_06_2026 Nhan dinh WASDE.docx")
    
    try:
        doc.save(filename)
        print(f"SUCCESS: {filename}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    run_export()
