from ibapi.wrapper import EWrapper
from ibapi.contract import Contract as IBcontract
from threading import Thread
import queue, datetime
import trading.utils as utils


class TestWrapper(EWrapper):
    """
    The wrapper deals with the action coming back from the IB gateway or TWS instance
    We override methods in EWrapper that will get called when this action happens, like currentTime
    Extra methods are added as we need to store the results in this object
    """

    def __init__(self):
        self._my_contract_details = {}
        self._my_market_data_dict = {}
        self._my_requested_execution = {}
        self._my_accounts = {}
        self.init_error()

        # We set these up as we could get things coming along before we run an init
        self._my_executions_stream = queue.Queue()
        self._my_commission_stream = queue.Queue()
        self._my_open_orders = queue.Queue()
        self._my_positions = queue.Queue()

    # error handling code
    def init_error(self):
        error_queue = queue.Queue()
        self._my_errors = error_queue

    def get_error(self, timeout=5):
        if self.is_error():
            try:
                return self._my_errors.get(timeout=timeout)
            except queue.Empty:
                return None

        return None

    def is_error(self):
        an_error_if = not self._my_errors.empty()
        return an_error_if

    def error(self, id, errorCode, errorString):
        # Overriden method
        errormsg = "IB error id %d errorcode %d string %s" % (
            id, errorCode, errorString)
        self._my_errors.put(errormsg)
    ###########################
    ## CONTRACT DETAILS CODE ##
    ###########################

    def init_contractdetails(self, reqId):
        contract_details_queue = self._my_contract_details[reqId] = queue.Queue(
        )

        return contract_details_queue

    def contractDetails(self, reqId, contractDetails):
        # overridden method

        if reqId not in self._my_contract_details.keys():
            self.init_contractdetails(reqId)

        self._my_contract_details[reqId].put(contractDetails)

    def contractDetailsEnd(self, reqId):
        # overriden method
        if reqId not in self._my_contract_details.keys():
            self.init_contractdetails(reqId)

        self._my_contract_details[reqId].put(utils.FINISHED)
    ########################
    ## HISTORIC DATA CODE ##
    ########################

    def init_historicprices(self, tickerid):
        historic_data_queue = self._my_market_data_dict[tickerid] = queue.Queue(
        )

        return historic_data_queue

    def historicalData(self, tickerid, bar):

        # Overriden method
        # Note I'm choosing to ignore barCount, WAP and hasGaps but you could use them if you like
        bardata = (bar.date, bar.open, bar.high,
                   bar.low, bar.close, bar.volume)

        historic_data_dict = self._my_market_data_dict

        # Add on to the current data
        if tickerid not in historic_data_dict.keys():
            self.init_historicprices(tickerid)

        historic_data_dict[tickerid].put(bardata)

    def historicalDataEnd(self, tickerid, start: str, end: str):
        # Overriden method

        if tickerid not in self._my_market_data_dict.keys():
            self.init_historicprices(tickerid)

        self._my_market_data_dict[tickerid].put(utils.FINISHED)
    ####################
    ## LIVE DATA CODE ##
    ####################

    def init_market_data(self, tickerid):
        market_data_queue = self._my_market_data_dict[tickerid] = queue.Queue()

        return market_data_queue

    def get_time_stamp(self):
        # Time stamp to apply to market data
        # We could also use IB server time
        return datetime.datetime.now()

    def tickPrice(self, tickerid, tickType, price, attrib):
        # Overriden method

        # For simplicity I'm ignoring these but they could be useful to you...
        # See the documentation http://interactivebrokers.github.io/tws-api/md_receive.html#gsc.tab=0
        # attrib.canAutoExecute
        # attrib.pastLimit

        this_tick_data = utils.IBtick(self.get_time_stamp(), tickType, price)
        self._my_market_data_dict[tickerid].put(this_tick_data)

    def tickSize(self, tickerid, tickType, size):
        # Overriden method

        this_tick_data = utils.IBtick(self.get_time_stamp(), tickType, size)
        self._my_market_data_dict[tickerid].put(this_tick_data)

    def tickString(self, tickerid, tickType, value):
        # Overriden method

        # value is a string, make it a float, and then in the parent class will be resolved to int if size
        this_tick_data = utils.IBtick(
            self.get_time_stamp(), tickType, float(value))
        self._my_market_data_dict[tickerid].put(this_tick_data)

    def tickGeneric(self, tickerid, tickType, value):
        # Overriden method

        this_tick_data = utils.IBtick(self.get_time_stamp(), tickType, value)
        self._my_market_data_dict[tickerid].put(this_tick_data)
    ##########################
    ## ORDER PLACEMENT CODE ##
    ##########################

    def init_open_orders(self):
        open_orders_queue = self._my_open_orders = queue.Queue()

        return open_orders_queue

    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permid,
                    parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):

        order_details = utils.orderInformation(orderId, status=status, filled=filled,
                                               avgFillPrice=avgFillPrice, permid=permid,
                                               parentId=parentId, lastFillPrice=lastFillPrice, clientId=clientId,
                                               whyHeld=whyHeld, mktCapPrice=mktCapPrice)

        self._my_open_orders.put(order_details)

    def openOrder(self, orderId, contract, order, orderstate):
        """
        Tells us about any orders we are working now
        overriden method
        """

        order_details = utils.orderInformation(
            orderId, contract=contract, order=order, orderstate=orderstate)
        self._my_open_orders.put(order_details)

    def openOrderEnd(self):
        """
        Finished getting open orders
        Overriden method
        """

        self._my_open_orders.put(utils.FINISHED)

    """ Executions and commissions
    requested executions get dropped into single queue: self._my_requested_execution[reqId]
    Those that arrive as orders are completed without a relevant reqId go into self._my_executions_stream
    All commissions go into self._my_commission_stream (could be requested or not)
    The *_stream queues are permanent, and init when the TestWrapper instance is created
    """

    def init_requested_execution_data(self, reqId):
        execution_queue = self._my_requested_execution[reqId] = queue.Queue()

        return execution_queue

    def access_commission_stream(self):
        # Access to the 'permanent' queue for commissions

        return self._my_commission_stream

    def access_executions_stream(self):
        # Access to the 'permanent' queue for executions

        return self._my_executions_stream

    def commissionReport(self, commreport):
        """
        This is called if
        a) we have submitted an order and a fill has come back
        b) We have asked for recent fills to be given to us
        However no reqid is ever passed
        overriden method
        :param commreport:
        :return:
        """

        commdata = utils.execInformation(commreport.execId, Commission=commreport.commission,
                                         commission_currency=commreport.currency,
                                         realisedpnl=commreport.realizedPNL)

        # there are some other things in commreport you could add
        # make sure you add them to the .attributes() field of the execInformation class

        # These always go into the 'stream' as could be from a request, or a fill thats just happened
        self._my_commission_stream.put(commdata)

    def execDetails(self, reqId, contract, execution):
        """
        This is called if
        a) we have submitted an order and a fill has come back (in which case reqId will be FILL_CODE)
        b) We have asked for recent fills to be given to us (reqId will be
        See API docs for more details
        """
        # overriden method

        execdata = utils.execInformation(execution.execId, contract=contract,
                                         ClientId=execution.clientId, OrderId=execution.orderId,
                                         time=execution.time, AvgPrice=execution.avgPrice,
                                         AcctNumber=execution.acctNumber, Shares=execution.shares,
                                         Price=execution.price)

        # there are some other things in execution you could add
        # make sure you add them to the .attributes() field of the execInformation class

        reqId = int(reqId)

        # We eithier put this into a stream if its just happened, or store it for a specific request
        if reqId == utils.FILL_CODE:
            self._my_executions_stream.put(execdata)
        else:
            self._my_requested_execution[reqId].put(execdata)

    def execDetailsEnd(self, reqId):
        """
        No more orders to look at if execution details requested
        """
        self._my_requested_execution[reqId].put(utils.FINISHED)

    # order ids

    def init_nextvalidid(self):

        orderid_queue = self._my_orderid_data = queue.Queue()

        return orderid_queue

    def nextValidId(self, orderId):
        """
        Give the next valid order id
        Note this doesn't 'burn' the ID; if you call again without executing the next ID will be the same
        If you're executing through multiple clients you are probably better off having an explicit counter
        """
        if getattr(self, '_my_orderid_data', None) is None:
            # getting an ID which we haven't asked for
            # this happens, IB server just sends this along occassionally
            self.init_nextvalidid()

        self._my_orderid_data.put(orderId)
    ########################
    ## GET POSITIONS CODE ##
    ########################

    def init_positions(self):
        positions_queue = self._my_positions = queue.Queue()

        return positions_queue

    def position(self, account, contract, position,
                 avgCost):

        # uses a simple tuple, but you could do other, fancier, things here
        position_object = (account, contract, position,
                           avgCost)

        self._my_positions.put(position_object)

    def positionEnd(self):
        # overriden method

        self._my_positions.put(utils.FINISHED)
    #########################
    ## GET ACCOUNTING DATA ##
    #########################

    def init_accounts(self, accountName):
        accounting_queue = self._my_accounts[accountName] = queue.Queue()

        return accounting_queue

    def updateAccountValue(self, key: str, val: str, currency: str,
                           accountName: str):

        # use this to seperate out different account data
        data = utils.identifed_as(
            utils.ACCOUNT_VALUE_FLAG, (key, val, currency))
        self._my_accounts[accountName].put(data)

    def updatePortfolio(self, contract, position: float,
                        marketPrice: float, marketValue: float,
                        averageCost: float, unrealizedPNL: float,
                        realizedPNL: float, accountName: str):

        # use this to seperate out different account data
        data = utils.identifed_as(utils.ACCOUNT_UPDATE_FLAG, (contract, position, marketPrice, marketValue, averageCost,
                                                              unrealizedPNL, realizedPNL))
        self._my_accounts[accountName].put(data)

    def updateAccountTime(self, accountName: str, timeStamp: str):

        # use this to seperate out different account data
        data = utils.identifed_as(utils.ACCOUNT_TIME_FLAG, timeStamp)
        self._my_accounts[accountName].put(data)

    def accountDownloadEnd(self, accountName: str):

        self._my_accounts[accountName].put(utils.FINISHED)
