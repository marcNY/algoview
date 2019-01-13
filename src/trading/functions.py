from ibapi.contract import Contract as IBcontract
from ibapi.order import Order
from ibapi.execution import ExecutionFilter
from threading import Thread
import numpy as np
import pandas as pd
import datetime as dt
import time, queue, importlib, collections
import utils
import database as db
from wrapper import TestWrapper
from client import TestClient

TV_to_IB = db.TV_to_IB
conId_to_ul = db.conId_to_ul


def reconnect(app=None, client=1):
    exception = None
    info = None
    try:
        if app is None or not isinstance(app, TestApp):
            app = TestApp("127.0.0.1", 4001, client)
            info = "app init ever None or wrong object was passed"
        if app.isConnected() == False:
            app.connect("127.0.0.1", 4001, client)
            if app.isConnected() == False:
                info = 'app cannot connect probably IB Gateway not connected'
            else:
                info = 'app existed and reconnected'
        else:
            info = 'app already connected'
    except Exception as Exc:
        exception = Exc

    return {'app': app, 'exception': exception, 'info': info}


def make_contract(app, underlying):
    reconnect(app)
    exception = None
    try:
        TV_to_IB[underlying]
    except Exception as Exc:
        exception = Exc
    ibcontract = utils.create_contract(TV_to_IB[underlying]['symbol'], TV_to_IB[underlying]['secType'],
                                       TV_to_IB[underlying]['currency'], TV_to_IB[underlying]['exchange'],
                                       TV_to_IB[underlying]['expiry'])
    contract_dets = app.resolve_ib_contract(ibcontract)
    resolved_ibcontract = contract_dets['ibcontract']
    minTick = contract_dets['minTick']
    
    return {'ibcontract': resolved_ibcontract, 'minTick': minTick, 'exception': exception}


def make_order(app, contract_dets, message):
    reconnect(app)
    ibcontract = contract_dets['ibcontract']
    minTick = contract_dets['minTick']
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
            app, ibcontract, order_params['u'], order_params['c'], order_params['b'])['unit']
        order.totalQuantity = int(q * unit)
    else:
        order.totalQuantity = int(get_pos(app, ibcontract)['position'])

    order.transmit = True

    return order


def calc_unit(app, ibcontract, unit_size, initial_capital, barSize):
    '''
    INPUTS
    unit_size: % of initial_capital(USD) allocated
    timeframe: the timeframe used to generate the alerts

    OUTPUTS
    unit: number of contracts to be traded on each entry
    '''
    reconnect(app)
    exception = None
    durationStr, barSizeSetting = utils.calc_bar_dur(barSize)
    n = 0
    while n==0:
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
    try:
        unit = float(unit_size) / 100 * float(initial_capital) / (N * mult)
    except Exception as Exc:
        exception = Exc

    return {'unit': unit, 'exception': exception}


def get_pos(app, ibcontract):
    holdings = app.get_current_positions()
    pos = 0
    info = None

    for item in holdings:
        if ibcontract.conId == item[1].conId:
            pos = item[2]

    if pos == 0:
        info = 'No position to exit'

    return {'position': pos, 'info': info}


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
        time = item[item.find('time')+6:item.find('AvgPrice')-1]
        OrderId = int(item[item.find('OrderId')+9:item.find('time')-1])
        AvgPrice = float(
            item[item.find('AvgPrice')+10:item.find('Price', item.find('AvgPrice')+5)-1])
        if len(item) > item.find('Shares')+15:
            Shares = int(
                float(item[item.find('Shares')+8:item.find('Commission')-1]))
        else:
            Shares = int(float(item[item.find('Shares')+8:len(item)]))
        conId = int(item[item.find('Execution')+22:item.find(',')])
        underlying = conId_to_ul[conId]
        ClientId = int(item[item.find('ClientId')+10:item.find('OrderId')-1])

        exec_tuples.append(
            (underlying, time, OrderId, AvgPrice, Shares, conId, ClientId))
    exec_df = pd.DataFrame(exec_tuples,
                           columns=['underlying', 'time', 'OrderId', 'AvgPrice', 'Shares', 'conId', 'ClientId'])

    exec_df.set_index('time', inplace=True)

    return exec_df


def get_openOrders(app):
    reconnect(app)
    orders_dict = app.get_open_orders()
    orders_list = [str(v) for k, v in orders_dict.items()]
    orders_tuples = []
    for item in orders_list:
        conId = int(item[18:item.find(',')])
        underlying = conId_to_ul[conId]
        quantity = int(item[item.find('BUY')+4:item.find('@')])
        price = float(item[item.find('@')+1:item.find('DAY')-1])
        status = item[item.find('status')+8:item.find('filled')-1]
        if item.find('MKT')>0:
            order_type = 'market'
        else:
            order_type = 'limit'
        if item.find('BUY')>0:
            direction = 'buy'
        else:
            direction = 'sell'
        filled = float(item[item.find('filled')+8:item.find('avgFillPrice')-1])
        avgFillPrice = float(item[item.find('avgFillPrice')+14:item.find('permid')-1])
        clientId = int(item[item.find('clientId')+10:item.find('whyHeld')-1])

        orders_tuples.append(
            (status, underlying, direction, order_type, quantity, price, filled, avgFillPrice, conId, clientId))
    orders_df = pd.DataFrame(orders_tuples,
                           columns=['status', 'underlying', 'direction', 'order type', 'quantity', 'price', 'filled', 'avg fill px', 'conId', 'ClientId'])
    # orders_df.set_index('time', inplace=True)
    app.disconnect()
    
    return orders_df


def check_fill(app, order1, orderid1):
    """
    Check_fill: check if order has been filled, 
    return False if the order has not been filled and True if it has been executed
    """
    reconnect(app)
    fill_status = False
    counter = 0
    Shares = 0
    price = 0
    while fill_status == False and counter < 5:
        counter += 1
        exec_dict = app.get_executions_and_commissions()
        exec_list = [str(v) for k, v in exec_dict.items()]
        for item in exec_list:
            if int(item[item.find('OrderId')+9:item.find('time')-1]) == orderid1:
                price = float(item[item.find('AvgPrice')+10:item.find('Price', item.find('AvgPrice')+5)-1])
                if len(item) > item.find('Shares')+15:
                    Shares += int(float(item[item.find('Shares') +
                                             8:item.find('Commission')-1]))
                else:
                    Shares += int(float(item[item.find('Shares')+8:len(item)]))
                if Shares == order1.totalQuantity:
                    fill_status = True
        time.sleep(1)
    
    return {'fill_status': fill_status, 'price': price}


class TestApp(TestWrapper, TestClient):
    def __init__(self, ipaddress, portid, clientid):
        TestWrapper.__init__(self)
        TestClient.__init__(self, wrapper=self)

        self.connect(ipaddress, portid, clientid)

        thread = Thread(target=self.run)
        thread.start()

        setattr(self, "_thread", thread)

        self.init_error()
