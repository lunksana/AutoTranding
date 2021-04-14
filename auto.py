# 注意点：
# 1.常见的挂单状态有open，closed，expired，canceled，在订单取消或者创建过程中都需要考虑这些状态
# 2.成交额与手续费之间的关系
# 3.设置一个检测函数，每次订单操作之前和之后都进行一次检测，同时设置一个定时任务，定期进行必要的订单检测
# 4.合理使用mongodb的查询功能


import ccxt
import time
import pymongo
import schedule
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
# 判断已成交挂单和成交订单之间的关系
# closed_order_ids = []
# for i in bn.fetch_closed_orders(symbol):
#     closed_order_ids.append(i['id'])

# trade_ids = []
# for i in bn.fetch_my_trades(symbol):
#     trade_ids.append(i['order'])
# print(len(closed_order_ids),len(trade_ids))
# same_id = 0
# for i in closed_order_ids:
#     if i in trade_ids:
#         same_id += 1
# print(same_id)
        
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
        open_order_id.append(order[id])
    if id in open_order_id:
        return True
    else:
        return False

# 开单信息写入数据库
'''
普通订单
{'amount': 0.001,
 'average': None,
 'clientOrderId': 'x-xcKtGhcuf1a9378f36cb2aec509b64',
 'cost': 0.0,
 'datetime': None,
 'fee': None,
 'filled': 0.0,
 'id': '17682474698',
 'info': {'avgPrice': '0.00000',
          'clientOrderId': 'x-xcKtGhcuf1a9378f36cb2aec509b64',
          'closePosition': False,
          'cumQty': '0',
          'cumQuote': '0',
          'executedQty': '0',
          'orderId': 17682474698,
          'origQty': '0.001',
          'origType': 'LIMIT',
          'positionSide': 'LONG',
          'price': '58000',
          'priceProtect': False,
          'reduceOnly': False,
          'side': 'BUY',
          'status': 'NEW',
          'stopPrice': '0',
          'symbol': 'BTCUSDT',
          'timeInForce': 'GTC',
          'type': 'LIMIT',
          'updateTime': 1618115969768,
          'workingType': 'CONTRACT_PRICE'},
 'lastTradeTimestamp': None,
 'postOnly': False,
 'price': 58000.0,
 'remaining': 0.001,
 'side': 'buy',
 'status': 'open',
 'stopPrice': 0.0,
 'symbol': 'BTC/USDT',
 'timeInForce': 'GTC',
 'timestamp': None,
 'trades': None,
 'type': 'limit'}
 
 {'amount': 0.0,
 'average': None,
 'clientOrderId': 'x-xcKtGhcu42cfdc23e6cec93994c6bc',
 'cost': 0.0,
 'datetime': None,
 'fee': None,
 'filled': 0.0,
 'id': '17682940118',
 'info': {'avgPrice': '0.00000',
          'clientOrderId': 'x-xcKtGhcu42cfdc23e6cec93994c6bc',
          'closePosition': True,
          'cumQty': '0',
          'cumQuote': '0',
          'executedQty': '0',
          'orderId': 17682940118,
          'origQty': '0',
          'origType': 'TAKE_PROFIT_MARKET',
          'positionSide': 'LONG',
          'price': '0',
          'priceProtect': False,
          'reduceOnly': True,
          'side': 'SELL',
          'status': 'NEW',
          'stopPrice': '61000',
          'symbol': 'BTCUSDT',
          'timeInForce': 'GTC',
          'type': 'TAKE_PROFIT_MARKET',
          'updateTime': 1618116649437,
          'workingType': 'CONTRACT_PRICE'},
 'lastTradeTimestamp': None,
 'postOnly': False,
 'price': 0.0,
 'remaining': 0.0,
 'side': 'sell',
 'status': 'open',
 'stopPrice': 61000.0,
 'symbol': 'BTC/USDT',
 'timeInForce': 'GTC',
 'timestamp': None,
 'trades': None,
 'type': 'take_profit_market'}
 
 trade
 {'amount': 0.004,
  'cost': 241.8,
  'datetime': '2021-04-11T02:47:42.087Z',
  'fee': {'cost': 0.04836, 'currency': 'USDT'},
  'id': '680489898',
  'info': {'buyer': True,
           'commission': '0.04836000',
           'commissionAsset': 'USDT',
           'id': 680489898,
           'maker': True,
           'marginAsset': 'USDT',
           'orderId': 17679419275,
           'positionSide': 'LONG',
           'price': '60450',
           'qty': '0.004',
           'quoteQty': '241.80000',
           'realizedPnl': '0',
           'side': 'BUY',
           'symbol': 'BTCUSDT',
           'time': 1618109262087},
  'order': '17679419275',
  'price': 60450.0,
  'side': 'buy',
  'symbol': 'BTC/USDT',
  'takerOrMaker': 'maker',
  'timestamp': 1618109262087,
  'type': None}
'''
def db_insert(data_info):
    val = 'clientOrderId'
    if val in data_info.keys():
        col = order_col
        col_dict = {
            'order_id': data_info['id'],
            'order_status': data_info['status'],
            'order_price': data_info['price'],
            'order_amount': data_info['amount'],
            'order_side': data_info['side'],
            'order_positionSide': data_info['info']['positionSide'],
            'order_uptime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data_info['info']['updateTime']/1000))
        }
    elif isinstance(data_info,float):
        month = time.strftime('%m',time.localtime(time.time()))
        col = price_db[month]
        col_dict = {
            'btc_price': data_info,
            'updatetime': time.strftime('%d-%H:%M:%S',time.localtime(time.time()))
        }
    else:
        col = trade_col
        col_dict = {
            'trade_id': data_info['order'],
            'trade_price': data_info['price'],
            'trade_amount': data_info['amount'],
            'trade_cost': data_info['fee']['cost'],
            'trade_P&L': float(data_info['info']['realizedPn1']),
            'trade_side': data_info['info']['side'],
            'trade_positionSide': data_info['info']['positionSide'],
            'trade_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data_info['timestamp']/1000))
        }
    col.insert_one(col_dict)
    return


