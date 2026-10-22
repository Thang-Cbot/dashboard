from pathlib import Path
import datetime

mv_file = Path("D:/0_Thang_Drive/Antigravity/Cbot/pages/6_MuaVu.py")
content = mv_file.read_text(encoding="utf-8")
content = content.replace("<div class='mv-card-title'>{cot_dot} Dòng Tiền COT – ZW</div>", "<div class='mv-card-title'>{cot_dot} Dòng Tiền COT – {commodity}</div>")
mv_file.write_text(content, encoding="utf-8")

trigger_file = Path("D:/0_Thang_Drive/Antigravity/Cbot/Data/output/.streamlit_trigger")
trigger_file.write_text(datetime.datetime.now().isoformat())
print("Trigger touched & MuaVu updated!")
