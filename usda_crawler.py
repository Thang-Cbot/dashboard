import requests
import re
import json
import datetime
import pytz

def parse_val(val):
    val = val.strip()
    if val == '-' or val == 'NA' or val == 'N/A' or not val:
        return 0
    val = re.sub(r'[^\d\.]', '', val)
    try:
        return float(val) if '.' in val else int(val)
    except ValueError:
        return 0

def get_next_wasde_date():
    current_utc = datetime.datetime.now(datetime.timezone.utc)
    et_tz = pytz.timezone('US/Eastern')
    vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    wasde_dates_2026 = [
        (1, 12), (2, 10), (3, 10), (4, 9), (5, 12), (6, 11),
        (7, 10), (8, 12), (9, 11), (10, 9), (11, 10), (12, 10)
    ]
    for m, d in wasde_dates_2026:
        dt_et = et_tz.localize(datetime.datetime(2026, m, d, 12, 0))
        if dt_et > current_utc:
            dt_vn = dt_et.astimezone(vn_tz)
            return dt_vn.strftime("%d/%m/%Y lúc %H:%M (VN)")
    return "Đang chờ lịch báo cáo năm sau"

def get_next_weekly_report(weekday, hour_et, minute_et=0):
    current_utc = datetime.datetime.now(datetime.timezone.utc)
    et_tz = pytz.timezone('US/Eastern')
    vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    current_et = current_utc.astimezone(et_tz)
    
    days_ahead = weekday - current_et.weekday()
    if days_ahead < 0:
        days_ahead += 7
        
    target_date = current_et.date() + datetime.timedelta(days=days_ahead)
    target_dt_et = et_tz.localize(datetime.datetime(target_date.year, target_date.month, target_date.day, hour_et, minute_et))
    
    if days_ahead == 0 and target_dt_et <= current_utc:
        target_dt_et += datetime.timedelta(days=7)
        
    target_dt_vn = target_dt_et.astimezone(vn_tz)
    return target_dt_vn.strftime("%d/%m/%Y lúc %H:%M (VN)")

def get_latest_release_txt_url(pub_id):
    url = f"https://esmis.nal.usda.gov/api/v1/release/findByPubId/{pub_id}"
    try:
        res = requests.get(url, timeout=15)
        if res.status_code == 200:
            releases = res.json().get("results", [])
            if releases:
                files = releases[0].get("files", [])
                for f in files:
                    if f.endswith('.txt'):
                        rel_date = releases[0].get("release_datetime", "")
                        return f, rel_date
    except Exception as e:
        print(f"Error querying ESMIS API for pub_id {pub_id}: {e}")
    return None, None

