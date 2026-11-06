"""Simulador multimoeda: somente dados públicos; nunca envia ordens à Binance."""
import argparse, os, time
from datetime import datetime, timezone
from paper_bot import market, strategy, risk, execution
from paper_bot.database import Store
from robo_sol import notify

DB='paper_trading.sqlite3'

def today(): return datetime.now(timezone.utc).date().isoformat()

def describe_trade(t):
    _,symbol,side,price,qty,fee,pnl,reason=t
    msg=f'{"COMPRA" if side=="BUY" else "VENDA"} SIMULADA {symbol}\nPreço: {price:.6f} USDT | Quantidade: {qty:.8f}\nTaxa estimada: {fee:.4f} USDT\nMotivo: {reason}'
    if pnl is not None: msg+=f'\nResultado líquido estimado: {pnl:+.4f} USDT'
    return msg

def cycle(store,state,symbols,armed):
    positions=state['positions']
    bids={}
    # If any held asset cannot be valued, no new position is opened.
    complete=True
    for symbol in list(positions):
        try: bids[symbol]=market.price(symbol)[0]
        except Exception as exc:
            complete=False
            print(f'{symbol}: preço indisponível ({type(exc).__name__}); entradas suspensas.',flush=True)
    if complete:
        total=execution.equity(state,bids)
        if state.get('day')!=today():
            state['day']=today(); state['day_start']=total; state['halted']=False
        if total<=state['day_start']*(1-risk.DAILY_LOSS): state['halted']=True
        store.save(state)
    # Stops use current bid, checked on every pass, not exchange-hosted orders.
    for symbol in list(positions):
        if symbol not in bids: continue
        reason=risk.exit_reason(positions[symbol]['entry'],bids[symbol],None)
        if reason:
            trade=execution.sell(state,symbol,bids[symbol],reason)
            store.save(state,trade); notify(describe_trade(trade))
    for symbol in dict.fromkeys(list(state['positions'])+symbols):
        try:
            candles=market.candles(symbol); candle_id=int(candles[-1][0])
            prior=state['last_candles'].get(symbol)
            if prior == candle_id: continue
            signal, details=strategy.signal(candles)
            state['last_candles'][symbol]=candle_id
            # Newly seen symbols and first cycle after restart establish a baseline only.
            eligible=armed and prior is not None and candle_id-prior==300000
            if eligible and symbol in state['positions'] and signal=='sell':
                bid=market.price(symbol)[0]
                trade=execution.sell(state,symbol,bid,'cruzamento de baixa')
                store.save(state,trade); notify(describe_trade(trade))
            elif eligible and signal=='buy' and complete and not state.get('halted'):
                held_bids={s:market.price(s)[0] for s in state['positions']}
                eq=execution.equity(state,held_bids)
                if eq<=state['day_start']*(1-risk.DAILY_LOSS): state['halted']=True
                if not state.get('halted') and risk.entry_allowed(eq,state['day_start'],state['positions'],symbol):
                    bid,ask=market.price(symbol)
                    budget=risk.order_budget(state['cash'],eq)
                    if budget>0:
                        trade=execution.buy(state,symbol,ask,budget)
                        store.save(state,trade); notify(describe_trade(trade))
            store.save(state)
        except Exception as exc:
            print(f'{symbol}: consulta ou análise falhou ({type(exc).__name__}).',flush=True)
    return state

def main():
    parser=argparse.ArgumentParser(description='Simulação local: nenhuma ordem real é enviada.')
    parser.add_argument('--banco',default=DB)
    parser.add_argument('--capital-usdt',type=float,help='saldo inicial USDT, apenas ao criar o banco; padrão: R$ 100 convertidos ao preço público')
    parser.add_argument('--status',action='store_true',help='mostrar posições e resultados registrados')
    args=parser.parse_args(); store=Store(args.banco); state=store.load()
    if args.status:
        if not state: raise SystemExit('Banco ainda não inicializado.')
        count,pnl,wins=store.summary()
        print(f"Caixa: {state['cash']:.4f} USDT | Posições abertas: {len(state['positions'])} | Vendas: {count} | Lucro realizado: {pnl:+.4f} USDT | Vendas positivas: {wins}")
        for s,p in state['positions'].items(): print(f"{s}: {p['quantity']:.8f} | entrada {p['entry']:.6f} | custo {p['cost']:.4f} USDT")
        return
    if not state:
        if args.capital_usdt is not None: capital=args.capital_usdt
        else:
            try: capital=100/market.brl_price()
            except Exception: raise SystemExit('Não foi possível converter R$ 100. Tente mais tarde ou informe --capital-usdt.')
        if not 0<capital<1000000: raise SystemExit('Capital inicial inválido.')
        state={'cash':capital,'initial':capital,'positions':{},'last_candles':{},'day':None,'day_start':None,'halted':False}
        store.save(state)
    notify(f'Simulador multimoeda iniciado. Capital inicial: {state["initial"]:.4f} USDT. Nenhuma ordem real será enviada.')
    symbols=[]; last_scan=0; armed=False
    try:
        while True:
            if time.monotonic()-last_scan>3600 or not symbols:
                try:
                    symbols=market.scan(); last_scan=time.monotonic()
                    print('Ativos:', ', '.join(symbols),flush=True)
                except Exception as exc: print('Scanner indisponível:',type(exc).__name__,flush=True)
            state=cycle(store,state,symbols,armed); armed=True
            count,pnl,wins=store.summary()
            print(f"Caixa: {state['cash']:.4f} USDT | posições: {len(state['positions'])} | vendas: {count} | resultado realizado: {pnl:+.4f} | entradas bloqueadas: {state.get('halted',False)}",flush=True)
            time.sleep(30)
    except KeyboardInterrupt: print('\nSimulador encerrado.')

if __name__=='__main__': main()
