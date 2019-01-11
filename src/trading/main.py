import trading.functions as fn

# Temporary, should be replaced by TradingView alert
underlying = 'EURUSD'
msg = 'n=entryL1 d=long t=m p=0 q=1 u=1 c=10000 b=1h'


def execute_message(underlying, msg):
    try:
        app = fn.reconnect()
        print("Calling make_contract")
        ibcontract, minTick = fn.make_contract(app, underlying)
        print("Calling make_order")
        order1 = fn.make_order(app, ibcontract, minTick, msg)
        print("place_new_IB_order")
        if order1.totalQuantity == 0:
            print("NOTHING TO TRADE")
            return
        orderid1 = app.place_new_IB_order(ibcontract, order1, orderid=None)
        fn.check_fill(app, order1, orderid1)
        app.disconnect()
    except:
        app.disconnect()
        raise
    return(orderid1)


if __name__ == "__main__":
    orderid = execute_message(underlying, msg)
    print("the code executued successfully, orderid=", orderid)