# 开单
def make_order(btc_price, amount):
    if amount > 0:
        new_order = bn.create_limit_buy_order(symbol, amount, btc_price, {'positionSide': 'LONG'})
    else:
        amount = abs(amount)
        new_order = bn.create_limit_sell_order(symbol, amount, btc_price, {'positionSide': 'SHORT'})
    db_insert(new_order)
    order_id = new_order['id']
    return order_id

        
    
        
                        


# 判断挂单是否成交
'''
也可以通过closed订单判断，成交的订单自动会进入closed订单中，fetch_closed_orders 'id' == fetch_my_traders 'order'
如果输入的是没有参数的情况，那将自动遍历订单，自动对已经发生变化的订单进行数据库操作
'''
def order_check(order_id = None):
    if order_id == None:
        db_order_list = list(order_col.find({},{'_id': 0, 'order_id': 1}))
        db_trade_list = list(trade_col.find({},{'_id': 0, 'trade_id': 1}))
        # mongodb查询生成的列表需要先进行赋值，之后再通过列表生成式生成需要的列表
        order_id_list = [x['order_id'] for x in db_order_list]
        trade_id_list = [x['trade_id'] for x in db_trade_list]
#        order_list = bn.fetch_orders(symbol)
#        order_dict = dict(zip([x['id'] for x in order_list],[x['status'] for x in order_list]))
        for id in order_id_list:
            order_status = bn.fetch_order_status(id, symbol)
            if order_col.find_one({'order_id': id})['order_status'] != order_status:
                order_col.find_one_and_update({'order_id': id}, {'$set': {'order_status': order_status}})
            if order_status == 'closed' and id not in trade_id_list:
                for trade in bn.fetch_my_trades(symbol):
                    if trade['order'] == id:
                        db_insert(trade)
    else:
        order_status = bn.fetch_order_status(order_id,symbol)    # 基于id获取订单状态
        open_order_list = [x['id'] for x in bn.fetch_open_orders(symbol)]
    
    # while order_status == "open":
    #     time.sleep(3)
    #     order_status = bn.fetch_order_status(order_id,symbol)
    #     continue
    if order_status == "closed":
        for trade in bn.fetch_my_trades(symbol):
            if trade['order'] == order_id:
                print("挂单已成交！")
                db_insert(trade)
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
        if i != None:
            if i['symbol'] == bn_symbol and float(i['entryPrice']) > 0:
                positions_list.append(i)
    return positions_list

# 建立持仓字典，方便查询
def positions_info(position_list):
    if len(position_list) > 1:
        if position_list[0]['positionSide'] == 'LONG':
            positions_info = dict(zip(['LONG','SHORT'],[position_list[0],position_list[1]]))
        else:
            positions_info = dict(zip(['SHORT','LONG'],[position_list[0],position_list[1]]))
    else:
        positions_info = dict([(position_list[0]['positionSide'],position_list[0])])
    return positions_info 
         

# 价格监测
def price_monitor(time):
    while True:
        btc_price = bn.fetch_ticker(symbol)['last']
        db_insert(btc_price)
        time.sleep(3)

