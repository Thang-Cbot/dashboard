import math

# ─────────────────────────────────────────────────────────────────────────────
# ICT ENGINE v2.0 — Nâng cấp theo DCBOT_Chart_T6.15R02
# Cải tiến:
#   1. MSS + Sweep + CHoCH (3 cấp độ, bắt tín hiệu sớm hơn và chính xác hơn)
#   2. HQ Order Block (lọc theo body >= 0.55 ATR)
#   3. Breaker Block (OB cũ bị phá → chuyển thành vùng đảo chiều)
#   4. Giữ nguyên EMA Zone làm vùng Entry (phù hợp đặc tính Nông sản CBOT)
# ─────────────────────────────────────────────────────────────────────────────

SWEEP_LOOKBACK  = 36   # Số nến lookback để xác nhận có Sweep trước MSS
CHOCH_LOOKBACK  = 36   # Số nến lookback để xác nhận CHoCH sau Sweep
HQ_OB_ATR_MULT  = 0.55 # Thân nến OB phải >= HQ_OB_ATR_MULT * ATR để là HQ OB


def is_num(v):
    return v is not None and isinstance(v, (int, float)) and math.isfinite(v)


def score_level(score, max_score):
    pct = score / max_score
    if pct >= 0.6: return 'strong'
    if pct >= 0.35: return 'moderate'
    return 'weak'


def calc_atr(candles, period=14):
    """Tính ATR đơn giản (True Range trung bình) cho từng nến."""
    trs = []
    for i in range(1, len(candles)):
        h = candles[i]['high']
        l = candles[i]['low']
        pc = candles[i - 1]['close']
        tr = max(h - l, abs(h - pc), abs(l - pc))
        trs.append(tr)
    # Sliding window ATR
    atrs = [None] * len(candles)
    for i in range(period, len(candles)):
        window = trs[max(0, i - period):i]
        if window:
            atrs[i] = sum(window) / len(window)
    return atrs


def find_swing_points(candles, lookback=3):
    """Tìm Swing High và Swing Low với lookback bars mỗi bên."""
    if not candles: return []
    results = []
    length = len(candles)
    for i in range(lookback, length - lookback):
        c = candles[i]
        is_swing_high = True
        is_swing_low = True
        for j in range(1, lookback + 1):
            left = candles[i - j]
            right = candles[i + j]
            if c['high'] <= left['high'] or c['high'] <= right['high']:
                is_swing_high = False
            if c['low'] >= left['low'] or c['low'] >= right['low']:
                is_swing_low = False
            if not is_swing_high and not is_swing_low:
                break
        if is_swing_high:
            results.append({'index': i, 'type': 'high', 'price': c['high'], 'time': c['time']})
        if is_swing_low:
            results.append({'index': i, 'type': 'low', 'price': c['low'], 'time': c['time']})
    return results


# ─────────────────────────────────────────────────────────────────────────────
# PHẦN 1: MSS + SWEEP + CHoCH (Nâng cấp từ DCBOT)
# ─────────────────────────────────────────────────────────────────────────────

