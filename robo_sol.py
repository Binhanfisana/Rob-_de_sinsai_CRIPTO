import json, os, time, urllib.request, urllib.parse
from datetime import datetime, timezone
from pathlib import Path

SYMBOL = 'SOLUSDT'
INTERVAL = '15m'
FAST, SLOW = 9, 21
FEE = 0.001
STATE = Path(__file__).with_name('estado.json')

def request(url, data=None):
    req = urllib.request.Request(url, data=data, headers={'User-Agent': 'sol-simulator/1.0'})
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.load(response)

def notify(message):
    print(message, flush=True)
    token, chat = os.getenv('TELEGRAM_TOKEN'), os.getenv('TELEGRAM_CHAT_ID')
    if token and chat:
        try:
            request('https://api.telegram.org/bot' + token + '/sendMessage', urllib.parse.urlencode({'chat_id': chat, 'text': message}).encode())
        except Exception as exc:
            print('Falha ao enviar alerta:', type(exc).__name__, flush=True)

def ema(values, period):
    result = sum(values[:period]) / period
    for value in values[period:]:
        result += (2 / (period + 1)) * (value - result)
    return result

def save(state):
    temp = STATE.with_suffix('.tmp')
    temp.write_text(json.dumps(state, indent=2), encoding='utf-8')
    temp.replace(STATE)

def main():
    initial = float(os.getenv('SALDO_INICIAL_USDT', '1000'))
    amount = float(os.getenv('VALOR_POR_OPERACAO_USDT', '100'))
    if initial <= 0 or amount <= 0:
        raise ValueError('Os valores devem ser positivos.')
    state = json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {'cash': initial, 'qty': 0, 'cost': 0, 'last': None}
    notify('Simulador SOL/USDT iniciado. Nenhuma ordem real será enviada.')
    while True:
        try:
            candles = request('https://data-api.binance.vision/api/v3/klines?symbol=SOLUSDT&interval=15m&limit=150')
            now = int(time.time() * 1000)
            candles = [c for c in candles if int(c[6]) < now]
            if len(candles) < SLOW + 2:
                raise ValueError('Histórico insuficiente')
            last = int(candles[-1][0])
            if state['last'] != last:
                prices = [float(c[4]) for c in candles]
                prev = ema(prices[:-1], FAST) - ema(prices[:-1], SLOW)
                curr = ema(prices, FAST) - ema(prices, SLOW)
                price = prices[-1]
                label = datetime.fromtimestamp(last / 1000, timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
                message = None
                # Do not act on a historical signal at startup.
                if state['last'] is not None:
                    if prev <= 0 < curr and state['qty'] == 0:
                        spend = min(amount, state['cash'])
                        if spend > 0:
                            state['qty'] = spend * (1 - FEE) / price
                            state['cash'] -= spend
                            state['cost'] = spend
                            message = f'COMPRA SIMULADA SOL/USDT\nPreço: {price:.4f} USDT\nValor: {spend:.2f} USDT\nCandle: {label}\nMotivo: EMA 9 cruzou acima da EMA 21.'
                    elif prev >= 0 > curr and state['qty'] > 0:
                        proceeds = state['qty'] * price * (1 - FEE)
                        pnl = proceeds - state['cost']
                        state['cash'] += proceeds
                        state['qty'] = state['cost'] = 0
                        message = f'VENDA SIMULADA SOL/USDT\nPreço: {price:.4f} USDT\nResultado: {pnl:+.2f} USDT\nSaldo: {state["cash"]:.2f} USDT\nCandle: {label}\nMotivo: EMA 9 cruzou abaixo da EMA 21.'
                state['last'] = last
                save(state)
                if message: notify(message)
            time.sleep(30)
        except Exception as exc:
            print('Erro de consulta:', type(exc).__name__, '— nova tentativa em 60 segundos.', flush=True)
            time.sleep(60)

if __name__ == '__main__':
    main()
