from ibapi.contract import Contract as IBcontract
from ibapi.order import Order
from ibapi.execution import ExecutionFilter
from threading import Thread
import numpy as np, pandas as pd, datetime as dt, time
import queue, importlib, collections, utils, functions as fn

## Temporary, should be replaced by TradingView alert
underlying = 'XLV'
msg = 'n=entryL1 d=long t=m p=0 q=1 u=1 c=10000 b=1h'

fn.reconnect()

ibcontract, minTick = fn.make_contract(app, underlying)
order1 = fn.make_order(app, ibcontract, minTick, msg)
# orderid1 = place_new_IB_order(app, ibcontract, order1, orderid=None)

app.disconnect()