def detect_mss(candles, swing_points):
    """
    Phát hiện Market Structure Shift (MSS) + Sweep + CHoCH theo chuẩn ICT/DCBOT.
    
    3 cấp độ tín hiệu:
    - 'sweep'  : Giá phá qua Swing High/Low nhưng ĐÓNG CỬA ngược lại → Liquidity Sweep (giả)
    - 'choch'  : Sau Sweep, close vượt high của cây nến sweep → Change of Character (sớm)
    - 'mss'    : Close đóng hẳn qua Swing High/Low → MSS thật (mạnh nhất)
    
    Returns list of events:
    {
        'index', 'type' (bullish/bearish), 'signal' (mss/choch/sweep),
        'price', 'time', 'breakLevel', 'had_sweep' (bool)
    }
    """
    if not candles or not swing_points or len(swing_points) < 4:
        return []

    results = []
    last_swing_high = None
    last_swing_low  = None

    # Sweep tracking
    last_bsl_sweep_idx = None  # Lần sweep gần nhất qua BSL (Buy Side Liquidity = Swing High)
    last_ssl_sweep_idx = None  # Lần sweep gần nhất qua SSL (Sell Side Liquidity = Swing Low)
    last_bsl_sweep_high = None  # High của cây nến sweep BSL (dùng cho CHoCH)
    last_ssl_sweep_low  = None  # Low của cây nến sweep SSL (dùng cho CHoCH)

    swing_at_index = {}
    for sp in swing_points:
        idx = sp['index']
        if idx not in swing_at_index: swing_at_index[idx] = []
        swing_at_index[idx].append(sp)

    for i in range(len(candles)):
        c = candles[i]

        # Cập nhật Swing Points mới nhất
        if i in swing_at_index:
            for ev in swing_at_index[i]:
                if ev['type'] == 'high': last_swing_high = ev
                else: last_swing_low = ev

        if not last_swing_high or not last_swing_low:
            continue

        # ── BSL Sweep: High phá qua Swing High nhưng Close đóng lại dưới ──
        if c['high'] > last_swing_high['price'] and c['close'] < last_swing_high['price'] and i > last_swing_high['index']:
            last_bsl_sweep_idx  = i
            last_bsl_sweep_high = c['high']
            results.append({
                'index': i, 'type': 'bearish', 'signal': 'sweep',
                'price': c['close'], 'time': c['time'],
                'breakLevel': last_swing_high['price'], 'had_sweep': False
            })

        # ── SSL Sweep: Low phá qua Swing Low nhưng Close đóng lại trên ──
        if c['low'] < last_swing_low['price'] and c['close'] > last_swing_low['price'] and i > last_swing_low['index']:
            last_ssl_sweep_idx  = i
            last_ssl_sweep_low  = c['low']
            results.append({
                'index': i, 'type': 'bullish', 'signal': 'sweep',
                'price': c['close'], 'time': c['time'],
                'breakLevel': last_swing_low['price'], 'had_sweep': False
            })

        # ── Bull CHoCH: Sau SSL Sweep, close vượt high của cây sweep đó ──
        if (last_ssl_sweep_idx is not None
                and last_bsl_sweep_high is None  # chưa bị đảo lại bởi BSL
                and i > last_ssl_sweep_idx
                and (i - last_ssl_sweep_idx) <= CHOCH_LOOKBACK
                and last_ssl_sweep_low is not None
                and c['close'] > candles[last_ssl_sweep_idx]['high']):
            recent_ssl = True
            # Thêm vào kết quả nếu chưa có CHoCH/MSS bullish gần đây
            if not results or results[-1].get('signal') not in ('choch', 'mss') or results[-1]['type'] != 'bullish':
                results.append({
                    'index': i, 'type': 'bullish', 'signal': 'choch',
                    'price': c['close'], 'time': c['time'],
                    'breakLevel': last_swing_low['price'], 'had_sweep': True
                })

        # ── Bear CHoCH: Sau BSL Sweep, close phá qua low của cây sweep đó ──
        if (last_bsl_sweep_idx is not None
                and last_ssl_sweep_low is None
                and i > last_bsl_sweep_idx
                and (i - last_bsl_sweep_idx) <= CHOCH_LOOKBACK
                and last_bsl_sweep_high is not None
                and c['close'] < candles[last_bsl_sweep_idx]['low']):
            if not results or results[-1].get('signal') not in ('choch', 'mss') or results[-1]['type'] != 'bearish':
                results.append({
                    'index': i, 'type': 'bearish', 'signal': 'choch',
                    'price': c['close'], 'time': c['time'],
                    'breakLevel': last_swing_high['price'], 'had_sweep': True
                })

        # ── Bullish MSS thật: Close đóng hẳn TRÊN Swing High ──
        if c['close'] > last_swing_high['price'] and i > last_swing_high['index']:
            had_sweep = (last_ssl_sweep_idx is not None
                         and (i - last_ssl_sweep_idx) <= SWEEP_LOOKBACK)
            last_event = results[-1] if results else None
            duplicate = (last_event and last_event['type'] == 'bullish'
                         and last_event['signal'] == 'mss'
                         and last_event['breakLevel'] == last_swing_high['price'])
            if not duplicate:
                results.append({
                    'index': i, 'type': 'bullish', 'signal': 'mss',
                    'price': c['close'], 'time': c['time'],
                    'breakLevel': last_swing_high['price'], 'had_sweep': had_sweep
                })
                # Reset sweep sau khi MSS xác nhận
                last_ssl_sweep_idx = None
                last_ssl_sweep_low  = None

        # ── Bearish MSS thật: Close đóng hẳn DƯỚI Swing Low ──
        if c['close'] < last_swing_low['price'] and i > last_swing_low['index']:
            had_sweep = (last_bsl_sweep_idx is not None
                         and (i - last_bsl_sweep_idx) <= SWEEP_LOOKBACK)
            last_event = results[-1] if results else None
            duplicate = (last_event and last_event['type'] == 'bearish'
                         and last_event['signal'] == 'mss'
                         and last_event['breakLevel'] == last_swing_low['price'])
            if not duplicate:
                results.append({
                    'index': i, 'type': 'bearish', 'signal': 'mss',
                    'price': c['close'], 'time': c['time'],
                    'breakLevel': last_swing_low['price'], 'had_sweep': had_sweep
                })
                # Reset sweep sau khi MSS xác nhận
                last_bsl_sweep_idx  = None
                last_bsl_sweep_high = None

    return results


