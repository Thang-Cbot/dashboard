# 🌾 HƯỚNG DẪN TOÀN TẬP: CÁCH LẤY BÁO CÁO USDA (API, LINK TẢI & SCRIPT PYTHON)

Tài liệu này tổng hợp chi tiết tất cả các nguồn lấy báo cáo của **Bộ Nông Nghiệp Hoa Kỳ (USDA)** phục vụ phân tích cơ bản và giao dịch các hợp đồng hàng hóa nông sản trên sàn CBOT (**Ngô - ZC, Lúa Mì - ZW, Đậu Tương - ZS, Khô Đậu - ZM, Dầu Đậu - ZL**).

---

## 📅 PHẦN 1: CÁC BÁO CÁO TRỌNG YẾU & LỊCH CÔNG BỐ

| Tên Báo Cáo | Cơ Quan Phát Hành | Chu Kỳ | Giờ Mỹ (ET) | Giờ Việt Nam (ICT) | Tác Động Thị Trường |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **WASDE** (Cung Cầu Thế Giới) | USDA OCE / WAOB | Hàng tháng (ngày 8 - 12) | 12:00 PM | **23:00 / 24:00 (Đêm)** | 🔴 **Cực mạnh (Tạo gap lớn)** |
| **Crop Progress** (Tiến độ & Tỷ lệ Tốt/Xấu) | USDA NASS | Hàng tuần (Thứ Hai, T4–T11) | 04:00 PM | **03:00 / 04:00 sáng Thứ Ba** | 🟠 Mạnh (Theo mùa vụ) |
| **Weekly Export Sales** (Xuất khẩu tuần) | USDA FAS | Hàng tuần (Thứ Năm) | 08:30 AM | **19:30 / 20:30 tối Thứ Năm** | 🟠 Khá mạnh (Dòng tiền mua) |
| **Grain Stocks** (Tồn kho ngũ cốc) | USDA NASS | Hàng quý (Tháng 1, 3, 6, 9) | 12:00 PM | **23:00 / 24:00** | 🔴 **Cực mạnh** |
| **Prospective Plantings** (Dự phóng diện tích) | USDA NASS | Hàng năm (Ngày 31/03) | 12:00 PM | **23:00** | 🔴 **Cực mạnh** |
| **Acreage Report** (Diện tích gieo trồng thực tế) | USDA NASS | Hàng năm (Ngày 30/06) | 12:00 PM | **23:00** | 🔴 **Cực mạnh** |
| **Crop Production** (Sản lượng mùa vụ Mỹ) | USDA NASS | Hàng tháng (cùng WASDE) | 12:00 PM | **23:00 / 24:00** | 🔴 Rất mạnh |

> 💡 *Lưu ý về giờ:* Từ Chủ Nhật thứ 2 của Tháng 3 đến Chủ Nhật đầu tiên của Tháng 11 là **Giờ Mùa Hè (EDT)** (Việt Nam đi trước 11 tiếng: 12:00 PM ET = 23:00 VN). Mùa đông là **Giờ Tiêu Chuẩn (EST)** (Việt Nam đi trước 12 tiếng: 12:00 PM ET = 24:00 VN).

---

## 🌐 PHẦN 2: CÁC LINK TRỰC TIẾP TẢI BÁO CÁO (WEB / TXT / PDF)

