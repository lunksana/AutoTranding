import ccxt
import time
import pymongo
import pandas as pd
import userapi
from concurrent.futures import ThreadPoolExecutor
from pprint import pprint
from cyberbrain import trace

# 初始化变量及数据库
symbol = 'BTC/USDT'
dbclient = pymongo.MongoClient(userapi.dbaddr,userapi.dbport)
db = dbclient['bn']
price_db = dbclient['price']
# 挂单
order_col = db['orders']
# 已成交订单
trade_col = db['trades']
# 资金情况
funds_col = db['funds']
# 持仓情况
positions_col = db['positions']

bn = ccxt.binance({
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
        'adjustForTimeDifference': True
    },
    'apiKey': userapi.apiKey,
    'secret': userapi.secret
}) 

# 价格涨幅波动
#@trace
def avg_ch(time):
    ohlcv = bn.fetchOHLCV('BTC/USDT',time)
    ch_sum = 0
    for i in ohlcv:
        ch_sum += abs(i[2]-i[3])
    return int(ch_sum/len(ohlcv))



pprint(bn.fetch_balance()['free'])
#pprint(bn.fetch_open_orders('BTC/USDT'))
pprint(bn.fetch_ticker('BTC/USDT')['last'])
#pprint(bn.fetch_orders('BTC/USDT')[-3])



#bn.create_order('BTC/USDT','limit','sell',0.002,66000,{'positionSide': 'SHORT'})
#pprint(bn.fetchOHLCV('BTC/USDT','1h')[-1])
#btc_price = bn.fetch_ticker('BTC/USDT')['last']

#pprint(bn.fapiPrivate_get_account()['assets'])
#pprint(bn.fapiPrivate_get_usertrades({'symbol': 'BTCUSDT'})[-1])
#pprint(bn.fetch_my_trades('BTC/USDT')[-1])
#pprint(bn.fetch_open_orders('BTC/USDT'))
# while btc_price > 56000:
#     if btc_price > 60000:
#         order_price = btc_price + 50
#         bn.create_order('BTC/USDT','limit','buy',0.01,order_price,{'positionSide': 'SHORT'})
#     elif btc_price <= 57000:
#         order_price = btc_price - 50
#         bn.create_order('BTC/USDT','limit','buy',0.005,order_price,{'positionSide': 'SHORT'})
#     elif btc_price <= 56500:
#         order_price = btc_price - 50
#         bn.create_order('BTC/USDT','limit','buy',0.005,order_price,{'positionSide': 'SHORT'})
    
print(int(avg_ch('1h') * 0.618))

#pprint(bn.fetch_closed_orders(symbol))
closed_order_ids = []
for i in bn.fetch_closed_orders(symbol):
    closed_order_ids.append(i['id'])

trade_ids = []
for i in bn.fetch_my_trades(symbol):
    trade_ids.append(i['order'])
print(len(closed_order_ids),len(trade_ids))
same_id = 0
for i in closed_order_ids:
    if i in trade_ids:
        same_id += 1
print(same_id)
        
#pprint(bn.create_order('BTC/USDT', 'limit', 'sell', 0.001, 62000, {'positionSide': 'SHORT'}))




#print(bn.fetch_balance())

#pprint(bn.fetchOHLCV('BTC/USDT', '15m'))
# 价格波动值
# def avg_price(time):
#     su1 = 0
#     su2 = 0
#     ohlcv = bn.fetchOHLCV(symbol,time)
#     for i in ohlcv:
#         su1 += abs(float(i[2]) - float(i[3]))
#         su2 += abs(float(i[1]) - float(i[4]))
#     return int(su1/len(ohlcv)),int(su2/len(ohlcv))

# 检测订单是否还是挂单状态
def id_check(id):
    open_order_id = []
    for order in bn.fetch_open_orders(symbol):
        open_order_id.append(order['id'])
    if id in open_order_id:
        return True
    else:
        return False

# 开单
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
        'order_uptime': time.strftime('%Y-%m-%d %H:%M%S', time.localtime(new_order['info']['updatetime']))
    }
    order_col.insert_one(order_info)
    order_id = order_info['order_id']
    return order_id

