"""Limites da carteira simulada em USDT."""
FEE=0.001
STOP=0.015
TAKE=0.03
MAX_POSITIONS=2
DAILY_LOSS=0.03

def entry_allowed(equity, daily_start, positions, symbol):
    return daily_start>0 and equity>daily_start*(1-DAILY_LOSS) and len(positions)<MAX_POSITIONS and symbol not in positions

def order_budget(cash, equity):
    return min(cash,equity*0.5)

def exit_reason(entry,bid,signal):
    if bid<=entry*(1-STOP): return 'stop-loss'
    if bid>=entry*(1+TAKE): return 'take-profit'
    if signal=='sell': return 'cruzamento de baixa'
    return None
