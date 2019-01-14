import trading.functions as fn
import os
import time
cwd = os.getcwd()
print(cwd)
if cwd.find('src') != len(cwd)-3:
    if cwd.find('algoview') == len(cwd)-8:
        os.chdir(cwd + '/src')
    elif len(cwd) > cwd.find('src')+3:
        os.chdir(cwd[:cwd.find('src')+3])
    else:
        print('Warning: cannot resolve path')


# Example of underlying/msg from a TradingView alert
underlying = 'EURUSD'
msg = 'n=entryL1 d=long t=m p=0 q=1 u=1 c=10000 b=1h'


def execute_message(underlying, msg):
    start_time = time.time()

    error = None
    info = None
    fill_status = False
    avg_price = 0
    orderid1 = None

    try:
        app = fn.reconnect()['app']
        contract_dets = fn.make_contract(app, underlying)
        order1 = fn.make_order(app, contract_dets, msg)

        if order1.totalQuantity != 0:
            orderid1 = app.place_new_IB_order(
                contract_dets['ibcontract'], order1, orderid=None)
            fill_dets = fn.check_fill(app, order1, orderid1)
            fill_status = fill_dets['fill_status']
            avg_price = fill_dets['price']
        else:
            info = "Nothing to trade"

        exec_df = fn.get_execDetails(app)
        orders_df = fn.get_openOrders(app)
            
        app.disconnect()
    except Exception as Exc:
        app.disconnect()
        error = str(Exc)

    end_time = time.time()

    return({'order_id': orderid1, 'fill_status': fill_status, 'avg_price': avg_price, 'error': error, 'info': info, 'start_time': start_time, 'end_time': end_time})


if __name__ == "__main__":
    orderid = execute_message(underlying, msg)
    print("the code executued successfully, orderid=", orderid)
