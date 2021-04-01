import ccxt
import time
from pprint import pprint
import pymongo

symbol = 'BTC/USDT'
dbclient = pymongo.MongoClient("mongodb://192.168.10.2:27017/")
db = dbclient['bn']
order_col = db['orders']
trade_col = db['trades']
funds_col = db['funds']


bn = ccxt.binance({
    'enableRateLimit': True,
    'options': {'defaultType': 'future'},
    'apiKey': "wjbSUEfNMqGRjKgbqhhVzagdEp8j9L1oocoeDrjRTPcrWAvya0sfGqu1bhBBSh5T",
    'secret': "66sewwthz780T70w0w9I6Uz8fAF9u4O9XvcjiASMOCMpf0t8BRsjKK6hqnjfAybR"
})

#print(bn.fetch_balance())

#pprint(bn.fetchOHLCV('BTC/USDT', '15m'))
def avg_price(time):
    su1 = 0
    su2 = 0
    ohlcv = bn.fetchOHLCV(symbol,time)
    for i in ohlcv:
        su1 += abs(float(i[2]) - float(i[3]))
        su2 += abs(float(i[1]) - float(i[4]))
    return int(su1/len(ohlcv)),int(su2/len(ohlcv))

def id_check(id):
    open_order_id = []
    for order in bn.fetch_open_orders(symbol):
        open_order_id.append(order['id'])
    if id in open_order_id:
        return True
    else:
        return False

def make_order(btc_price, amount):
    if amount > 0:
        new_order = bn.create_limit_buy_order(symbol, amount, btc_price, {'positionSide': 'LONG'})
    else:
        amount = abs(amount)
        new_order = bn.create_limit_sell_order(symbol, amount, btc_price, {'positionSide': 'SHORT'})
    order_info = {
        'order_id': new_order['id'],
        'order_status': new_order['status'],
        'order_price': new_order['price'],
        'order_amount': new_order['amount'],
        'order_side': new_order['side'],
        'order_positionSide': new_order['info']['positionSide'],
        'order_uptime': time.strftime('%Y-%m-%d %H:%M%S', time.localtime(new_order['info']['updatetime']/1000))
    }
    order_col.insert_one(order_info)
    order_id = order_info['order_id']
    while True:
        for trade in bn.fetch_my_trades(symbol):
            if trade['order'] == order_id:
                print("挂单已成交！")
                trade_info = {
                    'trade_id': trade['order'],
                    'trade_price': trade['price'],
                    'trade_amount': trade['amount'],
                    'trade_cost': trade['fee']['cost'],
                    'trade_P&L': float(trade['info']['realizedPn1']),
                    'trade_side': trade['info']['side'],
                    'trade_positionSide': trade['info']['positionSide'],
                    'trade_time': trade['datetime']                
                }
                trade_col.insert_one(trade_info)
                order_col.find_one_and_update({'order_id': order_id}, {'$set': {'order_status': 'deal'}})
                break
            else:
                time.sleep(3)