def parse_wasde(text):
    res = {}
    
    proj_years = re.findall(r'(\d{4}/\d{2})\s+Proj\.', text)
    if proj_years:
        proj_year = proj_years[-1] + " Proj."
    else:
        proj_year = "2026/27 Proj."
        
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    report_month = "May"
    for m in months:
        if m in text[:2000] or m.upper() in text[:2000]:
            report_month = m
            
    # 1. Ending Stocks & Competitors
    tables = [
        ("ZC", "World Corn Supply and Use"),
        ("ZS", "World Soybean Supply and Use"),
        ("ZW", "World Wheat Supply and Use")
    ]
    
    for code, heading in tables:
        pos = text.find(heading)
        if pos != -1:
            sub = text[pos:pos+12000]
            proj_pos = sub.find(proj_year)
            if proj_pos != -1:
                proj_sub = sub[proj_pos:proj_pos+1800]
                world_match = re.search(r'(World\s*[\d/]*\s*\n\s*' + report_month + r'\s+.*)', proj_sub)
                if not world_match:
                    world_match = re.search(r'(World\s*[\d/]*\s+' + report_month + r'\s+.*)', proj_sub)
                if not world_match:
                    world_match = re.search(r'(' + report_month + r'\s+[\d\.,\s]+)', proj_sub)
                    
                if world_match:
                    line = world_match.group(1)
                    parts = line.split()
                    val = parse_val(parts[-1])
                    if code not in res:
                        res[code] = {}
                    res[code]["global"] = val
                    
                # Extract competitors production
                if code == "ZC":
                    br_match = re.search(r'Brazil\s+.*?' + report_month + r'\s+[\d\.]+\s+[\d\.]+\s+[\d\.]+\s+([\d\.]+)', proj_sub)
                    ar_match = re.search(r'Argentina\s+.*?' + report_month + r'\s+[\d\.]+\s+[\d\.]+\s+[\d\.]+\s+([\d\.]+)', proj_sub)
                    if br_match: res[code]["brazil_prod"] = parse_val(br_match.group(1))
                    if ar_match: res[code]["argentina_prod"] = parse_val(ar_match.group(1))
                elif code == "ZS":
                    br_match = re.search(r'Brazil\s+.*?' + report_month + r'\s+[\d\.]+\s+[\d\.]+\s+[\d\.]+\s+([\d\.]+)', proj_sub)
                    ar_match = re.search(r'Argentina\s+.*?' + report_month + r'\s+[\d\.]+\s+[\d\.]+\s+[\d\.]+\s+([\d\.]+)', proj_sub)
                    if br_match: res[code]["brazil_prod"] = parse_val(br_match.group(1))
                    if ar_match: res[code]["argentina_prod"] = parse_val(ar_match.group(1))
                elif code == "ZW":
                    au_match = re.search(r'Australia\s+.*?' + report_month + r'\s+[\d\.]+\s+[\d\.]+\s+[\d\.]+\s+([\d\.]+)', proj_sub)
                    ru_match = re.search(r'Russia\s+.*?' + report_month + r'\s+[\d\.]+\s+[\d\.]+\s+[\d\.]+\s+([\d\.]+)', proj_sub)
                    if au_match: res[code]["australia_prod"] = parse_val(au_match.group(1))
                    if ru_match: res[code]["russia_prod"] = parse_val(ru_match.group(1))
                    
    # 2. US Ending Stocks
    zw_pos = text.find("U.S. Wheat Supply and Use")
    if zw_pos != -1:
        sub = text[zw_pos:zw_pos+3000]
        for line in sub.split('\n'):
            if "Ending Stocks" in line:
                if "ZW" not in res: res["ZW"] = {}
                res["ZW"]["us"] = parse_val(line.split()[-1])
                break
                
    zs_pos = text.find("U.S. Soybeans and Products Supply and Use")
    if zs_pos != -1:
        sub = text[zs_pos:zs_pos+3000]
        for line in sub.split('\n'):
            if "Ending Stocks" in line:
                if "ZS" not in res: res["ZS"] = {}
                res["ZS"]["us"] = parse_val(line.split()[-1])
                break
                
    zc_table_pos = text.find("U.S. Feed Grain and Corn Supply and Use")
    if zc_table_pos != -1:
        sub_table = text[zc_table_pos:zc_table_pos+5000]
        corn_subhead_pos = sub_table.find("CORN")
        if corn_subhead_pos != -1:
            sub_corn = sub_table[corn_subhead_pos:corn_subhead_pos+2500]
            for line in sub_corn.split('\n'):
                if "Ending Stocks" in line:
                    if "ZC" not in res: res["ZC"] = {}
                    res["ZC"]["us"] = parse_val(line.split()[-1])
                    break
                    
    res["report_month"] = report_month
    return res

