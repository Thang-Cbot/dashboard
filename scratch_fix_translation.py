import re

with open('pages/4_Weather_Map.py', 'r', encoding='utf-8') as f:
    content = f.read()

translation_logic = """    for bad, good in [("NiA\\xc3\\xb1o","Niño"),("NiA o","Niño"),("NiAo","Niño"),("La Ni?a","La Niña"),("chA?u","châu"),("A?c","Úc")]:
        enso_status = enso_status.replace(bad, good)
        enso_desc   = enso_desc.replace(bad, good)
        
    # Translate ENSO Status
    if "Advisory" in enso_status:
        enso_status = enso_status.replace("Advisory", "(Cảnh Báo)")
    if "Watch" in enso_status:
        enso_status = enso_status.replace("Watch", "(Theo Dõi)")
        
    # Translate ENSO Description
    desc_lower = enso_desc.lower()
    if "strengthening" in desc_lower and "90%" in desc_lower:
        enso_desc = "El Niño đang mạnh lên, với hơn 90% khả năng sẽ trở thành đợt siêu El Nino cực đoan (rất mạnh) trong mùa thu và đông năm 2026-27 ở Bán cầu Bắc."
    elif "el niño conditions are present" in desc_lower:
        enso_desc = "Hiện tượng El Niño đang xuất hiện và dự kiến sẽ tiếp tục kéo dài."
    elif "la niña conditions are present" in desc_lower:
        enso_desc = "Hiện tượng La Niña đang xuất hiện và dự kiến sẽ tiếp tục kéo dài."
    elif "neutral" in desc_lower:
        enso_desc = "Trạng thái ENSO hiện tại đang ở mức trung tính (Neutral)."
    elif "transition" in desc_lower and "la niña" in desc_lower:
        enso_desc = "Dự kiến sẽ chuyển sang trạng thái La Niña trong vài tháng tới."
"""

# Replace the old loop
content = re.sub(
    r'    for bad, good in \[\(\"NiA\\xc3\\xb1o\",\"Niño\"\).*?enso_desc\.replace\(bad, good\)',
    translation_logic,
    content,
    flags=re.DOTALL
)

with open('pages/4_Weather_Map.py', 'w', encoding='utf-8') as f:
    f.write(content)
