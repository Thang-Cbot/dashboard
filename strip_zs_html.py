import re

with open('dashboard_template.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove ZS references from CSS
content = re.sub(r'--zs:#ff9f43;', '', content)
content = re.sub(r'\.nbtn\.zs.*?\}', '', content)
content = re.sub(r'\.hcard\.zs::before.*?\}', '', content)

# 2. Add NEWS button and tab body
news_nav = '<div class="nbtn news" onclick="showTab(\'news\',this)"><div class="pip"></div>📰 TIN TỨC & MÙA VỤ</div>'
content = re.sub(r'<div class="nbtn zs" onclick="showTab\(\'zs\',this\)">.*?</div>\n', news_nav + '\n', content)

# Add NEWS tab HTML structure (just before Alarm tab)
news_tab_html = '''<div id="tab-news" class="tab">
    <div class="row" style="margin-bottom:16px;">
      <div class="box" style="flex:1;">
        <div class="bx-head"><h2>📰 TIN TỨC, CUNG CẦU & THỜI TIẾT</h2></div>
        <div class="bx-body" id="news-content" style="padding: 16px;">
          Đang tải dữ liệu...
        </div>
      </div>
    </div>
  </div>
'''
content = re.sub(r'(<div id="tab-alarm" class="tab">)', news_tab_html + r'\1', content)

# Remove ZS code from JS
content = re.sub(r'var codes = \[\'ZC\', \'ZW\', \'ZS\'\];', "var codes = ['ZC', 'ZW'];", content)
content = re.sub(r'ZS: \{ color: \'var\(--zs\)\', emoji: \'🌱\', name: \'ĐẬU TƯƠNG\', desc: \'Chicago Board of Trade \| CBOT Soybean Futures\' \},?\n?', '', content)
content = re.sub(r'var titles = \{"ZC": "🌽 NGÔ \(CORN\)", "ZW": "🌾 LÚA MÌ \(WHEAT\)", "ZS": "🌱 ĐẬU TƯƠNG \(SOYBEAN\)"\};', 'var titles = {"ZC": "🌽 NGÔ (CORN)", "ZW": "🌾 LÚA MÌ (WHEAT)"};', content)

# Fix JS to generate NEWS content
# We will append logic into the main DOMContentLoaded or build process.
news_js = '''
    // Build NEWS Tab
    if (D.news) {
      let newsHtml = <h3>🌦 Báo Cáo Thời Tiết (ENSO & Khu Vực)</h3>;
      if(D.news.weather_long && D.news.weather_long.enso_status) {
          newsHtml += <div class="info-row"><strong>Trạng thái ENSO:</strong>  - </div>;
      }
      if(D.news.weather_short && D.news.weather_short.regions) {
          newsHtml += <table class="styled-table" style="width:100%; margin-top:10px;">
          <tr><th>Khu Vực</th><th>Cây Trồng</th><th>Cảnh Báo</th><th>Mưa 3 Ngày (mm)</th><th>Nhiệt Độ Max (°C)</th></tr>;
          for (let [rname, rdata] of Object.entries(D.news.weather_short.regions)) {
              let alertCol = (rdata.risk_assessment && rdata.risk_assessment.includes('kho han') || rdata.risk_assessment.includes('nang nong')) ? <span style="color:var(--red); font-weight:bold"></span> : <span style="color:var(--green);"></span>;
              newsHtml += <tr><td></td><td></td><td></td><td></td><td></td></tr>;
          }
          newsHtml += </table>;
      }
      
      newsHtml += <h3 style="margin-top: 24px;">🚢 Báo Cáo Xuất Khẩu (Export Sales)</h3>;
      if(D.news.export_sales && D.news.export_sales.status) {
          newsHtml += <div class="info-row"><strong>Trạng thái:</strong> </div>;
      } else {
          newsHtml += <div class="info-row">Chưa có dữ liệu mới.</div>;
      }
      
      newsHtml += <h3 style="margin-top: 24px;">📊 Cung Cầu Mùa Vụ (USDA)</h3>;
      newsHtml += <div class="info-row" style="color:var(--t2);">Dữ liệu Cung Cầu Ngô: Gieo trồng , Thu hoạch  (G/E: )</div>;
      newsHtml += <div class="info-row" style="color:var(--t2);">Dữ liệu Cung Cầu Lúa Mì: Thu hoạch  (G/E: )</div>;

      document.getElementById('news-content').innerHTML = newsHtml;
    }
'''
# inject news_js right after document.getElementById('brent-v') lines or just before console.log("Rendered!");
content = re.sub(r'(console\.log\("Rendered!"\);)', news_js + r'\n    \1', content)

with open('dashboard_template.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("HTML template modified.")
