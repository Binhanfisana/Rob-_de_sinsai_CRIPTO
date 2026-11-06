"""Dados públicos da Binance, sem acesso a conta ou ordens."""
import json, time, urllib.request
BASE='https://data-api.binance.vision'

def get(path):
    req=urllib.request.Request(BASE+path,headers={'User-Agent':'crypto-paper-bot/1.0'})
    with urllib.request.urlopen(req,timeout=15) as response: return json.load(response)

def brl_price():
    data=get('/api/v3/ticker/bookTicker?symbol=USDTBRL')
    price=float(data['askPrice'])
    if price <= 0: raise ValueError('Cotação BRL indisponível')
    return price

def scan(limit=20):
    info=get('/api/v3/exchangeInfo')
    allowed={x['symbol'] for x in info['symbols'] if x['status']=='TRADING' and x['quoteAsset']=='USDT' and x.get('isSpotTradingAllowed') and x['baseAsset'] not in {'USDC','FDUSD','TUSD','USDP','DAI','EUR','BRL'} and not x['baseAsset'].endswith(('UP','DOWN','BULL','BEAR'))}
    tickers=get('/api/v3/ticker/24hr')
    ranked=sorted((t for t in tickers if t['symbol'] in allowed and float(t['quoteVolume'])>0),key=lambda t:float(t['quoteVolume']),reverse=True)
    if not ranked: raise ValueError('Nenhum ativo disponível')
    return [t['symbol'] for t in ranked[:limit]]

def candles(symbol):
    data=get('/api/v3/klines?symbol='+symbol+'&interval=5m&limit=150')
    now=int(time.time()*1000)
    closed=[x for x in data if int(x[6])<now]
    if len(closed)<100: raise ValueError('Histórico insuficiente')
    if any(int(b[0])-int(a[0])!=300000 for a,b in zip(closed,closed[1:])): raise ValueError('Lacuna nos candles')
    if now-int(closed[-1][6])>600000: raise ValueError('Dados atrasados')
    return closed

def price(symbol):
    d=get('/api/v3/ticker/bookTicker?symbol='+symbol)
    bid,ask=float(d['bidPrice']),float(d['askPrice'])
    if bid<=0 or ask<=0 or bid>ask: raise ValueError('Preço indisponível')
    return bid,ask