def get_last_confirmed_mss(mss_events):
    """Lấy MSS xác nhận cuối cùng (ưu tiên: mss > choch > sweep) để xác định xu hướng."""
    # Ưu tiên signal mạnh nhất, gần nhất
    priority = {'mss': 3, 'choch': 2, 'sweep': 1}
    confirmed = [e for e in mss_events if e['signal'] in ('mss', 'choch')]
    if confirmed:
        return confirmed[-1]
    if mss_events:
        return mss_events[-1]
    return None


# ─────────────────────────────────────────────────────────────────────────────
# PHẦN 2: FVG (Giữ nguyên, bổ sung lọc FVG quan trọng)
# ─────────────────────────────────────────────────────────────────────────────

def find_fvg(candles, mss_events=None):
    """
    Tìm Fair Value Gap (FVG) — chỉ giữ FVG trong context MSS/Sweep (quan trọng).
    Bull FVG: low[i+2] > high[i]
    Bear FVG: high[i+2] < low[i]
    """
    if not candles or len(candles) < 3: return []

    # Tập hợp các bar có MSS/Sweep để xác định context
    mss_bars = set()
    if mss_events:
        for e in mss_events:
            for offset in range(-5, SWEEP_LOOKBACK + 1):
                mss_bars.add(e['index'] + offset)

    results = []
    for i in range(len(candles) - 2):
        c1 = candles[i]
        c3 = candles[i + 2]
        in_context = not mss_events or (i in mss_bars or (i + 2) in mss_bars)

        # Bull FVG
        if c3['low'] > c1['high']:
            fvg = {
                'startIndex': i, 'endIndex': i + 2, 'type': 'bullish',
                'top': c3['low'], 'bottom': c1['high'],
                'filled': False, 'fillIndex': None,
                'important': in_context
            }
            for k in range(i + 3, len(candles)):
                if candles[k]['low'] <= fvg['bottom']:
                    fvg['filled'] = True
                    fvg['fillIndex'] = k
                    break
            results.append(fvg)

        # Bear FVG
        if c3['high'] < c1['low']:
            fvgB = {
                'startIndex': i, 'endIndex': i + 2, 'type': 'bearish',
                'top': c1['low'], 'bottom': c3['high'],
                'filled': False, 'fillIndex': None,
                'important': in_context
            }
            for k in range(i + 3, len(candles)):
                if candles[k]['high'] >= fvgB['top']:
                    fvgB['filled'] = True
                    fvgB['fillIndex'] = k
                    break
            results.append(fvgB)
    return results


