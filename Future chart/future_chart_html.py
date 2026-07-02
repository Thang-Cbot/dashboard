# -*- coding: utf-8 -*-
"""
future_chart_html.py — Multi-Tab HTML Generator
Reads future_chart_data.json and generates a full HTML file with ZC / ZW / ZS tabs.
Each tab has: 4H candlestick + Actual (yellow), Daily chart, Factor bars, Events, Table.
"""
import os, json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, "future_chart_data.json")
HTML_PATH = os.path.join(BASE_DIR, "future_chart.html")

COMMODITIES = {
    "ZC": {"name": "🌽 Ngô (ZC)", "full": "Ngô CBOT (ZCU26)", "unit": "cents/bushel", "color": "#fbbf24"},
    "ZW": {"name": "🌾 Lúa mì (ZW)", "full": "Lúa mì CBOT (ZWU26)", "unit": "cents/bushel", "color": "#4ade80"},
    "ZS": {"name": "🌱 Đậu tương (ZS)", "full": "Đậu tương CBOT (ZSU26)", "unit": "cents/bushel", "color": "#a78bfa"},
}

def fmt_c4h(candles):
    lines = []
    for c in candles:
        day = c.get("day","")
        # Extract date and session: "Mon 15/06" + "Asia 07-11" -> "15/06 07-11"
        parts = day.split(" ")
        date_str = parts[1] if len(parts) > 1 else day
        sess = c.get("session","")
        sess_parts = sess.split(" ")
        sess_str = sess_parts[-1] if sess_parts else sess
        label = f"{date_str} {sess_str}"
        lines.append(f'["{label}",{c["open"]:.2f},{c["high"]:.2f},{c["low"]:.2f},{c["close"]:.2f}]')
    return "[\n  " + ",\n  ".join(lines) + "\n]"

def fmt_actual(actual_data):
    lines = []
    for a in actual_data:
        lines.append(f'["{a["label"]}",{a["price"]:.2f}]')
    return "[\n  " + ",\n  ".join(lines) + "\n]" if lines else "[]"

def fmt_daily(daily_summary, anchor):
    lines = []
    for day, d in daily_summary.items():
        sc = d.get("scenario","").replace('"',"'")
        logic = d.get("logic","").replace('"',"'")
        o,h,l,c = d["open"],d["high"],d["low"],d["close"]
        chg = c - o
        if chg > 2: scl = "su"
        elif chg > 0: scl = "sm"
        elif chg < -2: scl = "sj"
        else: scl = "sq"
        lines.append(f'{{d:"{day}",o:{o:.2f},h:{h:.2f},l:{l:.2f},c:{c:.2f},sc:"{sc}",scl:"{scl}",logic:"{logic}"}}')
    return "[\n  " + ",\n  ".join(lines) + "\n]"

def fmt_factors(scores):
    lines = []
    for k, v in scores.items():
        lines.append(f'{{n:"{k}",s:{v:+.1f},m:1.5}}')
    return "[\n  " + ",\n  ".join(lines) + "\n]"

def fmt_events(events_dict):
    lines = []
    for date, desc in events_dict.items():
        is_major = "QUAN TRỌNG" in desc or "BIẾN ĐỘNG" in desc
        cls = "ev emaj" if is_major else "ev"
        lines.append(f'{{"cls":"{cls}","date":"{date}","desc":"{desc.replace(chr(34), chr(39))}"}}')
    return "[\n  " + ",\n  ".join(lines) + "\n]"