# 建立止损止盈单
'''
Type	                        强制要求的参数
LIMIT	                        timeInForce, quantity, price
MARKET	                        quantity
STOP, TAKE_PROFIT	            quantity, price, stopPrice
STOP_MARKET, TAKE_PROFIT_MARKET	stopPrice
TRAILING_STOP_MARKET	        callbackRate
'''
def create_tpsl_order(type, ratio, price, poside):
    upperType = type.upper()
    quantityIsNeeded =False
    priceIsNeeded = False
    stoppriceIsNeeded = False
    positionsideIsNeeded = False
    closepositionIsNeeded = False
    typeList = ['STOP', 'TAKE_PROFIT', 'STOP_MARKET', 'TAKE_PROFIT_MARKET']
    if upperType not in typeList:
        print('订单模式错误！请重新输入！！')
        return
    else:
        if upperType == 'STOP' or upperType == 'TAKE_PROFIT':
            quantityIsNeeded = True
            priceIsNeeded = True
            stoppriceIsNeeded = True
            positionsideIsNeeded = True
        elif upperType == 'STOP_MARKET' or upperType == 'TAKE_PROFIT_MARKET':
            stoppriceIsNeeded = True
            closepositionIsNeeded = True
            positionsideIsNeeded = True
            quantity = None
    # 必要参数
    # amount,side,positionSide
    if positionsideIsNeeded:
        if poside not in ['LONG','SHORT']:
            print('持仓参数错误，请重新尝试！')
            return
        else:
            positionSide = poside
            position = positions_info(fetch_positions(symbol))[poside]
            if poside == 'LONG':
                side = 'SELL'
            else:
                side = 'BUY'
    if quantityIsNeeded:
        if ratio == None:
            print('订单数量错误！')
            return
        elif ratio > 1 or ratio < 0:
            print('订单数量超过范围！')
            return
        else:
            quantity = round((float(position['positionAmt']) * ratio),3)
            # 保留三位小数
            if quantity == 0:
                print('数值太小！')
                return
    if priceIsNeeded or stoppriceIsNeeded:
        stopPrice = price
    if closepositionIsNeeded:
        closePosition = True
    else:
        closePosition = False
    the_order = bn.create_order(symbol, type, side, quantity, price, {
        'stopPrice': stopPrice,
        'positionSide': positionSide,
        'closePosition': closePosition
    })
    db_insert(the_order)
    return the_order['id']

