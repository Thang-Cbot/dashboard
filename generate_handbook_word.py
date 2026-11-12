import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn
import os

doc = docx.Document()

# Set Margins
for section in doc.sections:
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

# Color Palette: Deep Navy & Dark Slate
COLOR_PRIMARY = RGBColor(24, 43, 73)      # Deep Navy #182B49
COLOR_SECONDARY = RGBColor(41, 128, 185)  # Blue #2980B9
COLOR_DARK = RGBColor(44, 62, 80)         # Charcoal #2C3E50
COLOR_MUTED = RGBColor(127, 140, 141)     # Muted Gray #7F8C8D
COLOR_ALERT = RGBColor(192, 57, 43)       # Dark Red #C0392B
COLOR_SUCCESS = RGBColor(39, 174, 96)     # Green #27AE60

def set_cell_background(cell, fill_hex):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def add_header_callout(doc, text, fill_hex="EBF5FB", border_hex="2980B9"):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.columns[0].width = Inches(6.8)
    cell = table.cell(0, 0)
    set_cell_background(cell, fill_hex)
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
    
    # Border left
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(f'<w:tcBorders {nsdecls("w")}><w:left w:val="single" w:sz="24" w:space="0" w:color="{border_hex}"/><w:top w:val="none"/><w:right w:val="none"/><w:bottom w:val="none"/></w:tcBorders>')
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(10.5)
    run.font.color.rgb = COLOR_DARK
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

# ----------------- COVER / HEADER -----------------
title_p = doc.add_paragraph()
title_p.paragraph_format.space_before = Pt(10)
title_p.paragraph_format.space_after = Pt(2)
title_run = title_p.add_run("CẨM NANG THỰC CHIẾN GIAO DỊCH CBOT")
title_run.font.name = 'Calibri'
title_run.font.size = Pt(22)
title_run.font.bold = True
title_run.font.color.rgb = COLOR_PRIMARY

sub_p = doc.add_paragraph()
sub_p.paragraph_format.space_after = Pt(14)
sub_run = sub_p.add_run("BÍ QUYẾT ĐỌC VỊ ĐẢO CHIỀU KỲ ROLLOVER & CHIẾN THUẬT LƯỚT SÓNG HIT & RUN THEO CALENDAR SPREAD")
sub_run.font.name = 'Calibri'
sub_run.font.size = Pt(13)
sub_run.font.bold = True
sub_run.font.color.rgb = COLOR_SECONDARY

# Meta info
meta_p = doc.add_paragraph()
meta_p.paragraph_format.space_after = Pt(18)
meta_run = meta_p.add_run("Tài liệu nội bộ | Dữ liệu kiểm chứng 10 năm (2016 - 2026) | Đối tượng: Lúa mì (ZW) & Ngô (ZC)")
meta_run.font.name = 'Calibri'
meta_run.font.size = Pt(9.5)
meta_run.font.italic = True
meta_run.font.color.rgb = COLOR_MUTED

# Divider
p_div = doc.add_paragraph()
p_div.paragraph_format.space_after = Pt(12)
run_div = p_div.add_run("—" * 65)
run_div.font.color.rgb = COLOR_SECONDARY

# ----------------- PHẦN I -----------------
h1 = doc.add_paragraph()
h1.paragraph_format.space_before = Pt(14)
h1.paragraph_format.space_after = Pt(6)
r = h1.add_run("PHẦN I: BẢN CHẤT CƠ CHẾ VẬN HÀNH CỦA BIG MONEY KHI ROLLOVER")
r.font.name = 'Calibri'
r.font.size = Pt(14)
r.font.bold = True
r.font.color.rgb = COLOR_PRIMARY

p = doc.add_paragraph()
p.paragraph_format.line_spacing = 1.15
p.paragraph_format.space_after = Pt(8)
p.add_run("Rollover không phải là sự kiện ngẫu nhiên mà là hoạt động kỹ thuật mang tính bắt buộc của các quỹ phòng hộ (Hedge Funds) và các định chế quản lý tài sản lớn trên sàn CBOT:")

