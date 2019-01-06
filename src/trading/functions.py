from ibapi.contract import Contract as IBcontract
from ibapi.order import Order
from ibapi.execution import ExecutionFilter
from threading import Thread
import numpy as np, pandas as pd, datetime as dt, time
import queue, importlib, collections, utils
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
            'XLV' : {'symbol' : 'XLV', 'secType' : 'STK', 'currency' : 'USD', 'exchange' : 'ISLAND',
                      'expiry' : None},
           }


def make_contract(app, underlying):
    if underlying not in TV_to_IB:
        return 'Error: no details available for this underlying'
    ibcontract = utils.create_contract(TV_to_IB[underlying]['symbol'], TV_to_IB[underlying]['secType'], 
                                        TV_to_IB[underlying]['currency'], TV_to_IB[underlying]['exchange'],
                                        TV_to_IB[underlying]['expiry'])
    resolved_ibcontract, minTick = app.resolve_ib_contract(ibcontract)

    return resolved_ibcontract, minTick


def make_order(app, ibcontract, minTick, message):
    order_params = { k:v for k,v in (x.split('=') for x in message.split(' ')) }
    order = Order()
    if order_params['t']=='l':
        order.orderType = "LMT"
        order.tif = 'DAY'
        best_bid, best_offer = app.get_quotes(ibcontract)
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
    
    q = int(order_params['q'])
    if q>0:
        unit = calc_unit(app, ibcontract, order_params['u'], order_params['c'], order_params['b'])
        order.totalQuantity = q * unit
    else:
        order.totalQuantity = app.get_holdings(ibcontract)
    
    order.transmit = True
    print(order)

    return order


def calc_unit(app, ibcontract, unit_size, initial_capital, barSize):
    '''
    INPUTS
    unit_size: % of initial_capital(USD) allocated
    timeframe: the timeframe used to generate the alerts

    OUTPUTS
    unit: number of contracts to be traded on each entry
    '''
    durationStr, barSizeSetting = utils.calc_bar_dur(barSize)
    hist_mkt_data = app.get_IB_historical_data(ibcontract, durationStr, barSizeSetting)
    n = len(hist_mkt_data)
    sum_temp = 0
    for row in hist_mkt_data[n-20:n]:
        sum_temp += row[2] - row[3]
    N = sum_temp / 20

    if ibcontract.multiplier=='':
        mult = 1.0
    else:
        mult = ibcontract.multiplier
    unit = ( float(unit_size) / 100 * float(initial_capital) ) / ( N * mult )

    return unit


def get_holdings(app, ibcontract):
    holdings = app.get_current_positions()
    return holdings


def get_quotes(app, ibcontract):
    tickerid = app.start_getting_IB_market_data(ibcontract, whatToShow='BID')
    time.sleep(5)
    best_bid = app.stop_getting_IB_market_data(tickerid)
    
    return best_bid #, best_offer


class TestApp(TestWrapper, TestClient):
    def __init__(self, ipaddress, portid, clientid):
        TestWrapper.__init__(self)
        TestClient.__init__(self, wrapper=self)

        self.connect(ipaddress, portid, clientid)

        thread = Thread(target = self.run)
        thread.start()

        setattr(self, "_thread", thread)

        self.init_error()