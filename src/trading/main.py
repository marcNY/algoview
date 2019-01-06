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
import utils
import functions as fn

# Temporary, should be replaced by TradingView alert
underlying = 'XLV'
msg = 'n=entryL1 d=long t=m p=0 q=1 u=1 c=10000 b=1h'


def execute_message(underlying, msg):
    try:
        app = fn.reconnect()
        print("Calling make_contract")
        ibcontract, minTick = fn.make_contract(app, underlying)
        print("Calling make_order")
        order1 = fn.make_order(app, ibcontract, minTick, msg)
        print("place_new_IB_order")
        orderid1 = app.place_new_IB_order(ibcontract, order1, orderid=None)
        app.disconnect()
    except Exception:
        app.disconnect()
        raise Exception
    return(orderid1)


if __name__ == "__main__":
    orderid = execute_message(underlying, msg)
    print("the code executued successfully, orderid=", orderid)
