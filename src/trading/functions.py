from ibapi.contract import Contract as IBcontract
from ibapi.order import Order
from ibapi.execution import ExecutionFilter
from threading import Thread
import numpy as np
import pandas as pd
import datetime as dt
import time
import queue
import importlib
import collections
import trading.utils as utils
from trading.wrapper import TestWrapper
from trading.client import TestClient


TV_to_IB = {'EURUSD': {'symbol': 'EUR', 'secType': 'CASH', 'currency': 'USD', 'exchange': 'IDEALPRO',
                       'expiry': None},
            'ES1!, 1': {'symbol': 'ES', 'secType': 'FUT', 'currency': 'USD', 'exchange': 'GLOBEX',
                        'expiry': '201903'},
            'SPY': {'symbol': 'SPY', 'secType': 'STK', 'currency': 'USD', 'exchange': 'ARCA',
                    'expiry': None},
            'CL1!, 1': {'symbol': 'CL', 'secType': 'FUT', 'currency': 'USD', 'exchange': 'NYMEX',
                        'expiry': '201902'},
            'USO': {'symbol': 'USO', 'secType': 'STK', 'currency': 'USD', 'exchange': 'ARCA',
                    'expiry': None},
            'GC1!, 1': {'symbol': 'GC', 'secType': 'FUT', 'currency': 'USD', 'exchange': 'NYMEX',
                        'expiry': '201902'},
            'GLD': {'symbol': 'GLD', 'secType': 'STK', 'currency': 'USD', 'exchange': 'ARCA',
                    'expiry': None},
            'TY1!, 1': {'symbol': 'ZN', 'secType': 'FUT', 'currency': 'USD', 'exchange': 'ECBOT',
                        'expiry': '201903'},
            'IBKR': {'symbol': 'IBKR', 'secType': 'STK', 'currency': 'USD', 'exchange': 'ISLAND',
                     'expiry': None},
            'XLV': {'symbol': 'XLV', 'secType': 'STK', 'currency': 'USD', 'exchange': 'ISLAND',
                    'expiry': None},
            }


def reconnect(app=None, client=1):
    try:
        if app is None:
            app = TestApp("127.0.0.1", 4001, client)
        if app.isConnected() == False:
            app.connect("127.0.0.1", 4001, client)
            if app.isConnected() == False:
                print('IB Gateway not connected')
            else:
                print('App reconnected')
        else:
            print('App already connected')
    except NameError:
        app = TestApp("127.0.0.1", 4001, client)
        if app.isConnected() == False:
            print('IB Gateway not connected')
        else:
            print('App instantiated & connected')

    return app


def make_contract(app, underlying):
    reconnect(app)
    if underlying not in TV_to_IB:
        return 'Error: no details available for this underlying'
    ibcontract = utils.create_contract(TV_to_IB[underlying]['symbol'], TV_to_IB[underlying]['secType'],
                                       TV_to_IB[underlying]['currency'], TV_to_IB[underlying]['exchange'],
                                       TV_to_IB[underlying]['expiry'])
    resolved_ibcontract, minTick = app.resolve_ib_contract(ibcontract)

    return resolved_ibcontract, minTick


def make_order(app, ibcontract, minTick, message):
    reconnect(app)
    order_params = {k: v for k, v in (x.split('=')
                                      for x in message.split(' '))}
    order = Order()
    if order_params['t'] == 'l':
        order.orderType = "LMT"
        order.tif = 'DAY'
        best_bid, best_offer = get_quotes(app, ibcontract)
        if order_params['d'] == 'long':
            order.action = "BUY"
            order.lmtPrice = best_bid + int(order_params['p']) * minTick
        else:
            order.action = "SELL"
            order.lmtPrice = best_offer + int(order_params['p']) * minTick

    elif order_params['t'] == 'm':
        order.orderType = "MKT"
        if order_params['d'] == 'long':
            order.action = "BUY"
        else:
            order.action = "SELL"

    q = int(order_params['q'])
    if q > 0:
        unit = calc_unit(
            app, ibcontract, order_params['u'], order_params['c'], order_params['b'])
        order.totalQuantity = int(q * unit)
    else:
        order.totalQuantity = int(get_pos(app, ibcontract))

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
    hist_mkt_data = app.get_IB_historical_data(
        ibcontract, durationStr, barSizeSetting)
    n = len(hist_mkt_data)
    sum_temp = 0
    for row in hist_mkt_data[n-20:n]:
        sum_temp += row[2] - row[3]
    N = sum_temp / 20

    if ibcontract.multiplier == '':
        mult = 1.0
    else:
        mult = ibcontract.multiplier
    unit = float(unit_size) / 100 * float(initial_capital) / (N * mult)

    return unit