p_list = doc.add_paragraph(style='List Bullet')
p_list.paragraph_format.space_after = Pt(4)
p_list.add_run("First Notice Day (FND - Ngày thông báo đầu tiên): ").bold = True
p_list.add_run("Rơi vào ngày làm việc cuối cùng của tháng trước tháng đáo hạn (ví dụ: ngày 30/11 cho hợp đồng Tháng 12 kỳ Z). Các quỹ đầu cơ (Managed Money) tuyệt đối không nhận hàng vật chất, do đó họ bắt buộc phải đóng hoặc cuộn (Roll) toàn bộ vị thế trước FND.")

p_list2 = doc.add_paragraph(style='List Bullet')
p_list2.paragraph_format.space_after = Pt(8)
p_list2.add_run("Cơ chế Legging chủ động: ").bold = True
p_list2.add_run("Với quy mô hàng chục nghìn hợp đồng, Big Money không bao giờ cuộn lệnh 2 chiều cùng lúc. Họ quản trị rủi ro bằng cách đè/kéo một chiều ở kỳ hạn gần trước để tối ưu hóa biên độ lợi nhuận, ép các nhà đầu tư nhỏ lẻ cắt lỗ, rồi mới thong thả gom hàng ở kỳ hạn sau.")

add_header_callout(doc, "QUY TẮC CỐT TỬ: Khi Quỹ đang ôm vị thế Bán Khống cực đại (Net Short > 70.000 - 87.000 HĐ), việc đáo hạn tại ngày FND (T-0) và T+1 thực chất là hành động BẮT BUỘC PHẢI MUA LẠI BÙ LỆNH (Buy-To-Cover). Khi nguồn cung ở hợp đồng sắp chết đã cạn kiệt, lực mua cưỡng bức này kích hoạt một cú giật nảy Short Squeeze cực mạnh!")

# ----------------- PHẦN II -----------------
h2 = doc.add_paragraph()
h2.paragraph_format.space_before = Pt(16)
h2.paragraph_format.space_after = Pt(6)
r = h2.add_run("PHẦN II: CẨM NANG XÁC ĐỊNH XU HƯỚNG ĐẢO CHIỀU KHI ROLLOVER")
r.font.name = 'Calibri'
r.font.size = Pt(14)
r.font.bold = True
r.font.color.rgb = COLOR_PRIMARY

p = doc.add_paragraph()
p.paragraph_format.line_spacing = 1.15
p.paragraph_format.space_after = Pt(8)
p.add_run("Để bắt trúng đáy đảo chiều của một kỳ Rollover, nhà giao dịch cần áp dụng ")
p.add_run("Bộ lọc 4 Điều Kiện Kích Hoạt Đảo Chiều Tuyệt Đối (The Reversal Quad-Filter):").bold = True

# Bảng 4 điều kiện
table_f = doc.add_table(rows=5, cols=3)
table_f.alignment = WD_TABLE_ALIGNMENT.CENTER
table_f.autofit = False
table_f.columns[0].width = Inches(1.8)
table_f.columns[1].width = Inches(2.2)
table_f.columns[2].width = Inches(2.8)

headers = ["Thước Đo / Yếu Tố", "Ngưỡng Kích Hoạt Chuẩn", "Bản Chất Dòng Tiền Big Money"]
for col_idx, text in enumerate(headers):
    cell = table_f.cell(0, col_idx)
    set_cell_background(cell, "182B49")
    set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
    p = cell.paragraphs[0]
    r = p.add_run(text)
    r.font.name = 'Calibri'
    r.font.size = Pt(10)
    r.font.bold = True
    r.font.color.rgb = RGBColor(255, 255, 255)

filters_data = [
    ("1. Vị thế Quỹ (COT Report)", "Net Short cực trị:\n> 70k - 87k hợp đồng", "Cạn kiệt người bán (Seller Exhaustion). Toàn thị trường đã ôm Short, không còn ai bán mới để đè giá thủng sâu."),
    ("2. Sàn Giá Vốn Nông Dân\n(Cash Breakeven)", "Rơi sát vùng:\n560 - 586 cents/giạ", "Nông dân đóng cửa kho găm hàng (Farmer Holding), từ chối bán lỗ. Các nước nhập khẩu lớn (Ai Cập, Trung Đông) ồ ạt mở thầu gom hàng."),
    ("3. Tín hiệu Kỹ thuật D1\n(Price Action)", "• Mô hình 2 Đáy (Double Bottom)\n• Cột Volume Xanh cực đại\n• RSI bẻ gập từ vùng < 25", "Hấp thụ thanh khoản cao trào (Climactic Absorption). Big Money thò tay nuốt chửng toàn bộ lệnh bán cắt lỗ của nhỏ lẻ."),
    ("4. Mốc Thời Gian FND\n(Countdown to FND)", "Rơi vào giai đoạn:\nTừ T-2 đến FND (T-0) và T+1", "Thời điểm phe Bán phải đầu hàng và mua trả hàng để né nghĩa vụ giao nhận ngũ cốc vật chất.")
]