# ─────────────────────────────────────────────────────────────────────────────
# PHẦN 3: ORDER BLOCK + HQ OB + BREAKER BLOCK (Nâng cấp từ DCBOT)
# ─────────────────────────────────────────────────────────────────────────────

def find_order_blocks(candles, mss_events, atr_list=None):
    """
    Tìm Order Block (OB) gắn với từng MSS event.
    
    Nâng cấp:
    - HQ OB: thân nến >= 0.55 * ATR (lọc OB chất lượng cao)
    - Breaker Block: OB bị giá phá qua sau này → đảo vai trò
    
    Returns: list of OB dicts với trường 'hq' (bool) và 'breaker' (bool)
    """
    if not candles or not mss_events: return []
    results = []

    for mss in mss_events:
        # Chỉ xét MSS thật và CHoCH (bỏ qua Sweep đơn thuần)
        if mss.get('signal') == 'sweep':
            continue

        ob_candle = None
        ob_index  = -1

        if mss['type'] == 'bullish':
            # Bull OB: Nến đỏ (bearish candle) ngay trước MSS, càng gần càng tốt
            for j in range(mss['index'] - 1, max(mss['index'] - 10, -1), -1):
                if candles[j]['close'] < candles[j]['open']:
                    ob_candle = candles[j]
                    ob_index  = j
                    break
        else:
            # Bear OB: Nến xanh (bullish candle) ngay trước MSS
            for j in range(mss['index'] - 1, max(mss['index'] - 10, -1), -1):
                if candles[j]['close'] > candles[j]['open']:
                    ob_candle = candles[j]
                    ob_index  = j
                    break

        if not ob_candle:
            continue

        # Tính ATR tại thời điểm OB
        atr_val = None
        if atr_list and ob_index < len(atr_list):
            atr_val = atr_list[ob_index]
        if not atr_val and is_num(ob_candle.get('atr')):
            atr_val = ob_candle['atr']

        body = abs(ob_candle['close'] - ob_candle['open'])
        is_hq = (atr_val is not None and body >= HQ_OB_ATR_MULT * atr_val)

        ob = {
            'index':     ob_index,
            'mss_index': mss['index'],
            'type':      mss['type'],
            'top':       ob_candle['high'],
            'bottom':    ob_candle['low'],
            'time':      ob_candle['time'],
            'mitigated': False,
            'hq':        is_hq,          # High Quality OB flag
            'breaker':   False,          # Sẽ set True nếu bị phá → Breaker Block
            'had_sweep': mss.get('had_sweep', False)
        }

        # Kiểm tra mitigated (OB bị chạm)
        for k in range(mss['index'] + 1, len(candles)):
            c = candles[k]
            if ob['type'] == 'bullish':
                if c['low'] <= ob['bottom']:
                    ob['mitigated'] = True
                    break
            else:
                if c['high'] >= ob['top']:
                    ob['mitigated'] = True
                    break

        # Kiểm tra Breaker Block: OB bị giá phá hoàn toàn (close vượt qua)
        for k in range(mss['index'] + 1, len(candles)):
            c = candles[k]
            if ob['type'] == 'bullish' and c['close'] < ob['bottom']:
                ob['breaker'] = True
                break
            if ob['type'] == 'bearish' and c['close'] > ob['top']:
                ob['breaker'] = True
                break

        results.append(ob)

    return results


# ─────────────────────────────────────────────────────────────────────────────
# PHẦN 4: BOTTOM / TOP ZONES (Giữ nguyên + nâng cấp có CHoCH)
# ─────────────────────────────────────────────────────────────────────────────

