/**
 * ICT Smart Money Dashboard - Main Application Controller
 * Handles UI interactions, analysis panel, tab switching, and PNG export.
 */
(function () {
  'use strict';

  /* ── state ── */
  let currentSymbol = 'ZC';
  let analysisResults = {};
  let renderer = null;

  /* ── DOM refs (set in init) ── */
  let mainCanvas, rsiCanvas, tabBtns, layerToggles;
  let panelEl, exportBtn, symbolTitle, symbolSubtitle;

  /* ── helpers ── */
  const $ = (s, p) => (p || document).querySelector(s);
  const $$ = (s, p) => [...(p || document).querySelectorAll(s)];

  /* ================================================================
     Analysis Panel
     ================================================================ */
  function renderAnalysisPanel(symbol) {
    const a = analysisResults[symbol];
    if (!a || !a.summary) {
      panelEl.innerHTML = '<p class="panel-empty">No data</p>';
      return;
    }
    const s = a.summary;

    const trendIcon = s.currentTrend === 'bullish' ? '↗' : s.currentTrend === 'bearish' ? '↘' : '→';
    const trendClass = s.currentTrend === 'bullish' ? 'bull' : s.currentTrend === 'bearish' ? 'bear' : 'neutral';

    const recMap = {
      BUY_ZONE: { label: 'VÙNG MUA', cls: 'rec-buy', icon: '🟢' },
      ACCUMULATE: { label: 'TÍCH LŨY', cls: 'rec-acc', icon: '🔵' },
      SELL_ZONE: { label: 'VÙNG BÁN', cls: 'rec-sell', icon: '🔴' },
      WAIT: { label: 'CHỜ ĐỢI', cls: 'rec-wait', icon: '⏳' },
    };
    const rec = recMap[s.recommendation] || recMap.WAIT;

    const stars = (score, max) => {
      const filled = Math.round((score / max) * 5);
      return '★'.repeat(filled) + '☆'.repeat(5 - filled);
    };

    // Recent MSS events (last 3)
    const recentMSS = a.mssEvents.slice(-3).reverse();
    const mssHTML = recentMSS.length
      ? recentMSS.map(m => `
        <div class="event-row ${m.type}">
          <span class="event-icon">${m.type === 'bullish' ? '▲' : '▼'}</span>
          <span class="event-label">${m.type === 'bullish' ? 'Bullish' : 'Bearish'} MSS</span>
          <span class="event-price">${m.price.toFixed(2)}</span>
          <span class="event-time">${m.time.slice(5, 16)}</span>
        </div>`).join('')
      : '<p class="no-events">Không có MSS gần đây</p>';

    // Unfilled FVGs (last 5)
    const unfilledFVG = a.fvgZones.filter(f => !f.filled).slice(-5).reverse();
    const fvgHTML = unfilledFVG.length
      ? unfilledFVG.map(f => `
        <div class="event-row ${f.type}">
          <span class="event-icon">${f.type === 'bullish' ? '▧' : '▨'}</span>
          <span class="event-label">${f.type === 'bullish' ? 'Bull' : 'Bear'} FVG</span>
          <span class="event-price">${f.bottom.toFixed(1)} - ${f.top.toFixed(1)}</span>
        </div>`).join('')
      : '<p class="no-events">Không có FVG chưa lấp</p>';

    // Active Order Blocks (last 3)
    const activeOB = a.orderBlocks.filter(o => !o.mitigated).slice(-3).reverse();
    const obHTML = activeOB.length
      ? activeOB.map(o => `
        <div class="event-row ${o.type}">
          <span class="event-icon">${o.type === 'bullish' ? '🟩' : '🟥'}</span>
          <span class="event-label">${o.type === 'bullish' ? 'Demand' : 'Supply'} OB</span>
          <span class="event-price">${o.bottom.toFixed(1)} - ${o.top.toFixed(1)}</span>
        </div>`).join('')
      : '<p class="no-events">Không có OB active</p>';

    // Bottom zones
    const latestBottom = a.bottomZones.length ? a.bottomZones[a.bottomZones.length - 1] : null;
    const bottomHTML = latestBottom
      ? `<div class="score-display ${latestBottom.level}">
           <span class="score-stars">${stars(latestBottom.score, latestBottom.maxScore)}</span>
           <span class="score-label">${latestBottom.level.toUpperCase()}</span>
         </div>
         <ul class="factor-list">${latestBottom.factors.map(f => `<li>${f}</li>`).join('')}</ul>`
      : '<p class="no-events">Chưa phát hiện vùng đáy rõ ràng</p>';

    // Growth momentum
    const latestGrowth = a.growthSignals.length ? a.growthSignals[a.growthSignals.length - 1] : null;
    const growthHTML = latestGrowth
      ? `<div class="score-display ${latestGrowth.level}">
           <span class="score-stars">${stars(latestGrowth.score, 8)}</span>
           <span class="score-label">${latestGrowth.level.toUpperCase()}</span>
         </div>
         <ul class="factor-list">${latestGrowth.factors.map(f => `<li>${f}</li>`).join('')}</ul>`
      : '<p class="no-events">Chưa có tín hiệu đà tăng trưởng</p>';

    // Trade Setup
    const setup = s.tradeSetup;
    const setupHTML = setup
      ? `
        <div class="panel-section setup-section">
          <h3 class="section-title">🎯 Đề Xuất Lệnh (Win Rate: ${setup.winRate})</h3>
          <div class="setup-card ${setup.type.toLowerCase()}">
            <div class="setup-header">
              <span class="setup-type">${setup.type}</span>
              <span class="setup-reason">${setup.reason}</span>
            </div>
            <div class="setup-details">
              <div class="setup-row"><span>Entry Zone:</span> <strong>${setup.entryRange}</strong></div>
              <div class="setup-row"><span>Stop Loss:</span> <strong class="sl-text">${setup.stopLoss}</strong></div>
              <div class="setup-row"><span>Take Profit:</span> <strong class="tp-text">${setup.takeProfit}</strong></div>
            </div>
          </div>
        </div>
      `
      : `<div class="panel-section setup-section">
           <h3 class="section-title">🎯 Đề Xuất Lệnh</h3>
           <p class="no-events">Chưa có setup với Win Rate > 65% lúc này.</p>
         </div>`;

    // Current price info
    const candles = CHART_DATA[symbol];
    const last = candles[candles.length - 1];

    panelEl.innerHTML = `
      <!-- Current Price -->
      <div class="panel-section price-section">
        <div class="current-price">
          <span class="price-value ${trendClass}">${last.close.toFixed(2)}</span>
          <span class="price-change ${trendClass}">${trendIcon} ${s.currentTrend.toUpperCase()}</span>
        </div>
        <div class="price-meta">
          <span>EMA21: ${last.ema21.toFixed(2)}</span>
          <span>EMA50: ${last.ema50.toFixed(2)}</span>
          <span>RSI: ${last.rsi.toFixed(1)}</span>
          <span>ATR: ${last.atr.toFixed(2)}</span>
        </div>
      </div>

      <!-- Recommendation -->
      <div class="panel-section rec-section">
        <div class="rec-badge ${rec.cls}">
          <span class="rec-icon">${rec.icon}</span>
          <span class="rec-text">${rec.label}</span>
        </div>
      </div>
      
      ${setupHTML}

      <!-- MSS Events -->
      <div class="panel-section">
        <h3 class="section-title">⚡ Market Structure Shift</h3>
        <div class="event-list">${mssHTML}</div>
      </div>

      <!-- FVG Zones -->
      <div class="panel-section">
        <h3 class="section-title">📐 Fair Value Gaps (Unfilled: ${s.unfilledFVGs})</h3>
        <div class="event-list">${fvgHTML}</div>
      </div>

      <!-- Order Blocks -->
      <div class="panel-section">
        <h3 class="section-title">🧱 Order Blocks (Active: ${s.activeOrderBlocks})</h3>
        <div class="event-list">${obHTML}</div>
      </div>

      <!-- Bottom Zone -->
      <div class="panel-section">
        <h3 class="section-title">🎯 Vùng Đáy Detection</h3>
        ${bottomHTML}
      </div>

      <!-- Growth Momentum -->
      <div class="panel-section">
        <h3 class="section-title">🚀 Đà Tăng Trưởng</h3>
        ${growthHTML}
      </div>

      <!-- Stats -->
      <div class="panel-section stats-section">
        <h3 class="section-title">📊 Thống kê</h3>
        <div class="stat-grid">
          <div class="stat"><span class="stat-val">${a.swingPoints.filter(s=>s.type==='high').length}</span><span class="stat-lbl">Swing High</span></div>
          <div class="stat"><span class="stat-val">${a.swingPoints.filter(s=>s.type==='low').length}</span><span class="stat-lbl">Swing Low</span></div>
          <div class="stat"><span class="stat-val">${a.mssEvents.length}</span><span class="stat-lbl">MSS Total</span></div>
          <div class="stat"><span class="stat-val">${a.fvgZones.length}</span><span class="stat-lbl">FVG Total</span></div>
          <div class="stat"><span class="stat-val">${a.orderBlocks.length}</span><span class="stat-lbl">OB Total</span></div>
          <div class="stat"><span class="stat-val">${candles.length}</span><span class="stat-lbl">Candles</span></div>
        </div>
      </div>
    `;
  }

  /* ================================================================
     Tab Switching
     ================================================================ */
  function switchTab(symbol) {
    currentSymbol = symbol;
    tabBtns.forEach(btn => {
      btn.classList.toggle('active', btn.dataset.symbol === symbol);
    });

    symbolTitle.textContent = CHART_LABELS[symbol] || symbol;
    const candles = CHART_DATA[symbol];
    if (candles && candles.length) {
      symbolSubtitle.textContent = `${candles[0].time.slice(0,10)} → ${candles[candles.length-1].time.slice(0,10)} | ${candles.length} nến H1`;
    }

    if (renderer && analysisResults[symbol]) {
      renderer.setData(candles, analysisResults[symbol]);
      renderer.render();
    }
    renderAnalysisPanel(symbol);
  }

  /* ================================================================
     Layer Toggles
     ================================================================ */
  function setupLayerToggles() {
    layerToggles.forEach(toggle => {
      toggle.addEventListener('change', () => {
        if (renderer) {
          renderer.toggleLayer(toggle.dataset.layer, toggle.checked);
          renderer.render();
        }
      });
    });
  }

  /* ================================================================
     Export PNG
     ================================================================ */
  function handleExport() {
    if (!renderer) return;
    const dataUrl = renderer.exportPNG(CHART_LABELS[currentSymbol] || currentSymbol);
    const link = document.createElement('a');
    link.download = `ICT_${currentSymbol}_${new Date().toISOString().slice(0,10)}.png`;
    link.href = dataUrl;
    link.click();
  }

  /* ================================================================
     Resize Handler
     ================================================================ */
  function handleResize() {
    if (!renderer) return;
    const container = $('#chart-container');
    if (!container) return;
    const rect = container.getBoundingClientRect();
    mainCanvas.width = rect.width;
    mainCanvas.height = rect.height * 0.75;
    rsiCanvas.width = rect.width;
    rsiCanvas.height = rect.height * 0.25;
    renderer.render();
  }

  /* ================================================================
     Tooltip
     ================================================================ */
  function setupTooltip() {
    const tooltip = $('#tooltip');
    if (!tooltip || !mainCanvas) return;

    mainCanvas.addEventListener('mousemove', (e) => {
      if (!renderer) return;
      const rect = mainCanvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const info = renderer.getMouseCandle(x, y);
      if (info && info.candle) {
        const c = info.candle;
        const ictInfo = info.ictEvents || [];
        tooltip.style.display = 'block';
        tooltip.style.left = (e.clientX + 15) + 'px';
        tooltip.style.top = (e.clientY - 10) + 'px';
        // Keep tooltip in viewport
        const tr = tooltip.getBoundingClientRect();
        if (tr.right > window.innerWidth) {
          tooltip.style.left = (e.clientX - tr.width - 15) + 'px';
        }
        if (tr.bottom > window.innerHeight) {
          tooltip.style.top = (e.clientY - tr.height - 10) + 'px';
        }

        const changePercent = ((c.close - c.open) / c.open * 100).toFixed(2);
        const changeSign = c.close >= c.open ? '+' : '';
        const changeClass = c.close >= c.open ? 'bull' : 'bear';

        let eventsHTML = '';
        if (ictInfo.length > 0) {
          eventsHTML = `<div class="tooltip-events">${ictInfo.map(e => `<span class="tooltip-event ${e.type}">${e.label}</span>`).join('')}</div>`;
        }

        tooltip.innerHTML = `
          <div class="tooltip-header">${c.time}</div>
          <div class="tooltip-ohlc">
            <span>O: ${c.open.toFixed(2)}</span>
            <span>H: ${c.high.toFixed(2)}</span>
            <span>L: ${c.low.toFixed(2)}</span>
            <span class="${changeClass}">C: ${c.close.toFixed(2)} (${changeSign}${changePercent}%)</span>
          </div>
          <div class="tooltip-indicators">
            <span>EMA21: ${c.ema21.toFixed(2)}</span>
            <span>EMA50: ${c.ema50.toFixed(2)}</span>
            <span>RSI: ${c.rsi.toFixed(1)}</span>
            <span>ATR: ${c.atr.toFixed(2)}</span>
          </div>
          ${eventsHTML}
        `;
      } else {
        tooltip.style.display = 'none';
      }
    });

    mainCanvas.addEventListener('mouseleave', () => {
      tooltip.style.display = 'none';
    });
  }

  /* ================================================================
     Init
     ================================================================ */
  function init() {
    console.log('[ICT Dashboard] Initializing...');

    // DOM refs
    mainCanvas = $('#main-canvas');
    rsiCanvas = $('#rsi-canvas');
    tabBtns = $$('.sym-btn');
    layerToggles = $$('.layer-toggle');
    panelEl = $('#analysis-panel');
    exportBtn = $('#export-btn');
    symbolTitle = $('#symbol-title');
    symbolSubtitle = $('#symbol-subtitle');

    if (!mainCanvas || !rsiCanvas) {
      console.error('[ICT Dashboard] Canvas elements not found!');
      return;
    }

    // Run ICT analysis for all symbols
    console.log('[ICT Dashboard] Running ICT analysis...');
    for (const symbol of Object.keys(CHART_DATA)) {
      const candles = CHART_DATA[symbol];
      if (candles && candles.length > 0) {
        console.log(`  Analyzing ${symbol}: ${candles.length} candles`);
        analysisResults[symbol] = ICTEngine.analyze(candles);
        const s = analysisResults[symbol].summary;
        console.log(`  ${symbol} → Trend: ${s.currentTrend}, MSS: ${analysisResults[symbol].mssEvents.length}, FVG: ${analysisResults[symbol].fvgZones.length}, OB: ${analysisResults[symbol].orderBlocks.length}`);
      }
    }

    // Setup chart renderer
    const container = $('#chart-container');
    const rect = container.getBoundingClientRect();
    mainCanvas.width = rect.width;
    mainCanvas.height = rect.height * 0.75;
    rsiCanvas.width = rect.width;
    rsiCanvas.height = rect.height * 0.25;

    renderer = new ChartRenderer(mainCanvas, rsiCanvas, { theme: 'dark' });

    // Tab switching
    tabBtns.forEach(btn => {
      btn.addEventListener('click', () => switchTab(btn.dataset.symbol));
    });

    // Layer toggles
    setupLayerToggles();

    // Export
    if (exportBtn) exportBtn.addEventListener('click', handleExport);

    // Tooltip
    setupTooltip();

    // Resize
    window.addEventListener('resize', () => {
      clearTimeout(window._resizeTimer);
      window._resizeTimer = setTimeout(handleResize, 150);
    });

    // Initial render
    switchTab('ZC');

    console.log('[ICT Dashboard] Ready!');
    window.loadSymbol = switchTab;
  }

  // Start when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