for row_idx, row_data in enumerate(filters_data, start=1):
    bg_color = "F8F9F9" if row_idx % 2 == 1 else "FFFFFF"
    for col_idx, text in enumerate(row_data):
        cell = table_f.cell(row_idx, col_idx)
        set_cell_background(cell, bg_color)
        set_cell_margins(cell, top=90, bottom=90, left=110, right=110)
        p = cell.paragraphs[0]
        p.paragraph_format.line_spacing = 1.15
        r = p.add_run(text)
        r.font.name = 'Calibri'
        r.font.size = Pt(9.5)
        if col_idx == 0:
            r.font.bold = True
            r.font.color.rgb = COLOR_DARK
        elif col_idx == 1:
            r.font.bold = True
            r.font.color.rgb = COLOR_SECONDARY
        else:
            r.font.color.rgb = COLOR_DARK

doc.add_paragraph().paragraph_format.space_after = Pt(4)

# Thống kê 10 năm
p_sub = doc.add_paragraph()
p_sub.paragraph_format.space_before = Pt(8)
p_sub.paragraph_format.space_after = Pt(4)
r = p_sub.add_run("Bảng Thống Kê Định Lượng Hành Vi Giá 54 Kỳ Rollover (10 Năm Lịch Sử):")
r.font.name = 'Calibri'
r.font.bold = True
r.font.size = Pt(11)
r.font.color.rgb = COLOR_DARK

table_stat = doc.add_table(rows=3, cols=8)
table_stat.alignment = WD_TABLE_ALIGNMENT.CENTER
table_stat.autofit = False
for col in table_stat.columns:
    col.width = Inches(0.85)

headers_stat = ["Trạng Thái COT", "T-5", "T-4", "T-3", "T-2", "T-1", "FND (T-0)", "T+1"]
for col_idx, text in enumerate(headers_stat):
    cell = table_stat.cell(0, col_idx)
    set_cell_background(cell, "2C3E50")
    set_cell_margins(cell, top=80, bottom=80, left=60, right=60)
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    r.font.name = 'Calibri'
    r.font.size = Pt(9)
    r.font.bold = True
    r.font.color.rgb = RGBColor(255, 255, 255)

stats_rows = [
    ("Quỹ ôm SHORT (Lúa mì ZW)", "-0.32%\n(69% Đỏ)", "-0.33%\n(67% Đỏ)", "-0.00%\n(59% Đỏ)", "-0.14%\n(51% Đỏ)", "-0.18%\n(51% Đỏ)", "+0.39%\n(61.5% Xanh)", "+0.11%\n(51% Xanh)"),
    ("Quỹ ôm SHORT (Ngô ZC)", "-0.15%", "-0.32%\n(71% Đỏ)", "-0.54%\n(58% Đỏ)", "-0.36%\n(79% Đỏ)", "+0.26%\n(50% Xanh)", "+0.65%\n(58.3% Xanh)", "+0.69%\n(66.7% Xanh)")
]

for row_idx, row_data in enumerate(stats_rows, start=1):
    for col_idx, text in enumerate(row_data):
        cell = table_stat.cell(row_idx, col_idx)
        bg = "E8F8F5" if col_idx in [6, 7] else ("FFFFFF" if row_idx % 2 == 0 else "FDFEFE")
        set_cell_background(cell, bg)
        set_cell_margins(cell, top=70, bottom=70, left=50, right=50)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(text)
        r.font.name = 'Calibri'
        r.font.size = Pt(8.5)
        if col_idx in [6, 7]:
            r.font.bold = True
            r.font.color.rgb = COLOR_SUCCESS
        else:
            r.font.color.rgb = COLOR_DARK

doc.add_paragraph().paragraph_format.space_after = Pt(8)