# 取消订单，基于输入的内容和类型进行订单的取消
# 取消订单类型 全部，限价，止盈，止损，或者直接基于订单id来进行，也可以直接基于做空做多来进行操作
# 实际应该以价格为主要依据进行挂单的取消，上述的要求并不能满足本程序的要求
# 取消订单的同时必须及时修改数据库中的记录
# def cancel_my_order(order_info):
#     order_list = bn.fetch_open_orders(symbol)
#     input_info = order_info.upper()
#     typeList = ['LIMIT','STOP', 'TAKE_PROFIT', 'STOP_MARKET', 'TAKE_PROFIT_MARKET','ALL','LONG','SHORT']
#     if len(order_list) == 0:
#         print('无有效挂单！')
#         return
#     else:
#         if input_info.isdigit():
#             order_id = []
#             for i in order_list:
#                 order_id.append(i['order'])
#             if input_info not in order_id:
#                 print('请输入有效的挂单id！')
#                 return
#             else:
#                 bn.cancel_order(order_info)
#         elif input_info not in typeList:
#             print('输入的参数错误！')
#             return
#         else:
#             for i in order_list:
#                 if i['info']['type'] == input_info or i['info']['positionSide'] == input_info:
#                     bn.cancel_order(i['order'])
#     return
'''
[{'amount': 0.009,
  'average': None,
  'clientOrderId': 'android_X4i3W1JW5ag26BRIjUQS',
  'cost': 0.0,
  'datetime': '2021-04-13T03:11:17.686Z',
  'fee': None,
  'filled': 0.0,
  'id': '17768902260',
  'info': {'avgPrice': '0',
           'clientOrderId': 'android_X4i3W1JW5ag26BRIjUQS',
           'closePosition': False,
           'cumQuote': '0',
           'executedQty': '0',
           'orderId': 17768902260,
           'origQty': '0.009',
           'origType': 'TAKE_PROFIT',
           'positionSide': 'SHORT',
           'price': '59960',
           'priceProtect': True,
           'reduceOnly': True,
           'side': 'BUY',
           'status': 'NEW',
           'stopPrice': '60000',
           'symbol': 'BTCUSDT',
           'time': 1618283477686,
           'timeInForce': 'GTE_GTC',
           'type': 'TAKE_PROFIT',
           'updateTime': 1618283477686,
           'workingType': 'MARK_PRICE'},
  'lastTradeTimestamp': None,
  'postOnly': False,
  'price': 59960.0,
  'remaining': 0.009,
  'side': 'buy',
  'status': 'open',
  'stopPrice': 60000.0,
  'symbol': 'BTC/USDT',
  'timeInForce': 'GTE_GTC',
  'timestamp': 1618283477686,
  'trades': None,
  'type': 'take_profit'},
 {'amount': 0.009,
  'average': None,
  'clientOrderId': 'android_SKXBLBNSxo4a8A642VdE',
  'cost': 0.0,
  'datetime': '2021-04-13T04:16:30.842Z',
  'fee': None,
  'filled': 0.0,
  'id': '17770965625',
  'info': {'avgPrice': '0',
           'clientOrderId': 'android_SKXBLBNSxo4a8A642VdE',
           'closePosition': False,
           'cumQuote': '0',
           'executedQty': '0',
           'orderId': 17770965625,
           'origQty': '0.009',
           'origType': 'TAKE_PROFIT_MARKET',
           'positionSide': 'SHORT',
           'price': '0',
           'priceProtect': True,
           'reduceOnly': True,
           'side': 'BUY',
           'status': 'NEW',
           'stopPrice': '60000',
           'symbol': 'BTCUSDT',
           'time': 1618287390842,
           'timeInForce': 'GTE_GTC',
           'type': 'TAKE_PROFIT_MARKET',
           'updateTime': 1618287390842,
           'workingType': 'MARK_PRICE'},
  'lastTradeTimestamp': None,
  'postOnly': False,
  'price': 0.0,
  'remaining': 0.009,
  'side': 'buy',
  'status': 'open',
  'stopPrice': 60000.0,
  'symbol': 'BTC/USDT',
  'timeInForce': 'GTE_GTC',
  'timestamp': 1618287390842,
  'trades': None,
  'type': 'take_profit_market'}
  {'amount': 0.001,
  'average': None,
  'clientOrderId': 'android_ugamlTypfKwGxaS34H5K',
  'cost': 0.0,
  'datetime': '2021-04-13T05:19:15.533Z',
  'fee': None,
  'filled': 0.0,
  'id': '17772746108',
  'info': {'avgPrice': '0',
           'clientOrderId': 'android_ugamlTypfKwGxaS34H5K',
           'closePosition': False,
           'cumQuote': '0',
           'executedQty': '0',
           'orderId': 17772746108,
           'origQty': '0.001',
           'origType': 'LIMIT',
           'positionSide': 'LONG',
           'price': '58000',
           'priceProtect': False,
           'reduceOnly': False,
           'side': 'BUY',
           'status': 'NEW',
           'stopPrice': '0',
           'symbol': 'BTCUSDT',
           'time': 1618291155533,
           'timeInForce': 'GTC',
           'type': 'LIMIT',
           'updateTime': 1618291155533,
           'workingType': 'CONTRACT_PRICE'},
  'lastTradeTimestamp': None,
  'postOnly': False,
  'price': 58000.0,
  'remaining': 0.001,
  'side': 'buy',
  'status': 'open',
  'stopPrice': 0.0,
  'symbol': 'BTC/USDT',
  'timeInForce': 'GTC',
  'timestamp': 1618291155533,
  'trades': None,
  'type': 'limit'}]
order_info = {
    'stopPrice': xxx,
    'positionSide': 'LONG'&'SHORT',
    'type': xxx
}
order_dict = {
    'id': {
        'positionSide': xxx,
        'type': xxx,
        'price': xxx,
        'stopPrice': xxx
    }
}
'''

def cancel_my_order(order_info):
    order_list = bn.fetch_open_orders(symbol)
    if len(order_list) == 0:
        print('无有效挂单！')
        return
    elif isinstance(order_info,dict) != True:
        print('输入类型错误！')
        return
    else:
        order_dict = {}
        for i in order_list:
            format_values = {
                'positionSide': i['info']['positionSide'],
                'type': i['type'],
                'price': i['price'],
                'stopPrice': float(i['info']['stopPrice'])
            }
            id_key = i['id']
            order_dict[id_key] = format_values
    
            
        
        

    

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

#print(positions_info(fetch_positions(symbol)))
#pprint(bn.fetch_my_trades(symbol,limit=1))
#pprint(create_tpsl_order('TAKE_PROFIT', 0.2, 61000, 'LONG'))
pprint(bn.fetch_open_orders(symbol))
#pprint(bn.fetch_orders(symbol,limit=4))
#pprint(len([x['id'] for x in bn.fetch_orders(symbol)]))