def detect_bottom_zones(candles, swing_points, mss_events, fvg_zones):
    if not candles: return []
    swing_lows = [sp for sp in (swing_points or []) if sp['type'] == 'low']
    if not swing_lows: return []

    MSS_PROXIMITY    = 10
    ATR_LOOKBACK     = 14
    ATR_SPIKE_MULT   = 1.5
    SUPPORT_TOLERANCE = 0.02

    results = []
    for sl in swing_lows:
        idx = sl['index']
        c   = candles[idx]
        score   = 0
        factors = []

        if is_num(c.get('rsi')) and c['rsi'] < 30:
            score += 2
            factors.append(f"RSI oversold ({c['rsi']:.1f})")

        if mss_events:
            for mss in mss_events:
                if mss['type'] == 'bullish' and abs(mss['index'] - idx) <= MSS_PROXIMITY:
                    bonus = 4 if mss.get('had_sweep') and mss.get('signal') == 'mss' else (3 if mss.get('signal') == 'mss' else 2)
                    score += bonus
                    label  = "Bullish MSS (sweep-confirmed)" if mss.get('had_sweep') else f"Bullish {mss.get('signal','mss').upper()} nearby"
                    factors.append(label)
                    break

        if fvg_zones:
            for fvg in fvg_zones:
                if fvg['type'] == 'bullish' and not fvg['filled'] and fvg['top'] <= sl['price']:
                    score += 1
                    factors.append("Unfilled bullish FVG below")
                    break

        near_support = False
        if is_num(c.get('s1')) and c['s1'] > 0:
            if abs(sl['price'] - c['s1']) / c['s1'] <= SUPPORT_TOLERANCE:
                near_support = True
        if not near_support and is_num(c.get('s2')) and c['s2'] > 0:
            if abs(sl['price'] - c['s2']) / c['s2'] <= SUPPORT_TOLERANCE:
                near_support = True
        if near_support:
            score += 1
            factors.append("Near S1/S2 support")

        if is_num(c.get('atr')) and idx >= ATR_LOOKBACK:
            atr_vals = [candles[a]['atr'] for a in range(idx - ATR_LOOKBACK, idx) if is_num(candles[a].get('atr'))]
            if atr_vals:
                atr_avg = sum(atr_vals) / len(atr_vals)
                if c['atr'] > atr_avg * ATR_SPIKE_MULT:
                    score += 1
                    factors.append("ATR spike")

        results.append({
            'index': idx, 'score': score, 'maxScore': 8, 'level': score_level(score, 8),
            'price': sl['price'], 'time': c['time'], 'factors': factors
        })
    return results


def detect_top_zones(candles, swing_points, mss_events, fvg_zones):
    if not candles: return []
    swing_highs = [sp for sp in (swing_points or []) if sp['type'] == 'high']
    if not swing_highs: return []

    MSS_PROXIMITY    = 10
    ATR_LOOKBACK     = 14
    ATR_SPIKE_MULT   = 1.5
    SUPPORT_TOLERANCE = 0.02

    results = []
    for sh in swing_highs:
        idx = sh['index']
        c   = candles[idx]
        score   = 0
        factors = []

        if is_num(c.get('rsi')) and c['rsi'] > 70:
            score += 2
            factors.append(f"RSI overbought ({c['rsi']:.1f})")

        if mss_events:
            for mss in mss_events:
                if mss['type'] == 'bearish' and abs(mss['index'] - idx) <= MSS_PROXIMITY:
                    bonus = 4 if mss.get('had_sweep') and mss.get('signal') == 'mss' else (3 if mss.get('signal') == 'mss' else 2)
                    score += bonus
                    label  = "Bearish MSS (sweep-confirmed)" if mss.get('had_sweep') else f"Bearish {mss.get('signal','mss').upper()} nearby"
                    factors.append(label)
                    break

        if fvg_zones:
            for fvg in fvg_zones:
                if fvg['type'] == 'bearish' and not fvg['filled'] and fvg['bottom'] >= sh['price']:
                    score += 1
                    factors.append("Unfilled bearish FVG above")
                    break

        near_resistance = False
        if is_num(c.get('r1')) and c['r1'] > 0:
            if abs(sh['price'] - c['r1']) / c['r1'] <= SUPPORT_TOLERANCE:
                near_resistance = True
        if not near_resistance and is_num(c.get('r2')) and c['r2'] > 0:
            if abs(sh['price'] - c['r2']) / c['r2'] <= SUPPORT_TOLERANCE:
                near_resistance = True
        if near_resistance:
            score += 1
            factors.append("Near R1/R2 resistance")

        if is_num(c.get('atr')) and idx >= ATR_LOOKBACK:
            atr_vals = [candles[a]['atr'] for a in range(idx - ATR_LOOKBACK, idx) if is_num(candles[a].get('atr'))]
            if atr_vals:
                atr_avg = sum(atr_vals) / len(atr_vals)
                if c['atr'] > atr_avg * ATR_SPIKE_MULT:
                    score += 1
                    factors.append("ATR spike")

        results.append({
            'index': idx, 'score': score, 'maxScore': 8, 'level': score_level(score, 8),
            'price': sh['price'], 'time': c['time'], 'factors': factors
        })
    return results


