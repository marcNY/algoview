# %% Change working directory from the workspace root to the ipynb file location. Turn this addition off with the DataSciece.changeDirOnImportExport setting
import os

# %%
from importlib import reload as rel
import numpy as np
import pandas as pd
import datetime as dt
import time
import queue
import collections
import utils
import functions as fn
import OrderPlacement as op
import AccountPositions as ap
# %% [markdown]
# #### Simulated inputs (from extension)

# %%
underlying = 'XLV'
msg = 'n=entryL1 d=long t=m p=0 q=1 u=1 c=10000 b=1h'

# %%


def connect(app=None):
    if app is None:
        app = fn.TestApp("127.0.0.1", 4002, 1)
        print('App connected')
    if app.isConnected() == False:
        app.connect("127.0.0.1", 4002, 1)
        print('App reconnected')
    else:
        print('App already connected')
    return app


app = connect()
try:
    ibcontract, minTick = fn.make_contract(app, underlying)
    order1 = fn.make_order(app, ibcontract, minTick, msg)
    #orderid1 = op.place_new_IB_order(app, ibcontract, order1, orderid=None)
except:
    app.disconnect()
    raise Exception('The program raised an error')
app.disconnect()
print(str(ibcontract))
print(str(minTick))
print(str(order1))
