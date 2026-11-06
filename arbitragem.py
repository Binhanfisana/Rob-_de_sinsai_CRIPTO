"""Comparação informativa Spot/P2P; não executa ordens."""
import argparse, json, os, sys, urllib.request, urllib.parse
from datetime import datetime, timezone
from robo_sol import request

PAIRS = {'BRL': ('USDTBRL', False), 'EUR': ('EURUSDT', True)}

def quote(fiat, amount):
    if fiat not in PAIRS: raise ValueError('Par Spot direto não configurado')
    symbol, inverse = PAIRS[fiat]
    info = request('https://data-api.binance.vision/api/v3/ticker/bookTicker?symbol=' + symbol)
    # USDT/fiat: comprar USDT no ask. Fiat/USDT: vender fiat no bid.
    raw = float(info['bidPrice'] if inverse else info['askPrice'])
    if raw <= 0: raise ValueError('Livro Spot sem preço válido')
    spot = 1/raw if inverse else raw
    size = float(info['bidQty'] if inverse else info['askQty'])
    spot_usdt_depth = size * raw if inverse else size
    body = json.dumps({'asset':'USDT','fiat':fiat,'tradeType':'SELL','page':1,'rows':20,'payTypes':[], 'transAmount':str(amount)}).encode()
    req = urllib.request.Request('https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search', data=body, headers={'Content-Type':'application/json','User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as resp: data = json.load(resp)
    if str(data.get('code')) != '000000': raise ValueError('Consulta P2P recusada')
    offers = []
    for item in data.get('data', []):
        ad = item['adv']
        price = float(ad['price'])
        if price > 0 and float(ad['minSingleTransAmount']) <= amount <= float(ad['maxSingleTransAmount']) and float(ad['surplusAmount'])*price >= amount:
            offers.append((price, ad))
    if not offers: raise ValueError('Sem anúncio P2P compatível com o valor')
    price, ad = max(offers, key=lambda x:x[0])
    return {'fiat':fiat,'spot':spot,'p2p':price,'spread':(price/spot-1)*100,'depth':spot_usdt_depth,'symbol':symbol,'min':ad['minSingleTransAmount'],'max':ad['maxSingleTransAmount']}

def report(results, errors, amount):
    now = datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')
    lines = [f'📊 Comparação USDT Spot → P2P | {now}', f'Valor P2P: {amount:g} unidades da moeda local', '']
    for r in results:
        f=r['fiat']; pct=r['spread']; icon='🟢' if pct>0 else '🔴'
        lines += [f'{icon} {f}: {pct:+.2f}% bruto', f'Compra Spot: {r["spot"]:.4f} {f}/USDT ({r["symbol"]})', f'Venda P2P: {r["p2p"]:.4f} {f}/USDT', f'Limite do anúncio: {r["min"]} a {r["max"]} {f}; liquidez no melhor preço Spot: {r["depth"]:.2f} USDT', f'https://www.binance.com/pt-BR/trade/{r["symbol"][:-4]}_{r["symbol"][-4:]}?type=spot' if r['symbol']=='EURUSDT' else 'https://www.binance.com/pt-BR/trade/USDT_BRL?type=spot', f'https://p2p.binance.com/pt-BR/trade/sell/USDT?fiat={f}', '']
    for f, error in errors: lines.append(f'⚪ {f}: {error}')
    lines += ['', 'Gráfico — diferença percentual bruta']
    for r in results:
        p=r['spread']; n=min(20,round(abs(p)*2)); bar='█'*n or '▏'
        lines.append(f'{r["fiat"]} {"−" if p<0 else "+"} {bar} {p:+.2f}%')
    lines += ['', 'Estimativa bruta, sem taxas, slippage, disponibilidade, pagamento ou impostos. Não garante execução nem lucro. Verifique limites, liquidez e contraparte. Gráfico: cada bloco ≈ 0,5 ponto percentual (máximo 20 blocos).']
    return '\n'.join(lines)

def main():
    if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    parser=argparse.ArgumentParser(description='Compara preços públicos Spot e P2P; não opera.')
    parser.add_argument('--valor',type=float,default=500,help='valor em cada moeda fiduciária (padrão: 500)')
    parser.add_argument('--telegram',action='store_true',help='enviar relatório ao Telegram')
    args=parser.parse_args()
    if not 0 < args.valor < 10000000: parser.error('Valor inválido')
    results=[]; errors=[]
    for fiat in ['BRL','EUR','USD']:
        try: results.append(quote(fiat,args.valor))
        except Exception as exc: errors.append((fiat, str(exc) if isinstance(exc,ValueError) else 'cotação indisponível'))
    msg=report(results,errors,args.valor)
    print(msg,flush=True)
    if args.telegram:
        token=os.getenv('TELEGRAM_TOKEN'); chat=os.getenv('TELEGRAM_CHAT_ID')
        if not token or not chat: raise SystemExit('Configure TELEGRAM_TOKEN e TELEGRAM_CHAT_ID.')
        try:
            response=request('https://api.telegram.org/bot'+token+'/sendMessage',urllib.parse.urlencode({'chat_id':chat,'text':msg,'disable_web_page_preview':'true'}).encode())
            if not response.get('ok'): raise ValueError('envio recusado')
            print('Relatório enviado.')
        except Exception: raise SystemExit('Falha no envio ao Telegram; confira as credenciais e a conexão.')

if __name__=='__main__': main()

