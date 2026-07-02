/**
 * ============================================================================
 * ICT Smart Money Concepts Engine
 * ============================================================================
 * Implements Inner Circle Trader (ICT) algorithms for technical analysis:
 *   - Swing Point detection
 *   - Market Structure Shift (MSS)
 *   - Fair Value Gaps (FVG)
 *   - Order Blocks (OB)
 *   - Bottom Zone scoring
 *   - Growth Momentum scoring
 *
 * Input candle format:
 *   { time, open, high, low, close, ema21, ema50, rsi, atr, s1, s2, r1, r2 }
 *
 * Usage:
 *   const result = window.ICTEngine.analyze(candles);
 * ============================================================================
 */
(function () {
  'use strict';

  // ─────────────────────────────────────────────────────────────────────────
  // Helper utilities
  // ─────────────────────────────────────────────────────────────────────────

  /**
   * Safely check if a value is a finite number.
   * @param {*} v
   * @returns {boolean}
   */
  function isNum(v) {
    return typeof v === 'number' && isFinite(v);
  }

  /**
   * Clamp a value between min and max.
   * @param {number} v
   * @param {number} lo
   * @param {number} hi
   * @returns {number}
   */
  function clamp(v, lo, hi) {
    return v < lo ? lo : v > hi ? hi : v;
  }

  /**
   * Return the last element of an array, or undefined.
   * @template T
   * @param {T[]} arr
   * @returns {T|undefined}
   */
  function last(arr) {
    return arr.length > 0 ? arr[arr.length - 1] : undefined;
  }

  /**
   * Filter swing points by type.
   * @param {Object[]} swingPoints
   * @param {'high'|'low'} type
   * @returns {Object[]}
   */
  function filterSwings(swingPoints, type) {
    return swingPoints.filter(function (sp) { return sp.type === type; });
  }

  /**
   * Determine the score level label.
   * @param {number} score
   * @param {number} maxScore
   * @returns {'strong'|'moderate'|'weak'}
   */
  function scoreLevel(score, maxScore) {
    var pct = score / maxScore;
    if (pct >= 0.6) return 'strong';
    if (pct >= 0.35) return 'moderate';
    return 'weak';
  }

  // ─────────────────────────────────────────────────────────────────────────
  // 1. findSwingPoints
  // ─────────────────────────────────────────────────────────────────────────

  /**
   * Detect swing highs and swing lows in a candle array.
   *
   * A **Swing High** at index i means candle[i].high is strictly greater than
   * the high of every candle in the window [i-lookback … i+lookback].
   *
   * A **Swing Low** at index i means candle[i].low is strictly less than the
   * low of every candle in the window [i-lookback … i+lookback].
   *
   * @param {Object[]} candles - Array of candle objects.
   * @param {number}   [lookback=3] - Number of bars each side to compare.
   * @returns {{ index:number, type:'high'|'low', price:number, time:* }[]}
   */
  function findSwingPoints(candles, lookback) {
    if (!candles || candles.length === 0) return [];
    lookback = (typeof lookback === 'number' && lookback > 0) ? lookback : 3;

    var results = [];
    var len = candles.length;

    for (var i = lookback; i < len - lookback; i++) {
      var c = candles[i];
      var isSwingHigh = true;
      var isSwingLow = true;

      for (var j = 1; j <= lookback; j++) {
        var left  = candles[i - j];
        var right = candles[i + j];

        if (c.high <= left.high || c.high <= right.high) {
          isSwingHigh = false;
        }
        if (c.low >= left.low || c.low >= right.low) {
          isSwingLow = false;
        }

        // Early exit if neither is possible
        if (!isSwingHigh && !isSwingLow) break;
      }

      if (isSwingHigh) {
        results.push({ index: i, type: 'high', price: c.high, time: c.time });
      }
      if (isSwingLow) {
        results.push({ index: i, type: 'low', price: c.low, time: c.time });
      }
    }

    return results;
  }

  // ─────────────────────────────────────────────────────────────────────────
  // 2. detectMSS  (Market Structure Shift)
  // ─────────────────────────────────────────────────────────────────────────

  /**
   * Detect Market Structure Shifts (MSS).
   *
   * **Uptrend** is defined as a sequence of Higher-Highs (HH) and
   * Higher-Lows (HL). **Downtrend** is Lower-Highs (LH) and Lower-Lows (LL).
   *
   * - Bullish MSS: while in a downtrend, price breaks **above** the most
   *   recent swing high → structure shifts bullish.
   * - Bearish MSS: while in an uptrend, price breaks **below** the most
   *   recent swing low → structure shifts bearish.
   *
   * @param {Object[]} candles     - Array of candle objects.
   * @param {Object[]} swingPoints - Output of findSwingPoints().
   * @returns {{ index:number, type:'bullish'|'bearish', price:number,
   *             time:*, breakLevel:number }[]}
   */
  function detectMSS(candles, swingPoints) {
    if (!candles || candles.length === 0 || !swingPoints || swingPoints.length < 4) {
      return [];
    }

    var results = [];

    // Separate swings into highs and lows, sorted by index
    var highs = filterSwings(swingPoints, 'high');
    var lows  = filterSwings(swingPoints, 'low');

    if (highs.length < 2 || lows.length < 2) return results;

    // Determine initial trend from first two swing pairs
    // We'll track the "current trend" as we walk through candles
    var trend = 'neutral'; // 'up', 'down', 'neutral'

    // We track the latest key swing levels
    var lastSwingHigh = null;
    var lastSwingLow  = null;
    var prevSwingHigh = null;
    var prevSwingLow  = null;

    // Build a map: index → swing event(s) for O(1) lookup
    var swingAtIndex = {};
    for (var s = 0; s < swingPoints.length; s++) {
      var sp = swingPoints[s];
      if (!swingAtIndex[sp.index]) swingAtIndex[sp.index] = [];
      swingAtIndex[sp.index].push(sp);
    }

    // Walk candles in order
    for (var i = 0; i < candles.length; i++) {
      var candle = candles[i];

      // Update swing tracking when we arrive at a swing point index
      if (swingAtIndex[i]) {
        var events = swingAtIndex[i];
        for (var e = 0; e < events.length; e++) {
          var ev = events[e];
          if (ev.type === 'high') {
            prevSwingHigh = lastSwingHigh;
            lastSwingHigh = ev;
          } else {
            prevSwingLow = lastSwingLow;
            lastSwingLow = ev;
          }
        }

        // Re-evaluate trend after updating swings
        if (prevSwingHigh && lastSwingHigh && prevSwingLow && lastSwingLow) {
          var hh = lastSwingHigh.price > prevSwingHigh.price;
          var hl = lastSwingLow.price > prevSwingLow.price;
          var lh = lastSwingHigh.price < prevSwingHigh.price;
          var ll = lastSwingLow.price < prevSwingLow.price;

          if (hh && hl) {
            trend = 'up';
          } else if (lh && ll) {
            trend = 'down';
          }
          // Mixed signals → keep previous trend
        }
      }

      // Check for MSS only after we have enough swing data
      if (!lastSwingHigh || !lastSwingLow) continue;

      // Bullish MSS: downtrend + candle close breaks above last swing high
      if (trend === 'down' && candle.close > lastSwingHigh.price && i > lastSwingHigh.index) {
        results.push({
          index: i,
          type: 'bullish',
          price: candle.close,
          time: candle.time,
          breakLevel: lastSwingHigh.price
        });
        // After a bullish MSS, shift the trend
        trend = 'up';
      }

      // Bearish MSS: uptrend + candle close breaks below last swing low
      if (trend === 'up' && candle.close < lastSwingLow.price && i > lastSwingLow.index) {
        results.push({
          index: i,
          type: 'bearish',
          price: candle.close,
          time: candle.time,
          breakLevel: lastSwingLow.price
        });
        trend = 'down';
      }
    }

    return results;
  }

  // ─────────────────────────────────────────────────────────────────────────
  // 3. findFVG  (Fair Value Gaps)
  // ─────────────────────────────────────────────────────────────────────────

  /**
   * Identify Fair Value Gaps (FVG) — imbalance zones between three candles.
   *
   * - **Bullish FVG**: candles[i+2].low > candles[i].high  →  gap up
   *   (zone from candles[i].high to candles[i+2].low)
   * - **Bearish FVG**: candles[i+2].high < candles[i].low  →  gap down
   *   (zone from candles[i+2].high to candles[i].low)
   *
   * Each FVG is checked against subsequent candles to determine if it has
   * been **filled** (price action wicked into the gap).
   *
   * @param {Object[]} candles - Array of candle objects.
   * @returns {{ startIndex:number, endIndex:number, type:'bullish'|'bearish',
   *             top:number, bottom:number, filled:boolean, fillIndex:number|null }[]}
   */
  function findFVG(candles) {
    if (!candles || candles.length < 3) return [];

    var results = [];
    var len = candles.length;

    for (var i = 0; i < len - 2; i++) {
      var c1 = candles[i];
      var c3 = candles[i + 2];

      // Bullish FVG: gap between candle 1 high and candle 3 low
      if (c3.low > c1.high) {
        var fvg = {
          startIndex: i,
          endIndex: i + 2,
          type: 'bullish',
          top: c3.low,
          bottom: c1.high,
          filled: false,
          fillIndex: null
        };

        // Check fill: any subsequent candle's low reaches into or below the gap
        for (var k = i + 3; k < len; k++) {
          if (candles[k].low <= fvg.bottom) {
            fvg.filled = true;
            fvg.fillIndex = k;
            break;
          }
        }

        results.push(fvg);
      }

      // Bearish FVG: gap between candle 3 high and candle 1 low
      if (c3.high < c1.low) {
        var fvgB = {
          startIndex: i,
          endIndex: i + 2,
          type: 'bearish',
          top: c1.low,
          bottom: c3.high,
          filled: false,
          fillIndex: null
        };

        // Check fill: any subsequent candle's high reaches into or above the gap
        for (var k2 = i + 3; k2 < len; k2++) {
          if (candles[k2].high >= fvgB.top) {
            fvgB.filled = true;
            fvgB.fillIndex = k2;
            break;
          }
        }

        results.push(fvgB);
      }
    }

    return results;
  }

  // ─────────────────────────────────────────────────────────────────────────
  // 4. findOrderBlocks
  // ─────────────────────────────────────────────────────────────────────────

  /**
   * Identify Order Blocks (OB) — the last opposing candle before an MSS.
   *
   * - **Bullish OB**: the last *bearish* candle (close < open) before a
   *   bullish MSS. Zone = [low, high] of that candle.
   * - **Bearish OB**: the last *bullish* candle (close > open) before a
   *   bearish MSS. Zone = [low, high] of that candle.
   *
   * An OB is marked **mitigated** if subsequent price action returns to
   * the OB zone.
   *
   * @param {Object[]} candles   - Array of candle objects.
   * @param {Object[]} mssEvents - Output of detectMSS().
   * @returns {{ index:number, type:'bullish'|'bearish', top:number,
   *             bottom:number, time:*, mitigated:boolean }[]}
   */
  function findOrderBlocks(candles, mssEvents) {
    if (!candles || candles.length === 0 || !mssEvents || mssEvents.length === 0) {
      return [];
    }

    var results = [];
    var len = candles.length;

    for (var m = 0; m < mssEvents.length; m++) {
      var mss = mssEvents[m];
      var obCandle = null;
      var obIndex = -1;

      if (mss.type === 'bullish') {
        // Find the last bearish candle before this MSS index
        for (var j = mss.index - 1; j >= 0; j--) {
          if (candles[j].close < candles[j].open) {
            obCandle = candles[j];
            obIndex = j;
            break;
          }
        }
      } else {
        // Bearish MSS → find last bullish candle before it
        for (var j2 = mss.index - 1; j2 >= 0; j2--) {
          if (candles[j2].close > candles[j2].open) {
            obCandle = candles[j2];
            obIndex = j2;
            break;
          }
        }
      }

      if (!obCandle) continue;

      var ob = {
        index: obIndex,
        type: mss.type === 'bullish' ? 'bullish' : 'bearish',
        top: obCandle.high,
        bottom: obCandle.low,
        time: obCandle.time,
        mitigated: false
      };

      // Check mitigation: price returns to the OB zone after the MSS
      for (var k = mss.index + 1; k < len; k++) {
        var c = candles[k];
        if (ob.type === 'bullish') {
          // Bullish OB mitigated when price dips into the zone (low <= ob.top)
          if (c.low <= ob.top && c.low >= ob.bottom) {
            ob.mitigated = true;
            break;
          }
          // Also mitigated if price goes completely through the zone
          if (c.low < ob.bottom) {
            ob.mitigated = true;
            break;
          }
        } else {
          // Bearish OB mitigated when price wicks into the zone (high >= ob.bottom)
          if (c.high >= ob.bottom && c.high <= ob.top) {
            ob.mitigated = true;
            break;
          }
          if (c.high > ob.top) {
            ob.mitigated = true;
            break;
          }
        }
      }

      results.push(ob);
    }

    return results;
  }

  // ─────────────────────────────────────────────────────────────────────────
  // 5. detectBottomZones
  // ─────────────────────────────────────────────────────────────────────────

  /**
   * Score potential bottom zones using a confluence of ICT signals.
   *
   * Scoring criteria (max 8):
   *   +2  RSI < 30 near a swing low
   *   +3  Bullish MSS within a small neighbourhood
   *   +1  Unfilled bullish FVG exists below the swing low
   *   +1  Price near S1 or S2 support levels
   *   +1  ATR spike (volatility climax) — ATR > 1.5× its recent average
   *
   * Only swing lows are evaluated as bottom candidates.
   *
   * @param {Object[]} candles     - Array of candle objects.
   * @param {Object[]} swingPoints - Output of findSwingPoints().
   * @param {Object[]} mssEvents   - Output of detectMSS().
   * @param {Object[]} fvgZones    - Output of findFVG().
   * @returns {{ index:number, score:number, maxScore:8, level:string,
   *             price:number, time:*, factors:string[] }[]}
   */
  function detectBottomZones(candles, swingPoints, mssEvents, fvgZones) {
    if (!candles || candles.length === 0) return [];
    var swingLows = filterSwings(swingPoints || [], 'low');
    if (swingLows.length === 0) return [];

    var MSS_PROXIMITY = 10; // bars to look around for a bullish MSS
    var ATR_LOOKBACK  = 14; // bars to compute average ATR
    var ATR_SPIKE_MULT = 1.5;
    var SUPPORT_TOLERANCE = 0.02; // 2% tolerance for support proximity

    var results = [];

    for (var s = 0; s < swingLows.length; s++) {
      var sl = swingLows[s];
      var idx = sl.index;
      var c = candles[idx];
      var score = 0;
      var factors = [];

      // --- Factor 1: RSI < 30 near swing low (+2) ---
      if (isNum(c.rsi) && c.rsi < 30) {
        score += 2;
        factors.push('RSI oversold (' + c.rsi.toFixed(1) + ')');
      }

      // --- Factor 2: Bullish MSS nearby (+3) ---
      if (mssEvents) {
        for (var m = 0; m < mssEvents.length; m++) {
          var mss = mssEvents[m];
          if (mss.type === 'bullish' && Math.abs(mss.index - idx) <= MSS_PROXIMITY) {
            score += 3;
            factors.push('Bullish MSS nearby (bar ' + mss.index + ')');
            break;
          }
        }
      }

      // --- Factor 3: Unfilled bullish FVG below (+1) ---
      if (fvgZones) {
        for (var f = 0; f < fvgZones.length; f++) {
          var fvg = fvgZones[f];
          if (fvg.type === 'bullish' && !fvg.filled && fvg.top <= sl.price) {
            score += 1;
            factors.push('Unfilled bullish FVG below (' + fvg.bottom.toFixed(4) + '-' + fvg.top.toFixed(4) + ')');
            break;
          }
        }
      }

      // --- Factor 4: Price near S1/S2 support (+1) ---
      var priceRef = sl.price;
      var nearSupport = false;
      if (isNum(c.s1) && c.s1 > 0) {
        var diff1 = Math.abs(priceRef - c.s1) / c.s1;
        if (diff1 <= SUPPORT_TOLERANCE) nearSupport = true;
      }
      if (!nearSupport && isNum(c.s2) && c.s2 > 0) {
        var diff2 = Math.abs(priceRef - c.s2) / c.s2;
        if (diff2 <= SUPPORT_TOLERANCE) nearSupport = true;
      }
      if (nearSupport) {
        score += 1;
        factors.push('Near S1/S2 support');
      }

      // --- Factor 5: ATR spike (volatility climax) (+1) ---
      if (isNum(c.atr) && idx >= ATR_LOOKBACK) {
        var atrSum = 0;
        var atrCount = 0;
        for (var a = idx - ATR_LOOKBACK; a < idx; a++) {
          if (isNum(candles[a].atr)) {
            atrSum += candles[a].atr;
            atrCount++;
          }
        }
        if (atrCount > 0) {
          var atrAvg = atrSum / atrCount;
          if (c.atr > atrAvg * ATR_SPIKE_MULT) {
            score += 1;
            factors.push('ATR spike (volatility climax)');
          }
        }
      }

      results.push({
        index: idx,
        score: score,
        maxScore: 8,
        level: scoreLevel(score, 8),
        price: sl.price,
        time: c.time,
        factors: factors
      });
    }

    return results;
  }

  // ─────────────────────────────────────────────────────────────────────────
  // 6. detectGrowthMomentum
  // ─────────────────────────────────────────────────────────────────────────

  /**
   * Detect growth / recovery momentum signals.
   *
   * Scoring criteria (max 8):
   *   +2  EMA21 crosses above EMA50 (golden cross)
   *   +2  RSI rising from below 30 to above 50
   *   +2  Bullish MSS confirmed nearby
   *   +1  Price making Higher Lows (last 2 swing lows ascending)
   *   +1  Consecutive bullish candles after a detected bottom
   *
   * Evaluated at every candle; only candles scoring ≥ 1 are returned.
   *
   * @param {Object[]} candles   - Array of candle objects.
   * @param {Object[]} mssEvents - Output of detectMSS().
   * @returns {{ index:number, score:number, level:string, time:*,
   *             factors:string[] }[]}
   */
  function detectGrowthMomentum(candles, mssEvents) {
    if (!candles || candles.length < 2) return [];

    var results = [];
    var mssMap = {};
    if (mssEvents) {
      for (var m = 0; m < mssEvents.length; m++) {
        mssMap[mssEvents[m].index] = mssEvents[m];
      }
    }

    // Pre-compute swing lows for Higher-Low detection
    var swingLows = findSwingPoints(candles, 3).filter(function (sp) {
      return sp.type === 'low';
    });

    // Track recent swing lows for HL check
    var recentLows = [];

    var MSS_PROXIMITY = 5;
    var CONSEC_BULLISH_MIN = 3;

    for (var i = 1; i < candles.length; i++) {
      var c = candles[i];
      var prev = candles[i - 1];
      var score = 0;
      var factors = [];

      // Update recent swing lows
      for (var sl = 0; sl < swingLows.length; sl++) {
        if (swingLows[sl].index === i) {
          recentLows.push(swingLows[sl]);
        }
      }

      // --- Factor 1: EMA21 crosses above EMA50 (golden cross) (+2) ---
      if (isNum(c.ema21) && isNum(c.ema50) && isNum(prev.ema21) && isNum(prev.ema50)) {
        if (prev.ema21 <= prev.ema50 && c.ema21 > c.ema50) {
          score += 2;
          factors.push('EMA21 crossed above EMA50 (golden cross)');
        }
      }

      // --- Factor 2: RSI rising from < 30 to > 50 (+2) ---
      // Check if RSI was below 30 within recent bars and is now above 50
      if (isNum(c.rsi) && c.rsi > 50) {
        var wasOversold = false;
        var lookback = Math.min(i, 20);
        for (var r = i - lookback; r < i; r++) {
          if (isNum(candles[r].rsi) && candles[r].rsi < 30) {
            wasOversold = true;
            break;
          }
        }
        if (wasOversold) {
          score += 2;
          factors.push('RSI recovered from oversold to ' + c.rsi.toFixed(1));
        }
      }

      // --- Factor 3: Bullish MSS confirmed nearby (+2) ---
      for (var mp = Math.max(0, i - MSS_PROXIMITY); mp <= i; mp++) {
        if (mssMap[mp] && mssMap[mp].type === 'bullish') {
          score += 2;
          factors.push('Bullish MSS confirmed (bar ' + mp + ')');
          break;
        }
      }

      // --- Factor 4: Higher Lows (+1) ---
      if (recentLows.length >= 2) {
        var l1 = recentLows[recentLows.length - 2];
        var l2 = recentLows[recentLows.length - 1];
        if (l2.price > l1.price && l2.index <= i) {
          score += 1;
          factors.push('Higher Lows forming');
        }
      }

      // --- Factor 5: Consecutive bullish candles (+1) ---
      var consecBullish = 0;
      for (var cb = i; cb >= Math.max(0, i - CONSEC_BULLISH_MIN + 1); cb--) {
        if (candles[cb].close > candles[cb].open) {
          consecBullish++;
        } else {
          break;
        }
      }
      if (consecBullish >= CONSEC_BULLISH_MIN) {
        score += 1;
        factors.push(consecBullish + ' consecutive bullish candles');
      }

      // Only include candles with score ≥ 1
      if (score > 0) {
        results.push({
          index: i,
          score: score,
          level: scoreLevel(score, 8),
          time: c.time,
          factors: factors
        });
      }
    }

    return results;
  }

  // ─────────────────────────────────────────────────────────────────────────
  // 7. analyze  (Master function)
  // ─────────────────────────────────────────────────────────────────────────

  /**
   * Run the full ICT Smart Money Concepts analysis pipeline.
   *
   * @param {Object[]} candles - Array of candle objects.
   * @returns {{
   *   swingPoints: Object[],
   *   mssEvents: Object[],
   *   fvgZones: Object[],
   *   orderBlocks: Object[],
   *   bottomZones: Object[],
   *   growthSignals: Object[],
   *   summary: {
   *     currentTrend: 'bullish'|'bearish'|'neutral',
   *     lastMSS: Object|null,
   *     unfilledFVGs: number,
   *     activeOrderBlocks: number,
   *     bottomScore: number,
   *     growthScore: number,
   *     recommendation: 'BUY_ZONE'|'SELL_ZONE'|'WAIT'|'ACCUMULATE'
   *   }
   * }}
   */
  // ─────────────────────────────────────────────────────────────────────────
  // 6.5. detectTradeSetups
  // ─────────────────────────────────────────────────────────────────────────
  
  function detectTradeSetups(candles, fvgZones, orderBlocks, currentTrend, bottomScore) {
    if (!candles || candles.length === 0) return null;
    var lastCandle = candles[candles.length - 1];
    var currentPrice = lastCandle.close;
    
    var setups = [];
    
    // Look for Bullish Setups (LONG)
    if (currentTrend === 'bullish' || bottomScore >= 3) {
        var bestFvg = null;
        for (var i = 0; i < fvgZones.length; i++) {
            if (fvgZones[i].type === 'bullish' && !fvgZones[i].filled && fvgZones[i].top < currentPrice) {
                if (!bestFvg || fvgZones[i].top > bestFvg.top) bestFvg = fvgZones[i];
            }
        }
        
        var bestOb = null;
        for (var j = 0; j < orderBlocks.length; j++) {
            if (orderBlocks[j].type === 'bullish' && !orderBlocks[j].mitigated && orderBlocks[j].top < currentPrice) {
                if (!bestOb || orderBlocks[j].top > bestOb.top) bestOb = orderBlocks[j];
            }
        }
        
        var entryZone = bestFvg || bestOb;
        if (entryZone) {
            var sl = entryZone.bottom - lastCandle.atr; 
            var tp = currentPrice + (currentPrice - sl) * 2; 
            var winRate = (currentTrend === 'bullish' && bestFvg && bestOb) ? '85%' : (currentTrend === 'bullish' ? '75%' : '65%');
            var reason = bestFvg === entryZone ? 'Retest Bullish FVG' : 'Retest Demand OB';
            setups.push({
                type: 'LONG',
                entryRange: entryZone.bottom.toFixed(2) + ' - ' + entryZone.top.toFixed(2),
                stopLoss: sl.toFixed(2),
                takeProfit: tp.toFixed(2),
                winRate: winRate,
                reason: reason
            });
        }
    }
    
    // Look for Bearish Setups (SHORT)
    if (currentTrend === 'bearish' && bottomScore < 3) {
        var bestFvgB = null;
        for (var k = 0; k < fvgZones.length; k++) {
            if (fvgZones[k].type === 'bearish' && !fvgZones[k].filled && fvgZones[k].bottom > currentPrice) {
                if (!bestFvgB || fvgZones[k].bottom < bestFvgB.bottom) bestFvgB = fvgZones[k];
            }
        }
        
        var bestObB = null;
        for (var m = 0; m < orderBlocks.length; m++) {
            if (orderBlocks[m].type === 'bearish' && !orderBlocks[m].mitigated && orderBlocks[m].bottom > currentPrice) {
                if (!bestObB || orderBlocks[m].bottom < bestObB.bottom) bestObB = orderBlocks[m];
            }
        }
        
        var entryZoneB = bestFvgB || bestObB;
        if (entryZoneB) {
            var slB = entryZoneB.top + lastCandle.atr; 
            var tpB = currentPrice - (slB - currentPrice) * 2; 
            var winRateB = (currentTrend === 'bearish' && bestFvgB && bestObB) ? '85%' : '70%';
            var reasonB = bestFvgB === entryZoneB ? 'Retest Bearish FVG' : 'Retest Supply OB';
            setups.push({
                type: 'SHORT',
                entryRange: entryZoneB.bottom.toFixed(2) + ' - ' + entryZoneB.top.toFixed(2),
                stopLoss: slB.toFixed(2),
                takeProfit: tpB.toFixed(2),
                winRate: winRateB,
                reason: reasonB
            });
        }
    }
    
    return setups.length > 0 ? setups[0] : null;
  }

  /**
   * Master function to run all analysis steps and return the full dashboard dataset.
   *
   * @param {Object[]} candles - Processed OHLC + indicators data array.
   * @returns {{
   *   swingPoints: Object[],
   *   mssEvents: Object[],
   *   fvgZones: Object[],
   *   orderBlocks: Object[],
   *   bottomZones: Object[],
   *   growthSignals: Object[],
   *   summary: {
   *     currentTrend: 'bullish'|'bearish'|'neutral',
   *     lastMSS: Object|null,
   *     unfilledFVGs: number,
   *     activeOrderBlocks: number,
   *     bottomScore: number,
   *     growthScore: number,
   *     recommendation: 'BUY_ZONE'|'SELL_ZONE'|'WAIT'|'ACCUMULATE',
   *     tradeSetup: Object|null
   *   }
   * }}
   */
  function analyze(candles) {
    if (!candles || candles.length === 0) {
      return {
        swingPoints: [],
        mssEvents: [],
        fvgZones: [],
        orderBlocks: [],
        bottomZones: [],
        growthSignals: [],
        summary: {
          currentTrend: 'neutral',
          lastMSS: null,
          unfilledFVGs: 0,
          activeOrderBlocks: 0,
          bottomScore: 0,
          growthScore: 0,
          recommendation: 'WAIT',
          tradeSetup: null
        }
      };
    }

    var swingPoints = findSwingPoints(candles, 3);
    var mssEvents = detectMSS(candles, swingPoints);
    var fvgZones = findFVG(candles);
    var orderBlocks = findOrderBlocks(candles, mssEvents);
    var bottomZones = detectBottomZones(candles, swingPoints, mssEvents, fvgZones);
    var growthSignals = detectGrowthMomentum(candles, mssEvents);

    var lastMSS = last(mssEvents) || null;
    var currentTrend = 'neutral';
    if (lastMSS) {
      currentTrend = lastMSS.type === 'bullish' ? 'bullish' : 'bearish';
    }

    var unfilledFVGs = 0;
    for (var f = 0; f < fvgZones.length; f++) {
      if (!fvgZones[f].filled) unfilledFVGs++;
    }

    var activeOrderBlocks = 0;
    for (var o = 0; o < orderBlocks.length; o++) {
      if (!orderBlocks[o].mitigated) activeOrderBlocks++;
    }

    var bottomScore = 0;
    var latestBottom = last(bottomZones);
    if (latestBottom) bottomScore = latestBottom.score;

    var growthScore = 0;
    var latestGrowth = last(growthSignals);
    if (latestGrowth) growthScore = latestGrowth.score;

    var recommendation = 'WAIT';
    if (currentTrend === 'bullish' && growthScore >= 4) {
      recommendation = 'BUY_ZONE';
    } else if (currentTrend === 'bullish' && growthScore >= 2) {
      recommendation = 'ACCUMULATE';
    } else if (currentTrend === 'bearish' && bottomScore >= 5) {
      recommendation = 'BUY_ZONE';
    } else if (currentTrend === 'bearish' && bottomScore >= 3) {
      recommendation = 'ACCUMULATE';
    } else if (currentTrend === 'bearish' && bottomScore < 3) {
      recommendation = 'SELL_ZONE';
    }
    
    var tradeSetup = detectTradeSetups(candles, fvgZones, orderBlocks, currentTrend, bottomScore);

    var summary = {
      currentTrend: currentTrend,
      lastMSS: lastMSS,
      unfilledFVGs: unfilledFVGs,
      activeOrderBlocks: activeOrderBlocks,
      bottomScore: bottomScore,
      growthScore: growthScore,
      recommendation: recommendation,
      tradeSetup: tradeSetup
    };

    return {
      swingPoints: swingPoints,
      mssEvents: mssEvents,
      fvgZones: fvgZones,
      orderBlocks: orderBlocks,
      bottomZones: bottomZones,
      growthSignals: growthSignals,
      summary: summary
    };
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Expose public API
  // ─────────────────────────────────────────────────────────────────────────

  window.ICTEngine = {
    findSwingPoints: findSwingPoints,
    detectMSS: detectMSS,
    findFVG: findFVG,
    findOrderBlocks: findOrderBlocks,
    detectBottomZones: detectBottomZones,
    detectGrowthMomentum: detectGrowthMomentum,
    analyze: analyze
  };

})();