### 1. Báo cáo WASDE (World Agricultural Supply and Demand Estimates)
* **Trang chủ WASDE (USDA OCE):** [https://www.usda.gov/oce/commodity/wasde](https://www.usda.gov/oce/commodity/wasde)
* **Báo cáo WASDE bản mới nhất (Text .txt):** [https://www.usda.gov/oce/commodity/wasde/latest.txt](https://www.usda.gov/oce/commodity/wasde/latest.txt)
* **Báo cáo WASDE bản mới nhất (PDF):** [https://www.usda.gov/oce/commodity/wasde/latest.pdf](https://www.usda.gov/oce/commodity/wasde/latest.pdf)
* **Báo cáo WASDE bản mới nhất (Excel / Spreadsheets):** [https://www.usda.gov/oce/commodity/wasde/latest.xls](https://www.usda.gov/oce/commodity/wasde/latest.xls)
* **Lịch công bố WASDE cả năm:** [https://www.usda.gov/oce/commodity-markets/wasde/wasde-report-dates](https://www.usda.gov/oce/commodity-markets/wasde/wasde-report-dates)

### 2. Báo cáo NASS (Crop Progress, Grain Stocks, Acreage)
* **Trang chủ NASS Publications:** [https://www.nass.usda.gov/Publications/](https://www.nass.usda.gov/Publications/)
* **Crop Progress mới nhất:** [https://www.nass.usda.gov/Publications/Crop_Progress/index.php](https://www.nass.usda.gov/Publications/Crop_Progress/index.php)
* **Grain Stocks (Tồn kho):** [https://usda.library.cornell.edu/concern/publications/xg94hp534](https://usda.library.cornell.edu/concern/publications/xg94hp534)

### 3. Báo cáo FAS (Export Sales & PSD Online)
* **FAS Weekly Export Sales Reporting (ESR):** [https://apps.fas.usda.gov/esrquery/](https://apps.fas.usda.gov/esrquery/)
* **PSD Online (Cơ sở dữ liệu Cung cầu toàn cầu PSD):** [https://apps.fas.usda.gov/psdonline/app/index.html#/app/home](https://apps.fas.usda.gov/psdonline/app/index.html#/app/home)
* **Tải trọn bộ dữ liệu PSD dạng CSV (Khuyên dùng phân tích lịch sử):** [https://apps.fas.usda.gov/psdonline/app/index.html#/app/downloads](https://apps.fas.usda.gov/psdonline/app/index.html#/app/downloads)

---

## ⚡ PHẦN 3: CÁC CỔNG API LẤY DỮ LIỆU TỰ ĐỘNG

### 🚀 Cách 1: USDA Cornell ESMIS API (Khuyên dùng nhất - Không cần API Key)
Đây là cổng API của Thư viện Albert R. Mann (Đại học Cornell phối hợp cùng USDA) lưu trữ toàn bộ các bản phát hành tức thì của USDA.
* **Ưu điểm:** **Hoàn toàn miễn phí, tốc độ phản hồi 0.1 giây, KHÔNG CẦN ĐĂNG KÝ KEY**.
* **Base URL:** `https://esmis.nal.usda.gov/api/v1/release/findByPubId/{pub_id}`

#### Bảng tra cứu Mã Ấn Phẩm (`pub_id`):
| Mã `pub_id` | Tên Ấn Phẩm | Định dạng file có sẵn |
| :--- | :--- | :--- |
| **`1659`** | **WASDE** (Cung cầu thế giới) | `.txt`, `.pdf`, `.zip`, `.xml` |
| **`2179`** | **Crop Progress** (Tiến độ mùa vụ tuần) | `.txt`, `.pdf`, `.csv` |
| **`1008`** | **Grain Stocks** (Tồn kho hàng quý) | `.txt`, `.pdf`, `.csv` |
| **`1071`** | **Prospective Plantings** (Dự kiến gieo trồng) | `.txt`, `.pdf`, `.csv` |
| **`1000`** | **Acreage** (Diện tích gieo trồng) | `.txt`, `.pdf`, `.csv` |
| **`1021`** | **Crop Production** (Sản lượng mùa vụ) | `.txt`, `.pdf`, `.csv` |

#### Đoạn Code Python mẫu (Lấy link file .txt mới nhất):
```python
import requests

def get_latest_usda_report(pub_id="1659"):
    """
    pub_id="1659": WASDE
    pub_id="2179": Crop Progress
    """
    url = f"https://esmis.nal.usda.gov/api/v1/release/findByPubId/{pub_id}"
    res = requests.get(url, timeout=10)
    if res.status_code == 200:
        data = res.json()
        results = data.get("results", [])
        if results:
            latest = results[0]
            print(f"Bản phát hành: {latest.get('release_title')}")
            print(f"Thời gian công bố: {latest.get('release_datetime')}")
            for f in latest.get("files", []):
                if f.endswith(".txt"):
                    print(f"👉 Link File TXT: {f}")
                    # Tải nội dung
                    content = requests.get(f).text
                    return content
    return None

# Chạy thử lấy WASDE mới nhất:
wasde_text = get_latest_usda_report("1659")
```

---

### 🔑 Cách 2: USDA NASS Quick Stats API (Dữ liệu thống kê có cấu trúc)
Dành cho việc truy vấn số liệu thống kê chuỗi thời gian (time-series), năng suất (Yield), diện tích (Harvested Area), tỷ lệ nảy mầm/thu hoạch chi tiết theo từng tiểu bang của Mỹ.
* **Đăng ký API Key miễn phí:** [https://quickstats.nass.usda.gov/api](https://quickstats.nass.usda.gov/api) (Điền email là nhận key ngay lập tức).
* **Endpoint chính:** `https://quickstats.nass.usda.gov/api/api_GET/`

#### Đoạn Code Python mẫu:
```python
import requests

API_KEY = "YOUR_NASS_API_KEY_HERE"

def get_crop_progress(commodity="CORN", year=2026):
    url = "https://quickstats.nass.usda.gov/api/api_GET/"
    params = {
        "key": API_KEY,
        "source_desc": "SURVEY",
        "sector_desc": "CROPS",
        "group_desc": "FIELD CROPS",
        "commodity_desc": commodity,
        "statisticcat_desc": "PROGRESS",
        "year__GE": year,
        "format": "JSON"
    }
    res = requests.get(url, params=params, timeout=20)
    if res.status_code == 200:
        records = res.json().get("data", [])
        print(f"Lấy thành công {len(records)} bản ghi.")
        return records
    else:
        print(f"Lỗi: {res.status_code} - {res.text}")
        return []
```

---

### 🚢 Cách 3: USDA FAS Open Data API (Xuất khẩu hàng tuần)
Cổng dữ liệu mở của Cục Nông Nghiệp Đối Ngoại Hoa Kỳ (FAS) phục vụ theo dõi lượng đơn hàng xuất khẩu đi các nước (nhất là Trung Quốc, Mexico, Nhật Bản).
* **Cổng thông tin:** [https://apps.fas.usda.gov/opendataweb/home](https://apps.fas.usda.gov/opendataweb/home)
* **Đăng ký API Key:** Thông qua cổng [Data.gov](https://api.data.gov/signup/).
* **Endpoint API Export Sales:**
  `https://apps.fas.usda.gov/OpenDataWeb/api/esr/exports/commodityCode/{code}/allCountries/marketYear/{year}`
  * Mã Ngô (Corn): `104`
  * Mã Đậu tương (Soybeans): `801`
  * Mã Lúa mì (Wheat): `101`

---

## 🛠️ PHẦN 4: CÁC SCRIPT SẴN CÓ TRONG DỰ ÁN CBOT CỦA BẠN

Trong hệ thống bot CBOT hiện tại của bạn, các file sau đã được lập trình sẵn để tự động crawl và phân tích báo cáo USDA:

1. **`usda_crawler.py`**:
   * Tự động crawl WASDE (`pub_id=1659`) và Crop Progress (`pub_id=2179`) qua ESMIS API.
   * Tự bóc tách các chỉ số:
     * **Ending Stocks (Tồn kho cuối kỳ)** Mỹ & Toàn cầu (ZC, ZS, ZW).
     * **Production (Sản lượng)** Mỹ, Brazil, Argentina, Nga, Úc.
     * **Good/Excellent %**: Đánh giá tỷ lệ chất lượng cây trồng.
   * Tính toán điểm **Bullish / Bearish Score** và xuất ra JSON cập nhật thẳng vào giao diện `pages/3_News.py`.

2. **`precisely_fetch_wasde.py`**:
   * Script "bắn tỉa" thời gian thực: Căn đúng giây **23:00:00 (hoặc 24:00:00) ngày ra tin WASDE** để gửi request liên tục, giật file WASDE về máy tính trong vòng **1-2 giây đầu tiên** trước khi giá CBOT biến động mạnh.

---

## 💡 PHẦN 5: BÍ QUYẾT ĐỌC BÁO CÁO CHO TRADER CBOT

Khi báo cáo USDA (đặc biệt là WASDE) được công bố, giá thị trường phản ứng theo nguyên tắc **Thực tế so với Dự báo (Actual vs. Estimate)** chứ không phải so với tháng trước:

$$\text{Chênh Lệch (Surprise)} = \text{Số Liệu Thực Tế USDA} - \text{Dự Báo Của Chuyên Gia (Bloomberg/Reuters Consensuses)}$$

1. **Tồn kho cuối kỳ (Ending Stocks) THẤP HƠN dự báo:** ➔ **BULLISH 🚀 (Giá TĂNG mạnh)**. Nguồn cung thắt chặt hơn kỳ vọng.
2. **Tồn kho cuối kỳ (Ending Stocks) CAO HƠN dự báo:** ➔ **BEARISH 🩸 (Giá GIẢM mạnh)**. Nguồn cung dồi dào, dư thừa.
3. **Tỷ lệ Good/Excellent của Crop Progress GIẢM:** ➔ **BULLISH 🚀 (Thời tiết xấu gây hại năng suất)**.
4. **Tỷ lệ Good/Excellent TĂNG:** ➔ **BEARISH 🩸 (Mùa vụ bội thu)**.
