import pandas as pd
import ict_engine

for code in ['ZC', 'ZW', 'ZS']:
    df = pd.read_csv(f'{code}_active_H1.csv')
    df_ict = df.rename(columns={
        'Time': 'time', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close',
        'EMA_21': 'ema21', 'EMA_50': 'ema50', 'RSI': 'rsi', 'ATR': 'atr',
        'S1': 's1', 'S2': 's2', 'R1': 'r1', 'R2': 'r2'
    })
    candles  = df_ict.to_dict('records')
    last     = candles[-1]
    result   = ict_engine.analyze(candles)

    all_mss  = result['mss']           # Tất cả events (sweep + choch + mss)
    real_mss = result['real_mss']      # Chỉ MSS thật
    trend    = result['trend']
    setup    = result['setup']
    ob_list  = result['ob']
    last_confirmed_mss = result.get('last_mss_event')

    price        = last['close']
    ema21        = last.get('ema21', 0)
    ema50        = last.get('ema50', 0)
    entry_bottom = min(ema21, ema50)
    entry_top    = max(ema21, ema50)

    # Đếm theo signal type
    sweep_count = sum(1 for e in all_mss if e.get('signal') == 'sweep')
    choch_count = sum(1 for e in all_mss if e.get('signal') == 'choch')
    mss_count   = len(real_mss)

    # HQ OB và Breaker Block
    hq_obs   = [o for o in ob_list if o.get('hq') and not o['mitigated']]
    breakers = [o for o in ob_list if o.get('breaker')]

    print(f'=== {code} ===')
    print(f'  Gia hien tai  : {price:.2f}')
    print(f'  EMA 21        : {ema21:.2f}')
    print(f'  EMA 50        : {ema50:.2f}')
    print(f'  Vung EMA      : {entry_bottom:.2f} - {entry_top:.2f}')
    print(f'  Events        : {sweep_count} Sweep | {choch_count} CHoCH | {mss_count} MSS that')
    print(f'  Xu huong MSS  : {trend}')

    if last_confirmed_mss:
        candle_since = len(candles) - 1 - last_confirmed_mss['index']
        sweep_info   = " [Sweep-confirmed ✓]" if last_confirmed_mss.get('had_sweep') else ""
        print(f'  MSS cuoi cung : {last_confirmed_mss["type"]} ({last_confirmed_mss.get("signal","?")}{sweep_info}) | {candle_since} nen truoc')

    if hq_obs:
        print(f'  HQ OB         : {len(hq_obs)} zone(s) — {hq_obs[-1]["type"]} | {hq_obs[-1]["bottom"]:.2f} - {hq_obs[-1]["top"]:.2f}')
    if breakers:
        print(f'  Breaker Block : {len(breakers)} zone(s) — {breakers[-1]["type"]} | {breakers[-1]["bottom"]:.2f} - {breakers[-1]["top"]:.2f}')

    if setup:
        print(f'  Setup         : {setup["type"]} | Entry: {setup["entryRange"]} | Win Rate: {setup["winRate"]}%')
        print(f'  Ly do         : {setup["reason"]}')
    else:
        if trend == 'bullish':
            if entry_top >= price:
                print(f'  Ly do khong co LONG: EMA top ({entry_top:.2f}) >= Gia ({price:.2f}) => Gia dang duoi/trong vung EMA')
        elif trend == 'bearish':
            if entry_bottom <= price:
                print(f'  Ly do khong co SHORT: EMA bottom ({entry_bottom:.2f}) <= Gia ({price:.2f}) => Gia dang tren/trong vung EMA')
        else:
            print(f'  Xu huong: {trend} - Chua co MSS ro rang')
    print()
