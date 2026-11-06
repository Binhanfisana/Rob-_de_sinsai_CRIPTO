"""Backtest de candles fechados; execução na abertura do candle seguinte."""
import argparse, csv, time
from datetime import datetime, timezone
from robo_sol import request, ema, FAST, SLOW, FEE

URL = 'https://data-api.binance.vision/api/v3/klines?symbol=SOLUSDT&interval=15m&limit=1000&startTime='

def backtest(candles, initial=1000.0, amount=100.0):
    cash, qty, cost, pending = initial, 0.0, 0.0, None
    trades, equity = [], []
    for i in range(150, len(candles)):
        candle = candles[i]
        op, close = float(candle[1]), float(candle[4])
        if pending == 'buy' and not qty:
            cost = min(amount, cash)
            qty = cost * (1-FEE) / op
            cash -= cost
        elif pending == 'sell' and qty:
            proceeds = qty * op * (1-FEE)
            trades.append(proceeds-cost)
            cash += proceeds
            qty, cost = 0.0, 0.0
        pending = None
        prices = [float(c[4]) for c in candles[i-149:i+1]]
        prev = ema(prices[:-1], FAST) - ema(prices[:-1], SLOW)
        curr = ema(prices, FAST) - ema(prices, SLOW)
        if prev <= 0 < curr and not qty: pending = 'buy'
        if prev >= 0 > curr and qty: pending = 'sell'
        equity.append(cash + qty * close * (1-FEE))
    peak, drawdown = initial, 0.0
    for value in equity:
        peak = max(peak, value)
        drawdown = max(drawdown, (peak-value)/peak)
    return cash, qty, trades, equity[-1] if equity else initial, drawdown

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dias', type=int, default=90)
    args = parser.parse_args()
    if not 2 <= args.dias <= 365: parser.error('Use de 2 a 365 dias')
    now = int(time.time()*1000)
    start = now - args.dias*86400000
    candles = []
    while start < now:
        batch = request(URL + str(start))
        if not batch: break
        batch = [c for c in batch if int(c[6]) < now]
        if not batch: break
        candles.extend(batch)
        start = int(batch[-1][0]) + 900000
        if len(batch) < 1000: break
    if len(candles) < 152: raise RuntimeError('Histórico insuficiente')
    if any(int(b[0])-int(a[0]) != 900000 for a,b in zip(candles,candles[1:])): raise RuntimeError('Lacuna nos candles; teste interrompido')
    cash, qty, trades, final, dd = backtest(candles)
    date = lambda x: datetime.fromtimestamp(int(x)/1000, timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    print(f'Período: {date(candles[0][0])} a {date(candles[-1][6])}; {len(candles)} candles')
    print(f'Saldo inicial: 1000 USDT; valor por compra: 100 USDT; taxa: {FEE*100:.1f}% por ordem')
    print(f'Patrimônio final estimado: {final:.2f} USDT; retorno: {(final/1000-1)*100:+.2f}%')
    print(f'Vendas concluídas: {len(trades)}; positivas: {sum(t>0 for t in trades)}; drawdown máximo: {dd*100:.2f}%')
    print(f'Posição aberta: {qty:.6f} SOL; caixa: {cash:.2f} USDT')
    print('Execução simulada na abertura seguinte; não inclui slippage ou indisponibilidade.')

if __name__ == '__main__': main()