def build_tab_script(code, c_data, meta):
    anchor = meta.get("anchor_price", 0)
    ema21 = meta.get("key_levels", {}).get("ema21", anchor)
    ema50 = meta.get("key_levels", {}).get("ema50", anchor)
    mss = meta.get("key_levels", {}).get("mss_trigger", meta.get("key_levels",{}).get("r1", anchor+2))
    composite = meta.get("composite_bias", 0)
    color = COMMODITIES[code]["color"]

    c4h_js    = fmt_c4h(c_data.get("candles_4h", []))
    actual_js = fmt_actual(c_data.get("actual_data", []))
    daily_js  = fmt_daily(c_data.get("daily_summary", {}), anchor)
    factors_js= fmt_factors(meta.get("detailed_scores", {}))
    events_raw= meta.get("key_events", {})

    wf = c_data.get("week_forecast", {})
    wk_high   = wf.get("high", anchor)
    wk_low    = wf.get("low", anchor)
    wk_close  = wf.get("close", anchor)
    wk_net    = wf.get("net_change", 0)

    net_cls   = "pos" if wk_net >= 0 else "neg"
    net_sign  = "+" if wk_net >= 0 else ""

    bias_bar_pct = min(100, abs(composite / 6.0) * 100)
    scenarios_text = c_data.get("scenarios_text","").replace("`","'").replace("\\","\\\\")

    events_html_items = ""
    for date, desc in events_raw.items():
        is_major = "QUAN TRỌNG" in desc or "BIẾN ĐỘNG" in desc
        cls = "ev emaj" if is_major else "ev"
        events_html_items += f'<div class="{cls}"><div class="ed">{date}</div><div class="et">{desc}</div></div>\n          '

    # Parse scenarios into phase cards
    phase_cards_html = ""
    phase_colors = ["#f87171", "#4ade80", "#38bdf8", "#a78bfa", "#fbbf24"]
    phase_icons = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
    phases = [p.strip() for p in scenarios_text.strip().split("PHASE") if p.strip()]
    for i, ph in enumerate(phases):
        lines = [l.strip() for l in ph.split("\\n") if l.strip()]
        title = lines[0] if lines else ""
        body = " ".join(lines[1:]) if len(lines) > 1 else ""
        pc = phase_colors[i % len(phase_colors)]
        ic = phase_icons[i % len(phase_icons)]
        phase_cards_html += f"""<div class="ph-card" style="border-top-color:{pc}">
          <div class="ph-icon">{ic}</div>
          <div class="ph-body">
            <div class="ph-title" style="color:{pc}">PHASE {title}</div>
            <div class="ph-desc">{body}</div>
          </div>
        </div>"""

    return f"""
<!-- ═══════════════ TAB: {code} ═══════════════ -->
<div id="tab_{code}" class="tab-pane" style="display:none">

  <!-- HERO + SCENARIO STRIP -->
  <div class="hero" style="border-top-color:{color}40;background:linear-gradient(135deg,rgba(56,189,248,0.04),{color}08)">
    <div class="hero-info">
      <h2 style="background:linear-gradient(90deg,{color},{color}99);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">{COMMODITIES[code]['full']} — Kịch Bản Tuần 15-19/06/2026</h2>
      <p>Anchor: {anchor:.2f}&cent; &nbsp;|&nbsp; Bias: {composite:+.2f} &nbsp;|&nbsp; Model: V3+V4+ICT+Mùa Vụ</p>
    </div>
    <div class="metrics">
      <div class="metric"><div class="mv neu">{anchor:.2f}</div><div class="ml">Anchor</div></div>
      <div class="metric"><div class="mv pos">{wk_high:.2f}</div><div class="ml">Wk High</div></div>
      <div class="metric"><div class="mv neg">{wk_low:.2f}</div><div class="ml">Wk Low</div></div>
      <div class="metric"><div class="mv {net_cls}">{wk_close:.2f}</div><div class="ml">Wk Close</div></div>
      <div class="metric"><div class="mv {net_cls}">{net_sign}{wk_net:.2f}&cent;</div><div class="ml">Net Chg</div></div>
    </div>
  </div>

  <!-- SCENARIO PHASE CARDS (compact strip) -->
  <div class="ph-strip">
    <div class="ph-strip-label">🧠 Luận Giải Kịch Bản AI — {code}</div>
    <div class="ph-cards">
      {phase_cards_html}
    </div>
  </div>

  <!-- 4H CHART -->
  <div class="card">
    <div class="card-header">
      <div>
        <div class="ch-title">📈 {COMMODITIES[code]['full']} — Nến Mô Phỏng 4H</div>
        <div class="ch-sub">Anchor: {anchor:.2f} &middot; Frame: 4H &middot; Tuần 15-19/06/2026</div>
      </div>
      <div class="legend">
        <div class="li"><div class="ld" style="background:#26a69a"></div><span>Bull</span></div>
        <div class="li"><div class="ld" style="background:#ef5350"></div><span>Bear</span></div>
        <div class="li"><div class="ld" style="background:#fbbf24;height:2px;box-shadow:0 0 5px #fbbf24"></div><span style="color:#fbbf24;font-weight:bold">Giá Thực Tế</span></div>
        <div class="li"><div class="ld" style="background:#38bdf8;height:1px"></div><span>EMA 21</span></div>
        <div class="li"><div class="ld" style="background:#a78bfa;height:1px"></div><span>EMA 50</span></div>
      </div>
    </div>
    <div id="chart4h_{code}" style="width:100%;height:550px"></div>
  </div>

  <!-- DAILY CHART -->
  <div class="card">
    <div class="card-header">
      <div>
        <div class="ch-title">📅 Tổng Quan Ngày — Daily OHLC</div>
        <div class="ch-sub">5 ngày giao dịch · Mon 15/06 → Fri 19/06 · 2026</div>
      </div>
    </div>
    <div id="chartday_{code}" style="width:100%;height:310px"></div>
  </div>

  <!-- TABLE + FACTORS + EVENTS -->
  <div class="grid2">
    <!-- Detailed Table (full width) -->
    <div class="panel" style="grid-column:span 2">
      <div class="ph">📋 Chi Tiết Dự Báo Từng Ngày — {code}</div>
      <div class="pb">
        <table>
          <thead><tr><th>Ngày</th><th>Open</th><th>High</th><th>Low</th><th>Close</th><th>Thay đổi</th><th>Biên độ</th><th>Kịch bản</th><th>Logic chính</th></tr></thead>
          <tbody id="dtbody_{code}"></tbody>
        </table>
      </div>
    </div>

    <!-- Factors -->
    <div class="panel">
      <div class="ph">⚖️ Phân Tích Đa Nhân Tố (Bias Score) — {code}</div>
      <div class="pb">
        <div class="conf-wrap">
          <div class="cl">TỔNG ĐIỂM</div>
          <div class="cb"><div class="cbi" style="width:{bias_bar_pct:.0f}%;background:{color}"></div></div>
          <div class="cv" style="color:{color}">{composite:+.1f}</div>
        </div>
        <div class="flist" id="flist_{code}"></div>
      </div>
    </div>

    <!-- Events -->
    <div class="panel">
      <div class="ph" style="color:#fbbf24">📅 Lịch Sự Kiện Tuần — {code}</div>
      <div class="pb">
        <div class="evl">
          {events_html_items}
        </div>
      </div>
    </div>
  </div>

</div>

<script>
(function(){{
  const C4H_{code} = {c4h_js};
  const ACTUAL_{code} = {actual_js};
  const DAILY_{code} = {daily_js};
  const FACTORS_{code} = {factors_js};
  const ANCHOR_{code} = {anchor};
  const EMA21_{code} = {ema21};
  const EMA50_{code} = {ema50};

  // Build 4H chart
  function buildChart4h_{code}(){{
    const xs = C4H_{code}.map(r=>r[0]);
    const act_xs = ACTUAL_{code}.map(r=>r[0]);
    const act_ys = ACTUAL_{code}.map(r=>r[1]);
    const ema21v = xs.map((_,i)=>+(EMA21_{code}+(i*0.05)).toFixed(2));
    const ema50v = xs.map((_,i)=>+(EMA50_{code}+(i*0.04)).toFixed(2));
    const mss = {mss:.2f};
    const allY = C4H_{code}.flatMap(r=>[r[2],r[3]]).concat(act_ys).filter(v=>v>0);
    const yMin = Math.min(...allY)*0.997;
    const yMax = Math.max(...allY)*1.003;
    const sh = [
      {{type:'line',x0:xs[0],x1:xs[xs.length-1],y0:mss,y1:mss,line:{{color:'#fbbf24',width:1.5,dash:'dashdot'}},layer:'below'}},
      ...[5,11,17,23].map(i=>i<xs.length?{{type:'line',x0:xs[i],x1:xs[i],y0:0,y1:1e5,line:{{color:'rgba(255,255,255,0.04)',width:1}},layer:'below'}}:null).filter(Boolean)
    ];
    Plotly.newPlot('chart4h_{code}',[
      {{type:'candlestick',x:xs,open:C4H_{code}.map(r=>r[1]),high:C4H_{code}.map(r=>r[2]),low:C4H_{code}.map(r=>r[3]),close:C4H_{code}.map(r=>r[4]),
        increasing:{{line:{{color:'#26a69a',width:1.5}},fillcolor:'#26a69a'}},
        decreasing:{{line:{{color:'#ef5350',width:1.5}},fillcolor:'#ef5350'}},
        name:'{code} Simulated',whiskerwidth:0.8}},
      {{type:'scatter',x:xs,y:ema21v,mode:'lines',line:{{color:'#38bdf8',width:1.5,dash:'dot'}},name:'EMA 21'}},
      {{type:'scatter',x:xs,y:ema50v,mode:'lines',line:{{color:'#a78bfa',width:1.5,dash:'dash'}},name:'EMA 50'}},
      {{type:'scatter',x:act_xs,y:act_ys,mode:'lines+markers',
        line:{{color:'#fbbf24',width:3}},marker:{{size:8,color:'#fbbf24',line:{{color:'#000',width:1}}}},
        name:'Giá Thực Tế',hovertemplate:'<b>%{{x}}</b><br>Actual: %{{y:.2f}}<extra></extra>'}}
    ],{{
      paper_bgcolor:'#131929',plot_bgcolor:'#0f1525',
      font:{{family:'JetBrains Mono,monospace',color:'#94a3b8',size:10}},
      xaxis:{{tickangle:-35,gridcolor:'rgba(30,45,74,0.45)',rangeslider:{{visible:false}},color:'#64748b',tickfont:{{size:8.5}}}},
      yaxis:{{title:'Price ({COMMODITIES[code]["unit"]})',gridcolor:'rgba(30,45,74,0.35)',tickformat:'.2f',color:'#64748b',side:'right',range:[yMin,yMax],tickfont:{{size:9}}}},
      margin:{{l:8,r:85,t:18,b:65}},shapes:sh,showlegend:true,
      legend:{{x:0.01,y:0.99,bgcolor:'rgba(10,14,26,0.88)',bordercolor:'rgba(30,45,74,0.8)',borderwidth:1,font:{{size:8.5}}}},
      hovermode:'x unified'
    }},{{responsive:true,displayModeBar:false}});
  }}

  // Build Daily chart
  function buildChartDay_{code}(){{
    const x = DAILY_{code}.map(d=>d.d);
    const allY2 = DAILY_{code}.flatMap(d=>[d.h,d.l]);
    const yMin2 = Math.min(...allY2)*0.997;
    const yMax2 = Math.max(...allY2)*1.003;
    Plotly.newPlot('chartday_{code}',[
      {{type:'candlestick',x,open:DAILY_{code}.map(d=>d.o),high:DAILY_{code}.map(d=>d.h),low:DAILY_{code}.map(d=>d.l),close:DAILY_{code}.map(d=>d.c),
        increasing:{{line:{{color:'#26a69a',width:2.5}},fillcolor:'rgba(38,166,154,0.85)'}},
        decreasing:{{line:{{color:'#ef5350',width:2.5}},fillcolor:'rgba(239,83,80,0.85)'}},
        name:'{code} Daily',whiskerwidth:0.4}}
    ],{{
      paper_bgcolor:'#131929',plot_bgcolor:'#0f1525',
      font:{{family:'JetBrains Mono,monospace',color:'#94a3b8',size:10}},
      xaxis:{{gridcolor:'rgba(30,45,74,0.4)',color:'#64748b',rangeslider:{{visible:false}}}},
      yaxis:{{title:'Price',gridcolor:'rgba(30,45,74,0.35)',tickformat:'.2f',color:'#64748b',side:'right',range:[yMin2,yMax2]}},
      margin:{{l:8,r:85,t:18,b:40}},showlegend:false
    }},{{responsive:true,displayModeBar:false}});
  }}

  // Build Table
  function buildTable_{code}(){{
    const b = document.getElementById('dtbody_{code}');
    let prev = ANCHOR_{code};
    DAILY_{code}.forEach(d=>{{
      const chg = d.c - prev; prev = d.c;
      const col = chg>=0?'#4ade80':'#f87171';
      const s = chg>=0?'+':'';
      const tr = document.createElement('tr');
      tr.innerHTML = `<td style="font-weight:700">${{d.d}}</td><td style="color:#94a3b8">${{d.o.toFixed(2)}}</td><td style="color:#4ade80">${{d.h.toFixed(2)}}</td><td style="color:#f87171">${{d.l.toFixed(2)}}</td><td style="color:${{col}};font-weight:700">${{d.c.toFixed(2)}}</td><td style="color:${{col}};font-weight:700">${{s}}${{chg.toFixed(2)}}&cent;</td><td style="color:#fbbf24">${{(d.h-d.l).toFixed(2)}}&cent;</td><td><span class="sb ${{d.scl}}">${{d.sc}}</span></td><td style="color:#64748b;font-size:0.68rem">${{d.logic}}</td>`;
      b.appendChild(tr);
    }});
  }}

  // Build Factors
  function buildFactors_{code}(){{
    const c = document.getElementById('flist_{code}');
    FACTORS_{code}.forEach(f=>{{
      const pct = Math.abs(f.s/f.m*100).toFixed(0), bull = f.s>=0, col = bull?'#4ade80':'#f87171';
      const d = document.createElement('div'); d.className='fi';
      d.innerHTML=`<div class="fh"><span class="fn">${{f.n}}</span><span class="fs" style="color:${{col}}">${{(f.s>=0?'+':'')+f.s.toFixed(1)}}</span></div><div class="fb"><div class="fbi ${{bull?'fbu':'fbd'}}" style="width:${{pct}}%"></div></div>`;
      c.appendChild(d);
    }});
  }}

  // Register init (charts only built when tab is shown)
  window['_init_{code}'] = function(){{
    buildChart4h_{code}();
    buildChartDay_{code}();
    buildTable_{code}();
    buildFactors_{code}();
    window['_init_{code}'] = null; // run once
  }};
}})();
</script>
"""

