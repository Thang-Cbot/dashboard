import json
from pathlib import Path

overview_file = Path("D:/0_Thang_Drive/Antigravity/Cbot/pages/1_Overview.py")
content = overview_file.read_text(encoding="utf-8")

old_code = """        # 5. COT ZC
        zc_cot = get_cot_by_code(cot, "ZC")
        if zc_cot:
            net  = zc_cot.get("net_position", 0) or 0
            chg  = zc_cot.get("change", 0) or 0
            quad = zc_cot.get("quadrant", zc_cot.get("quadrant_label", "—"))
            nc   = "#22c55e" if chg > 0 else "#ef4444"
            arrow = "▲" if chg > 0 else "▼"
            points.append(f"📊 <b>COT Ngô (ZC):</b> Net <span style='color:{nc}'>{net:+,} HD</span> ({arrow}{abs(chg):,}) — {quad}")"""

new_code = """        # 5. COT ZC
        zc_cot = get_cot_by_code(cot, "ZC")
        if zc_cot:
            net  = zc_cot.get("net_position", 0) or 0
            chg  = zc_cot.get("change", 0) or 0
            quad = zc_cot.get("quadrant", zc_cot.get("quadrant_label", "—"))
            nc   = "#22c55e" if chg > 0 else "#ef4444"
            arrow = "▲" if chg > 0 else "▼"
            net_est = zc_cot.get("net_estimated")
            est_str = f" | Est: <b>{net_est:+,.0f} HD</b>" if net_est is not None else ""
            points.append(f"🌽 <b>COT Ngô (ZC):</b> Net <span style='color:{nc}'>{net:+,} HD</span> ({arrow}{abs(chg):,}){est_str} — {quad}")

        # 6. COT ZW (Lúa Mì)
        zw_cot = get_cot_by_code(cot, "ZW")
        if zw_cot:
            net  = zw_cot.get("net_position", 0) or 0
            chg  = zw_cot.get("change", 0) or 0
            quad = zw_cot.get("quadrant", zw_cot.get("quadrant_label", "—"))
            nc   = "#22c55e" if chg > 0 else "#ef4444"
            arrow = "▲" if chg > 0 else "▼"
            net_est = zw_cot.get("net_estimated")
            est_str = f" | Est: <b>{net_est:+,.0f} HD</b>" if net_est is not None else ""
            points.append(f"🌾 <b>COT Lúa Mì (ZW):</b> Net <span style='color:{nc}'>{net:+,} HD</span> ({arrow}{abs(chg):,}){est_str} — {quad}")"""

# Handle both CRLF and LF
content_lf = content.replace("\r\n", "\n")
old_code_lf = old_code.replace("\r\n", "\n")

if old_code_lf in content_lf:
    content_lf = content_lf.replace(old_code_lf, new_code.replace("\r\n", "\n"))
    content_lf = content_lf.replace("for i, pt in enumerate(points[:6], 1):", "for i, pt in enumerate(points, 1):")
    overview_file.write_text(content_lf, encoding="utf-8")
    print("SUCCESS")
else:
    print("FAILED TO FIND TARGET")
