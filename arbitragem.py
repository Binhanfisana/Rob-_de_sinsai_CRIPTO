"""Comparação informativa Spot/P2P; não executa ordens."""
import argparse, html, io, json, os, sys, urllib.request, urllib.parse, uuid
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
    lines = [f'<b>📊 Relatório de Arbitragem USDT</b>', f'{now} | Valor P2P: {amount:g} por moeda', '']
    for r in results:
        f = r['fiat']; pct = r['spread']; icon = '🟢⬆️' if pct > 0 else '🔴⬇️'
        spot_url = 'https://www.binance.com/pt-BR/trade/EUR_USDT?type=spot' if f == 'EUR' else 'https://www.binance.com/pt-BR/trade/USDT_BRL?type=spot'
        p2p_url = f'https://p2p.binance.com/pt-BR/trade/sell/USDT?fiat={f}'
        lines += [f'• <b>{f}</b> {icon} <code>{pct:+.2f}%</code>',
                  f'  <b>Spot:</b> <code>{r["spot"]:.4f}</code>',
                  f'  <b>P2P:</b> <code>{r["p2p"]:.4f}</code>',
                  f'  <b>Diferença:</b> <code>{r["p2p"]-r["spot"]:+.4f}</code>',
                  f'  <a href="{spot_url}">Comprar USDT no Spot</a> | <a href="{p2p_url}">Vender USDT no P2P</a>', '']
    for f, error in errors: lines.append(f'• <b>{html.escape(f)}</b>: {html.escape(error)}')
    lines += ['', 'Diferença bruta: não inclui taxas, liquidez, impostos ou riscos. Não garante execução nem lucro.', '#Arbitragem #Crypto #USDT']
    return '\n'.join(lines)

def chart(results, errors):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        raise RuntimeError('Instale a biblioteca Pillow: python -m pip install Pillow')
    image = Image.new('RGB', (1100, 620), 'white')
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype('arial.ttf', 22)
        title = ImageFont.truetype('arial.ttf', 27)
    except OSError:
        font = title = ImageFont.load_default()
    draw.text((40, 18), 'Oportunidades de Arbitragem (%) - USDT vs. Fiat', fill='#222222', font=title)
    left, top, right, bottom = 105, 90, 1060, 520
    draw.rectangle((left, top, right, bottom), fill='#ebebf2')
    values = [r['spread'] for r in results]
    bound = max(1.0, max((abs(v) for v in values), default=1.0) * 1.3)
    zero = (top+bottom)//2
    for i in range(-2, 3):
        y = zero - i*(bottom-top)/4
        draw.line((left,y,right,y),fill='#ffffff',width=2)
        draw.text((10,y-12), f'{bound*i/2:+.1f}%', fill='#555555',font=font)
    draw.line((left,zero,right,zero),fill='#888888',width=2)
    by_fiat = {r['fiat']:r for r in results}
    for i, fiat in enumerate(('EUR','BRL','USD')):
        x = left + (i+0.5)*(right-left)/3
        draw.text((x-23,bottom+12),fiat,fill='#222222',font=font)
        if fiat not in by_fiat:
            draw.text((x-60,zero+12),'Sem dados',fill='#777777',font=font)
            continue
        val=by_fiat[fiat]['spread']; y=zero-val/bound*(bottom-top)/2
        draw.rectangle((x-80,min(y,zero),x+80,max(y,zero)),fill='#008a12' if val>=0 else '#e52424')
        draw.text((x-42,y-30 if val>=0 else y+5),f'{val:+.2f}%',fill='#222222',font=font)
    buffer=io.BytesIO(); image.save(buffer, format='PNG'); return buffer.getvalue()

def send_photo(token, chat, image, caption):
    boundary = '----codex' + uuid.uuid4().hex
    parts=[]
    def field(name, value):
        parts.append((f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n').encode('utf-8'))
    field('chat_id', chat); field('caption', caption); field('parse_mode','HTML')
    parts.append((f'--{boundary}\r\nContent-Disposition: form-data; name="photo"; filename="grafico.png"\r\nContent-Type: image/png\r\n\r\n').encode() + image + b'\r\n')
    parts.append(f'--{boundary}--\r\n'.encode())
    req=urllib.request.Request('https://api.telegram.org/bot'+token+'/sendPhoto',data=b''.join(parts),headers={'Content-Type':'multipart/form-data; boundary='+boundary})
    with urllib.request.urlopen(req,timeout=20) as response: result=json.load(response)
    if not result.get('ok'): raise ValueError('envio recusado')

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
    print(html.unescape(__import__('re').sub(r'<[^>]+>', '', msg)),flush=True)
    try:
        image = chart(results, errors)
    except RuntimeError as exc:
        raise SystemExit(str(exc))
    with open('grafico_arbitragem.png', 'wb') as output: output.write(image)
    print('Gráfico salvo em grafico_arbitragem.png.')
    if args.telegram:
        token=os.getenv('TELEGRAM_TOKEN'); chat=os.getenv('TELEGRAM_CHAT_ID')
        if not token or not chat: raise SystemExit('Configure TELEGRAM_TOKEN e TELEGRAM_CHAT_ID.')
        try:
            send_photo(token, chat, image, msg)
            print('Relatório enviado.')
        except Exception: raise SystemExit('Falha no envio ao Telegram; confira as credenciais e a conexão.')

if __name__=='__main__': main()

