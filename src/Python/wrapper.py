from ibapi.wrapper import EWrapper
from threading import Thread
import queue, datetime, utils


class TestWrapper(EWrapper):
    """
    The wrapper deals with the action coming back from the IB gateway or TWS instance
    We override methods in EWrapper that will get called when this action happens, like currentTime
    Extra methods are added as we need to store the results in this object
    """

    def __init__(self):
        self._my_contract_details = {}
        self._my_market_data_dict = {}

    ## error handling code
    def init_error(self):
        error_queue=queue.Queue()
        self._my_errors = error_queue

    def get_error(self, timeout=5):
        if self.is_error():
            try:
                return self._my_errors.get(timeout=timeout)
            except queue.Empty:
                return None

        return None

    def is_error(self):
        an_error_if=not self._my_errors.empty()
        return an_error_if

    def error(self, id, errorCode, errorString):
        ## Overriden method
        errormsg = "IB error id %d errorcode %d string %s" % (id, errorCode, errorString)
        self._my_errors.put(errormsg)


    ## get contract details code
    def init_contractdetails(self, reqId):
        contract_details_queue = self._my_contract_details[reqId] = queue.Queue()

        return contract_details_queue

    def contractDetails(self, reqId, contractDetails):
        ## overridden method

        if reqId not in self._my_contract_details.keys():
            self.init_contractdetails(reqId)

        self._my_contract_details[reqId].put(contractDetails)

    def contractDetailsEnd(self, reqId):
        ## overriden method
        if reqId not in self._my_contract_details.keys():
            self.init_contractdetails(reqId)

        self._my_contract_details[reqId].put(utils.FINISHED)

    ## HISTORIC DATA CODE
    def init_historicprices(self, tickerid):
        historic_data_queue = self._my_market_data_dict[tickerid] = queue.Queue()

        return historic_data_queue


    def historicalData(self, tickerid , bar):

        ## Overriden method
        ## Note I'm choosing to ignore barCount, WAP and hasGaps but you could use them if you like
        bardata=(bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume)

        historic_data_dict = self._my_market_data_dict

        ## Add on to the current data
        if tickerid not in historic_data_dict.keys():
            self.init_historicprices(tickerid)

        historic_data_dict[tickerid].put(bardata)

    def historicalDataEnd(self, tickerid, start:str, end:str):
        ## Overriden method

        if tickerid not in self._my_market_data_dict.keys():
            self.init_historicprices(tickerid)

        self._my_market_data_dict[tickerid].put(utils.FINISHED)
    
    ## LIVE DATA CODE
    def init_market_data(self, tickerid):
        market_data_queue = self._my_market_data_dict[tickerid] = queue.Queue()

        return market_data_queue


    def get_time_stamp(self):
        ## Time stamp to apply to market data
        ## We could also use IB server time
        return datetime.datetime.now()


    def tickPrice(self, tickerid , tickType, price, attrib):
        ## Overriden method

        ## For simplicity I'm ignoring these but they could be useful to you...
        ## See the documentation http://interactivebrokers.github.io/tws-api/md_receive.html#gsc.tab=0
        # attrib.canAutoExecute
        # attrib.pastLimit

        this_tick_data = utils.IBtick(self.get_time_stamp(),tickType, price)
        self._my_market_data_dict[tickerid].put(this_tick_data)


    def tickSize(self, tickerid, tickType, size):
        ## Overriden method

        this_tick_data = utils.IBtick(self.get_time_stamp(), tickType, size)
        self._my_market_data_dict[tickerid].put(this_tick_data)


    def tickString(self, tickerid, tickType, value):
        ## Overriden method

        ## value is a string, make it a float, and then in the parent class will be resolved to int if size
        this_tick_data = utils.IBtick(self.get_time_stamp(),tickType, float(value))
        self._my_market_data_dict[tickerid].put(this_tick_data)


    def tickGeneric(self, tickerid, tickType, value):
        ## Overriden method

        this_tick_data = utils.IBtick(self.get_time_stamp(),tickType, value)
        self._my_market_data_dict[tickerid].put(this_tick_data)