def build_html(all_data):
    tabs_nav = ""
    tabs_content = ""
    first = True
    for code, info in COMMODITIES.items():
        if code not in all_data:
            continue
        active_cls = "tab-btn active" if first else "tab-btn"
        tabs_nav += f'<button class="{active_cls}" onclick="showTab(\'{code}\')" id="tbtn_{code}" style="--tc:{info["color"]}">{info["name"]}</button>\n'
        tabs_content += build_tab_script(code, all_data[code], all_data[code].get("meta", {}))
        first = False

    first_code = list(COMMODITIES.keys())[0]

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FUTURE CHART — ZC/ZW/ZS Multi-Commodity Simulation | Jun 15-19, 2026</title>
<meta name="description" content="AI-powered price simulation for CBOT ZC, ZW, ZS futures — Week of June 15-19, 2026.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@300;400;600;700;900&display=swap" rel="stylesheet">
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  :root {{
    --bg-primary:#0a0e1a;--bg-secondary:#0f1525;--bg-card:#131929;--bg-card2:#1a2138;
    --border:#1e2d4a;--accent-blue:#38bdf8;--accent-cyan:#22d3ee;--accent-green:#4ade80;
    --accent-red:#f87171;--accent-amber:#fbbf24;--accent-purple:#a78bfa;
    --text-primary:#e2e8f0;--text-muted:#64748b;--text-dim:#94a3b8;
  }}
  *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Inter',sans-serif;background:var(--bg-primary);color:var(--text-primary);min-height:100vh;overflow-x:hidden}}
  body::before{{content:'';position:fixed;inset:0;background-image:linear-gradient(rgba(56,189,248,0.025) 1px,transparent 1px),linear-gradient(90deg,rgba(56,189,248,0.025) 1px,transparent 1px);background-size:40px 40px;pointer-events:none;z-index:0}}
  header{{position:relative;z-index:10;padding:1.25rem 2rem;background:rgba(10,14,26,0.97);border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem}}
  .logo-wrap{{display:flex;align-items:center;gap:1rem}}
  .logo-icon{{width:42px;height:42px;background:linear-gradient(135deg,#38bdf8,#818cf8);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1.3rem;box-shadow:0 0 25px rgba(56,189,248,0.5);animation:pulse 3s ease-in-out infinite}}
  @keyframes pulse{{0%,100%{{box-shadow:0 0 20px rgba(56,189,248,0.4)}}50%{{box-shadow:0 0 45px rgba(56,189,248,0.85))}}}}
  h1{{font-size:1.35rem;font-weight:900;background:linear-gradient(90deg,#38bdf8,#818cf8,#22d3ee);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;letter-spacing:-0.02em}}
  .logo-sub{{font-size:0.68rem;color:var(--text-muted);font-family:'JetBrains Mono',monospace;letter-spacing:0.1em;text-transform:uppercase;margin-top:0.1rem}}
  .badges{{display:flex;gap:0.6rem;flex-wrap:wrap}}
  .badge{{display:flex;align-items:center;gap:0.35rem;padding:0.28rem 0.7rem;border-radius:999px;font-size:0.7rem;font-family:'JetBrains Mono',monospace;font-weight:600;border:1px solid}}
  .b-live{{background:rgba(74,222,128,0.1);border-color:rgba(74,222,128,0.4);color:#4ade80}}
  .b-mod{{background:rgba(56,189,248,0.1);border-color:rgba(56,189,248,0.4);color:#38bdf8}}
  .dot{{width:6px;height:6px;border-radius:50%;background:currentColor;animation:blink 1.4s ease-in-out infinite}}
  @keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:0.25}}}}
  
  /* TAB NAV */
  .tab-nav{{position:sticky;top:0;z-index:20;background:rgba(10,14,26,0.98);border-bottom:1px solid var(--border);padding:0 1.5rem;display:flex;gap:0.25rem;backdrop-filter:blur(12px)}}
  .tab-btn{{padding:0.85rem 1.5rem;font-size:0.82rem;font-weight:700;font-family:'Inter',sans-serif;cursor:pointer;border:none;background:transparent;color:var(--text-muted);border-bottom:2px solid transparent;transition:all 0.25s;white-space:nowrap}}
  .tab-btn:hover{{color:var(--text-primary);background:rgba(255,255,255,0.03)}}
  .tab-btn.active{{color:var(--tc,#38bdf8);border-bottom-color:var(--tc,#38bdf8)}}
  
  main{{position:relative;z-index:1;max-width:1600px;margin:0 auto;padding:1.5rem 1.5rem 3rem;display:flex;flex-direction:column;gap:1.5rem}}
  .tab-pane{{display:flex;flex-direction:column;gap:1.5rem}}
  .hero{{background:linear-gradient(135deg,rgba(56,189,248,0.07),rgba(129,140,248,0.05),rgba(34,211,238,0.03));border:1px solid var(--border);border-top:2px solid rgba(56,189,248,0.45);border-radius:16px;padding:1.5rem 2rem;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1.5rem;overflow:hidden;position:relative}}
  .hero::after{{content:'';position:absolute;top:-60%;right:-5%;width:350px;height:350px;background:radial-gradient(circle,rgba(56,189,248,0.07),transparent 70%);pointer-events:none}}
  .hero-info h2{{font-size:1.1rem;font-weight:700;margin-bottom:0.3rem}}
  .hero-info p{{font-size:0.75rem;color:var(--text-muted);font-family:'JetBrains Mono',monospace}}
  .metrics{{display:flex;gap:1.75rem;flex-wrap:wrap}}
  .metric{{text-align:center}}
  .mv{{font-family:'JetBrains Mono',monospace;font-size:1.4rem;font-weight:700;line-height:1;margin-bottom:0.2rem}}
  .ml{{font-size:0.62rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.1em}}
  .pos{{color:#4ade80}}.neg{{color:#f87171}}.neu{{color:#38bdf8}}.amb{{color:#fbbf24}}
  .card{{background:var(--bg-card);border:1px solid var(--border);border-radius:16px;overflow:hidden;box-shadow:0 0 25px rgba(56,189,248,0.08)}}
  .card-header{{padding:0.9rem 1.5rem;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:0.75rem;border-bottom:1px solid var(--border);background:linear-gradient(90deg,rgba(56,189,248,0.06),transparent)}}
  .ch-title{{font-size:0.85rem;font-weight:700;display:flex;align-items:center;gap:0.5rem}}
  .ch-sub{{font-size:0.67rem;color:var(--text-muted);font-family:'JetBrains Mono',monospace;margin-top:0.1rem}}
  .legend{{display:flex;gap:0.85rem;font-size:0.68rem;font-family:'JetBrains Mono',monospace;flex-wrap:wrap}}
  .li{{display:flex;align-items:center;gap:0.35rem}}
  .ld{{width:12px;height:3px;border-radius:2px}}
  .grid2{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1.25rem}}
  .panel{{background:var(--bg-card);border:1px solid var(--border);border-radius:14px;overflow:hidden;transition:border-color 0.3s,box-shadow 0.3s}}
  .panel:hover{{border-color:rgba(56,189,248,0.28);box-shadow:0 0 20px rgba(56,189,248,0.1)}}
  .ph{{padding:0.8rem 1.2rem;border-bottom:1px solid var(--border);font-size:0.73rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;display:flex;align-items:center;gap:0.45rem;color:var(--accent-blue);background:linear-gradient(90deg,rgba(56,189,248,0.07),transparent)}}
  .pb{{padding:1rem 1.2rem}}
  table{{width:100%;border-collapse:collapse;font-size:0.78rem}}
  thead th{{padding:0.5rem 0.7rem;text-align:left;font-family:'JetBrains Mono',monospace;font-size:0.63rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.08em;border-bottom:1px solid var(--border)}}
  tbody td{{padding:0.6rem 0.7rem;font-family:'JetBrains Mono',monospace;font-size:0.75rem;border-bottom:1px solid rgba(30,45,74,0.4)}}
  tbody tr:last-child td{{border-bottom:none}}
  tbody tr:hover td{{background:rgba(56,189,248,0.035)}}
  .sb{{font-size:0.63rem;padding:0.18rem 0.5rem;border-radius:4px;font-weight:600;letter-spacing:0.04em;border:1px solid}}
  .sj{{background:rgba(248,113,113,0.13);color:#fca5a5;border-color:rgba(248,113,113,0.3)}}
  .su{{background:rgba(74,222,128,0.11);color:#86efac;border-color:rgba(74,222,128,0.3)}}
  .sm{{background:rgba(56,189,248,0.11);color:#7dd3fc;border-color:rgba(56,189,248,0.3)}}
  .sc{{background:rgba(167,139,250,0.11);color:#c4b5fd;border-color:rgba(167,139,250,0.3)}}
  .sq{{background:rgba(251,191,36,0.11);color:#fde68a;border-color:rgba(251,191,36,0.3)}}
  .flist{{display:flex;flex-direction:column;gap:0.55rem}}
  .fi{{display:flex;flex-direction:column;gap:0.22rem}}
  .fh{{display:flex;justify-content:space-between;align-items:center}}
  .fn{{font-size:0.7rem;color:var(--text-dim)}}
  .fs{{font-family:'JetBrains Mono',monospace;font-size:0.73rem;font-weight:700}}
  .fb{{height:4px;background:rgba(255,255,255,0.06);border-radius:99px;overflow:hidden}}
  .fbi{{height:100%;border-radius:99px;transition:width 1.2s ease}}
  .fbu{{background:linear-gradient(90deg,#4ade80,#22d3ee)}}
  .fbd{{background:linear-gradient(90deg,#f87171,#fb923c)}}
  .conf-wrap{{display:flex;align-items:center;gap:0.85rem;padding:0.85rem;background:rgba(56,189,248,0.05);border:1px solid rgba(56,189,248,0.2);border-radius:10px;margin-bottom:0.85rem}}
  .cl{{font-size:0.68rem;color:var(--text-muted);min-width:75px;font-family:'JetBrains Mono',monospace}}
  .cb{{flex:1;height:7px;background:rgba(255,255,255,0.06);border-radius:99px;overflow:hidden}}
  .cbi{{height:100%;border-radius:99px}}
  .cv{{font-family:'JetBrains Mono',monospace;font-size:0.82rem;font-weight:700;min-width:36px;text-align:right}}
  .evl{{display:flex;flex-direction:column;gap:0.5rem}}
  .ev{{display:flex;gap:0.7rem;padding:0.55rem 0.7rem;border-radius:8px;background:rgba(255,255,255,0.02);border:1px solid var(--border);align-items:flex-start}}
  .ed{{font-family:'JetBrains Mono',monospace;font-size:0.68rem;font-weight:700;color:#fbbf24;min-width:60px;white-space:nowrap}}
  .et{{font-size:0.7rem;color:var(--text-dim);line-height:1.5}}
  .emaj{{border-color:rgba(248,113,113,0.28)!important;background:rgba(248,113,113,0.04)!important}}
  .emaj .ed{{color:#f87171}}
  .disclaim{{background:rgba(251,191,36,0.06);border:1px solid rgba(251,191,36,0.2);border-radius:12px;padding:1rem 1.5rem;font-size:0.7rem;color:#fde68a;line-height:1.75;text-align:center}}
  
  /* PHASE SCENARIO STRIP */
  .ph-strip{{background:var(--bg-card);border:1px solid var(--border);border-radius:16px;padding:1rem 1.5rem;box-shadow:0 0 20px rgba(56,189,248,0.06)}}
  .ph-strip-label{{font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;color:#a78bfa;margin-bottom:0.85rem;display:flex;align-items:center;gap:0.5rem}}
  .ph-strip-label::before{{content:'';flex:1;height:1px;background:linear-gradient(90deg,rgba(167,139,250,0.3),transparent)}}
  .ph-cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:0.75rem}}
  .ph-card{{background:var(--bg-card2);border:1px solid var(--border);border-top:2px solid;border-radius:12px;padding:0.85rem 1rem;display:flex;gap:0.65rem;align-items:flex-start;transition:all 0.25s}}
  .ph-card:hover{{transform:translateY(-2px);box-shadow:0 6px 20px rgba(0,0,0,0.3);border-color:rgba(255,255,255,0.12)}}
  .ph-icon{{font-size:1.1rem;flex-shrink:0;margin-top:0.05rem}}
  .ph-body{{flex:1;min-width:0}}
  .ph-title{{font-size:0.68rem;font-weight:700;font-family:'JetBrains Mono',monospace;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:0.35rem;line-height:1.3}}
  .ph-desc{{font-size:0.7rem;color:var(--text-muted);line-height:1.55}}
  
  @media(max-width:768px){{header{{padding:1rem}}main{{padding:1rem;gap:1rem}}.hero{{padding:1rem}}.metrics{{gap:1rem}}.mv{{font-size:1.1rem}}.grid2{{grid-template-columns:1fr}}.tab-btn{{padding:0.6rem 0.9rem;font-size:0.75rem}}.ph-cards{{grid-template-columns:1fr 1fr}}}}
</style>
</head>
<body>
<header>
  <div class="logo-wrap">
    <div class="logo-icon">&#128200;</div>
    <div>
      <h1>FUTURE CHART</h1>
      <div class="logo-sub">ZC · ZW · ZS &middot; AI Price Simulation &middot; CBOT V3+V4+ICT+MuaVu</div>
    </div>
  </div>
  <div class="badges">
    <span class="badge b-live"><span class="dot"></span>AI ACTIVE</span>
    <span class="badge b-mod">MODEL v2.0</span>
    <span class="badge b-mod">Tuần 15-19/06/2026</span>
  </div>
</header>

<div class="tab-nav">
{tabs_nav}</div>

<main id="main-content">
{tabs_content}

  <div class="disclaim">
    &#9888;&#65039; <strong>KHUYẾN CÁO QUAN TRỌNG:</strong> Đây là mô hình <em>giả lập AI</em> dựa trên phân tích kỹ thuật (V3 Pro, V4 ICT), dữ liệu mùa vụ và yếu tố vĩ mô.
    <strong>KHÔNG phải khuyến nghị giao dịch.</strong> Thị trường thực tế có thể khác biệt hoàn toàn. Mục đích duy nhất là <em>kiểm định độ chính xác của hệ thống phân tích</em>.
  </div>
</main>

<script>
// Tab switching
function showTab(code) {{
  document.querySelectorAll('.tab-pane').forEach(p=>p.style.display='none');
  document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
  document.getElementById('tab_'+code).style.display='flex';
  document.getElementById('tbtn_'+code).classList.add('active');
  // Lazy init charts
  const fn = window['_init_'+code];
  if(fn) fn();
}}
// Init first tab
showTab('{first_code}');
</script>
</body>
</html>"""

def main():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        all_data = json.load(f)
    html = build_html(all_data)
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Successfully generated {HTML_PATH} with ZC/ZW/ZS tabs!")

if __name__ == "__main__":
    main()
