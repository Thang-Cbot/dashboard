/**
 * ChartRenderer - HTML5 Canvas Candlestick Chart with ICT Overlays
 * 
 * Renders financial candlestick data with ICT (Inner Circle Trader) analysis overlays
 * including FVG zones, Order Blocks, MSS markers, Swing Points, Bottom Zones, 
 * Growth Signals, EMA lines, and RSI sub-chart.
 *
 * Usage:
 *   const renderer = new ChartRenderer(mainCanvas, rsiCanvas, { theme: 'dark' });
 *   renderer.setData(candles, analysis);
 *   renderer.render();
 *
 * No ES modules - exposed as window.ChartRenderer
 */
(function () {
  'use strict';

  // ─────────────────────────────────────────────────
  // Color Theme
  // ─────────────────────────────────────────────────
  var COLORS = {
    bg:             '#0a0e17',
    grid:           '#1a2035',
    gridText:       '#4a5568',
    bullish:        '#00dc82',
    bearish:        '#ff4757',
    ema21:          '#00d2ff',
    ema50:          '#ff9f43',
    fvgBull:        'rgba(0,220,130,0.12)',
    fvgBear:        'rgba(255,71,87,0.12)',
    fvgBullBorder:  'rgba(0,220,130,0.45)',
    fvgBearBorder:  'rgba(255,71,87,0.45)',
    obBull:         'rgba(255,193,7,0.15)',
    obBear:         'rgba(156,39,176,0.15)',
    obBullBorder:   'rgba(255,193,7,0.6)',
    obBearBorder:   'rgba(156,39,176,0.6)',
    mssBull:        '#ffd700',
    mssBear:        '#ff00ff',
    crosshair:      'rgba(255,255,255,0.3)',
    tooltipBg:      'rgba(15,20,35,0.95)',
    tooltipBorder:  'rgba(255,255,255,0.15)',
    tooltipText:    '#e2e8f0',
    tooltipLabel:   '#718096',
    rsiLine:        '#00d2ff',
    rsiOverbought:  'rgba(255,71,87,0.1)',
    rsiOversold:    'rgba(0,220,130,0.1)',
    rsi70Line:      'rgba(255,71,87,0.5)',
    rsi30Line:      'rgba(0,220,130,0.5)',
    rsi50Line:      'rgba(255,255,255,0.1)',
    bottomGlow:     'rgba(0,220,130,0.08)',
    bottomStar:     '#00dc82',
    growthArrow:    '#ffd700',
    wickBullish:    '#00dc82',
    wickBearish:    '#ff4757',
    swingHigh:      '#ff4757',
    swingLow:       '#00dc82',
  };

  // ─────────────────────────────────────────────────
  // Layout Constants
  // ─────────────────────────────────────────────────
  var PADDING        = 10;
  var Y_AXIS_WIDTH   = 70;   // right-side price labels
  var X_AXIS_HEIGHT  = 30;   // bottom time labels
  var CANDLE_GAP     = 0.2;  // fraction of candle width used as gap
  var MIN_CANDLES    = 10;
  var MAX_CANDLES    = 500;
  var TOOLTIP_W      = 240;
  var TOOLTIP_LINE_H = 18;
  var Y_PAD_FACTOR   = 0.05; // 5% vertical padding

  // ─────────────────────────────────────────────────
  // Utility Helpers
  // ─────────────────────────────────────────────────

  /** Clamp value between min and max */
  function clamp(val, min, max) {
    return Math.max(min, Math.min(max, val));
  }

  /** Format a number to a sensible price string */
  function formatPrice(p) {
    if (p == null || isNaN(p)) return '—';
    if (Math.abs(p) >= 1000)  return p.toFixed(2);
    if (Math.abs(p) >= 1)     return p.toFixed(4);
    if (Math.abs(p) >= 0.01)  return p.toFixed(6);
    return p.toFixed(8);
  }

  /** Format timestamp to readable date+hour label */
  function formatTime(ts) {
    if (!ts) return '';
    var d = (ts instanceof Date) ? ts : new Date(ts);
    if (isNaN(d.getTime())) return String(ts);
    var mon = ('0' + (d.getMonth() + 1)).slice(-2);
    var day = ('0' + d.getDate()).slice(-2);
    var hrs = ('0' + d.getHours()).slice(-2);
    var min = ('0' + d.getMinutes()).slice(-2);
    return mon + '/' + day + ' ' + hrs + ':' + min;
  }

  /** Format timestamp for tooltip (more detail) */
  function formatTimeFull(ts) {
    if (!ts) return '';
    var d = (ts instanceof Date) ? ts : new Date(ts);
    if (isNaN(d.getTime())) return String(ts);
    var y   = d.getFullYear();
    var mon = ('0' + (d.getMonth() + 1)).slice(-2);
    var day = ('0' + d.getDate()).slice(-2);
    var hrs = ('0' + d.getHours()).slice(-2);
    var min = ('0' + d.getMinutes()).slice(-2);
    return y + '-' + mon + '-' + day + ' ' + hrs + ':' + min;
  }

  /** Compute nice grid step for a given range and desired ~N divisions */
  function niceStep(range, targetDivisions) {
    if (range <= 0 || !isFinite(range)) return 1;
    var rough = range / targetDivisions;
    var pow10 = Math.pow(10, Math.floor(Math.log10(rough)));
    var frac  = rough / pow10;
    var nice;
    if (frac <= 1.5)      nice = 1;
    else if (frac <= 3.5)  nice = 2;
    else if (frac <= 7.5)  nice = 5;
    else                    nice = 10;
    return nice * pow10;
  }

  /** Device pixel ratio helper */
  function getDPR() {
    return window.devicePixelRatio || 1;
  }

  // ─────────────────────────────────────────────────
  // ChartRenderer Class
  // ─────────────────────────────────────────────────

  /**
   * @constructor
   * @param {HTMLCanvasElement} mainCanvas - Canvas for the main price chart
   * @param {HTMLCanvasElement} rsiCanvas  - Canvas for the RSI sub-chart
   * @param {Object}           options     - { theme: 'dark' }
   */
  function ChartRenderer(mainCanvas, rsiCanvas, options) {
    if (!mainCanvas || !mainCanvas.getContext) {
      throw new Error('ChartRenderer: mainCanvas must be an HTMLCanvasElement');
    }
    options = options || {};

    this.mainCanvas = mainCanvas;
    this.rsiCanvas  = rsiCanvas || null;
    this.mainCtx    = mainCanvas.getContext('2d');
    this.rsiCtx     = rsiCanvas ? rsiCanvas.getContext('2d') : null;

    // Data
    this.candles    = [];
    this.analysis   = null;

    // Visible range (indices into candles array)
    this.startIdx   = 0;
    this.endIdx     = 0;

    // Layer visibility
    this.layers = {
      ema:    true,
      swing:  true,
      fvg:    true,
      ob:     true,
      mss:    true,
      bottom: true,
      growth: true,
    };

    // Interaction state
    this._mouseX      = -1;
    this._mouseY      = -1;
    this._isDragging   = false;
    this._dragStartX   = 0;
    this._dragStartIdx = 0;
    this._dirty        = true;
    this._rafId        = null;

    // Cached chart area dimensions (computed on each render)
    this._chartArea = { x: 0, y: 0, w: 0, h: 0 };
    this._rsiArea   = { x: 0, y: 0, w: 0, h: 0 };
    this._priceMin  = 0;
    this._priceMax  = 1;

    // Bind event handlers
    this._onMouseMove  = this._handleMouseMove.bind(this);
    this._onMouseDown  = this._handleMouseDown.bind(this);
    this._onMouseUp    = this._handleMouseUp.bind(this);
    this._onMouseLeave = this._handleMouseLeave.bind(this);
    this._onWheel      = this._handleWheel.bind(this);
    this._onResize     = this._handleResize.bind(this);

    // Attach events
    this.mainCanvas.addEventListener('mousemove',  this._onMouseMove);
    this.mainCanvas.addEventListener('mousedown',  this._onMouseDown);
    this.mainCanvas.addEventListener('mouseup',    this._onMouseUp);
    this.mainCanvas.addEventListener('mouseleave', this._onMouseLeave);
    this.mainCanvas.addEventListener('wheel',      this._onWheel, { passive: false });

    if (this.rsiCanvas) {
      this.rsiCanvas.addEventListener('mousemove',  this._onMouseMove);
      this.rsiCanvas.addEventListener('mousedown',  this._onMouseDown);
      this.rsiCanvas.addEventListener('mouseup',    this._onMouseUp);
      this.rsiCanvas.addEventListener('mouseleave', this._onMouseLeave);
      this.rsiCanvas.addEventListener('wheel',      this._onWheel, { passive: false });
    }

    window.addEventListener('resize', this._onResize);

    // Initial sizing
    this._syncCanvasSize();

    // Start render loop
    this._startRenderLoop();
  }

  // ─── Public API ──────────────────────────────────

  /**
   * Set candle data and ICT analysis results.
   * @param {Array}  candles  - [{ time, open, high, low, close, ema21, ema50, rsi, atr }, ...]
   * @param {Object} analysis - Result from ICTEngine.analyze()
   */
  ChartRenderer.prototype.setData = function (candles, analysis) {
    this.candles  = candles || [];
    this.analysis = analysis || null;

    // Default visible range: last ~80 candles or all if fewer
    var total = this.candles.length;
    if (total > 0) {
      this.endIdx   = total - 1;
      this.startIdx = Math.max(0, total - 80);
    } else {
      this.startIdx = 0;
      this.endIdx   = 0;
    }
    this._markDirty();
  };

  /**
   * Set visible candle range explicitly.
   * @param {number} startIdx
   * @param {number} endIdx
   */
  ChartRenderer.prototype.setVisibleRange = function (startIdx, endIdx) {
    var total = this.candles.length;
    if (total === 0) return;
    this.startIdx = clamp(Math.floor(startIdx), 0, total - 1);
    this.endIdx   = clamp(Math.floor(endIdx), this.startIdx, total - 1);
    if (this.endIdx - this.startIdx < MIN_CANDLES - 1) {
      this.endIdx = Math.min(this.startIdx + MIN_CANDLES - 1, total - 1);
    }
    this._markDirty();
  };

  /**
   * Toggle an overlay layer on or off.
   * @param {string}  layerName - 'ema','swing','fvg','ob','mss','bottom','growth'
   * @param {boolean} visible
   */
  ChartRenderer.prototype.toggleLayer = function (layerName, visible) {
    if (this.layers.hasOwnProperty(layerName)) {
      this.layers[layerName] = !!visible;
      this._markDirty();
    }
  };

  /**
   * Force a render on the next animation frame.
   */
  ChartRenderer.prototype.render = function () {
    this._markDirty();
  };

  /**
   * Export combined main + RSI chart as a PNG data URL.
   * @returns {string} data URL
   */
  ChartRenderer.prototype.exportPNG = function () {
    var mainW = this.mainCanvas.width;
    var mainH = this.mainCanvas.height;
    var rsiH  = this.rsiCanvas ? this.rsiCanvas.height : 0;
    var rsiW  = this.rsiCanvas ? this.rsiCanvas.width : 0;
    var titleH = 40;

    var totalW = Math.max(mainW, rsiW);
    var totalH = titleH + mainH + rsiH;

    var exportCanvas = document.createElement('canvas');
    exportCanvas.width  = totalW;
    exportCanvas.height = totalH;
    var ctx = exportCanvas.getContext('2d');

    // Dark background
    ctx.fillStyle = COLORS.bg;
    ctx.fillRect(0, 0, totalW, totalH);

    // Title bar
    ctx.fillStyle = '#e2e8f0';
    ctx.font      = 'bold 16px monospace';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    var titleText = 'Antigravity ICT Chart';
    if (this.candles.length > 0) {
      var first = this.candles[this.startIdx];
      var last  = this.candles[this.endIdx];
      titleText += '  |  ' + formatTimeFull(first.time) + ' → ' + formatTimeFull(last.time);
    }
    ctx.fillText(titleText, 12, titleH / 2);

    // Draw main canvas
    ctx.drawImage(this.mainCanvas, 0, titleH);

    // Draw RSI canvas
    if (this.rsiCanvas) {
      ctx.drawImage(this.rsiCanvas, 0, titleH + mainH);
    }

    return exportCanvas.toDataURL('image/png');
  };

  /**
   * Dispose event listeners and stop render loop.
   */
  ChartRenderer.prototype.destroy = function () {
    if (this._rafId) {
      cancelAnimationFrame(this._rafId);
      this._rafId = null;
    }
    this.mainCanvas.removeEventListener('mousemove',  this._onMouseMove);
    this.mainCanvas.removeEventListener('mousedown',  this._onMouseDown);
    this.mainCanvas.removeEventListener('mouseup',    this._onMouseUp);
    this.mainCanvas.removeEventListener('mouseleave', this._onMouseLeave);
    this.mainCanvas.removeEventListener('wheel',      this._onWheel);

    if (this.rsiCanvas) {
      this.rsiCanvas.removeEventListener('mousemove',  this._onMouseMove);
      this.rsiCanvas.removeEventListener('mousedown',  this._onMouseDown);
      this.rsiCanvas.removeEventListener('mouseup',    this._onMouseUp);
      this.rsiCanvas.removeEventListener('mouseleave', this._onMouseLeave);
      this.rsiCanvas.removeEventListener('wheel',      this._onWheel);
    }
    window.removeEventListener('resize', this._onResize);
  };

  // ─── Internal: Canvas Sizing ────────────────────

  ChartRenderer.prototype._syncCanvasSize = function () {
    var dpr = getDPR();

    // Main canvas
    var rect = this.mainCanvas.getBoundingClientRect();
    this.mainCanvas.width  = Math.round(rect.width * dpr);
    this.mainCanvas.height = Math.round(rect.height * dpr);
    this.mainCtx.setTransform(dpr, 0, 0, dpr, 0, 0);

    // Store CSS-pixel dimensions for layout math
    this._mainW = rect.width;
    this._mainH = rect.height;

    // RSI canvas
    if (this.rsiCanvas) {
      var rRect = this.rsiCanvas.getBoundingClientRect();
      this.rsiCanvas.width  = Math.round(rRect.width * dpr);
      this.rsiCanvas.height = Math.round(rRect.height * dpr);
      this.rsiCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
      this._rsiW = rRect.width;
      this._rsiH = rRect.height;
    } else {
      this._rsiW = 0;
      this._rsiH = 0;
    }
  };

  // ─── Internal: Render Loop ──────────────────────

  ChartRenderer.prototype._markDirty = function () {
    this._dirty = true;
  };

  ChartRenderer.prototype._startRenderLoop = function () {
    var self = this;
    function loop() {
      if (self._dirty) {
        self._dirty = false;
        self._renderAll();
      }
      self._rafId = requestAnimationFrame(loop);
    }
    self._rafId = requestAnimationFrame(loop);
  };

  // ─── Internal: Full Render Pipeline ─────────────

  ChartRenderer.prototype._renderAll = function () {
    this._syncCanvasSize();
    this._computeChartArea();
    this._computePriceRange();
    this._renderMainChart();
    this._renderRSIChart();
  };

  /** Compute the drawable chart area (excluding axis labels and padding) */
  ChartRenderer.prototype._computeChartArea = function () {
    this._chartArea = {
      x: PADDING,
      y: PADDING,
      w: this._mainW - PADDING * 2 - Y_AXIS_WIDTH,
      h: this._mainH - PADDING * 2 - X_AXIS_HEIGHT,
    };

    if (this.rsiCanvas) {
      this._rsiArea = {
        x: PADDING,
        y: PADDING,
        w: this._rsiW - PADDING * 2 - Y_AXIS_WIDTH,
        h: this._rsiH - PADDING * 2 - X_AXIS_HEIGHT,
      };
    }
  };

  /** Compute price min/max for visible candles with padding */
  ChartRenderer.prototype._computePriceRange = function () {
    var candles = this.candles;
    if (candles.length === 0) {
      this._priceMin = 0;
      this._priceMax = 1;
      return;
    }

    var lo = Infinity, hi = -Infinity;
    for (var i = this.startIdx; i <= this.endIdx && i < candles.length; i++) {
      var c = candles[i];
      if (c.low  < lo) lo = c.low;
      if (c.high > hi) hi = c.high;
      // Include EMA values in range so they aren't clipped
      if (c.ema21 != null && isFinite(c.ema21)) {
        if (c.ema21 < lo) lo = c.ema21;
        if (c.ema21 > hi) hi = c.ema21;
      }
      if (c.ema50 != null && isFinite(c.ema50)) {
        if (c.ema50 < lo) lo = c.ema50;
        if (c.ema50 > hi) hi = c.ema50;
      }
    }

    // Include FVG and OB zones in range if visible
    if (this.analysis) {
      if (this.layers.fvg && this.analysis.fvgZones) {
        this._expandRangeForZones(this.analysis.fvgZones, lo, hi, function (r) { lo = r[0]; hi = r[1]; });
      }
      if (this.layers.ob && this.analysis.orderBlocks) {
        this._expandRangeForZones(this.analysis.orderBlocks, lo, hi, function (r) { lo = r[0]; hi = r[1]; });
      }
    }

    if (!isFinite(lo) || !isFinite(hi) || lo === hi) {
      lo = lo === Infinity ? 0 : lo;
      hi = hi === -Infinity ? 1 : hi;
      if (lo === hi) { lo -= 1; hi += 1; }
    }

    var pad = (hi - lo) * Y_PAD_FACTOR;
    this._priceMin = lo - pad;
    this._priceMax = hi + pad;
  };

  /** Helper: expand lo/hi for zone arrays */
  ChartRenderer.prototype._expandRangeForZones = function (zones, lo, hi, cb) {
    for (var j = 0; j < zones.length; j++) {
      var z = zones[j];
      var zTop = z.top != null ? z.top : z.high;
      var zBot = z.bottom != null ? z.bottom : z.low;
      if (zTop != null && isFinite(zTop)) {
        if (zTop > hi) hi = zTop;
      }
      if (zBot != null && isFinite(zBot)) {
        if (zBot < lo) lo = zBot;
      }
    }
    cb([lo, hi]);
  };

  // ─── Coordinate Conversions ─────────────────────

  /** Convert a candle index to x pixel (center of the candle) */
  ChartRenderer.prototype._idxToX = function (idx) {
    var area  = this._chartArea;
    var count = this.endIdx - this.startIdx + 1;
    if (count <= 0) return area.x;
    var candleW = area.w / count;
    return area.x + (idx - this.startIdx + 0.5) * candleW;
  };

  /** Convert x pixel to fractional candle index */
  ChartRenderer.prototype._xToIdx = function (x) {
    var area  = this._chartArea;
    var count = this.endIdx - this.startIdx + 1;
    if (count <= 0) return this.startIdx;
    var candleW = area.w / count;
    return this.startIdx + (x - area.x) / candleW - 0.5;
  };

  /** Convert price to y pixel on main chart */
  ChartRenderer.prototype._priceToY = function (price) {
    var area = this._chartArea;
    var frac = (price - this._priceMin) / (this._priceMax - this._priceMin);
    return area.y + area.h * (1 - frac); // invert: higher price = lower y
  };

  /** Convert y pixel to price on main chart */
  ChartRenderer.prototype._yToPrice = function (y) {
    var area = this._chartArea;
    var frac = 1 - (y - area.y) / area.h;
    return this._priceMin + frac * (this._priceMax - this._priceMin);
  };

  /** Convert RSI value (0-100) to y pixel on RSI chart */
  ChartRenderer.prototype._rsiToY = function (rsi) {
    var area = this._rsiArea;
    return area.y + area.h * (1 - rsi / 100);
  };

  /** Get candle width in pixels */
  ChartRenderer.prototype._candleWidth = function () {
    var area  = this._chartArea;
    var count = this.endIdx - this.startIdx + 1;
    if (count <= 0) return 1;
    return area.w / count;
  };

  // ─── Main Chart Rendering ──────────────────────

  ChartRenderer.prototype._renderMainChart = function () {
    var ctx = this.mainCtx;
    var w   = this._mainW;
    var h   = this._mainH;

    // Clear
    ctx.fillStyle = COLORS.bg;
    ctx.fillRect(0, 0, w, h);

    if (this.candles.length === 0) {
      this._drawNoDataMessage(ctx, w, h);
      return;
    }

    // Render layers in order
    this._drawGrid(ctx);
    this._drawCandles(ctx);
    if (this.layers.ema)    this._drawEMA(ctx);
    if (this.layers.fvg)    this._drawFVGZones(ctx);
    if (this.layers.ob)     this._drawOrderBlocks(ctx);
    if (this.layers.swing)  this._drawSwingPoints(ctx);
    if (this.layers.mss)    this._drawMSSMarkers(ctx);
    if (this.layers.bottom) this._drawBottomZones(ctx);
    if (this.layers.growth) this._drawGrowthSignals(ctx);
    this._drawCrosshair(ctx);
    this._drawTooltip(ctx);
    this._drawYAxis(ctx);
    this._drawXAxis(ctx);
  };

  // ─── Grid ───────────────────────────────────────

  ChartRenderer.prototype._drawGrid = function (ctx) {
    var area = this._chartArea;
    var priceRange = this._priceMax - this._priceMin;
    var step = niceStep(priceRange, 8);

    ctx.strokeStyle = COLORS.grid;
    ctx.lineWidth   = 0.5;
    ctx.setLineDash([]);

    // Horizontal grid lines
    var firstLine = Math.ceil(this._priceMin / step) * step;
    for (var p = firstLine; p <= this._priceMax; p += step) {
      var y = this._priceToY(p);
      if (y < area.y || y > area.y + area.h) continue;
      ctx.beginPath();
      ctx.moveTo(area.x, y);
      ctx.lineTo(area.x + area.w, y);
      ctx.stroke();
    }

    // Vertical grid lines (every Nth candle)
    var count = this.endIdx - this.startIdx + 1;
    var labelEvery = Math.max(1, Math.floor(count / 8));
    for (var i = this.startIdx; i <= this.endIdx; i++) {
      if ((i - this.startIdx) % labelEvery !== 0) continue;
      var x = this._idxToX(i);
      ctx.beginPath();
      ctx.moveTo(x, area.y);
      ctx.lineTo(x, area.y + area.h);
      ctx.stroke();
    }
  };

  // ─── Y Axis (Price Labels) ─────────────────────

  ChartRenderer.prototype._drawYAxis = function (ctx) {
    var area = this._chartArea;
    var priceRange = this._priceMax - this._priceMin;
    var step = niceStep(priceRange, 8);
    var axisX = area.x + area.w;

    ctx.fillStyle    = COLORS.gridText;
    ctx.font         = '11px monospace';
    ctx.textAlign    = 'left';
    ctx.textBaseline = 'middle';

    var firstLine = Math.ceil(this._priceMin / step) * step;
    for (var p = firstLine; p <= this._priceMax; p += step) {
      var y = this._priceToY(p);
      if (y < area.y + 8 || y > area.y + area.h - 8) continue;
      ctx.fillText(formatPrice(p), axisX + 6, y);
    }

    // Border line
    ctx.strokeStyle = COLORS.grid;
    ctx.lineWidth   = 1;
    ctx.setLineDash([]);
    ctx.beginPath();
    ctx.moveTo(axisX, area.y);
    ctx.lineTo(axisX, area.y + area.h);
    ctx.stroke();
  };

  // ─── X Axis (Time Labels) ──────────────────────

  ChartRenderer.prototype._drawXAxis = function (ctx) {
    var area = this._chartArea;
    var axisY = area.y + area.h;
    var count = this.endIdx - this.startIdx + 1;
    var labelEvery = Math.max(1, Math.floor(count / 8));

    ctx.fillStyle    = COLORS.gridText;
    ctx.font         = '10px monospace';
    ctx.textAlign    = 'center';
    ctx.textBaseline = 'top';

    // Border line
    ctx.strokeStyle = COLORS.grid;
    ctx.lineWidth   = 1;
    ctx.setLineDash([]);
    ctx.beginPath();
    ctx.moveTo(area.x, axisY);
    ctx.lineTo(area.x + area.w, axisY);
    ctx.stroke();

    for (var i = this.startIdx; i <= this.endIdx; i++) {
      if ((i - this.startIdx) % labelEvery !== 0) continue;
      var x = this._idxToX(i);
      var candle = this.candles[i];
      if (!candle) continue;
      ctx.fillText(formatTime(candle.time), x, axisY + 6);
    }
  };

  // ─── No Data Message ────────────────────────────

  ChartRenderer.prototype._drawNoDataMessage = function (ctx, w, h) {
    ctx.fillStyle    = COLORS.gridText;
    ctx.font         = '14px monospace';
    ctx.textAlign    = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('No data available', w / 2, h / 2);
  };

  // ─── Candlesticks ──────────────────────────────

  ChartRenderer.prototype._drawCandles = function (ctx) {
    var area    = this._chartArea;
    var cw      = this._candleWidth();
    var bodyW   = cw * (1 - CANDLE_GAP);
    var halfBody = bodyW / 2;
    var wickW   = Math.max(1, bodyW * 0.12);

    for (var i = this.startIdx; i <= this.endIdx && i < this.candles.length; i++) {
      var c = this.candles[i];
      var x = this._idxToX(i);

      var oY = this._priceToY(c.open);
      var cY = this._priceToY(c.close);
      var hY = this._priceToY(c.high);
      var lY = this._priceToY(c.low);

      var isBull = c.close >= c.open;
      var color  = isBull ? COLORS.bullish : COLORS.bearish;
      var wickColor = isBull ? COLORS.wickBullish : COLORS.wickBearish;

      // Wick
      ctx.strokeStyle = wickColor;
      ctx.lineWidth   = wickW;
      ctx.setLineDash([]);
      ctx.beginPath();
      ctx.moveTo(x, hY);
      ctx.lineTo(x, lY);
      ctx.stroke();

      // Body
      var bodyTop = Math.min(oY, cY);
      var bodyH   = Math.abs(cY - oY);
      if (bodyH < 1) bodyH = 1; // minimum 1px body for doji

      ctx.fillStyle = color;
      ctx.fillRect(x - halfBody, bodyTop, bodyW, bodyH);
    }
  };

  // ─── EMA Lines ─────────────────────────────────

  ChartRenderer.prototype._drawEMA = function (ctx) {
    this._drawEMALine(ctx, 'ema21', COLORS.ema21, 1.5);
    this._drawEMALine(ctx, 'ema50', COLORS.ema50, 1.5);
  };

  ChartRenderer.prototype._drawEMALine = function (ctx, field, color, width) {
    ctx.strokeStyle = color;
    ctx.lineWidth   = width;
    ctx.setLineDash([]);
    ctx.lineJoin    = 'round';
    ctx.lineCap     = 'round';
    ctx.beginPath();

    var started = false;
    for (var i = this.startIdx; i <= this.endIdx && i < this.candles.length; i++) {
      var val = this.candles[i][field];
      if (val == null || !isFinite(val)) {
        started = false;
        continue;
      }
      var x = this._idxToX(i);
      var y = this._priceToY(val);
      if (!started) {
        ctx.moveTo(x, y);
        started = true;
      } else {
        ctx.lineTo(x, y);
      }
    }
    ctx.stroke();
  };

  // ─── FVG Zones ─────────────────────────────────

  ChartRenderer.prototype._drawFVGZones = function (ctx) {
    var analysis = this.analysis;
    if (!analysis || !analysis.fvgZones) return;

    var zones = analysis.fvgZones;
    for (var j = 0; j < zones.length; j++) {
      var z = zones[j];
      // Determine zone boundaries
      var zTop = z.top != null ? z.top : z.high;
      var zBot = z.bottom != null ? z.bottom : z.low;
      if (zTop == null || zBot == null) continue;

      var isBull = z.type === 'bullish' || z.direction === 'bullish' || z.side === 'bull';
      var filled = z.filled || z.mitigated || false;

      // Determine X range - from the FVG candle index to the right edge of visible area
      var startI = z.index != null ? z.index : z.startIndex;
      var endI   = z.endIndex != null ? z.endIndex : this.endIdx;
      if (startI == null || startI > this.endIdx || endI < this.startIdx) continue;

      var x1 = this._idxToX(Math.max(startI, this.startIdx)) - this._candleWidth() / 2;
      var x2 = this._idxToX(Math.min(endI, this.endIdx)) + this._candleWidth() / 2;
      var y1 = this._priceToY(zTop);
      var y2 = this._priceToY(zBot);

      // Fill
      ctx.fillStyle = isBull ? COLORS.fvgBull : COLORS.fvgBear;
      if (filled) {
        ctx.globalAlpha = 0.4; // dim filled FVGs
      }
      ctx.fillRect(x1, y1, x2 - x1, y2 - y1);

      // Dashed borders
      ctx.strokeStyle = isBull ? COLORS.fvgBullBorder : COLORS.fvgBearBorder;
      ctx.lineWidth   = 1;
      ctx.setLineDash([4, 3]);
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y1);
      ctx.moveTo(x1, y2);
      ctx.lineTo(x2, y2);
      ctx.stroke();
      ctx.setLineDash([]);

      // Strikethrough for filled FVGs
      if (filled) {
        ctx.strokeStyle = isBull ? COLORS.fvgBullBorder : COLORS.fvgBearBorder;
        ctx.lineWidth   = 1;
        ctx.setLineDash([6, 4]);
        var midY = (y1 + y2) / 2;
        ctx.beginPath();
        ctx.moveTo(x1, midY);
        ctx.lineTo(x2, midY);
        ctx.stroke();
        ctx.setLineDash([]);
      }

      ctx.globalAlpha = 1;
    }
  };

  // ─── Order Blocks ──────────────────────────────

  ChartRenderer.prototype._drawOrderBlocks = function (ctx) {
    var analysis = this.analysis;
    if (!analysis || !analysis.orderBlocks) return;

    var obs = analysis.orderBlocks;
    for (var j = 0; j < obs.length; j++) {
      var ob = obs[j];
      var obTop = ob.top != null ? ob.top : ob.high;
      var obBot = ob.bottom != null ? ob.bottom : ob.low;
      if (obTop == null || obBot == null) continue;

      var isBull = ob.type === 'bullish' || ob.direction === 'bullish' || ob.side === 'bull';

      var startI = ob.index != null ? ob.index : ob.startIndex;
      var endI   = ob.endIndex != null ? ob.endIndex : this.endIdx;
      if (startI == null || startI > this.endIdx || endI < this.startIdx) continue;

      var x1 = this._idxToX(Math.max(startI, this.startIdx)) - this._candleWidth() / 2;
      var x2 = this._idxToX(Math.min(endI, this.endIdx)) + this._candleWidth() / 2;
      var y1 = this._priceToY(obTop);
      var y2 = this._priceToY(obBot);

      // Fill
      ctx.fillStyle = isBull ? COLORS.obBull : COLORS.obBear;
      ctx.fillRect(x1, y1, x2 - x1, y2 - y1);

      // Solid border
      ctx.strokeStyle = isBull ? COLORS.obBullBorder : COLORS.obBearBorder;
      ctx.lineWidth   = 1.5;
      ctx.setLineDash([]);
      ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

      // Label
      ctx.fillStyle    = isBull ? COLORS.obBullBorder : COLORS.obBearBorder;
      ctx.font         = '9px monospace';
      ctx.textAlign    = 'left';
      ctx.textBaseline = 'top';
      ctx.fillText(isBull ? 'OB↑' : 'OB↓', x1 + 3, y1 + 2);
    }
  };

  // ─── Swing Points ─────────────────────────────

  ChartRenderer.prototype._drawSwingPoints = function (ctx) {
    var analysis = this.analysis;
    if (!analysis || !analysis.swingPoints) return;

    var pts = analysis.swingPoints;
    var cw  = this._candleWidth();

    for (var j = 0; j < pts.length; j++) {
      var pt = pts[j];
      var idx = pt.index;
      if (idx == null || idx < this.startIdx || idx > this.endIdx) continue;

      var isHigh = pt.type === 'high' || pt.type === 'swing_high' || pt.side === 'high';
      var price  = pt.price != null ? pt.price : (isHigh ? this.candles[idx].high : this.candles[idx].low);
      var x = this._idxToX(idx);
      var y = this._priceToY(price);
      var size = Math.max(5, cw * 0.35);

      if (isHigh) {
        // Red ▼ at swing highs (above the high)
        ctx.fillStyle = COLORS.swingHigh;
        ctx.beginPath();
        ctx.moveTo(x, y - size * 1.5);
        ctx.lineTo(x - size, y - size * 1.5 - size * 1.2);
        ctx.lineTo(x + size, y - size * 1.5 - size * 1.2);
        ctx.closePath();
        ctx.fill();
      } else {
        // Green ▲ at swing lows (below the low)
        ctx.fillStyle = COLORS.swingLow;
        ctx.beginPath();
        ctx.moveTo(x, y + size * 1.5);
        ctx.lineTo(x - size, y + size * 1.5 + size * 1.2);
        ctx.lineTo(x + size, y + size * 1.5 + size * 1.2);
        ctx.closePath();
        ctx.fill();
      }

      // Price label
      ctx.fillStyle    = isHigh ? COLORS.swingHigh : COLORS.swingLow;
      ctx.font         = '9px monospace';
      ctx.textAlign    = 'center';
      ctx.textBaseline = isHigh ? 'bottom' : 'top';
      var labelY = isHigh ? (y - size * 1.5 - size * 1.2 - 3) : (y + size * 1.5 + size * 1.2 + 3);
      ctx.fillText(formatPrice(price), x, labelY);
    }
  };

  // ─── MSS Markers ───────────────────────────────

  ChartRenderer.prototype._drawMSSMarkers = function (ctx) {
    var analysis = this.analysis;
    if (!analysis || !analysis.mssEvents) return;

    var signals = analysis.mssEvents;
    var area    = this._chartArea;

    for (var j = 0; j < signals.length; j++) {
      var s   = signals[j];
      var idx = s.index;
      if (idx == null || idx < this.startIdx || idx > this.endIdx) continue;

      var isBull = s.type === 'bullish' || s.direction === 'bullish' || s.side === 'bull';
      var color  = isBull ? COLORS.mssBull : COLORS.mssBear;
      var price  = s.price != null ? s.price : this.candles[idx].close;
      var x = this._idxToX(idx);
      var y = this._priceToY(price);

      // Vertical dashed line
      ctx.strokeStyle = color;
      ctx.lineWidth   = 1;
      ctx.setLineDash([4, 4]);
      ctx.globalAlpha = 0.5;
      ctx.beginPath();
      ctx.moveTo(x, area.y);
      ctx.lineTo(x, area.y + area.h);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.globalAlpha = 1;

      // Diamond shape
      var ds = 7;
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.moveTo(x, y - ds);
      ctx.lineTo(x + ds, y);
      ctx.lineTo(x, y + ds);
      ctx.lineTo(x - ds, y);
      ctx.closePath();
      ctx.fill();

      // Inner sparkle
      ctx.fillStyle = COLORS.bg;
      ctx.beginPath();
      ctx.arc(x, y, 2, 0, Math.PI * 2);
      ctx.fill();

      // Label
      ctx.fillStyle    = color;
      ctx.font         = 'bold 10px monospace';
      ctx.textAlign    = 'center';
      ctx.textBaseline = isBull ? 'top' : 'bottom';
      var labelText = isBull ? 'MSS ▲' : 'MSS ▼';
      var labelY    = isBull ? y + ds + 4 : y - ds - 4;
      ctx.fillText(labelText, x, labelY);
    }
  };

  // ─── Bottom Zones ──────────────────────────────

  ChartRenderer.prototype._drawBottomZones = function (ctx) {
    var analysis = this.analysis;
    if (!analysis || !analysis.bottomZones) return;

    var zones = analysis.bottomZones;
    var area  = this._chartArea;
    var cw    = this._candleWidth();

    for (var j = 0; j < zones.length; j++) {
      var bz  = zones[j];
      var idx = bz.index;
      if (idx == null || idx < this.startIdx || idx > this.endIdx) continue;

      var x     = this._idxToX(idx);
      var score = bz.score != null ? bz.score : '';

      // Glow region (3 candles wide around the detection point)
      var glowW = cw * 3;
      var gradient = ctx.createRadialGradient(x, area.y + area.h * 0.7, 0, x, area.y + area.h * 0.7, glowW);
      gradient.addColorStop(0, 'rgba(0,220,130,0.15)');
      gradient.addColorStop(1, 'rgba(0,220,130,0)');
      ctx.fillStyle = gradient;
      ctx.fillRect(x - glowW, area.y, glowW * 2, area.h);

      // Background highlight band
      ctx.fillStyle = COLORS.bottomGlow;
      ctx.fillRect(x - cw * 1.5, area.y, cw * 3, area.h);

      // Star icon at the low point
      var price = bz.price != null ? bz.price : this.candles[idx].low;
      var starY = this._priceToY(price);
      this._drawStar(ctx, x, starY + 16, 8, 5, COLORS.bottomStar);

      // Score text
      ctx.fillStyle    = COLORS.bottomStar;
      ctx.font         = 'bold 11px monospace';
      ctx.textAlign    = 'center';
      ctx.textBaseline = 'top';
      ctx.fillText('★ ' + score, x, starY + 28);
    }
  };

  /** Draw a 5-pointed star */
  ChartRenderer.prototype._drawStar = function (ctx, cx, cy, outerR, points, color) {
    var innerR = outerR * 0.45;
    ctx.fillStyle = color;
    ctx.beginPath();
    for (var i = 0; i < points * 2; i++) {
      var r     = i % 2 === 0 ? outerR : innerR;
      var angle = (Math.PI / 2 * 3) + (i * Math.PI / points);
      var x = cx + Math.cos(angle) * r;
      var y = cy + Math.sin(angle) * r;
      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    }
    ctx.closePath();
    ctx.fill();
  };

  // ─── Growth Signals ────────────────────────────

  ChartRenderer.prototype._drawGrowthSignals = function (ctx) {
    var analysis = this.analysis;
    if (!analysis || !analysis.growthSignals) return;

    var signals = analysis.growthSignals;
    var cw      = this._candleWidth();

    for (var j = 0; j < signals.length; j++) {
      var gs  = signals[j];
      var idx = gs.index;
      if (idx == null || idx < this.startIdx || idx > this.endIdx) continue;

      var x     = this._idxToX(idx);
      var price = gs.price != null ? gs.price : this.candles[idx].high;
      var y     = this._priceToY(price);
      var label = gs.label || 'Growth';

      // Rocket emoji
      ctx.font         = '16px serif';
      ctx.textAlign    = 'center';
      ctx.textBaseline = 'bottom';
      ctx.fillText('🚀', x, y - 12);

      // Up arrow
      ctx.strokeStyle = COLORS.growthArrow;
      ctx.lineWidth   = 2;
      ctx.setLineDash([]);
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(x, y - 10);
      ctx.moveTo(x - 4, y - 6);
      ctx.lineTo(x, y - 10);
      ctx.lineTo(x + 4, y - 6);
      ctx.stroke();

      // Label
      ctx.fillStyle    = COLORS.growthArrow;
      ctx.font         = 'bold 9px monospace';
      ctx.textAlign    = 'center';
      ctx.textBaseline = 'bottom';
      ctx.fillText(label, x, y - 28);
    }
  };

  // ─── Crosshair ─────────────────────────────────

  ChartRenderer.prototype._drawCrosshair = function (ctx) {
    if (this._mouseX < 0 || this._mouseY < 0) return;

    var area = this._chartArea;
    var mx   = this._mouseX;
    var my   = this._mouseY;

    // Only draw if mouse is within chart area
    if (mx < area.x || mx > area.x + area.w || my < area.y || my > area.y + area.h) return;

    ctx.strokeStyle = COLORS.crosshair;
    ctx.lineWidth   = 0.5;
    ctx.setLineDash([4, 3]);

    // Vertical line
    ctx.beginPath();
    ctx.moveTo(mx, area.y);
    ctx.lineTo(mx, area.y + area.h);
    ctx.stroke();

    // Horizontal line
    ctx.beginPath();
    ctx.moveTo(area.x, my);
    ctx.lineTo(area.x + area.w, my);
    ctx.stroke();

    ctx.setLineDash([]);

    // Price label on Y axis
    var price = this._yToPrice(my);
    var axisX = area.x + area.w;
    ctx.fillStyle = 'rgba(30,40,70,0.9)';
    ctx.fillRect(axisX + 1, my - 10, Y_AXIS_WIDTH - 2, 20);
    ctx.fillStyle    = '#e2e8f0';
    ctx.font         = '11px monospace';
    ctx.textAlign    = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText(formatPrice(price), axisX + 6, my);

    // Time label on X axis
    var snapIdx = Math.round(this._xToIdx(mx));
    if (snapIdx >= this.startIdx && snapIdx <= this.endIdx && snapIdx < this.candles.length) {
      var snapX = this._idxToX(snapIdx);
      var time  = this.candles[snapIdx].time;
      var axisY = area.y + area.h;
      var tLabel = formatTime(time);
      var tw = ctx.measureText(tLabel).width + 10;
      ctx.fillStyle = 'rgba(30,40,70,0.9)';
      ctx.fillRect(snapX - tw / 2, axisY + 1, tw, X_AXIS_HEIGHT - 2);
      ctx.fillStyle    = '#e2e8f0';
      ctx.textAlign    = 'center';
      ctx.textBaseline = 'top';
      ctx.fillText(tLabel, snapX, axisY + 6);
    }
  };

  // ─── Tooltip ───────────────────────────────────

  ChartRenderer.prototype._drawTooltip = function (ctx) {
    if (this._mouseX < 0 || this._mouseY < 0) return;

    var area = this._chartArea;
    var mx   = this._mouseX;
    var my   = this._mouseY;

    // Only when mouse in chart area
    if (mx < area.x || mx > area.x + area.w || my < area.y || my > area.y + area.h) return;

    var idx = Math.round(this._xToIdx(mx));
    if (idx < this.startIdx || idx > this.endIdx || idx >= this.candles.length) return;

    var c = this.candles[idx];
    if (!c) return;

    // Collect lines
    var lines = [];
    lines.push({ label: 'Time',  value: formatTimeFull(c.time) });
    lines.push({ label: 'Open',  value: formatPrice(c.open),  color: COLORS.tooltipText });
    lines.push({ label: 'High',  value: formatPrice(c.high),  color: COLORS.tooltipText });
    lines.push({ label: 'Low',   value: formatPrice(c.low),   color: COLORS.tooltipText });
    lines.push({ label: 'Close', value: formatPrice(c.close), color: c.close >= c.open ? COLORS.bullish : COLORS.bearish });

    if (c.ema21 != null) lines.push({ label: 'EMA21', value: formatPrice(c.ema21), color: COLORS.ema21 });
    if (c.ema50 != null) lines.push({ label: 'EMA50', value: formatPrice(c.ema50), color: COLORS.ema50 });
    if (c.rsi != null)   lines.push({ label: 'RSI',   value: c.rsi.toFixed(1),     color: COLORS.rsiLine });
    if (c.atr != null)   lines.push({ label: 'ATR',   value: formatPrice(c.atr),    color: COLORS.tooltipText });

    // Check for ICT events at this candle
    if (this.analysis) {
      var events = this._getEventsAtIndex(idx);
      for (var e = 0; e < events.length; e++) {
        lines.push({ label: 'ICT', value: events[e], color: COLORS.mssBull });
      }
    }

    // Tooltip dimensions
    var padH = 10;
    var padV = 8;
    var lineH = TOOLTIP_LINE_H;
    var tooltipH = padV * 2 + lines.length * lineH;
    var tooltipW = TOOLTIP_W;

    // Position: prefer right of cursor, flip if needed
    var tx = mx + 16;
    var ty = my - tooltipH / 2;
    if (tx + tooltipW > area.x + area.w) tx = mx - tooltipW - 16;
    if (ty < area.y) ty = area.y;
    if (ty + tooltipH > area.y + area.h) ty = area.y + area.h - tooltipH;

    // Background
    ctx.fillStyle   = COLORS.tooltipBg;
    ctx.strokeStyle = COLORS.tooltipBorder;
    ctx.lineWidth   = 1;
    ctx.setLineDash([]);
    this._roundRect(ctx, tx, ty, tooltipW, tooltipH, 6);
    ctx.fill();
    ctx.stroke();

    // Content
    ctx.font         = '11px monospace';
    ctx.textBaseline = 'middle';
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i];
      var ly   = ty + padV + i * lineH + lineH / 2;

      // Label
      ctx.fillStyle = COLORS.tooltipLabel;
      ctx.textAlign = 'left';
      ctx.fillText(line.label, tx + padH, ly);

      // Value
      ctx.fillStyle = line.color || COLORS.tooltipText;
      ctx.textAlign = 'right';
      ctx.fillText(line.value, tx + tooltipW - padH, ly);
    }
  };

  /** Helper: draw rounded rectangle path */
  ChartRenderer.prototype._roundRect = function (ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
  };

  /** Collect ICT event descriptions at a given candle index */
  ChartRenderer.prototype._getEventsAtIndex = function (idx) {
    var events = [];
    var a = this.analysis;
    if (!a) return events;

    if (a.mssEvents) {
      for (var i = 0; i < a.mssEvents.length; i++) {
        if (a.mssEvents[i].index === idx) {
          var s = a.mssEvents[i];
          var dir = (s.type === 'bullish' || s.direction === 'bullish') ? '▲' : '▼';
          events.push('MSS ' + dir);
        }
      }
    }
    if (a.fvgZones) {
      for (var i = 0; i < a.fvgZones.length; i++) {
        var z = a.fvgZones[i];
        var si = z.index != null ? z.index : z.startIndex;
        if (si === idx) {
          var type = (z.type === 'bullish' || z.direction === 'bullish') ? 'Bull' : 'Bear';
          events.push('FVG ' + type);
        }
      }
    }
    if (a.orderBlocks) {
      for (var i = 0; i < a.orderBlocks.length; i++) {
        var ob = a.orderBlocks[i];
        var si = ob.index != null ? ob.index : ob.startIndex;
        if (si === idx) {
          var type = (ob.type === 'bullish' || ob.direction === 'bullish') ? 'Bull' : 'Bear';
          events.push('OB ' + type);
        }
      }
    }
    if (a.swingPoints) {
      for (var i = 0; i < a.swingPoints.length; i++) {
        if (a.swingPoints[i].index === idx) {
          var sType = (a.swingPoints[i].type === 'high' || a.swingPoints[i].type === 'swing_high') ? 'High' : 'Low';
          events.push('Swing ' + sType);
        }
      }
    }
    if (a.bottomZones) {
      for (var i = 0; i < a.bottomZones.length; i++) {
        if (a.bottomZones[i].index === idx) {
          events.push('Bottom ★');
        }
      }
    }
    if (a.growthSignals) {
      for (var i = 0; i < a.growthSignals.length; i++) {
        if (a.growthSignals[i].index === idx) {
          events.push('Growth 🚀');
        }
      }
    }
    return events;
  };

  // ─── RSI Sub-Chart ─────────────────────────────

  ChartRenderer.prototype._renderRSIChart = function () {
    if (!this.rsiCanvas || !this.rsiCtx) return;

    var ctx  = this.rsiCtx;
    var w    = this._rsiW;
    var h    = this._rsiH;
    var area = this._rsiArea;

    // Clear
    ctx.fillStyle = COLORS.bg;
    ctx.fillRect(0, 0, w, h);

    if (this.candles.length === 0) return;

    // Overbought / Oversold zones
    var y70 = this._rsiToY(70);
    var y30 = this._rsiToY(30);
    var y0  = this._rsiToY(0);
    var y100 = this._rsiToY(100);

    // Overbought zone (>70)
    ctx.fillStyle = COLORS.rsiOverbought;
    ctx.fillRect(area.x, y100, area.w, y70 - y100);

    // Oversold zone (<30)
    ctx.fillStyle = COLORS.rsiOversold;
    ctx.fillRect(area.x, y30, area.w, y0 - y30);

    // Grid lines
    ctx.strokeStyle = COLORS.grid;
    ctx.lineWidth   = 0.5;
    ctx.setLineDash([]);
    // Border
    ctx.beginPath();
    ctx.moveTo(area.x, area.y);
    ctx.lineTo(area.x + area.w, area.y);
    ctx.moveTo(area.x, area.y + area.h);
    ctx.lineTo(area.x + area.w, area.y + area.h);
    ctx.stroke();

    // 70 line (red dashed)
    ctx.strokeStyle = COLORS.rsi70Line;
    ctx.lineWidth   = 1;
    ctx.setLineDash([5, 4]);
    ctx.beginPath();
    ctx.moveTo(area.x, y70);
    ctx.lineTo(area.x + area.w, y70);
    ctx.stroke();

    // 30 line (green dashed)
    ctx.strokeStyle = COLORS.rsi30Line;
    ctx.beginPath();
    ctx.moveTo(area.x, y30);
    ctx.lineTo(area.x + area.w, y30);
    ctx.stroke();
    ctx.setLineDash([]);

    // 50 line (subtle)
    var y50 = this._rsiToY(50);
    ctx.strokeStyle = COLORS.rsi50Line;
    ctx.lineWidth   = 0.5;
    ctx.beginPath();
    ctx.moveTo(area.x, y50);
    ctx.lineTo(area.x + area.w, y50);
    ctx.stroke();

    // RSI line
    ctx.strokeStyle = COLORS.rsiLine;
    ctx.lineWidth   = 1.5;
    ctx.lineJoin    = 'round';
    ctx.lineCap     = 'round';
    ctx.beginPath();

    var started = false;
    for (var i = this.startIdx; i <= this.endIdx && i < this.candles.length; i++) {
      var rsi = this.candles[i].rsi;
      if (rsi == null || !isFinite(rsi)) {
        started = false;
        continue;
      }
      var x = this._idxToX(i);
      var y = this._rsiToY(rsi);
      if (!started) {
        ctx.moveTo(x, y);
        started = true;
      } else {
        ctx.lineTo(x, y);
      }
    }
    ctx.stroke();

    // Y Axis labels (0, 30, 50, 70, 100)
    var axisX = area.x + area.w;
    ctx.fillStyle    = COLORS.gridText;
    ctx.font         = '10px monospace';
    ctx.textAlign    = 'left';
    ctx.textBaseline = 'middle';

    var rsiLabels = [0, 30, 50, 70, 100];
    for (var j = 0; j < rsiLabels.length; j++) {
      var ry = this._rsiToY(rsiLabels[j]);
      ctx.fillText(String(rsiLabels[j]), axisX + 6, ry);
    }

    // Right border line
    ctx.strokeStyle = COLORS.grid;
    ctx.lineWidth   = 1;
    ctx.setLineDash([]);
    ctx.beginPath();
    ctx.moveTo(axisX, area.y);
    ctx.lineTo(axisX, area.y + area.h);
    ctx.stroke();

    // X Axis (synced with main chart)
    var axisY = area.y + area.h;
    var count = this.endIdx - this.startIdx + 1;
    var labelEvery = Math.max(1, Math.floor(count / 8));

    ctx.fillStyle    = COLORS.gridText;
    ctx.font         = '10px monospace';
    ctx.textAlign    = 'center';
    ctx.textBaseline = 'top';

    ctx.strokeStyle = COLORS.grid;
    ctx.lineWidth   = 1;
    ctx.beginPath();
    ctx.moveTo(area.x, axisY);
    ctx.lineTo(area.x + area.w, axisY);
    ctx.stroke();

    for (var i = this.startIdx; i <= this.endIdx; i++) {
      if ((i - this.startIdx) % labelEvery !== 0) continue;
      var x      = this._idxToX(i);
      var candle = this.candles[i];
      if (!candle) continue;
      ctx.fillText(formatTime(candle.time), x, axisY + 6);
    }

    // Crosshair sync (vertical only)
    if (this._mouseX >= area.x && this._mouseX <= area.x + area.w) {
      ctx.strokeStyle = COLORS.crosshair;
      ctx.lineWidth   = 0.5;
      ctx.setLineDash([4, 3]);
      ctx.beginPath();
      ctx.moveTo(this._mouseX, area.y);
      ctx.lineTo(this._mouseX, area.y + area.h);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // RSI label for the "RSI" title
    ctx.fillStyle    = COLORS.gridText;
    ctx.font         = 'bold 10px monospace';
    ctx.textAlign    = 'left';
    ctx.textBaseline = 'top';
    ctx.fillText('RSI', area.x + 4, area.y + 4);
  };

  // ─── Event Handlers ────────────────────────────

  ChartRenderer.prototype._handleMouseMove = function (e) {
    var rect = this.mainCanvas.getBoundingClientRect();
    this._mouseX = e.clientX - rect.left;
    this._mouseY = e.clientY - rect.top;

    if (this._isDragging) {
      var dx     = this._mouseX - this._dragStartX;
      var cw     = this._candleWidth();
      var shift  = Math.round(-dx / cw);
      var total  = this.candles.length;
      var range  = this._dragEndIdx - this._dragStartIdx;

      var newStart = clamp(this._dragStartIdx + shift, 0, total - 1 - range);
      var newEnd   = newStart + range;

      this.startIdx = newStart;
      this.endIdx   = Math.min(newEnd, total - 1);
    }

    this._markDirty();
  };

  ChartRenderer.prototype._handleMouseDown = function (e) {
    if (e.button !== 0) return; // left click only
    this._isDragging   = true;
    this._dragStartX   = this._mouseX;
    this._dragStartIdx = this.startIdx;
    this._dragEndIdx   = this.endIdx;
    this.mainCanvas.style.cursor = 'grabbing';
    if (this.rsiCanvas) this.rsiCanvas.style.cursor = 'grabbing';
  };

  ChartRenderer.prototype._handleMouseUp = function () {
    this._isDragging = false;
    this.mainCanvas.style.cursor = 'crosshair';
    if (this.rsiCanvas) this.rsiCanvas.style.cursor = 'crosshair';
  };

  ChartRenderer.prototype._handleMouseLeave = function () {
    this._mouseX     = -1;
    this._mouseY     = -1;
    this._isDragging = false;
    this.mainCanvas.style.cursor = 'crosshair';
    if (this.rsiCanvas) this.rsiCanvas.style.cursor = 'crosshair';
    this._markDirty();
  };

  ChartRenderer.prototype._handleWheel = function (e) {
    e.preventDefault();

    var total = this.candles.length;
    if (total === 0) return;

    var delta = e.deltaY > 0 ? 1 : -1; // positive = zoom out
    var range = this.endIdx - this.startIdx;
    var zoomStep = Math.max(1, Math.round(range * 0.1));

    // Zoom centered on mouse position
    var area   = this._chartArea;
    var mouseRatio = (this._mouseX - area.x) / area.w;
    mouseRatio = clamp(mouseRatio, 0, 1);

    var newRange = range + delta * zoomStep * 2;
    newRange = clamp(newRange, MIN_CANDLES - 1, Math.min(MAX_CANDLES - 1, total - 1));

    var center    = this.startIdx + range * mouseRatio;
    var newStart  = Math.round(center - newRange * mouseRatio);
    var newEnd    = newStart + newRange;

    // Clamp
    if (newStart < 0) {
      newStart = 0;
      newEnd   = newRange;
    }
    if (newEnd >= total) {
      newEnd   = total - 1;
      newStart = Math.max(0, newEnd - newRange);
    }

    this.startIdx = newStart;
    this.endIdx   = newEnd;
    this._markDirty();
  };

  ChartRenderer.prototype._handleResize = function () {
    this._markDirty();
  };

  // ─── Public: getMouseCandle ─────────────────────

  /**
   * Get candle information at the current mouse position.
   * Returns null if mouse is outside chart area or no candle found.
   * @param {number} x - Mouse X relative to canvas
   * @param {number} y - Mouse Y relative to canvas
   * @returns {{ candle: Object, index: number, ictEvents: Array }|null}
   */
  ChartRenderer.prototype.getMouseCandle = function (x, y) {
    var area = this._chartArea;
    if (x < area.x || x > area.x + area.w || y < area.y || y > area.y + area.h) {
      return null;
    }
    var fractIdx = this._xToIdx(x);
    var idx = Math.round(fractIdx);
    if (idx < this.startIdx || idx > this.endIdx || idx >= this.candles.length || idx < 0) {
      return null;
    }
    var candle = this.candles[idx];
    if (!candle) return null;

    // Gather ICT events at this index
    var ictEvents = [];
    var a = this.analysis;
    if (a) {
      if (a.mssEvents) {
        for (var i = 0; i < a.mssEvents.length; i++) {
          if (a.mssEvents[i].index === idx) {
            ictEvents.push({ type: a.mssEvents[i].type, label: 'MSS ' + (a.mssEvents[i].type === 'bullish' ? '▲' : '▼') });
          }
        }
      }
      if (a.fvgZones) {
        for (var i = 0; i < a.fvgZones.length; i++) {
          var z = a.fvgZones[i];
          var si = z.startIndex != null ? z.startIndex : z.index;
          if (si === idx) {
            ictEvents.push({ type: z.type, label: (z.type === 'bullish' ? 'Bull' : 'Bear') + ' FVG' });
          }
        }
      }
      if (a.orderBlocks) {
        for (var i = 0; i < a.orderBlocks.length; i++) {
          var ob = a.orderBlocks[i];
          if (ob.index === idx) {
            ictEvents.push({ type: ob.type, label: (ob.type === 'bullish' ? 'Demand' : 'Supply') + ' OB' });
          }
        }
      }
      if (a.swingPoints) {
        for (var i = 0; i < a.swingPoints.length; i++) {
          if (a.swingPoints[i].index === idx) {
            ictEvents.push({ type: a.swingPoints[i].type === 'high' ? 'bearish' : 'bullish', label: 'Swing ' + (a.swingPoints[i].type === 'high' ? 'High' : 'Low') });
          }
        }
      }
    }

    return { candle: candle, index: idx, ictEvents: ictEvents };
  };

  // ─── Expose to Global ──────────────────────────

  window.ChartRenderer = ChartRenderer;

})();