# ─────────────────────────────────────────────────────────────────────────────
# PHẦN 5: SETUP DETECTION (EMA Zone giữ nguyên + nâng cấp Win Rate)
# ─────────────────────────────────────────────────────────────────────────────

def detect_trade_setups(candles, fvg_zones, order_blocks, current_trend, bottom_score, top_score, mss_events=None):
    """
    Xác định điểm vào lệnh:
    - Vùng Entry: EMA 21-50 (giữ nguyên — phù hợp nhất với CBOT Nông sản)
    - Win Rate nâng cấp: có thêm yếu tố Sweep-confirmed MSS, HQ OB, Breaker Block
    """
    if not candles: return None
    last_candle   = candles[-1]
    current_price = last_candle['close']
    ema21 = last_candle.get('ema21', current_price)
    ema50 = last_candle.get('ema50', ema21)
    atr   = last_candle.get('atr', 2.0)

    # Kiểm tra MSS gần nhất có sweep-confirmed không
    last_mss = get_last_confirmed_mss(mss_events) if mss_events else None
    sweep_confirmed = last_mss.get('had_sweep', False) if last_mss else False
    is_choch = last_mss.get('signal') == 'choch' if last_mss else False

    # ── LONG SETUP ──────────────────────────────────────────────────────────
    if current_trend == 'bullish' or bottom_score >= 3:
        entry_top    = max(ema21, ema50)
        entry_bottom = min(ema21, ema50)

        if entry_top < current_price:
            sl = entry_bottom - max(4.0, atr * 1.5)
            rr_distance = (entry_bottom - sl) * 2
            tp = entry_top + rr_distance

            has_fvg  = any(
                f['type'] == 'bullish' and not f['filled']
                and f['bottom'] >= entry_bottom and f['top'] <= entry_top
                for f in fvg_zones
            )
            has_ob   = any(
                o['type'] == 'bullish' and not o['mitigated'] and o['top'] <= entry_top
                for o in order_blocks
            )
            has_hq_ob = any(
                o['type'] == 'bullish' and not o['mitigated'] and o['top'] <= entry_top and o.get('hq')
                for o in order_blocks
            )
            has_breaker = any(
                o['type'] == 'bearish' and o.get('breaker') and o['bottom'] >= entry_bottom
                for o in order_blocks
            )

            # Tính Win Rate theo chất lượng tín hiệu
            win_rate = 65
            if current_trend == 'bullish':
                bonus = 0
                if sweep_confirmed: bonus += 10   # MSS có Sweep xác nhận trước → +10%
                if has_hq_ob:       bonus += 5    # HQ Order Block → +5%
                elif has_ob:        bonus += 3
                if has_fvg:         bonus += 3    # FVG hỗ trợ → +3%
                if has_breaker:     bonus += 4    # Breaker Block đảo chiều → +4%
                if is_choch:        bonus -= 5    # CHoCH chưa xác nhận đủ → -5%
                win_rate = min(90, 65 + bonus)

            reason = 'Cho Pullback ve vung EMA 21-50 de BUY'
            if sweep_confirmed: reason += ' + Sweep-confirmed MSS'
            if has_hq_ob:       reason += ' + HQ Order Block'
            elif has_ob:        reason += ' + Order Block'
            if has_fvg:         reason += ' + FVG ho tro'
            if has_breaker:     reason += ' + Breaker Block'

            return {
                'type': 'LONG',
                'entryRange': f"{entry_bottom:.2f} - {entry_top:.2f}",
                'stopLoss': sl, 'takeProfit': tp,
                'winRate': win_rate, 'reason': reason
            }

    # ── SHORT SETUP ─────────────────────────────────────────────────────────
    if current_trend == 'bearish' or top_score >= 3:
        entry_bottom = min(ema21, ema50)
        entry_top    = max(ema21, ema50)

        if entry_bottom > current_price:
            sl = entry_top + max(4.0, atr * 1.5)
            rr_distance = (sl - entry_top) * 2
            tp = entry_bottom - rr_distance

            has_fvg   = any(
                f['type'] == 'bearish' and not f['filled']
                and f['bottom'] >= entry_bottom and f['top'] <= entry_top
                for f in fvg_zones
            )
            has_ob    = any(
                o['type'] == 'bearish' and not o['mitigated'] and o['bottom'] >= entry_bottom
                for o in order_blocks
            )
            has_hq_ob = any(
                o['type'] == 'bearish' and not o['mitigated'] and o['bottom'] >= entry_bottom and o.get('hq')
                for o in order_blocks
            )
            has_breaker = any(
                o['type'] == 'bullish' and o.get('breaker') and o['top'] <= entry_top
                for o in order_blocks
            )

            win_rate = 65
            if current_trend == 'bearish':
                bonus = 0
                if sweep_confirmed: bonus += 10
                if has_hq_ob:       bonus += 5
                elif has_ob:        bonus += 3
                if has_fvg:         bonus += 3
                if has_breaker:     bonus += 4
                if is_choch:        bonus -= 5
                win_rate = min(90, 65 + bonus)

            reason = 'Cho hoi ve vung EMA 21-50 de SELL'
            if sweep_confirmed: reason += ' + Sweep-confirmed MSS'
            if has_hq_ob:       reason += ' + HQ Order Block'
            elif has_ob:        reason += ' + Order Block'
            if has_fvg:         reason += ' + FVG can'
            if has_breaker:     reason += ' + Breaker Block'

            return {
                'type': 'SHORT',
                'entryRange': f"{entry_bottom:.2f} - {entry_top:.2f}",
                'stopLoss': sl, 'takeProfit': tp,
                'winRate': win_rate, 'reason': reason
            }

    return None


