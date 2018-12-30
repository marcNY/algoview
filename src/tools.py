from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from ibapi.contract import Contract as IBcontract
from ibapi.order import Order
from ibapi.execution import ExecutionFilter
from threading import Thread
import numpy as np, pandas as pd, datetime as dt, time
import queue, importlib, tools, collections
import HistMktData as hmd, OrderPlacement as op

TV_to_IB = {'EURUSD' : {'symbol' : 'EUR', 'secType' : 'CASH', 'currency' : 'USD', 'exchange' : 'IDEALPRO'},
            'ES1!, 1' : {'symbol' : 'ES', 'secType' : 'FUT', 'currency' : 'USD', 'exchange' : 'GLOBEX_IND', 'expiry' : '201903'},
            'CL1!, 1' : {'symbol' : 'CL', 'secType' : 'FUT', 'currency' : 'USD', 'exchange' : 'NYMEX', 'expiry' : '201901'},
            'GC1!, 1' : {'symbol' : 'GC', 'secType' : 'FUT', 'currency' : 'USD', 'exchange' : 'NYMEX', 'expiry' : '201902'},
            'TY1!, 1' : {'symbol' : 'ZN', 'secType' : 'FUT', 'currency' : 'USD', 'exchange' : 'ECBOT', 'expiry' : '201903'},
           }

def create_contract(symbol='IBKR', secType='STK', currency='USD', exchange='ISLAND', expiry=None):
    contract = IBcontract()
    contract.symbol = symbol
    contract.secType = secType
    contract.currency = currency
    contract.exchange = exchange
    if expiry:
        contract.lastTradeDateOrContractMonth = expiry

    return contract

def get_hist_data(ibcontract, durationStr='1 D', barSizeSetting='1 hour'):
    app = hmd.TestApp("127.0.0.1", 4001, 1) # Connection
    resolved_ibcontract = app.resolve_ib_contract(ibcontract)
    historic_data = app.get_IB_historical_data(resolved_ibcontract, durationStr, barSizeSetting)
    app.disconnect() # Disconnection

    return historic_data
