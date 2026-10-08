with open('Data/macro_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace F1
content = content.replace(
    'score = manual_overrides.get("F1_Russia_Policy", {}).get("score", 5)\n    note  = manual_overrides.get("F1_Russia_Policy", {}).get("note", "")\n    status = "manual"  # Always manual\n    return {"score": score, "raw_value": raw_val, "raw_detail": raw_detail or note, "last_updated": last_up, "status": status}',
    'ov = manual_overrides.get("F1_Russia_Policy", {})\n    score = ov.get("score", 5)\n    note = ov.get("note", "")\n    return {"score": score, "raw_value": raw_val, "raw_detail": raw_detail or note, "last_updated": ov.get("updated_at", last_up), "status": "manual"}'
)

# Replace generic manual functions (F4, F4S, F5, F6, F7, F8, F12)
factors = ["F4_Weather_SH", "F4S_Supply_SH", "F5_Export_Sales", "F6_Export_Paces", "F7_Fund_Position", "F8_Geopolitics", "F12_Global_Demand"]
for f_key in factors:
    old_str = f'score = manual_overrides.get("{f_key}", {{}}).get("score", 5)\n    note  = manual_overrides.get("{f_key}", {{}}).get("note", "")\n    return {{"score": score, "raw_value": f"Điểm tự đánh giá: {{score}}/10", "raw_detail": note, "last_updated": "Thủ công", "status": "manual"}}'
    new_str = f'ov = manual_overrides.get("{f_key}", {{}})\n    score = ov.get("score", 5)\n    note = ov.get("note", "")\n    return {{"score": score, "raw_value": f"Điểm tự đánh giá: {{score}}/10", "raw_detail": note, "last_updated": ov.get("updated_at", "Thủ công"), "status": "manual"}}'
    content = content.replace(old_str, new_str)

# F3 is slightly different
old_f3 = 'ov = manual_overrides.get("F3_Other_Supply", manual_overrides.get("F3_EU_Supply", {}))\n    score = ov.get("score", 5)\n    note  = ov.get("note", "")\n    return {"score": score, "raw_value": f"Điểm tự đánh giá: {score}/10", "raw_detail": note, "last_updated": "Thủ công", "status": "manual"}'
new_f3 = 'ov = manual_overrides.get("F3_Other_Supply", manual_overrides.get("F3_EU_Supply", {}))\n    score = ov.get("score", 5)\n    note = ov.get("note", "")\n    return {"score": score, "raw_value": f"Điểm tự đánh giá: {score}/10", "raw_detail": note, "last_updated": ov.get("updated_at", "Thủ công"), "status": "manual"}'
content = content.replace(old_f3, new_f3)

with open('Data/macro_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("done")
