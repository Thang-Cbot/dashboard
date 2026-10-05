import re

with open('pages/5_Macro_Matrix.py', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = r'(# Step 4: Re-run macro engine to recalculate all scores)'
replacement = r'''# Step 3.5: AI Update Manual Overrides
        st.write("🤖 AI cập nhật các yếu tố Vĩ mô thủ công...")
        r35 = subprocess.run(
            [sys.executable, str(BASE_DIR / "Data" / "update_macro_overrides_ai.py")],
            capture_output=True, text=True, encoding="utf-8", env=env, timeout=120
        )
        st.write("✅ AI Overrides" if r35.returncode == 0 else f"⚠️ AI Lỗi: {r35.stderr[-200:] if r35.stderr else ''}")

        \1'''

content = re.sub(pattern, replacement, content)

with open('pages/5_Macro_Matrix.py', 'w', encoding='utf-8') as f:
    f.write(content)
