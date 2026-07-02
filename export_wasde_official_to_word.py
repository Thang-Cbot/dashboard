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
    wasde_md = """# BÁO CÁO PHÂN TÍCH CHUYÊN ĐỀ CHÍNH THỨC: KẾT QUẢ BÁO CÁO WASDE THÁNG 06/2026
*Được thực hiện ngay sau khi Bộ Nông nghiệp Hoa Kỳ (USDA) công bố báo cáo lúc 23:00 ngày 11/06/2026 (giờ Việt Nam)*

---

## I. Tổng hợp Số liệu WASDE Thực tế (Kỳ này) vs Kỳ trước & Dự báo
Trong báo cáo WASDE tháng 06/2026, USDA đã thể hiện quan điểm "chờ đợi và quan sát" (wait-and-see) cực kỳ rõ nét khi **giữ nguyên toàn bộ dự báo tồn kho cuối kỳ niên vụ mới (2026/27) của Mỹ** đối với Ngô, Đậu tương và Lúa mì đúng bằng mức dự báo của tháng 5. Do đó, các biến động giá chủ yếu đến từ việc so sánh số liệu thực tế này với kỳ vọng (dự báo trước đó) của giới phân tích thị trường.

### 1. Tồn kho cuối kỳ của Mỹ (US Ending Stocks)
*Đơn vị: Tỷ bushels*

| Nông sản | Kỳ trước (Tháng 5) | Dự báo của Giới phân tích | Thực tế công bố (Tháng 6) | Đánh giá tác động đến giá |
| :--- | :---: | :---: | :---: | :--- |
| **Ngô (Corn)** | **1.957** | **1.947** | **1.957** | **Hơi tiêu cực (Bearish):** Tồn kho cao hơn kỳ vọng của thị trường do USDA chưa cắt giảm diện tích gieo trồng sớm. |
| **Lúa mì (Wheat)** | **0.762** (762M) | **0.765** (765M) | **0.762** (762M) | **Hơi tích cực (Bullish):** Tồn kho thực tế thấp hơn kỳ vọng của thị trường, củng cố xu hướng thắt chặt nguồn cung lúa mì Mỹ. |
| **Đậu tương (Soy)** | **0.310** (310M) | **0.312** (312M) | **0.310** (310M) | **Hơi tích cực (Bullish):** Tồn kho thực tế thấp hơn dự đoán, phản ánh nhu cầu dầu sinh học nội địa cực kỳ vững chắc. |

### 2. Tồn kho cuối kỳ Thế giới (Global Ending Stocks)
*Đơn vị: Triệu tấn (MMT)*

| Nông sản | Kỳ trước (Tháng 5) | Dự báo của Giới phân tích | Thực tế công bố (Tháng 6) | Đánh giá tác động đến giá |
| :--- | :---: | :---: | :---: | :--- |
| **Ngô (Corn)** | **277.54** | **278.51** | **277.54** | **Hơi tích cực (Bullish):** Tồn kho thế giới thấp hơn dự báo của giới phân tích, xác nhận nguồn cung toàn cầu vẫn thắt chặt. |
| **Lúa mì (Wheat)** | **275.04** | **274.66** | **275.04** | **Hơi tiêu cực (Bearish):** Cao hơn kỳ vọng của giới phân tích nhưng xu hướng dài hạn vẫn là giảm liên tiếp năm thứ 4. |
| **Đậu tương (Soy)** | **124.78** | **125.10** | **124.78** | **Tích cực (Bullish):** Tồn kho thế giới thấp hơn kỳ vọng của thị trường, giảm nhẹ so với vụ trước. |

---

## II. Đánh giá Tác động & Xu hướng Giá Ngô (CBOT: ZC) và Lúa mì (CBOT: ZW)

### 1. Phân tích Xu hướng Ngô (ZC)
*   **Tác động ngắn hạn:** Việc tồn kho ngô Mỹ giữ nguyên ở mức **1.957 tỷ bushels** (cao hơn mức 1.947 tỷ bushels kỳ vọng) đã tạo ra một áp lực giảm kỹ thuật ngắn hạn. Giá ngô có xu hướng kiểm định lại các mức hỗ trợ cứng dưới vùng **417.50 - 418.00**.
*   **Xu hướng trung và dài hạn:** Xu hướng chủ đạo vẫn là **Tăng giá (Bullish)**. USDA giữ nguyên số liệu tồn kho thế giới ở mức **277.54 triệu tấn** (thấp nhất 12 năm). Chu kỳ thời tiết nắng nóng La Niña vào tháng 7 sắp tới (xác suất 82%) và tình hình hạn hán tại các vùng ngô vụ 2 (Safrinha) của Brazil sẽ là động lực tăng giá mạnh mẽ sau khi áp lực gieo trồng kết thúc.
*   **Khuyến nghị thực chiến:** Tận dụng nhịp điều chỉnh giảm kỹ thuật ngắn hạn do báo cáo để **Long on Dip (Canh mua khi điều chỉnh)** quanh vùng hỗ trợ **420.00 - 433.00** đối với các hợp đồng kỳ hạn xa (Tháng 9 và 12).

### 2. Phân tích Xu hướng Lúa mì (ZW)
*   **Tác động ngắn hạn:** Số liệu tồn kho thực tế **762 triệu bushels** (thấp hơn dự báo 765 triệu bushels) đã kích hoạt lực mua kỹ thuật (Short Covering), kéo giá phục hồi nhẹ trở lại sau chuỗi ngày giảm điều chỉnh do áp lực thu hoạch sớm.
*   **Xu hướng trung và dài hạn:** Xu hướng **Tăng giá rất mạnh (Bullish)** được củng cố. Chất lượng lúa mì đông của Mỹ cực kỳ thấp (chỉ **26% Good/Excellent** và **44% Poor/Very Poor**), kết hợp với thiệt hại sản lượng 41% tại Úc do El Niño cũ và sự sụt giảm ở khu vực Biển Đen sẽ đẩy lúa mì vào chu kỳ thiếu hụt nguồn cung nghiêm trọng nửa cuối năm 2026.
*   **Khuyến nghị thực chiến:** Áp dụng chiến lược **Accumulative Long (Mua gom tích lũy quyết liệt)** quanh vùng giá hỗ trợ **580.00 - 605.00** cho các hợp đồng Tháng 9/Tháng 12, đón nhịp hồi phục sau thu hoạch (Post-Harvest Bounce).

---

## III. Thiết lập Chiến lược Đặc biệt "MÙA VỤ 2026"

Quyết định đầu tư được phối hợp nhất quán qua 3 hệ thống giao dịch độc lập:
1.  **V3 Pro:** Tập trung giao dịch ngắn hạn (Intraday) và Swing Trading theo cản kỹ thuật H1/M15.
2.  **V4:** Vị thế vĩ mô dài hạn bám sát xu hướng dòng tiền.
3.  **MÙA VỤ 2026:** Giao dịch theo chu kỳ mùa vụ, giá thành sản xuất nông nghiệp và thời tiết thực tế.

### 1. Ma trận Giao dịch "MÙA VỤ 2026" - Cấu trúc 2 Giai đoạn (Dual-Leg Setup)

| HĐ Chỉ định | Chiến lược & Phân nhóm | Điểm vào lệnh Độc lập | Cắt lỗ bảo vệ vốn | Chốt lời & Tất toán | Phân bổ vốn |
| :---: | :--- | :---: | :---: | :---: | :---: |
| **ZCU26** (Corn) | Long Hold (Leg 1 - Ngắn hạn) | **420.00 - 433.00**<br>*(Tháng 6 - 7)* | **413.00** | **475.00** \| **495.00**<br>*(Tất toán: 15/07 - 25/07)* | **10%** |
| **ZCZ26** (Corn) | Long Hold (Leg 2 - Dài hạn) | **430.00 - 438.00**<br>*(Tháng 6 - 7)* | **422.00** | **510.00** \| **535.00**<br>*(Tất toán: 15/11 - 30/11)* | **5%** |
| **ZSX26** (Soy) | Long Accumulation (Leg 1 - 50%) | **1125.00 - 1140.00**<br>*(Tháng 6 - 7)* | **1105.00** | **1200.00** \| **1240.00**<br>*(Tất toán: 20/08 - 05/09)* | **10%** |
| **ZSX26** (Soy) | Long Accumulation (Leg 2 - 50%) | **1125.00 - 1140.00**<br>*(Tháng 6 - 7)* | **1105.00** | **1280.00** \| **1320.00**<br>*(Tất toán: 15/10 - 30/10)* | **10%** |
| **ZWU26** (Wheat)| Accumulative Long (Leg 1 - Ngắn hạn)| **580.00 - 595.00**<br>*(Tháng 6)* | **565.00** | **645.00** \| **675.00**<br>*(Tất toán: 10/08 - 20/08)* | **10%** |
| **ZWZ26** (Wheat)| Accumulative Long (Leg 2 - Dài hạn) | **590.00 - 605.00**<br>*(Tháng 6)* | **575.00** | **690.00** \| **720.00**<br>*(Tất toán: 15/11 - 30/11)* | **5%** |

### 2. Định nghĩa Chiến thuật & Quản lý Danh mục

#### A. Định nghĩa Biện chứng Chiến thuật:
*   **Long Hold (Mua và Nắm giữ Vị thế):** Mở vị thế Long tại vùng giá chỉ định và giữ chặt xuyên suốt thời kỳ nhạy cảm của mùa vụ (giai đoạn thụ phấn ngô trong tháng 7). Không thực hiện mua gom (DCA) thêm nếu giá chạy trong biên độ nhằm tránh nâng giá vốn trung bình khi Weather Premium được kích hoạt bất ngờ.
*   **Long Accumulation (Mua gom Tích lũy):** Chủ động chia nhỏ nguồn vốn giải ngân làm 3-4 phần để gom mua dần khi giá điều chỉnh sâu vào vùng chiết khấu. Chiến thuật này phù hợp với Đậu tương (ZSX26) để tối ưu hóa giá vốn trung bình sát giá thành sản xuất của nông dân Mỹ.

#### B. Phân bổ Vốn thực tế:
*   **Margin Buffer (Ký quỹ dự phòng):** Luôn duy trì **50% tổng vốn** ở trạng thái tự do để phòng ngừa rung lắc thị trường.
*   **Active Capital (Vốn giải ngân - 50%):**
    *   🌽 **Ngô (Corn):** Phân bổ **15%** tổng vốn (10% cho Leg 1 - ZCU26; 5% cho Leg 2 - ZCZ26).
    *   🌱 **Đậu tương (Soybeans):** Phân bổ **20%** tổng vốn (Long Accumulation ZSX26 chia đều).
    *   🌾 **Lúa mì (Wheat):** Phân bổ **15%** tổng vốn (10% cho Leg 1 - ZWU26; 5% cho Leg 2 - ZWZ26).

#### C. Quy tắc Tất toán Vị thế theo Mùa vụ (Seasonal Liquidation Protocol):
Vị thế mùa vụ phải tuân thủ nghiêm ngặt lịch tất toán thời gian, không phụ thuộc hoàn toàn vào giá mục tiêu kỹ thuật, do "phí bảo hiểm thời tiết" (Weather Premium) sẽ hao mòn rất nhanh sau giai đoạn thụ phấn/sinh trưởng đỉnh điểm:
*   **🌽 Ngô:** Tất toán Leg 1 (ZCU26) trước **25/07/2026**; Leg 2 (ZCZ26) chốt lời từ **15/11 - 30/11/2026**.
*   **🌱 Đậu tương:** Chốt đợt 1 từ **20/08 - 05/09/2026**; chốt đợt 2 từ **15/10 - 30/10/2026**.
*   **🌾 Lúa mì:** Tất toán Leg 1 (ZWU26) trước **20/08/2026**; Leg 2 (ZWZ26) chốt lời từ **15/11 - 30/11/2026**.

---
*Báo cáo được thực hiện bởi Hệ thống CBOT Pro V3 & V4.*
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
    filename = os.path.join(out_dir, "11_06_2026 Bao cao WASDE Chinh thuc.docx")
    
    try:
        doc.save(filename)
        print(f"SUCCESS: {filename}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    run_export()