def get_pos(app, ibcontract):
    holdings = app.get_current_positions()
    pos = 'NaN'

    for item in holdings:
        if ibcontract.conId == item[1].conId:
            pos = item[2]

    if pos == 'NaN':
        pos = 0
        print('No position to exit')

    return pos


def get_quotes(app, ibcontract):
    reconnect(app)
    tickerid = app.start_getting_IB_market_data(ibcontract, whatToShow='BID')
    time.sleep(1)
    quotes = app.stop_getting_IB_market_data(tickerid)

    return float(quotes.bid_price), float(quotes.ask_price)


def get_accountName(app):
    reconnect(app)
    positions_list = app.get_current_positions()
    accountName = positions_list[0][0]

    return accountName


def get_execDetails(app):
    reconnect(app)
    exec_dict = app.get_executions_and_commissions()
    exec_list = [str(v) for k, v in exec_dict.items()]
    exec_tuples = []
    for item in exec_list:
        conId = int(item[item.find('Execution')+22:item.find(',')])
        time = item[item.find('time')+6:item.find('AvgPrice')-1]
        OrderId = int(item[item.find('OrderId')+9:item.find('time')-1])
        AvgPrice = float(
            item[item.find('AvgPrice')+10:item.find('Price', item.find('AvgPrice')+5)-1])
        if len(item) > item.find('Shares')+15:
            Shares = int(
                float(item[item.find('Shares')+8:item.find('Commission')-1]))
        else:
            Shares = int(float(item[item.find('Shares')+8:len(item)]))
        ClientId = int(item[item.find('ClientId')+10:item.find('OrderId')-1])
        exec_tuples.append((conId, time, OrderId, AvgPrice, Shares, ClientId))
    exec_df = pd.DataFrame(exec_tuples, columns=[
                           'conId', 'time', 'OrderId', 'AvgPrice', 'Shares', 'ClientId'])
    exec_df.set_index('time', inplace=True)

    return exec_df


def check_fill(app, order1, orderid1):
    """
    Check_fill: check if order has been filled, 
    return False if the order has not been filled and True if it has been executed
    """
    reconnect(app)
    order_filled = False
    counter = 0
    Shares = 0
    while order_filled == False and counter < 5:
        counter += 1
        exec_dict = app.get_executions_and_commissions()
        exec_list = [str(v) for k, v in exec_dict.items()]
        for item in exec_list:
            if int(item[item.find('OrderId')+9:item.find('time')-1]) == orderid1:
                if len(item) > item.find('Shares')+15:
                    Shares += int(float(item[item.find('Shares') +
                                             8:item.find('Commission')-1]))
                else:
                    Shares += int(float(item[item.find('Shares')+8:len(item)]))
                if Shares == order1.totalQuantity:
                    order_filled = True
        time.sleep(1)

    if order_filled == True:
        print('== ORDER FILLED ==')
        return True
    else:
        print('WARNING: ORDER NOT FILLED')
        return False


class TestApp(TestWrapper, TestClient):
    def __init__(self, ipaddress, portid, clientid):
        TestWrapper.__init__(self)
        TestClient.__init__(self, wrapper=self)

        self.connect(ipaddress, portid, clientid)

        thread = Thread(target=self.run)
        thread.start()

        setattr(self, "_thread", thread)

        self.init_error()