# ─────────────────────────────────────────────────────────────────────────────
# PHẦN 6: ANALYZE — Hàm tổng hợp
# ─────────────────────────────────────────────────────────────────────────────

def analyze(candles):
    """
    Phân tích đầy đủ toàn bộ dữ liệu nến cho một mã hàng hóa.
    Returns dict với tất cả kết quả phân tích.
    """
    sp  = find_swing_points(candles)
    mss = detect_mss(candles, sp)
    fvg = find_fvg(candles, mss)
    ob  = find_order_blocks(candles, mss)
    bz  = detect_bottom_zones(candles, sp, mss, fvg)
    tz  = detect_top_zones(candles, sp, mss, fvg)

    # Xu hướng từ MSS xác nhận gần nhất (mss > choch > sweep)
    last_confirmed = get_last_confirmed_mss(mss)
    current_trend  = last_confirmed['type'] if last_confirmed else 'neutral'

    # Lấy MSS thật (signal='mss') để đếm và báo cáo
    real_mss = [e for e in mss if e.get('signal') == 'mss']

    last_bz      = bz[-1] if bz else None
    bottom_score = last_bz['score'] if last_bz else 0

    last_tz    = tz[-1] if tz else None
    top_score  = last_tz['score'] if last_tz else 0

    setup = detect_trade_setups(candles, fvg, ob, current_trend, bottom_score, top_score, mss)

    return {
        'swing_points': sp,
        'mss':          mss,          # Tất cả events: sweep + choch + mss
        'real_mss':     real_mss,     # Chỉ MSS thật (signal='mss')
        'fvg':          fvg,
        'ob':           ob,
        'bottom_zones': bz,
        'top_zones':    tz,
        'setup':        setup,
        'trend':        current_trend,
        'last_mss_event': last_confirmed
    }