def parse_crop_progress(text):
    res = {"ZC": {}, "ZS": {}, "ZW": {}}
    
    pos = text.find("Corn Planted - Selected States")
    if pos != -1:
        sub = text[pos:pos+5000]
        for line in sub.split('\n'):
            if re.match(r'^\s*18\s+States\s+\.+:', line):
                parts = line.split()
                res["ZC"]["planted"] = parse_val(parts[5])
                res["ZC"]["planted_avg"] = parse_val(parts[6])
                break
                
    pos = text.find("Corn Condition - Selected States")
    if pos != -1:
        sub = text[pos:pos+5000]
        for line in sub.split('\n'):
            if re.match(r'^\s*18\s+States\s+\.+:', line):
                parts = line.split()
                res["ZC"]["condition"] = parse_val(parts[6]) + parse_val(parts[7])
                break

    pos = text.find("Soybeans Planted - Selected States")
    if pos == -1: pos = text.find("Soybean Planted - Selected States")
    if pos != -1:
        sub = text[pos:pos+5000]
        for line in sub.split('\n'):
            if re.match(r'^\s*18\s+States\s+\.+:', line):
                parts = line.split()
                res["ZS"]["planted"] = parse_val(parts[5])
                res["ZS"]["planted_avg"] = parse_val(parts[6])
                break

    pos = text.find("Soybeans Condition - Selected States")
    if pos == -1: pos = text.find("Soybean Condition - Selected States")
    if pos != -1:
        sub = text[pos:pos+5000]
        for line in sub.split('\n'):
            if re.match(r'^\s*18\s+States\s+\.+:', line):
                parts = line.split()
                res["ZS"]["condition"] = parse_val(parts[6]) + parse_val(parts[7])
                break

    pos = text.find("Winter Wheat Condition - Selected States")
    if pos != -1:
        sub = text[pos:pos+5000]
        for line in sub.split('\n'):
            if re.match(r'^\s*18\s+States\s+\.+:', line):
                parts = line.split()
                res["ZW"]["ww_condition"] = parse_val(parts[6]) + parse_val(parts[7])
                break

    pos = text.find("Spring Wheat Condition - Selected States")
    if pos != -1:
        sub = text[pos:pos+5000]
        for line in sub.split('\n'):
            if re.match(r'^\s*6\s+States\s+\.+:', line):
                parts = line.split()
                res["ZW"]["sw_condition"] = parse_val(parts[6]) + parse_val(parts[7])
                break

    pos = text.find("Winter Wheat Harvested - Selected States")
    if pos != -1:
        sub = text[pos:pos+5000]
        for line in sub.split('\n'):
            if re.match(r'^\s*18\s+States\s+\.+:', line):
                parts = line.split()
                res["ZW"]["ww_harvested"] = parse_val(parts[5])
                res["ZW"]["ww_harvested_avg"] = parse_val(parts[6])
                break

    pos = text.find("Spring Wheat Harvested - Selected States")
    if pos != -1:
        sub = text[pos:pos+5000]
        for line in sub.split('\n'):
            if re.match(r'^\s*6\s+States\s+\.+:', line):
                parts = line.split()
                res["ZW"]["sw_harvested"] = parse_val(parts[5])
                break
                
    return res

def parse_inspections():
    url = "https://www.ams.usda.gov/mnreports/wa_gr101.txt"
    res = {}
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            lines = r.text.split('\n')
            report_date = ""
            for line in lines[:5]:
                if "USDA Market News" in line:
                    match = re.search(r'([A-Za-z]+ \d+, \d{4})', line)
                    if not match: match = re.search(r'([A-Za-z]+ \d+, \d{2})', line)
                    if not match: match = re.search(r'([A-Za-z]+ \d+ \d{4})', line)
                    if not match: report_date = line.replace("Washington, DC", "").replace("USDA Market News", "").strip()
                    else: report_date = match.group(1).strip()
            
            for line in lines:
                line_upper = line.upper()
                if line_upper.startswith("CORN ") or line_upper.startswith("SOYBEANS ") or line_upper.startswith("WHEAT "):
                    parts = line.split()
                    if len(parts) >= 2 and parts[1].replace(',', '').isdigit():
                        code = "ZC" if parts[0] == "CORN" else ("ZS" if parts[0] == "SOYBEANS" else "ZW")
                        res[code] = {"volume": parse_val(parts[1]), "date": report_date}
    except Exception as e:
        print(f"Error fetching AMS inspections: {e}")
    return res

def fetch_enso_status():
    url = "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso_advisory/ensodisc.txt"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            text = r.text[:1000]
            if "La Nina Advisory" in text or "La Nina conditions are present" in text:
                return "La Nina"
            elif "El Nino Advisory" in text or "El Nino conditions are present" in text:
                return "El Nino"
            else:
                return "Neutral / Transitioning"
    except Exception as e:
        print(f"Error fetching ENSO: {e}")
    return "Unknown"

