from ibapi.client import EClient
from ibapi.contract import Contract as IBcontract
from ibapi.execution import ExecutionFilter
import queue, datetime, time, trading.utils as utils
from copy import deepcopy


class TestClient(EClient):
    """
    The client method
    We don't override native methods, but instead call them from our own wrappers
    """

    def __init__(self, wrapper):
        # Set up with a wrapper inside
        EClient.__init__(self, wrapper)

        self._market_data_q_dict = {}
        self._commissions = utils.list_of_execInformation()
        # We use these to store accounting data
        self._account_cache = utils.simpleCache(max_staleness_seconds=5*60)
        # Override function
        self._account_cache.update_data = self._update_accounting_data

    def resolve_ib_contract(self, ibcontract, reqId=utils.DEFAULT_GET_CONTRACT_ID):
        """
        From a partially formed contract, returns a fully fledged version
        :returns fully resolved IB contract
        """

        # Make a place to store the data we're going to return
        info = None
        contract_details_queue = utils.finishableQueue(
            self.init_contractdetails(reqId))

        self.reqContractDetails(reqId, ibcontract)

        # Run until we get a valid contract(s) or get bored waiting
        max_wait_seconds = 2
        new_contract_details = contract_details_queue.get(
            timeout=max_wait_seconds)

        while self.wrapper.is_error():
            print(self.get_error())

        if contract_details_queue.timed_out():
            info = "Exceeded maximum wait for wrapper to confirm finished"
        
        no_contract_dets = False
        if len(new_contract_details) == 0:
            info = "Failed to get additional contract details: returning unresolved contract"
            no_contract_dets = True

        if len(new_contract_details) > 1:
            info = "got multiple contracts - using the first one"

        new_contract_details = new_contract_details[0]
        
        if no_contract_dets == False:
            resolved_ibcontract = new_contract_details.contract
            minTick = new_contract_details.minTick
        else:
            resolved_ibcontract = ibcontract
            minTick = 0

        return {'ibcontract': resolved_ibcontract, 'minTick': minTick, 'info': info}
    ##########################
    ## HISTORICAL DATA CODE ##
    ##########################

    def get_IB_historical_data(self, ibcontract, durationStr="1 M", barSizeSetting="1 day",
                               tickerid=utils.DEFAULT_HISTORIC_DATA_ID):
        """
        Returns historical prices for a contract, up to today
        ibcontract is a Contract
        :returns list of prices in 4 tuples: Open high low close volume
        """
        useRTH = 0
        whatToShow = 'TRADES'
        if ibcontract.secType == 'CASH' or ibcontract.secType == 'CMDTY':
            whatToShow = 'MIDPOINT'
        elif ibcontract.secType == 'STK':
            useRTH = 1

        # Make a place to store the data we're going to return
        historic_data_queue = utils.finishableQueue(
            self.init_historicprices(tickerid))

        # Request some historical data. Native method in EClient
        self.reqHistoricalData(
            tickerid,  # tickerId,
            ibcontract,  # contract,
            datetime.datetime.today().strftime("%Y%m%d %H:%M:%S %Z"),  # endDateTime,
            durationStr,  # durationStr,
            barSizeSetting,  # barSizeSetting,
            whatToShow,  # whatToShow,
            useRTH,  # useRTH,
            1,  # formatDate
            False,  # KeepUpToDate <== added for api 9.73.2
            []  # chartoptions not used
        )

        # Wait until we get a completed data, an error, or get bored waiting
        max_wait_seconds = 6

        historic_data = historic_data_queue.get(timeout=max_wait_seconds)

        while self.wrapper.is_error():
            print(self.get_error())

        if historic_data_queue.timed_out():
            print(
                "Exceeded maximum wait for wrapper to confirm finished - seems to be normal behaviour")

        self.cancelHistoricalData(tickerid)

        return historic_data
    ###########################
    ## LIVE MARKET DATA CODE ##
    ###########################

    def start_getting_IB_market_data(self, resolved_ibcontract, whatToShow=None, tickerid=utils.DEFAULT_GET_CONTRACT_ID):
        """
        Kick off market data streaming
        :param resolved_ibcontract: a Contract object
        :param tickerid: the identifier for the request
        :return: tickerid
        """
        
        useRTH = 0
        if resolved_ibcontract.secType == 'STK':
            useRTH = 1
        
        self._market_data_q_dict[tickerid] = self.wrapper.init_market_data(
            tickerid)
        self.reqMktData(tickerid, resolved_ibcontract, '1', True, False, [])
        # self.reqRealTimeBars(tickerid, resolved_ibcontract, 5, whatToShow, useRTH, [])

        return tickerid

    def stop_getting_IB_market_data(self, tickerid):
        """
        Stops the stream of market data and returns all the data we've had since we last asked for it
        :param tickerid: identifier for the request
        :return: market data
        """

        # native EClient method
        self.cancelMktData(tickerid)
        # self.cancelRealTimeBars(tickerid)

        # Sometimes a lag whilst this happens, this prevents 'orphan' ticks appearing
        time.sleep(1)

        market_data = self.get_IB_market_data(tickerid)

        # output ay errors
        while self.wrapper.is_error():
            print(self.get_error())

        return market_data

    def get_IB_market_data(self, tickerid):
        """
        Takes all the market data we have received so far out of the stack, and clear the stack
        :param tickerid: identifier for the request
        :return: market data
        """

        # how long to wait for next item
        max_wait_marketdataitem = 1
        market_data_q = self._market_data_q_dict[tickerid]

        market_data = []
        finished = False

        while not finished:
            try:
                market_data.append(market_data_q.get(timeout=max_wait_marketdataitem))
            except queue.Empty:
                # no more data
                finished = True
        
        quotes = utils.stream_of_ticks(market_data).as_pdDataFrame().resample("1S").last()[["bid_size", "bid_price", "ask_price", "ask_size"]]

        return quotes

    ##########################
    ## ORDER PLACEMENT CODE ##
    ##########################
    def get_next_brokerorderid(self):
        """
        Get next broker order id
        :return: broker order id, int; or TIME_OUT if unavailable
        """

        # Make a place to store the data we're going to return
        orderid_q = self.init_nextvalidid()

        self.reqIds(-1)  # -1 is irrelevant apparently (see IB API docs)

        # Run until we get a valid contract(s) or get bored waiting
        max_wait_seconds = 10
        try:
            brokerorderid = orderid_q.get(timeout=max_wait_seconds)
        except queue.Empty:
            print("Wrapper timeout waiting for broker orderid")
            brokerorderid = utils.TIME_OUT

        while self.wrapper.is_error():
            print(self.get_error(timeout=max_wait_seconds))

        return brokerorderid

    def place_new_IB_order(self, ibcontract, order, orderid=None):
        """
        Places an order
        Returns orderid
        """

        # We can either supply our own ID or ask IB to give us the next valid one
        if orderid is None:
            orderid = self.get_next_brokerorderid()

            if orderid is utils.TIME_OUT:
                raise Exception(
                    "I couldn't get an orderid from IB, and you didn't provide an orderid")

        # Note: It's possible if we have multiple trading instances for orderids to be submitted out of sequence
        # in which case IB will break

        # Place the order
        self.placeOrder(
            orderid,  # orderId,
            ibcontract,  # contract,
            order  # order
        )

        return orderid

    def any_open_orders(self):
        """
        Simple wrapper to tell us if we have any open orders
        """

        return len(self.get_open_orders()) > 0

    def get_open_orders(self):
        """
        Returns a list of any open orders
        """

        # store the orders somewhere
        open_orders_queue = utils.finishableQueue(self.init_open_orders())

        # You may prefer to use reqOpenOrders() which only retrieves orders for this client
        self.reqAllOpenOrders()

        # Run until we get a terimination or get bored waiting
        max_wait_seconds = 5
        open_orders_list = utils.list_of_orderInformation(
            open_orders_queue.get(timeout=max_wait_seconds))

        while self.wrapper.is_error():
            print(self.get_error())

        if open_orders_queue.timed_out():
            print(
                "Exceeded maximum wait for wrapper to confirm finished whilst getting orders")

        # open orders queue will be a jumble of order details, turn into a tidy dict with no duplicates
        open_orders_dict = open_orders_list.merged_dict()

        return open_orders_dict

    def get_executions_and_commissions(self, reqId=utils.DEFAULT_EXEC_TICKER, execution_filter=ExecutionFilter()):
        """
        Returns a list of all executions done today with commission data
        """

        # store somewhere
        execution_queue = utils.finishableQueue(
            self.init_requested_execution_data(reqId))

        # We can change ExecutionFilter to subset different orders
        # note this will also pull in commissions but we would use get_executions_with_commissions
        self.reqExecutions(reqId, execution_filter)

        # Run until we get a terimination or get bored waiting
        max_wait_seconds = 10
        exec_list = utils.list_of_execInformation(
            execution_queue.get(timeout=max_wait_seconds))

        while self.wrapper.is_error():
            print(self.get_error())

        if execution_queue.timed_out():
            print(
                "Exceeded maximum wait for wrapper to confirm finished whilst getting exec / commissions")

        # Commissions will arrive seperately. We get all of them, but will only use those relevant for us
        commissions = self._all_commissions()

        # glue them together, create a dict, remove duplicates
        all_data = exec_list.blended_dict(commissions)

        return all_data

    def _recent_fills(self):
        """
        Returns any fills since we last called recent_fills
        :return: list of executions as execInformation objects
        """

        # we don't set up a queue but access the permanent one
        fill_queue = self.access_executions_stream()

        list_of_fills = utils.list_of_execInformation()

        while not fill_queue.empty():
            max_wait_seconds = 5
            try:
                next_fill = fill_queue.get(timeout=max_wait_seconds)
                list_of_fills.append(next_fill)
            except queue.Empty:
                # corner case where Q emptied since we last checked if empty at top of while loop
                pass

        # note this could include duplicates and is a list
        return list_of_fills

    def recent_fills_and_commissions(self):
        """
        Return recent fills, with commissions added in
        :return: dict of execInformation objects, keys are execids
        """

        recent_fills = self._recent_fills()
        commissions = self._all_commissions()  # we want all commissions

        # glue them together, create a dict, remove duplicates
        all_data = recent_fills.blended_dict(commissions)

        return all_data

    def _recent_commissions(self):
        """
        Returns any commissions that are in the queue since we last checked
        :return: list of commissions as execInformation objects
        """

        # we don't set up a queue, as there is a permanent one
        comm_queue = self.access_commission_stream()

        list_of_comm = utils.list_of_execInformation()

        while not comm_queue.empty():
            max_wait_seconds = 5
            try:
                next_comm = comm_queue.get(timeout=max_wait_seconds)
                list_of_comm.append(next_comm)
            except queue.Empty:
                # corner case where Q emptied since we last checked if empty at top of while loop
                pass

        # note this could include duplicates and is a list
        return list_of_comm

    def _all_commissions(self):
        """
        Returns all commissions since we created this instance
        :return: list of commissions as execInformation objects
        """

        original_commissions = self._commissions
        latest_commissions = self._recent_commissions()

        all_commissions = utils.list_of_execInformation(
            original_commissions + latest_commissions)

        self._commissions = all_commissions

        # note this could include duplicates and is a list
        return all_commissions

    def cancel_order(self, orderid):

        # Has to be an order placed by this client. I don't check this here -
        # If you have multiple IDs then you you need to check this yourself.

        self.cancelOrder(orderid)

        # Wait until order is cancelled
        start_time = datetime.datetime.now()
        max_wait_seconds = 10

        finished = False

        while not finished:
            if orderid not in self.get_open_orders():
                # finally cancelled
                finished = True

            if (datetime.datetime.now() - start_time).seconds > max_wait_seconds:
                print(
                    "Wrapper didn't come back with confirmation that order was cancelled!")
                finished = True

    def cancel_all_orders(self):

        # Cancels all orders, from all client ids.
        # if you don't want to do this, then instead run .cancel_order over named IDs
        self.reqGlobalCancel()

        start_time = datetime.datetime.now()
        max_wait_seconds = 10

        finished = False

        while not finished:
            if not self.any_open_orders():
                # All orders finally cancelled
                finished = True
            if (datetime.datetime.now() - start_time).seconds > max_wait_seconds:
                print(
                    "Wrapper didn't come back with confirmation that all orders were cancelled!")
                finished = True

    ############################
    ## ACCOUNT POSITIONS CODE ##
    ############################
    def get_current_positions(self):
        """
        Current positions held
        :return:
        """

        # Make a place to store the data we're going to return
        positions_queue = utils.finishableQueue(self.init_positions())

        # ask for the data
        self.reqPositions()

        # poll until we get a termination or die of boredom
        max_wait_seconds = 8
        positions_list = positions_queue.get(timeout=max_wait_seconds)

        while self.wrapper.is_error():
            print(self.get_error())

        if positions_queue.timed_out():
            print(
                "Exceeded maximum wait for wrapper to confirm finished whilst getting positions")

        return positions_list

    def _update_accounting_data(self, accountName):
        """
        Update the accounting data in the cache
        :param accountName: account we want to get data for
        :return: nothing
        """

        # Make a place to store the data we're going to return
        accounting_queue = utils.finishableQueue(
            self.init_accounts(accountName))

        # ask for the data
        self.reqAccountUpdates(True, accountName)

        # poll until we get a termination or die of boredom
        max_wait_seconds = 5
        accounting_list = accounting_queue.get(timeout=max_wait_seconds)

        while self.wrapper.is_error():
            print(self.get_error())

        if accounting_queue.timed_out():
            print(
                "Exceeded maximum wait for wrapper to confirm finished whilst getting accounting data")

        # seperate things out, because this is one big queue of data with different things in it
        accounting_list = utils.list_of_identified_items(accounting_list)
        seperated_accounting_data = accounting_list.seperate_into_dict()

        # update the cache with different elements
        self._account_cache.update_cache(
            accountName, seperated_accounting_data)

        # return nothing, information is accessed via get_... methods

    def get_accounting_time_from_server(self, accountName):
        """
        Get the accounting time from IB server
        :return: accounting time as served up by IB
        """

        # All these functions follow the same pattern: check if stale or missing, if not return cache, else update values

        return self._account_cache.get_updated_cache(accountName, utils.ACCOUNT_TIME_FLAG)

    def get_accounting_values(self, accountName):
        """
        Get the accounting values from IB server
        :return: accounting values as served up by IB
        """

        # All these functions follow the same pattern: check if stale, if not return cache, else update values

        return self._account_cache.get_updated_cache(accountName, utils.ACCOUNT_VALUE_FLAG)

    def get_accounting_updates(self, accountName):
        """
        Get the accounting updates from IB server
        :return: accounting updates as served up by IB
        """

        # All these functions follow the same pattern: check if stale, if not return cache, else update values

        return self._account_cache.get_updated_cache(accountName, utils.ACCOUNT_UPDATE_FLAG)
