import re
with open('Data/macro_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

def replacer(match):
    prefix = match.group(1)
    factor_key = match.group(2)
    return f"""ov = manual_overrides.get("{factor_key}", {{}})
    score = ov.get("score", 5)
    note = ov.get("note", "")
    updated = ov.get("updated_at", "Thủ công")
    return {{"score": score, "raw_value": f"Điểm tự đánh giá: {{score}}/10", "raw_detail": note, "last_updated": updated, "status": "manual"}}"""

# Find patterns like:
# score = manual_overrides.get("F8_Geopolitics", {}).get("score", 5)
# note  = manual_overrides.get("F8_Geopolitics", {}).get("note", "")
# return {"score": score, "raw_value": f"Điểm tự đánh giá: {score}/10", "raw_detail": note, "last_updated": ov.get("updated_at", "Thủ công"), "status": "manual"}
content = re.sub(
    r'(?:ov = manual_overrides\.get\("[^"]+", manual_overrides\.get\("[^"]+", \{\}\)\)\n\s+score = ov\.get\("score", 5\)\n\s+note\s*=\s*ov\.get\("note", ""\)|score = manual_overrides\.get\("([^"]+)", \{\}\)\.get\("score", 5\)\n\s+note\s*=\s*manual_overrides\.get\("[^"]+", \{\}\)\.get\("note", ""\))\n\s+return \{"score": score, "raw_value": f"Điểm tự đánh giá: \{score\}/10", "raw_detail": note, "last_updated": ov\.get\("updated_at", "Thủ công"\), "status": "manual"\}',
    replacer,
    content
)

# For F1_Russia_Policy
content = re.sub(
    r'score = manual_overrides\.get\("F1_Russia_Policy", \{\}\)\.get\("score", 5\)\n\s+note\s*=\s*manual_overrides\.get\("F1_Russia_Policy", \{\}\)\.get\("note", ""\)\n\s+status = "manual".*?\n\s+return \{"score": score, "raw_value": raw_val, "raw_detail": raw_detail or note, "last_updated": last_up, "status": status\}',
    r'''ov = manual_overrides.get("F1_Russia_Policy", {})
    score = ov.get("score", 5)
    note = ov.get("note", "")
    updated = ov.get("updated_at", last_up)
    return {"score": score, "raw_value": raw_val, "raw_detail": raw_detail or note, "last_updated": updated, "status": "manual"}''',
    content
)

# Replace remaining ov.get("updated_at", "Thủ công") with properly declared ov where it wasn't caught
content = content.replace(
    '''ov = manual_overrides.get("F3_Other_Supply", manual_overrides.get("F3_EU_Supply", {}))
    score = ov.get("score", 5)
    note  = ov.get("note", "")
    return {"score": score, "raw_value": f"Điểm tự đánh giá: {score}/10", "raw_detail": note, "last_updated": ov.get("updated_at", "Thủ công"), "status": "manual"}''',
    '''ov = manual_overrides.get("F3_Other_Supply", manual_overrides.get("F3_EU_Supply", {}))
    score = ov.get("score", 5)
    note = ov.get("note", "")
    updated = ov.get("updated_at", "Thủ công")
    return {"score": score, "raw_value": f"Điểm tự đánh giá: {score}/10", "raw_detail": note, "last_updated": updated, "status": "manual"}'''
)

with open('Data/macro_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
