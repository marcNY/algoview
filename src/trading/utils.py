import numpy as np, pandas as pd
import queue, datetime

# Define global variables used in several modules:
global FINISHED
FINISHED = object() # marker for when queue is finished
global STARTED
STARTED = object()
global TIME_OUT
TIME_OUT = object()

global DEFAULT_HISTORIC_DATA_ID
DEFAULT_HISTORIC_DATA_ID = 50
global DEFAULT_GET_CONTRACT_ID
DEFAULT_GET_CONTRACT_ID = 43

class finishableQueue(object):

    def __init__(self, queue_to_finish):

        self._queue = queue_to_finish
        self.status = STARTED

    def get(self, timeout):
        """
        Returns a list of queue elements once timeout is finished, or a FINISHED flag is received in the queue
        :param timeout: how long to wait before giving up
        :return: list of queue elements
        """
        contents_of_queue=[]
        finished=False

        while not finished:
            try:
                current_element = self._queue.get(timeout=timeout)
                if current_element is FINISHED:
                    finished = True
                    self.status = FINISHED
                else:
                    contents_of_queue.append(current_element)
                    ## keep going and try and get more data

            except queue.Empty:
                ## If we hit a time out it's most probable we're not getting a finished element any time soon
                ## give up and return what we have
                finished = True
                self.status = TIME_OUT


        return contents_of_queue

    def timed_out(self):
        return self.status is TIME_OUT


def _nan_or_int(x):
    if not np.isnan(x):
        return int(x)
    else:
        return x

    
class stream_of_ticks(list):
    """
    Stream of ticks
    """

    def __init__(self, list_of_ticks):
        super().__init__(list_of_ticks)

    def as_pdDataFrame(self):

        if len(self)==0:
            ## no data; do a blank tick
            return tick(datetime.datetime.now()).as_pandas_row()

        pd_row_list=[tick.as_pandas_row() for tick in self]
        pd_data_frame=pd.concat(pd_row_list)

        return pd_data_frame


class tick(object):
    """
    Convenience method for storing ticks
    Not IB specific, use as abstract
    """
    def __init__(self, timestamp, bid_size=np.nan, bid_price=np.nan,
                 ask_size=np.nan, ask_price=np.nan,
                 last_trade_size=np.nan, last_trade_price=np.nan,
                 ignorable_tick_id=None):

        ## ignorable_tick_id keyword must match what is used in the IBtick class

        self.timestamp=timestamp
        self.bid_size=_nan_or_int(bid_size)
        self.bid_price=bid_price
        self.ask_size=_nan_or_int(ask_size)
        self.ask_price=ask_price
        self.last_trade_size=_nan_or_int(last_trade_size)
        self.last_trade_price=last_trade_price

    def __repr__(self):
        return self.as_pandas_row().__repr__()

    def as_pandas_row(self):
        """
        Tick as a pandas dataframe, single row, so we can concat together
        :return: pd.DataFrame
        """

        attributes=['bid_size','bid_price', 'ask_size', 'ask_price',
                    'last_trade_size', 'last_trade_price']

        self_as_dict=dict([(attr_name, getattr(self, attr_name)) for attr_name in attributes])

        return pd.DataFrame(self_as_dict, index=[self.timestamp])


class IBtick(tick):
    """
    Resolve IB tick categories
    """

    def __init__(self, timestamp, tickid, value):

        resolve_tickid=self.resolve_tickids(tickid)
        super().__init__(timestamp, **dict([(resolve_tickid, value)]))

    def resolve_tickids(self, tickid):

        tickid_dict=dict([("0", "bid_size"), ("1", "bid_price"), ("2", "ask_price"), ("3", "ask_size"),
                          ("4", "last_trade_price"), ("5", "last_trade_size")])

        if str(tickid) in tickid_dict.keys():
            return tickid_dict[str(tickid)]
        else:
            # This must be the same as the argument name in the parent class
            return "ignorable_tick_id"