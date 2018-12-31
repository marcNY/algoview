from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from ibapi.contract import Contract as IBcontract
from ibapi.order import Order
from ibapi.execution import ExecutionFilter
from threading import Thread
import numpy as np, pandas as pd, datetime as dt, time
import queue, importlib, tools, collections
import HistMktData as hmd, OrderPlacement as op

TV_to_IB = {'EURUSD' : {'symbol' : 'EUR', 'secType' : 'CASH', 'currency' : 'USD', 'exchange' : 'IDEALPRO', 'expiry' : None, 'multiplier' : 1},
            'ES1!, 1' : {'symbol' : 'ES', 'secType' : 'FUT', 'currency' : 'USD', 'exchange' : 'GLOBEX_IND', 'expiry' : '201903', 'multiplier' : 50},
            'CL1!, 1' : {'symbol' : 'CL', 'secType' : 'FUT', 'currency' : 'USD', 'exchange' : 'NYMEX', 'expiry' : '201901', 'multiplier' : 100},
            'GC1!, 1' : {'symbol' : 'GC', 'secType' : 'FUT', 'currency' : 'USD', 'exchange' : 'NYMEX', 'expiry' : '201902', 'multiplier' : 100},
            'TY1!, 1' : {'symbol' : 'ZN', 'secType' : 'FUT', 'currency' : 'USD', 'exchange' : 'ECBOT', 'expiry' : '201903', 'multiplier': 100},
            'IBKR' : {'symbol' : 'IBKR', 'secType' : 'STK', 'currency' : 'USD', 'exchange' : 'ISLAND', 'expiry' : None, 'multiplier' : 1},
           }

def parse_message(app, underlying, message):
    ibcontract = make_contract(app, underlying)
    best_bid=1.14
    best_offer=1.15
    order_params = { k:v for k,v in (x.split('=') for x in message.split(' ')) }
    order = Order()
    if order_params['t']=='l':
        order.orderType = "LMT"
        order.tif = 'DAY'
        if order_params['d']=='long':
            order.action = "BUY"
            order.lmtPrice = best_bid + int(order_params['p']) * TV_to_IB[underlying]['multiplier']
        else:
            order.action = "SELL"
            order.lmtPrice = best_offer + int(order_params['p']) * TV_to_IB[underlying]['multiplier']

    elif order_params['t']=='m':
        order.orderType = "MKT"
        if order_params['d']=='long':
            order.action = "BUY"
        else:
            order.action = "SELL"
    q = float(order_params['q'])
    if q>0:
        order.totalQuantity = q
    else:
        order.totalQuantity = q + 1
    order.transmit = True
    
    print(ibcontract)
    print(order)
    
    return ibcontract, order


def make_contract(app, underlying):
    if underlying not in TV_to_IB:
        return 'Error: no details available for this underlying'
    ibcontract = create_contract(TV_to_IB[underlying]['symbol'], TV_to_IB[underlying]['secType'], 
                                 TV_to_IB[underlying]['currency'], TV_to_IB[underlying]['exchange'],
                                 TV_to_IB[underlying]['expiry'])
    resolved_ibcontract = app.resolve_ib_contract(ibcontract)
    
    return resolved_ibcontract


def create_contract(symbol='IBKR', secType='STK', currency='USD', exchange='ISLAND', expiry=None):
    contract = IBcontract()
    contract.symbol = symbol
    contract.secType = secType
    contract.currency = currency
    contract.exchange = exchange
    if expiry is not None:
        contract.lastTradeDateOrContractMonth = expiry

    return contract


def get_hist_data(app, ibcontract, durationStr='1 D', barSizeSetting='1 hour'):
    resolved_ibcontract = app.resolve_ib_contract(ibcontract)
    historic_data = app.get_IB_historical_data(resolved_ibcontract, durationStr, barSizeSetting)

    return historic_data