"""Exemplo de estratégia, sem garantia de desempenho."""
from .indicators import ema, rsi, macd

def signal(candles):
    prices=[float(x[4]) for x in candles]
    volumes=[float(x[5]) for x in candles]
    before=ema(prices[:-1],9)-ema(prices[:-1],21)
    now=ema(prices,9)-ema(prices,21)
    r=rsi(prices); line,signal_line,_=macd(prices)
    volume=volumes[-1] > sum(volumes[-21:-1])/20
    buy=before<=0<now and 50<r<70 and line>signal_line and volume
    sell=before>=0>now
    return ('buy' if buy else 'sell' if sell else None), {'rsi':r,'macd':line,'volume':volume}
