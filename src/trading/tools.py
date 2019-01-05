from ibapi.contract import Contract as IBcontract
from ibapi.order import Order
from ibapi.execution import ExecutionFilter
from threading import Thread
import numpy as np, pandas as pd, datetime as dt, time
import queue, importlib, tools, collections
from wrapper import TestWrapper
from client import TestClient


TV_to_IB = {'EURUSD' : {'symbol' : 'EUR', 'secType' : 'CASH', 'currency' : 'USD', 'exchange' : 'IDEALPRO', 
                        'expiry' : None},
            'ES1!, 1' : {'symbol' : 'ES', 'secType' : 'FUT', 'currency' : 'USD', 'exchange' : 'GLOBEX',
                         'expiry' : '201903'},
            'SPY' : {'symbol' : 'SPY', 'secType' : 'STK', 'currency' : 'USD', 'exchange' : 'ARCA',
                     'expiry' : None},
            'CL1!, 1' : {'symbol' : 'CL', 'secType' : 'FUT', 'currency' : 'USD', 'exchange' : 'NYMEX',
                         'expiry' : '201902'},
            'USO' : {'symbol' : 'USO', 'secType' : 'STK', 'currency' : 'USD', 'exchange' : 'ARCA',
                         'expiry' : None},
            'GC1!, 1' : {'symbol' : 'GC', 'secType' : 'FUT', 'currency' : 'USD', 'exchange' : 'NYMEX',
                         'expiry' : '201902'},
            'GLD' : {'symbol' : 'GLD', 'secType' : 'STK', 'currency' : 'USD', 'exchange' : 'ARCA',
                     'expiry' : None},
            'TY1!, 1' : {'symbol' : 'ZN', 'secType' : 'FUT', 'currency' : 'USD', 'exchange' : 'ECBOT',
                         'expiry' : '201903'},
            'IBKR' : {'symbol' : 'IBKR', 'secType' : 'STK', 'currency' : 'USD', 'exchange' : 'ISLAND',
                      'expiry' : None},
           }

def parse_message(app, underlying, message):
    ibcontract, minTick = make_contract(app, underlying)
    best_bid=1.14
    best_offer=1.15
    order_params = { k:v for k,v in (x.split('=') for x in message.split(' ')) }
    order = Order()
    if order_params['t']=='l':
        order.orderType = "LMT"
        order.tif = 'DAY'
        if order_params['d']=='long':
            order.action = "BUY"
            order.lmtPrice = best_bid + int(order_params['p']) * minTick
        else:
            order.action = "SELL"
            order.lmtPrice = best_offer + int(order_params['p']) * minTick

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
    resolved_ibcontract, minTick = app.resolve_ib_contract(ibcontract)
    
    return resolved_ibcontract, minTick


def create_contract(symbol, secType, currency, exchange, expiry):
    contract = IBcontract()
    contract.symbol = symbol
    contract.secType = secType
    contract.currency = currency
    contract.exchange = exchange
    if expiry is not None:
        contract.lastTradeDateOrContractMonth = expiry

    return contract


def get_hist_data(app, ibcontract, durationStr='2 D', barSizeSetting='1 hour'):
    historic_data = app.get_IB_historical_data(ibcontract, durationStr, barSizeSetting)

    return historic_data


def calc_unit(app, ibcontract, unit_size, initial_capital, timeframe):
    '''
    INPUTS
    unit_size: % of initial_capital(USD) allocated
    timeframe: the timeframe used to generate the alerts
    
    OUTPUTS
    unit: number of contracts to be traded on each entry
    '''
    historic_data = app.get_IB_historical_data(resolved_ibcontract, durationStr, barSizeSetting)
    n = len(hist_mkt_data)
    sum = 0
    for row in hist_mkt_data[n-20:n]:
        sum += row[2] - row[3]
    N = sum / 20
    
    if ibcontract.multiplier=='':
        mult = 1
    else:
        mult = ibcontract.multiplier
    unit = ( unit_size / 100 * initial_capital ) / ( N * mult )
    
    return unit


class TestApp(TestWrapper, TestClient):
    def __init__(self, ipaddress, portid, clientid):
        TestWrapper.__init__(self)
        TestClient.__init__(self, wrapper=self)

        self.connect(ipaddress, portid, clientid)

        thread = Thread(target = self.run)
        thread.start()

        setattr(self, "_thread", thread)

        self.init_error()