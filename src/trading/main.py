import trading.functions as fn
import time
# Temporary, should be replaced by TradingView alert
underlying = 'EURUSD'
msg = 'n=entryL1 d=long t=m p=0 q=1 u=1 c=10000 b=1h'
# TODO: execute_message needs to return a dictionary including all information


def execute_message(underlying, msg):
    error = None
    start_time = time.time()
    try:
        app = fn.reconnect()['app']
        print("Calling make_contract")
        contract_dets = fn.make_contract(app, underlying)
        print("Calling make_order")
        order1 = fn.make_order(app, contract_dets, msg)
        if order1.totalQuantity == 0:
            print("NOTHING TO TRADE")
            return
        orderid1 = app.place_new_IB_order(contract_dets['ibcontract'], order1, orderid=None)
        filled = fn.check_fill(app, order1, orderid1)
        app.disconnect()
    except Exception as Exc:
        app.disconnect()
        error = Exc
    end_time = time.time()
    
    return({'order_id': orderid1, 'error': Exc, 'start_time': start_time, 'end_time': end_time})


if __name__ == "__main__":
    orderid = execute_message(underlying, msg)
    print("the code executued successfully, orderid=", orderid)