def run_crawler_and_update():
    print("=== STARTING USDA & MARKET DYNAMIC CRAWLER ===")
    
    # 1. WASDE
    wasde_url, wasde_date = get_latest_release_txt_url("1659")
    wasde_data = {}
    if wasde_url:
        print(f"Fetching WASDE from: {wasde_url}")
        r = requests.get(wasde_url, timeout=15)
        if r.status_code == 200:
            wasde_data = parse_wasde(r.text)
            print("Successfully parsed WASDE.")
            
    # 2. Crop Progress
    prog_url, prog_date = get_latest_release_txt_url("2179")
    prog_data = {}
    if prog_url:
        print(f"Fetching Crop Progress from: {prog_url}")
        r = requests.get(prog_url, timeout=15)
        if r.status_code == 200:
            prog_data = parse_crop_progress(r.text)
            print("Successfully parsed Crop Progress.")
            
    # 3. Export Inspections
    inspections_data = parse_inspections()
    print("Successfully parsed grain inspections.")

    # 4. ENSO Status
    enso_status = fetch_enso_status()
    print(f"NOAA ENSO Status: {enso_status}")
    
    # Update fundamental_data.json
    filename = r"Data\output\fundamental_data.json"
    try:
        with open(filename, "r", encoding="utf-8") as f:
            fund = json.load(f)
            
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        fund["last_updated_fundamentals"] = today_str
        
        wasde_next = get_next_wasde_date()
        cp_next = get_next_weekly_report(0, 16) # Monday 4 PM ET
        insp_next = get_next_weekly_report(0, 11) # Monday 11 AM ET
        
        def format_num(val): return f"{val:,.0f}" if isinstance(val, (int, float)) else str(val)
        
        new_wasde_month = wasde_data.get("report_month", "")
        current_wasde_month = fund.get("wasde_report_month", "")
        is_new_month = (new_wasde_month and new_wasde_month != current_wasde_month)
        if is_new_month:
            fund["wasde_report_month"] = new_wasde_month
            
        for code in ["ZC", "ZS", "ZW"]:
            # ENSO Update
            if enso_status == "El Nino":
                fund[code]["weather_long_term"]["latest"] = "El Niño vĩ mô (Xác nhận)"
                fund[code]["weather_long_term"]["forecast"] = "El Niño đang duy trì và có xu hướng mạnh lên."
            elif enso_status == "La Nina":
                fund[code]["weather_long_term"]["latest"] = "La Niña vĩ mô (Xác nhận)"
                fund[code]["weather_long_term"]["forecast"] = "La Niña đang duy trì, nguy cơ hạn hán cao."
                
            if code in wasde_data:
                us_stocks = wasde_data[code].get("us", 0)
                global_stocks = wasde_data[code].get("global", 0)
                
                if us_stocks > 0:
                    formatted_us = f"{format_num(us_stocks)} triệu bushels (2026/27)"
                    if is_new_month:
                        fund[code]["us_ending_stocks"]["previous"] = fund[code]["us_ending_stocks"].get("current", "N/A")
                        fund[code]["us_ending_stocks"]["forecast_next"] = "Chưa có dự báo (Đợi AI cập nhật trước kỳ báo cáo)"
                    fund[code]["us_ending_stocks"]["current"] = formatted_us
                    fund[code]["us_ending_stocks"]["next_date"] = wasde_next
                    
                if global_stocks > 0:
                    formatted_global = f"{global_stocks:.2f} triệu tấn (2026/27)"
                    if is_new_month:
                        fund[code]["global_ending_stocks"]["previous"] = fund[code]["global_ending_stocks"].get("current", "N/A")
                        fund[code]["global_ending_stocks"]["forecast_next"] = "Chưa có dự báo (Đợi AI cập nhật trước kỳ báo cáo)"
                    fund[code]["global_ending_stocks"]["current"] = formatted_global
                    fund[code]["global_ending_stocks"]["next_date"] = wasde_next
                    
                if code == "ZC":
                    br = wasde_data[code].get("brazil_prod", 0)
                    ar = wasde_data[code].get("argentina_prod", 0)
                    if br > 0 or ar > 0:
                        fund[code]["competitors"]["latest"] = f"Brazil: {br}M tấn | Argentina: {ar}M tấn"
                elif code == "ZS":
                    br = wasde_data[code].get("brazil_prod", 0)
                    ar = wasde_data[code].get("argentina_prod", 0)
                    if br > 0 or ar > 0:
                        fund[code]["competitors"]["latest"] = f"Brazil: {br}M tấn | Argentina: {ar}M tấn"
                elif code == "ZW":
                    au = wasde_data[code].get("australia_prod", 0)
                    ru = wasde_data[code].get("russia_prod", 0)
                    if au > 0 or ru > 0:
                        fund[code]["competitors"]["latest"] = f"Úc: {au}M tấn | Nga: {ru}M tấn"

            # Crop Progress
            if code in prog_data:
                p_data = prog_data[code]
                fmt_date = ""
                if prog_date:
                    try:
                        fmt_date = datetime.datetime.strptime(prog_date[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
                    except:
                        fmt_date = prog_date[:10]
                        
                def _upd_cp(f_name, new_val):
                    old_val = fund[code][f_name].get("latest", "")
                    if old_val and old_val != new_val:
                        fund[code][f_name]["previous"] = old_val
                        old_dt = fund[code][f_name].get("latest_date", "")
                        if old_dt: fund[code][f_name]["previous_date"] = old_dt
                    fund[code][f_name]["latest"] = new_val
                    fund[code][f_name]["next_date"] = cp_next
                    if fmt_date: fund[code][f_name]["latest_date"] = fmt_date

                if "planted" in p_data:
                    _upd_cp("us_planting", f"{p_data['planted']}% đã gieo trồng")
                
                if code == "ZW":
                    ww_c = f"Đông {p_data['ww_condition']}% G/E" if "ww_condition" in p_data else "Đông N/A (Cuối vụ)"
                    sw_c = f"Xuân {p_data['sw_condition']}% G/E" if "sw_condition" in p_data else "Xuân N/A"
                    _upd_cp("crop_condition", f"{ww_c}, {sw_c}")
                    
                    ww_h = f"Đông {p_data['ww_harvested']}% thu hoạch" if "ww_harvested" in p_data else "Đông N/A"
                    sw_h = f"Xuân {p_data['sw_harvested']}% thu hoạch" if "sw_harvested" in p_data else "Xuân N/A"
                    _upd_cp("harvest_progress", f"{ww_h}, {sw_h}")
                else:
                    if "condition" in p_data and p_data["condition"] > 0:
                        _upd_cp("crop_condition", f"{p_data['condition']}% Good to Excellent")
            # Export Inspections
            if code in inspections_data:
                insp = inspections_data[code]
                existing_latest = fund[code]["exports"].get("latest", "")
                sales_match = re.search(r'(Bán hàng ròng:[^\|]*\d[^\|]*)', existing_latest)
                if not sales_match: sales_match = re.search(r'(doanh số ròng[^\|]*\d[^\|]*)', existing_latest)
                sales_part = " | " + sales_match.group(1).strip() if sales_match else ""
                
                new_latest = f"Giao hàng (Inspections): {format_num(insp['volume'])} tấn (Tuần kết thúc {insp['date']}){sales_part}"
                if existing_latest and existing_latest != new_latest:
                    fund[code]["exports"]["previous"] = existing_latest
                fund[code]["exports"]["latest"] = new_latest
                fund[code]["exports"]["next_date"] = insp_next
                
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(fund, f, ensure_ascii=False, indent=2)
        print("=== Successfully updated fundamental_data.json ===")
        return True
    except Exception as e:
        print(f"Error updating fundamental_data.json: {e}")
        return False

if __name__ == '__main__':
    run_crawler_and_update()