# ----------------- PHẦN III -----------------
h3 = doc.add_paragraph()
h3.paragraph_format.space_before = Pt(16)
h3.paragraph_format.space_after = Pt(6)
r = h3.add_run("PHẦN III: CẨM NANG XÁC ĐỊNH XU HƯỚNG BỀN VỮNG CHO LỆNH HIT & RUN")
r.font.name = 'Calibri'
r.font.size = Pt(14)
r.font.bold = True
r.font.color.rgb = COLOR_PRIMARY

p = doc.add_paragraph()
p.paragraph_format.line_spacing = 1.15
p.paragraph_format.space_after = Pt(6)
p.add_run("Trong phiên Mỹ, việc soi chênh lệch bước giá giữa Kỳ Xa (Tháng 3 - H) và Kỳ Gần (Tháng 12 - Z) chính là chiếc radar chính xác nhất để phát hiện dòng tiền thuật toán của các tay chơi lớn.")

p_sub2 = doc.add_paragraph()
p_sub2.paragraph_format.space_before = Pt(6)
p_sub2.paragraph_format.space_after = Pt(4)
r = p_sub2.add_run("1. Quy Luật Vàng: 'Dòng Tiền Ở Đâu - Đánh Ở Đó'")
r.font.name = 'Calibri'
r.font.bold = True
r.font.size = Pt(11.5)
r.font.color.rgb = COLOR_SECONDARY

p_rule1 = doc.add_paragraph(style='List Bullet')
p_rule1.paragraph_format.space_after = Pt(4)
p_rule1.add_run("Thị trường TĂNG (Kỳ H tăng khỏe hơn Kỳ Z): ").bold = True
p_rule1.add_run("Ví dụ H tăng +3.0 mà Z chỉ tăng +1.6 (H lệch hơn Z > 1.2 giá) -> Dòng tiền gom hàng tập trung ở Kỳ H. ")
p_rule1.add_run("HÀNH ĐỘNG: MUA (LONG) KỲ H.").bold = True

p_rule2 = doc.add_paragraph(style='List Bullet')
p_rule2.paragraph_format.space_after = Pt(8)
p_rule2.add_run("Thị trường GIẢM (Kỳ Z sập sâu hơn Kỳ H): ").bold = True
p_rule2.add_run("Ví dụ Z giảm -3.0 mà H chỉ giảm -1.6 (Z sập hơn H > 1.2 giá) -> Áp lực bán tháo tháo chạy tập trung ở Kỳ Z. ")
p_rule2.add_run("HÀNH ĐỘNG: BÁN KHỐNG (SHORT) KỲ Z.").bold = True

p_sub3 = doc.add_paragraph()
p_sub3.paragraph_format.space_before = Pt(6)
p_sub3.paragraph_format.space_after = Pt(4)
r = p_sub3.add_run("2. Tại Sao Xu Hướng Đi Theo Kỳ Xa Luôn Là Xu Hướng BỀN VỮNG NHẤT?")
r.font.name = 'Calibri'
r.font.bold = True
r.font.size = Pt(11.5)
r.font.color.rgb = COLOR_SECONDARY

p_exp = doc.add_paragraph()
p_exp.paragraph_format.line_spacing = 1.15
p_exp.paragraph_format.space_after = Pt(8)
p_exp.add_run("• ")
p_exp.add_run("Kỳ gần (Z) là 'Chuyện trước mắt' (Nhiễu ngắn hạn): ").bold = True
p_exp.add_run("Chịu ảnh hưởng bởi nỗi sợ đáo hạn, nâng phí margin và nhỏ lẻ tháo chạy. Sóng của Z rất nhanh tắt.\n")
p_exp.add_run("• ")
p_exp.add_run("Kỳ xa (H) là 'Bản án của Tương lai' (Dòng tiền vĩ mô): ").bold = True
p_exp.add_run("Đại diện cho cung cầu quý tới, rủi ro mùa đông và thiệt hại logistics dài hạn. Nhỏ lẻ không bao giờ đủ vốn để đánh kỳ xa. Khi Kỳ Xa bứt phá độ lệch > 1.2 giá so với Kỳ Gần, đó là tuyên bố của các Quỹ Vĩ Mô (Macro Funds) về xu hướng của cả quý tiếp theo. Đi theo Kỳ Xa luôn là con sóng dài và ít bị quét Stoploss nhất!")

