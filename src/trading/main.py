from ibapi.contract import Contract as IBcontract
from ibapi.order import Order
from ibapi.execution import ExecutionFilter
from threading import Thread
import numpy as np, pandas as pd, datetime as dt, time
import queue, importlib, collections, utils, functions

## Initiate connection with IB server if not already connected, instanciate app if not already instantiated

app = TestApp("127.0.0.1", 7496, 1)
try:
    if app.isConnected()==False:
        app.connect("127.0.0.1", 7496, 1)
        time.sleep(1)
except NameError: app = TestApp("127.0.0.1", 7496, 1)

ibcontract, minTick = fn.make_contract(app, underlying)
order1 = fn.make_order(app, ibcontract, minTick, msg)
orderid1 = place_new_IB_order(app, ibcontract, order1, orderid=None)