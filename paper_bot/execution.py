"""Execução exclusivamente simulada em cotações públicas."""
from .risk import FEE
from .database import timestamp

def buy(state,symbol,ask,budget):
    if budget <= 0 or budget > state['cash']: raise ValueError('Saldo insuficiente')
    qty=budget*(1-FEE)/ask
    state['cash']-=budget
    state['positions'][symbol]={'quantity':qty,'entry':ask,'cost':budget}
    return (timestamp(),symbol,'BUY',ask,qty,budget*FEE,None,'sinal de compra')

def sell(state,symbol,bid,reason):
    p=state['positions'].pop(symbol); gross=p['quantity']*bid; fee=gross*FEE
    proceeds=gross-fee; state['cash']+=proceeds
    return (timestamp(),symbol,'SELL',bid,p['quantity'],fee,proceeds-p['cost'],reason)

def equity(state,bids):
    return state['cash']+sum(p['quantity']*bids[s]*(1-FEE) for s,p in state['positions'].items())