# ----------------- PHẦN IV -----------------
h4 = doc.add_paragraph()
h4.paragraph_format.space_before = Pt(16)
h4.paragraph_format.space_after = Pt(6)
r = h4.add_run("PHẦN IV: CHECKLIST QUY TRÌNH THỰC CHIẾN LỆNH LƯỚT SÓNG HIT & RUN")
r.font.name = 'Calibri'
r.font.size = Pt(14)
r.font.bold = True
r.font.color.rgb = COLOR_PRIMARY

table_steps = doc.add_table(rows=5, cols=2)
table_steps.alignment = WD_TABLE_ALIGNMENT.CENTER
table_steps.autofit = False
table_steps.columns[0].width = Inches(1.8)
table_steps.columns[1].width = Inches(5.0)

steps_data = [
    ("BƯỚC 1:\nBộ Lọc Thời Gian", "• BẮT BUỘC chỉ giao dịch trong phiên Mỹ: Từ 21:00 đến 23:30 (giờ VN).\n• Tuyệt đối bỏ qua phiên Á và Âu vì khối lượng mỏng, độ lệch giá chỉ là do bot giãn spread ảo."),
    ("BƯỚC 2:\nKiểm Tra Độ Lệch", "• Mở song song bảng điện tử Kỳ Z và Kỳ H.\n• Điều kiện bóp cò: Độ lệch giữa 2 kỳ PHẢI LỚN HƠN 1.2 GIÁ (xác nhận Big Money kích hoạt thuật toán TWAP/VWAP giải ngân khối lượng lớn)."),
    ("BƯỚC 3:\nĐiểm Vào Lệnh (Trigger)", "• Nếu Mua H: Chờ nến M5 hoặc M15 có nhịp Pullback nhẹ (1-2 nến đỏ nhỏ test cung), bóp cò MUA khi nến tiếp theo phá đỉnh cây nến đỏ vừa tạo.\n• Stop Loss cực ngắn: Đặt cách Entry chỉ 2.5 - 3.5 giá (dưới râu nến M15 gần nhất)."),
    ("BƯỚC 4:\nChốt Lời & Rút Quân", "• Mục tiêu chốt lời nhanh: Đặt Take Profit từ 4.0 đến 6.0 giá.\n• KỶ LUẬT THÉP: Rút sạch toàn bộ vị thế trước 00:30 đêm. Khi các quỹ khớp xong hạn ngạch trong ngày, lực mua/bán dừng lại và giá rất dễ đảo chiều trả điểm. Tuyệt đối không ôm lệnh qua đêm.")
]

for row_idx, (step_title, step_desc) in enumerate(steps_data):
    cell_title = table_steps.cell(row_idx, 0)
    cell_desc = table_steps.cell(row_idx, 1)
    
    set_cell_background(cell_title, "EBF5FB")
    set_cell_background(cell_desc, "FFFFFF")
    set_cell_margins(cell_title, top=100, bottom=100, left=120, right=120)
    set_cell_margins(cell_desc, top=100, bottom=100, left=140, right=140)
    
    p0 = cell_title.paragraphs[0]
    p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r0 = p0.add_run(step_title)
    r0.font.name = 'Calibri'
    r0.font.size = Pt(10)
    r0.font.bold = True
    r0.font.color.rgb = COLOR_SECONDARY
    
    p1 = cell_desc.paragraphs[0]
    p1.paragraph_format.line_spacing = 1.15
    for line in step_desc.split('\n'):
        if line.startswith('• BẮT BUỘC') or line.startswith('• KỶ LUẬT THÉP'):
            r1 = p1.add_run(line + '\n')
            r1.font.bold = True
            r1.font.color.rgb = COLOR_ALERT
        else:
            r1 = p1.add_run(line + '\n')
            r1.font.color.rgb = COLOR_DARK
        r1.font.name = 'Calibri'
        r1.font.size = Pt(9.5)

# Save Document
out_dir = "D:/0_Thang_Drive/Antigravity/Cbot/Daily Reports"
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "Cam_Nang_Rollover_Va_Hit_Run_Spread.docx")
doc.save(out_path)
print(f"SUCCESS: Saved handbook to {out_path}")