# 建立止损止盈单
'''
Type	                        强制要求的参数
LIMIT	                        timeInForce, quantity, price
MARKET	                        quantity
STOP, TAKE_PROFIT	            quantity, price, stopPrice
STOP_MARKET, TAKE_PROFIT_MARKET	stopPrice
TRAILING_STOP_MARKET	        callbackRate
'''
# 建立止损单
'''
bn.fapiPrivate_post_order({
    'symbol': 'BTCUSDT', #必要参数
    'side': 'SELL,BUY',  #必要参数
    'positionSide': 'LONG,SHORT', #以此判断此为空单还是多单
    'type': 'LIMIT,MARKET,STOP,TAKE_PROFIT,STOP_MARKET,TAKE_PROFIT_MARKET,TRAILING_STOP_MARKET', #必要参数
    'reduceOnly': 'True,false', #不能和closePosition一同使用
    'quantity': 0, #下单的数量，如果有closePosition则此参数无意义
    'price': 0, #价格，一般止损止盈都是以stopPrice为出发条件
    'newClientOrderId': '^[\.A-Z\:/a-z0-9_-]{1,36}$', #自定义订单ID
    'stopPrice': 0, #出发价格，STOP,STOP_MARKET,TAKE_PROFIT,TAKE_PROFIT_MARKET这几个类型是采用
    'closePosition': 'True,false', #不与reduceOnly及quantity一起使用，仅支持STOP_MARKET,TAKE_PROFIT_MARKET
    'workingType': 'MARK_PRICE,CONTRACT_PRICE' #stopPrice触发类型，默认为最新价格，也可更改为标记价格
})   
'''
def create_tpsl_order(type, ratio, price, positions_info):
    upperType = type.upper()
    typeList = ['STOP', 'TAKE_PROFIT', 'STOP_MARKET', 'TAKE_PROFIT_MARKET']
    if upperType not in typeList:
        print('订单模式错误！请重新输入！！')
        exit()
    else:
        if upperType == 'STOP' or upperType == 'TAKE_PROFIT':
            quantityIsNeeded = True
            priceIsNeeded = True
            stoppriceIsNeeded = True
        elif upperType == 'STOP_MARKET' or upperType == 'TAKE_PROFIT_MARKET':
            stoppriceIsNeeded = True
    if ratio == None:
        closepositionIsNeed = True
        quantityIsNeeded = False
    # 必要参数
    # amount,side,positionSide
    if len(positions_info) > 1:
        for i in positions_info:
            if i['positionSide'] == 'LONG':
                positionsSide = 'LONG'
                side = 'SELL'
            else:
                positionsSide = 'SHORT'
                side = 'BUY'
    else:
        if positions_info['positionSide'] == 'LONG':
            side = 'SELL'
        else:
            side = 'BUY'
        positionsSide = positions_info['positionSide']
        
    
        
                        


# 判断挂单是否成交
'''
也可以通过closed订单判断，成交的订单自动会进入closed订单中，fetch_closed_orders 'id' == fetch_my_traders 'order'
'''
def order_check(order_id):
    order_status = bn.fetch_order_status(order_id,symbol)
    while order_status == "open":
        time.sleep(3)
        order_status = bn.fetch_order_status(order_id,symbol)
        continue
    if order_status == "closed":
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
                order_col.find_one_and_update({'order_id': order_id}, {'$set': {'order_status': 'closed'}})
    else:
        order_col.find_one_and_update({'order_id': order_id}, {'$set': {'order_status': 'canceled'}})
    return order_status    
    


# MA计算
def ma(long,time):
    ohlcv = bn.fetchOHLCV(symbol,time)
    ohlcvsum = 0
    for i in range(0-long,0):
        ohlcvsum += ohlcv[i][4]
    return ohlcvsum/long

# 获取当前持仓
'''
获取的持仓信息
{'entryPrice': '56791.66666',
 'isolatedMargin': '31.97800937',
 'isolatedWallet': '27.75053162',
 'leverage': '20',
 'liquidationPrice': '54233.54768876',
 'marginType': 'isolated',
 'markPrice': '57214.41443521',
 'maxNotionalValue': '10000000',
 'notional': '572.14414435',
 'positionAmt': '0.010',
 'positionSide': 'LONG',
 'symbol': 'BTCUSDT',
 'unRealizedProfit': '4.22747775'}
'''
def fetch_positions(symbol):
    bn_symbol = symbol.replace('/','')
    positions_list = []
    for i in bn.fapiPrivateV2GetPositionRisk():
        if i['symbol'] == bn_symbol and float(i['entryPrice']) > 0:
            positions_list.append(i)
            position_info = {
                'symbol': symbol,
                'positionSide': i['positionSide'],
                'price': float(i['entryPrice']),
                'margin': float(i['isolatedWallet']),
                'amount': float(i['positionAmt']),
                'liquidationPrice': float(i['liquidationPrice']),
                'leverage': int(i['leverage'])
            }
            positions_col.insert_one(position_info)
    return positions_list

# 价格监测
def price_monitor(time):
    while True:
        btc_price = bn.fetch_ticker(symbol)['last']
        month = time.strftime('%m',time.localtime(time.time()))
        price_mouth_col = price_db[month]
        price_now = {
            'btc_price': btc_price,
            'updatetime': time.strftime('%d-%H:%M:%S',time.localtime(time.time()))
        }
        price_mouth_col.insert_one(price_now)
        time.sleep(3)

    

#pprint(bn.fetch_open_orders('BTC/USDT'))
#print(ma(5,'1h'))
# pprint(bn.fetch_ohlcv(symbol,'1m')[-1])
# pprint(bn.fetchOHLCV(symbol,'1m')[-1])
# pprint(bn.fetch_ohlcvc(symbol,'1m')[-1])
# 获取挂单情况，成交即closed，取消即canceled
#pprint(bn.fetch_order_status('17322430560',symbol))
#bn.fetchopenpositions(symbol)
# 获取转账记录
#pprint(bn.fetch_withdrawals())

#bn.create_limit_sell_order(symbol, 0, 0, {'stopPrice': 57000, 'type': 'stopmarket'})
# bn.create_order(symbol, 'TAKE_PROFIT_MARKET', 'SELL', 0, 0, {
#     'stopPrice': 57960, 'positionSide': 'LONG', 'closePosition': True})

# bn.fapiPrivate_post_order({
#     'symbol': 'BTCUSDT',
#     'positionSide': 'LONG',
#     'side': 'SELL',
#     'type': 'TAKE_PROFIT',
#     'quantity': 0.002,
#     'stopPrice': 56900,
#     'workingType': 'MARK_PRICE',
#     'price':
# })

# pprint(bn.fapiPrivateV2_get_account()['totalMaintMargin'])
# for i in bn.fapiPrivateV2GetPositionRisk():
#     if i['symbol'] == 'BTCUSDT' and float(i['entryPrice']) > 0:
#         pprint(i)
