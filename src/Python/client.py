from ibapi.client import EClient
import queue, datetime, utils, time


class TestClient(EClient):
    """
    The client method
    We don't override native methods, but instead call them from our own wrappers
    """
    def __init__(self, wrapper):
        ## Set up with a wrapper inside
        EClient.__init__(self, wrapper)
        
        self._market_data_q_dict = {}


    def resolve_ib_contract(self, ibcontract, reqId=utils.DEFAULT_GET_CONTRACT_ID):

        """
        From a partially formed contract, returns a fully fledged version
        :returns fully resolved IB contract
        """

        ## Make a place to store the data we're going to return
        contract_details_queue = utils.finishableQueue(self.init_contractdetails(reqId))

        print("Getting full contract details from the server... ")

        self.reqContractDetails(reqId, ibcontract)

        ## Run until we get a valid contract(s) or get bored waiting
        MAX_WAIT_SECONDS = 10
        new_contract_details = contract_details_queue.get(timeout = MAX_WAIT_SECONDS)

        while self.wrapper.is_error():
            print(self.get_error())

        if contract_details_queue.timed_out():
            print("Exceeded maximum wait for wrapper to confirm finished - seems to be normal behaviour")

        if len(new_contract_details)==0:
            print("Failed to get additional contract details: returning unresolved contract")
            return ibcontract

        if len(new_contract_details)>1:
            print("got multiple contracts - will use the first one")

        new_contract_details = new_contract_details[0]

        resolved_ibcontract = new_contract_details.contract
        minTick = new_contract_details.minTick

        return resolved_ibcontract, minTick


    def get_IB_historical_data(self, ibcontract, durationStr="1 M", barSizeSetting="1 day",
                               tickerid=utils.DEFAULT_HISTORIC_DATA_ID):

        """
        Returns historical prices for a contract, up to today
        ibcontract is a Contract
        :returns list of prices in 4 tuples: Open high low close volume
        """
        useRTH = 0
        whatToShow = 'TRADES'
        if ibcontract.secType=='CASH' or ibcontract.secType=='CMDTY':
            whatToShow = 'MIDPOINT'
        elif ibcontract.secType=='STK':
            useRTH = 1
        
        ## Make a place to store the data we're going to return
        historic_data_queue = utils.finishableQueue(self.init_historicprices(tickerid))

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
            [] ## chartoptions not used
        )

        ## Wait until we get a completed data, an error, or get bored waiting
        MAX_WAIT_SECONDS = 8
        print("Getting historical data from the server... could take up to %d seconds to complete " % MAX_WAIT_SECONDS)

        historic_data = historic_data_queue.get(timeout = MAX_WAIT_SECONDS)

        while self.wrapper.is_error():
            print(self.get_error())

        if historic_data_queue.timed_out():
            print("Exceeded maximum wait for wrapper to confirm finished - seems to be normal behaviour")

        self.cancelHistoricalData(tickerid)

        return historic_data
    

    def start_getting_IB_market_data(self, resolved_ibcontract, whatToShow, tickerid=utils.DEFAULT_GET_CONTRACT_ID):
        """
        Kick off market data streaming
        :param resolved_ibcontract: a Contract object
        :param tickerid: the identifier for the request
        :return: tickerid
        """
        self._market_data_q_dict[tickerid] = self.wrapper.init_market_data(tickerid)
        # self.reqMktData(tickerid, resolved_ibcontract, "", False, False, [])
        self.reqRealTimeBars(tickerid, resolved_ibcontract, 5, whatToShow, 1, [])

        return tickerid


    def stop_getting_IB_market_data(self, tickerid):
        """
        Stops the stream of market data and returns all the data we've had since we last asked for it
        :param tickerid: identifier for the request
        :return: market data
        """

        ## native EClient method
        self.cancelMktData(tickerid)

        ## Sometimes a lag whilst this happens, this prevents 'orphan' ticks appearing
        time.sleep(5)

        market_data = self.get_IB_market_data(tickerid)

        ## output ay errors
        while self.wrapper.is_error():
            print(self.get_error())

        return market_data


    def get_IB_market_data(self, tickerid):
        """
        Takes all the market data we have received so far out of the stack, and clear the stack
        :param tickerid: identifier for the request
        :return: market data
        """

        ## how long to wait for next item
        MAX_WAIT_MARKETDATAITEM = 5
        market_data_q = self._market_data_q_dict[tickerid]

        market_data=[]
        finished=False

        while not finished:
            try:
                market_data.append(market_data_q.get(timeout=MAX_WAIT_MARKETDATAITEM))
            except queue.Empty:
                ## no more data
                finished=True

        return utils.stream_of_ticks(market_data)