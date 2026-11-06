"""Indicadores para candles fechados; não executa operações."""

def ema(values, period):
    if period <= 0 or len(values) < period: raise ValueError('Histórico insuficiente para EMA')
    value = sum(values[:period]) / period
    for price in values[period:]: value += (price - value) * 2 / (period + 1)
    return value

def rsi(values, period=14):
    if period <= 0 or len(values) < period + 1: raise ValueError('Histórico insuficiente para RSI')
    changes = [b-a for a,b in zip(values, values[1:])]
    gain = sum(max(x,0) for x in changes[:period])/period
    loss = sum(max(-x,0) for x in changes[:period])/period
    for change in changes[period:]:
        gain = (gain*(period-1)+max(change,0))/period
        loss = (loss*(period-1)+max(-change,0))/period
    if loss == 0: return 100.0 if gain else 50.0
    return 100-100/(1+gain/loss)

def macd(values, fast=12, slow=26, signal=9):
    if not 0 < fast < slow or signal <= 0 or len(values) < slow+signal-1: raise ValueError('Histórico insuficiente para MACD')
    fast_value = sum(values[:fast])/fast
    fast_series = [fast_value]
    for price in values[fast:]:
        fast_value += (price-fast_value)*2/(fast+1)
        fast_series.append(fast_value)
    slow_value = sum(values[:slow])/slow
    line = [fast_series[slow-fast]-slow_value]
    for idx in range(slow, len(values)):
        slow_value += (values[idx]-slow_value)*2/(slow+1)
        line.append(fast_series[idx-fast+1]-slow_value)
    macd_value=line[-1]; signal_value=ema(line,signal)
    return macd_value, signal_value, macd_value-signal_value
