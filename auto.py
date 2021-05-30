# 注意点：
# 1.常见的挂单状态有open，closed，expired，canceled，在订单取消或者创建过程中都需要考虑这些状态
# 2.成交额与手续费之间的关系
# 3.设置一个检测函数，每次订单操作之前和之后都进行一次检测，同时设置一个定时任务，定期进行必要的订单检测
# 4.合理使用mongodb的查询功能
# 5.定时任务参照 https://lz5z.com/Python%E5%AE%9A%E6%97%B6%E4%BB%BB%E5%8A%A1%E7%9A%84%E5%AE%9E%E7%8E%B0%E6%96%B9%E5%BC%8F/

import ccxt
import time
import pymongo
#import schedule
# import pandas as pd
import threading
import userapi
import requests
import json
import logging
#from concurrent.futures import ThreadPoolExecutor, as_completed
#from multiprocessing import Process 
from pprint import pprint
from queue import Queue
#from cyberbrain import trace

# 初始化变量及数据库
symbol = 'BTC/USDT'
positions_split = 45
leverage = 16
que = Queue()
# 多进程模式下对接数据库的方式需要类似与如下类型
dbclient = pymongo.MongoClient(userapi.dbaddr, userapi.dbport)
db = dbclient['bn']
# db = pymongo.MongoClient(userapi.dbaddr, userapi.dbport).bn
# price_db = pymongo.MongoClient(userapi.dbaddr, userapi.dbport).price
# def db_link(name):
#     db = pymongo.MongoClient(userapi.dbaddr, userapi.dbport, connect = False)[name]
#     return db
# db = db_link('bn')
# price_db = db_link('price')
# # 挂单
# order_col = db_link('bn').orders
# # 已成交订单
# trade_col = db_link('bn').trades
# # 资金情况
# funds_col = db_link('bn').funds
price_db = dbclient['price']
order_col = db['orders']
trade_col = db['trades']
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
    time_list = ["5m","15m","30m","1h","2h","4h","6h","12h","1d"]
    limit_list = [2016,672,336,168,84,28,14,7]
    if time not in time_list:
        print('时间错误！')
        return
    else:
        localimit = limit_list[time_list.index(time)]            
    ohlcv = bn.fetchOHLCV(symbol,time,limit=localimit)
    ch_sum = 0
    for i in ohlcv:
        ch_sum += abs(i[2]-i[3])
    return int(ch_sum/len(ohlcv))



# pprint(bn.fetch_balance()['free'])
#pprint(bn.fetch_open_orders('BTC/USDT'))
#pprint(bn.fetch_ticker('BTC/USDT')['last'])
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
    
#print(int(avg_ch('1h') * 0.618))

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
# def id_check(id):
#     open_order_id = []
#     for order in bn.fetch_open_orders(symbol):
#         open_order_id.append(order[id])
#     if id in open_order_id:
#         return True
#     else:
#         return False

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
            'order_type': data_info['info']['type'],
            'order_price': data_info['price'],
            'order_amount': data_info['amount'],
            'order_side': data_info['side'],
            'order_positionSide': data_info['info']['positionSide'],
            'order_uptime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(data_info['info']['updateTime']) / 1000))
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
            'trade_P&L': float(data_info['info']['realizedPnl']),
            'trade_side': data_info['info']['side'],
            'trade_positionSide': data_info['info']['positionSide'],
            'trade_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(data_info['timestamp']) / 1000))
        }
    col.insert_one(col_dict)
    return

# 基于订单价格进行搜索
def db_search(side, price):
    order_list = list(order_col.find({'order_status': 'open', 'order_positionSide': side}, {'_id': 0, 'order_price': 1}))
    for order in order_list:
        if order['order_price'] == price:
            return True
        else:
          pass
    return False
    

# 判断挂单是否成交
'''
也可以通过closed订单判断，成交的订单自动会进入closed订单中，fetch_closed_orders 'id' == fetch_my_traders 'order'
如果输入的是没有参数的情况，那将自动遍历订单，自动对已经发生变化的订单进行数据库操作
'''
def order_check(order_id = None):
    db_order_list = list(order_col.find({},{'_id': 0, 'order_id': 1}).sort([('order_uptime', -1)]).limit(36))
    start_time = order_col.find_one({'order_id': db_order_list[-1]['order_id']})['order_uptime']
    db_trade_list = list(trade_col.find({'order_uptime': {'$gte': start_time}},{'_id': 0, 'trade_id': 1}))
    # mongodb查询生成的列表需要先进行赋值，之后再通过列表生成式生成需要的列表
    order_id_list = [x['order_id'] for x in db_order_list]
    trade_id_list = [x['trade_id'] for x in db_trade_list]
    open_order_id_list = [x['id'] for x in bn.fetch_open_orders(symbol)]
    if order_id == None:
#        all_closed_id_list = [x['id'] for x in bn.fetch_orders(symbol) if x['status'] == 'closed']
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
        if set(order_id_list).issuperset(set(open_order_id_list)):
            pass
        else:
            for id in open_order_id_list:
                if id not in order_id_list:
                    for order in bn.fetch_open_orders(symbol):
                        if order['id'] == id:
                            db_insert(order)
        return
    elif order_id.isdigit(): #判断输入的内容能否转换成数字
        order_status = bn.fetch_order_status(order_id,symbol)    # 基于id获取订单状态
        if order_id not in trade_id_list:   
    # while order_status == "open":
    #     time.sleep(3)
    #     order_status = bn.fetch_order_status(order_id,symbol)
    #     continue
            if order_status == 'closed':
                for trade in bn.fetch_my_trades(symbol):
                    if trade['order'] == order_id:
                        db_insert(trade)
                        order_col.find_one_and_update({'order_id': order_id}, {'$set': {'order_status': order_status}})
            elif order_status != 'open':
                order_col.find_one_and_update({'order_id': order_id}, {'$set': {'order_status': order_status}})
            order_check()
            return order_status
        else:
            order_check()
            return order_status
    else:
        print('输入错误！')
        order_check()
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
        
    


# MA计算
def ma(long, time):
    ohlcv = bn.fetchOHLCV(symbol, time, limit = long + 2)
    ohlcvsum = 0
    for i in range(0 - long, 0):
        ohlcvsum += ohlcv[i][4]
    return ohlcvsum / long

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
    for i in bn.fapiPrivateV2GetPositionRisk({'symbol': bn_symbol}):
        if i != None:
            if i['symbol'] == bn_symbol and float(i['entryPrice']) > 0:
                positions_list.append(i)
    return positions_list

def pos_status(side):
    bn_symbol = symbol.replace('/','')
    for pos in bn.fapiPrivateV2GetPositionRisk({'symbol': bn_symbol}):
        if pos != None and pos['symbol'] == bn_symbol and float(pos['entryPrice']) > 0 and pos['positionSide'] == side:
            return True
        else:
            pass
    return False

# 建立持仓字典，方便查询
def positions_info(position_list):
    if len(position_list) > 1:
        if position_list[0]['positionSide'] == 'LONG':
            positions_info = dict(zip(['LONG','SHORT'],[position_list[0],position_list[1]]))
        else:
            positions_info = dict(zip(['SHORT','LONG'],[position_list[0],position_list[1]]))
    elif len(position_list) == 0:
        positions_info = None
    else:
        positions_info = dict([(position_list[0]['positionSide'],position_list[0])])
    return positions_info 
         
# 修改杠杆
def ch_lev(lev):
    if len(fetch_positions(symbol)) > 0:
        print('在持仓模式下无法修改杠杆！')
        return
    elif lev < 1 or lev > 125:
        print('超出杠杆范围！')
        return
    else:
        print(bn.fapiPrivate_post_leverage({
            'symbol': symbol.replace('/', ''),
            'leverage': lev
        }))
        return

# 实时价格
def price_now():
    while True:
        btc_price = bn.fetch_ticker(symbol)['last']
        db_insert(btc_price)
        time.sleep(5)


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
    try_count = 3
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
            quantity = abs(round((float(position['positionAmt']) * ratio), 3)) #持仓取正
            # 保留三位小数
            if quantity == 0:
                print('数值太小！')
                return
    if priceIsNeeded or stoppriceIsNeeded:
        if not price.isdigit():
            print('必须输入价格！')
            return
        else:
            stopPrice = price
    if closepositionIsNeeded:
        closePosition = True
    else:
        closePosition = False
    while try_count > 0:
        try:
            the_order = bn.create_order(symbol, type, side, quantity, price, {
                'stopPrice': stopPrice,
                'positionSide': positionSide,
                'closePosition': closePosition,
                'workingType': 'MARK_PRICE'
            })
            break
        except:
            try_count -= 1
            if try_count == 0:
                return
            continue    
    db_insert(the_order)
    order_check()
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


def cancel_my_order(price, side, type):
    order_check()
    open_order = bn.fetch_open_orders(symbol)
    if len(open_order) == 0:
        print('无有效挂单！')
        return
    # elif isinstance(order_info,dict) != True:
    #     print('输入类型错误！')
    #     return
    else:
        order_id = order_col.find_one({'order_price': price, 'order_positionSide': side.upper(), 'order_type': type.upper()},{'_id': 0, 'order_id': 1})['order_id']
        bn.cancel_order(order_id,symbol)
        order_check()
    return
        
 
 # 追踪策略
 # 基于持仓价格进行价格追踪，基于基础的价格进行网格操作，需要考虑持仓的时效性     

# 测试持仓情况
def check_positions(side = None):
    positions = positions_info(fetch_positions(symbol))
    format_pos = {}
    if positions != None and len(positions) >= 1:
        for pos_side in positions.keys():
            format_pos[pos_side] = {
                'pos_price': float(positions[pos_side]['entryPrice']),
                'pos_amt': float(positions[pos_side]['positionAmt']),
                'pos_lq_price': float(positions[pos_side]['liquidationPrice']),
                'pos_lev': int(positions[pos_side]['leverage']),
                'pos_unp': float(positions[pos_side]['unRealizedProfit']),
                'pos_wallet': float(positions[pos_side]['isolatedWallet'])
            }
        if side != None and side in positions.keys():
            return True
    else:
        return False
    return format_pos
        

# 价格追踪，输入初始持仓价格，优先设置止损位，之后使用等差数列预生成网格价格点位
# def price_auto(pos_price, side, pos_lev):
#     diff_price = avg_ch('1h')
#     if side == 'LONG':
#         sl_price = pos_price - pos_price * 0.25 / pos_lev
#         price_list = [pos_price + x * diff_price for x in range(0,10)]
#     else:
#         sl_price = pos_price / (1 - 0.25 / pos_lev)
#         price_list = [pos_price - x * diff_price for x in range(0,10)]
#     # 完成初始的价格模型
#     return sl_price, price_list

# def mesh_price(pos_price,side):
#     price_step = avg_ch('5m')
#     if side == 'LONG':
#         mesh_price = pos_price + price_step
#     else:
#         mesh_price = pos_price - price_step
#     return mesh_price

# 基于push plus的推送功能    
def push_message(msg):
    token = userapi.pushtoken
    url = 'http://www.pushplus.plus/send'
    title = '数字货币运行脚本！'
    content = str(msg)
    data = {
        "token": token,
        "title": title,
        "content": content,
        "template": "json"
        }   
    body=json.dumps(data).encode(encoding='utf-8')
    headers = {'Content-Type':'application/json'}
    requests.post(url,data=body,headers=headers)

# 追踪价格，按照阶梯方式进行订单生成和取消
# 价格低于持仓价格的时候，建立25%的止损单，当价格超越持仓价格之后，进行追踪，每触发一个价格自动取消上一个止损单，并建立
# 一个新的止损点，并最终建立合适的止盈单
def Autotrading(side):
    try:
        if pos_status(side):
            print('函数启动时间：', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
            pos_lev = check_positions()[side]['pos_lev']
            pos_price = check_positions()[side]['pos_price']            
            defense_order_dict = {}
            defense_order_list = []
            if side == 'LONG':
                price_step = int(pos_price * 0.1 / pos_lev)
                limit_price = pos_price + price_step
                trigger_price = pos_price
                retry = 5
                while pos_status(side):
                    if bn.fetch_ticker(symbol)['last'] < pos_price - pos_price * 0.24 / pos_lev:
                        create_tpsl_order('STOP_MARKET', None, bn.fetch_ticker(symbol)['last'], side) #快速止损
                        break
                    else:
                        sl_price = round(pos_price - pos_price * 0.24 / pos_lev, 2)
                        if not db_search(side, sl_price):
                            alert_order = create_tpsl_order('STOP', 1, sl_price, side)#24%止损单
                        if bn.fetch_ticker(symbol)['last'] > trigger_price:
                            btc_price = bn.fetch_ticker(symbol)['last']
                            if btc_price < limit_price:
                                adj_value = round((trigger_price - pos_price) / price_step) -1
                                pt = 0.03 + 0.0175 * adj_value * (adj_value + 1)
                                if trigger_price <= pos_price:
                                    defense_price = int(pos_price - pos_price * 0.12 / pos_lev)                                 
                                else:
                                    #defense_price = int(pos_price + ch_5m * 0.782 * adj_value * (0.6 + 0.2 * adj_value))
                                    #defense_price = int(pos_price * (1 + (0.06 + 0.03 * adj_value) / pos_lev))
                                    defense_price = int(pos_price + pos_price * pt / pos_lev)
                                    # if abs(defense_price - pos_price) < 1:
                                    #     defense_price = int(pos_price + pos_price * 0.03 / pos_lev)
                                if trigger_price not in defense_order_dict.keys() and not db_search(side, defense_price):
                                    defense_order = create_tpsl_order('STOP', 1, defense_price, side) #防守订单
                                    if not defense_order.isdigit():
                                        continue
                                    defense_order_list.append(defense_order)
                                    defense_order_dict[trigger_price] = defense_order
                                    if len(defense_order_list) > 3:
                                        bn.cancel_order(defense_order_list[0], symbol)
                                        print('挂单{}已被取消！'.format(defense_order_list[0])) 
                                        del defense_order_list[0]
                                else:
                                    time.sleep(5)
                                    continue                            
                                print(defense_price, defense_order_list)
                            else:
                                if btc_price - limit_price > price_step:
                                    limit_price = limit_price + ((btc_price - limit_price) // price_step + 1) * price_step
                                else:
                                    limit_price += price_step
                                trigger_price = limit_price - price_step
                        # elif bn.fetch_ticker(symbol)['last'] < pos_price and time.time() - create_time > 600 and not db_search(side, int(pos_price - pos_price * 0.12 / pos_lev)):
                        #     safe_order_list.append(create_tpsl_order('STOP', 1, round(pos_price - pos_price * (0.24 - 0.02 * safe_nu) / pos_lev, 2)))
                        #     safe_nu += 1
                        #     create_time = time.time()
                    print(trigger_price, limit_price, bn.fetch_ticker(symbol)['last'])
                    if retry == 0:
                        time.sleep(10)
                        print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
                        retry = 5
                    else:
                        time.sleep(5)
                        retry -= 1
            else:
                price_step = pos_price / 1.1 * 0.1 / pos_lev
                limit_price = pos_price - price_step
                trigger_price = pos_price
                retry = 5
                while pos_status(side):
                    if bn.fetch_ticker(symbol)['last'] > pos_price / (1 - 0.24 / pos_lev):
                        create_tpsl_order('STOP_MARKET', None, bn.fetch_ticker(symbol)['last'], side) #快速止损
                        break
                    else:
                        sl_price = round(pos_price / (1 - 0.24 / pos_lev), 2)
                        if not db_search(side, sl_price):
                            alert_order = create_tpsl_order('STOP', 1, sl_price, side) #24%止损单
                        if bn.fetch_ticker(symbol)['last'] < trigger_price:
                            btc_price = bn.fetch_ticker(symbol)['last']
                            if btc_price > limit_price:
                                adj_value = round((pos_price - trigger_price) / price_step) - 1
                                pt = 0.03 + 0.0175 * adj_value * (adj_value + 1)
                                if trigger_price >= pos_price:
                                    defense_price = int(pos_price / (1 - 0.12 / pos_lev))                                 
                                else:
                                    defense_price = int(pos_price / ( 1 + pt / pos_lev))
                                    # defense_price = int(pos_price - ch_5m * 0.782 * adj_value * (0.6 + 0.2 * adj_value))
                                    # if abs(defense_price - pos_price) < 1:
                                    #     defense_price = int(pos_price / (1 + 0.03 / pos_lev))                               
                                if trigger_price not in defense_order_dict.keys() and not db_search(side, defense_price):
                                    defense_order = create_tpsl_order('STOP', 1, defense_price, side) #防守订单
                                    if not defense_order.isdigit():
                                        continue
                                    defense_order_list.append(defense_order)
                                    defense_order_dict[trigger_price] = defense_order
                                    if len(defense_order_list) > 3:
                                        bn.cancel_order(defense_order_list[0], symbol)
                                        print('挂单{}已被取消！'.format(defense_order_list[0]))
                                        del defense_order_list[0]
                                else:
                                    time.sleep(5)
                                    continue
                                print(defense_price, defense_order_list)
                            else:
                                if limit_price - btc_price > price_step:
                                    limit_price = limit_price - ((limit_price - btc_price) // price_step + 1) * price_step
                                else:
                                    limit_price -= price_step
                                trigger_price = limit_price + price_step
                    print(trigger_price, limit_price, bn.fetch_ticker(symbol)['last'])
                    if retry == 0:
                        time.sleep(10)
                        print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
                        retry = 5
                    else:
                        time.sleep(5)
                        retry -= 1
            try:
                bn.cancel_order(alert_order, symbol)
            except:
                pass
            finally:
                for order_id in defense_order_list:
                    try:
                        bn.cancel_order(order_id, symbol)
                    except:
                        pass
            order_check()
            trade_info = list(trade_col.find({'trade_P&L': {'$ne': 0}}).sort([('trade_time', -1)]).limit(1))
            push_msg = {
                '标题：': '{}订单已终止'.format(side),
                '持仓价格：': pos_price,
                '成交价格：': trade_info[0]['trade_price'],
                '盈亏情况：': trade_info[0]['trade_P&L'] - trade_info[0]['trade_cost'],
                '成交时间：': trade_info[0]['trade_time']
            }
            push_message(push_msg)
            print('函数运行结束时间：', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        else:
            order_check()
            print('无持仓！')
    except:
        Autotrading(side)

# 自动进行开单
def auto_create(side, mod):
    order_modes = {
        'm1': 'MA3-MA30调转',
        'm2': 'MA3-MA15调转，MA30差值秩序扩大',
        'm3': 'MA3-MA15,MA30持续上涨',
        'm4': 'MA3-MA15调转，MA30差值持续减小',
        'm5': 'MA5-MA15调转，MA30差值秩序扩大',
        'm6': 'MA5-MA30调转',
        'm7': 'MA5-MA15,MA30持续上涨',
        'm8': 'MA5-MA15调转，MA30差值持续减小'
    }
    order_mode = order_modes[mod]
    if side == 'SHORT':
        btc_price = bn.fetch_ticker(symbol)['last']
        order_price = int(btc_price - avg_ch('5m') * 0.382)
        balance = bn.fetch_total_balance()['USDT']
        amount = 0 - round(balance / positions_split / btc_price * leverage, 3)
        auto_order = make_order(order_price, amount)
    else:
        btc_price = bn.fetch_ticker(symbol)['last']
        order_price = int(btc_price + avg_ch('5m') * 0.382)
        balance = bn.fetch_total_balance()['USDT']
        amount = round(balance / positions_split / btc_price * leverage, 3)
        auto_order = make_order(order_price, amount)
    push_msg = {
        '标题：': '建立{}订单'.format(side),
        '订单ID：': auto_order,
        '成交量：': amount,
        '订单模式': order_mode,
        '订单成交时间：': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    }
    push_message(push_msg)
    return auto_order

def th_create(q_in):
    order_id, side, event = q_in.get()
    event.wait()
    if side != None and order_id not in [nu.getName() for nu in threading.enumerate()]:
        threading.Thread(target = Autotrading, args = (side,), name = order_id).start()
    else:
        return

# 使用event.wait()作为线程等待，当子线程执行event.set()之后即停止阻塞，实现了线程相应
def con_sel(q_out):
    side = None
    while ma(3, '15m') - ma(5, '15m') > 0:
        close_price = bn.fetch_ohlcv(symbol, '15m', limit = 1)[0][4]
        ma_15m_ch = ma(3, '15m') - ma(5, '15m')
        ma_30m_ch = ma(3, '30m') - ma(5, '30m')
        if ma_30m_ch < 0:
            time.sleep(1200)
            if ma(3, '15m') - ma(5, '15m') > ma_15m_ch + 30 and ma(3, '30m') - ma(5, '30m') > 30:
                side = 'LONG'
                mode = 'm1'
                break
            elif ma(3, '15m') - ma(5, '15m') < -60 and ma(3, '30m') - ma(5, '30m') < ma_30m_ch - 30:
                side = 'SHORT'
                mode = 'm2'
                break
            else:
                continue
        else:
            time.sleep(1200)
            if ma(3, '15m') - ma(5, '15m') > ma_15m_ch + 30 and ma(3, '30m') - ma(5, '30m') > ma_30m_ch + 30 and bn.fetch_ticker(symbol)['last'] > close_price:
                side = 'LONG'
                mode = 'm3'
                break
            elif ma(3, '15m') - ma(5, '15m') < -60 and bn.fetch_ticker(symbol)['last'] < close_price and ma(3, '30m') - ma(5, '30m') < ma_30m_ch - 30:
                side = 'SHORT'
                mode = 'm4'
                break
            else:
                continue
    while ma(5, '15m') - ma(3, '15m') > 0:
        close_price = bn.fetch_ohlcv(symbol, '15m', limit = 1)[0][4]
        ma_30m_ch = ma(5, '30m') - ma(3, '30m')
        ma_15m_ch = ma(5, '15m') - ma(3, '15m')
        if ma_30m_ch < 0:
            time.sleep(1200)
            if ma(5, '15m') - ma(3, '15m') < -60 and ma(5, '30m') - ma(3, '30m') < ma_30m_ch -30:
                side = 'LONG'
                mode = 'm5'
                break
            elif ma(5, '15m') - ma(3, '15m') > ma_15m_ch + 30 and ma(5, '30m') - ma(3, '30m') > 30:
                side = 'SHORT'
                mode = 'm6'
                break                  
            else:
                continue
        else:
            time.sleep(1200)
            if ma(5, '15m') - ma(3, '15m') > ma_15m_ch + 30 and ma(5, '30m') - ma(3, '30m') > ma_30m_ch + 30 and bn.fetch_ticker(symbol)['last'] < close_price:
                side = 'SHORT'
                mode = 'm7'
                break
            elif ma(5, '15m') - ma(3, '15m') < -60 and bn.fetch_ticker(symbol)['last'] > close_price and ma(5, '30m') - ma(3, '30m') < ma_30m_ch - 30:
                side = 'LONG'
                mode = 'm8'
                break
            else:
                continue
    event = threading.Event()
    if side != None and not pos_status(side):
        auto_order = auto_create(side, mode)
        time.sleep(5)
        q_out.put((auto_order, side, event))
        event.set()
    else:
        q_out.put((None, side, event))
        event.set()
        return
    
def Autoorders():
    print('主函数启动时间：', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    ch_lev(leverage)
    while 1:
        if bn.fetch_free_balance()['USDT'] <= 260:
            print('资金低于阈值！', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
            break
        else:
            pprint(threading.enumerate())
            print(bn.fetch_ticker(symbol)['last'])
            if ma(3, '15m') - ma(5, '15m') > 0:
                print('MA3 - MA5:', ma(3, '15m') - ma(5, '15m'))
                side = 'LONG'
                if side not in [nm.getName() for nm in threading.enumerate()]:
                    threading.Thread(target = con_sel, args = (que,), name = side).start()
                    threading.Thread(target = th_create, args = (que,), name = side + ' '+ str(time.strftime('%H:%M:%S', time.localtime(time.time())))).start()
                    time.sleep(60)
                    print('{}模式终止时间：'.format(side), time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))) 
                else:
                    time.sleep(300)
                    continue
                # while ma(3, '30m') - ma(5, '30m') > 0:
                #     close_price = bn.fetch_ohlcv(symbol, '15m', limit = 1)[0][4]
                #     ma_ch = ma(3, '30m') - ma(5, '30m')
                #     ma3 = ma(3, '15m')
                #     time.sleep(1200)
                #     if ma(5, '30m') - ma(3, '30m') > 90 and bn.fetch_ohlcv(symbol, '15m', limit = 1)[0][4] < close_price:
                #         side = 'SHORT'
                #         # if len(bn.fetch_open_orders(symbol)) < 2 and side not in [ x['info']['positionSide'] for x in bn.fetch_open_orders(symbol) if x['type'] == 'limit']:
                #         if not pos_status(side):
                #             auto_order = auto_create(side)
                #             time.sleep(5)
                #     elif ma(3, '30m') - ma(5, '30m') > 120:
                #         if ma(3, '30m') - ma(5, '30m') > ma_ch and ma(3, '15m') > ma3:
                #             side = 'LONG'
                #             if not pos_status(side):
                #                 auto_order = auto_create(side)
                #                 time.sleep(5)     
                #         else:
                #             continue
                #     else:
                #         continue
                #     if bn.fetch_order_status(auto_order, symbol) == 'closed':
                #         print('订单ID：', auto_order)
                #         threading.Thread(target = Autotrading, args = (side,), name = auto_order).start()
                #         # th_pos = threading.Thread(target = Autotrading, args = (side,))
                #         # th_pos.start()
                #         # th_pos.join()
                #         # pr_pos = Process(target = Autotrading, args = (side,))
                #         # pr_pos.start()
                #         # pr_pos.join()
                #         pprint(threading.enumerate())
                #         break
                #     else:
                #         bn.cancel_order(auto_order, symbol)
                #         continue                
            else:
                print('MA5 - MA3:', ma(5, '15m') - ma(3, '15m'))
                side = 'SHORT'
                if side not in [nm.getName() for nm in threading.enumerate()]:
                    threading.Thread(target = con_sel, args = (que,), name = side).start()
                    threading.Thread(target = th_create, args = (que,), name = side + ' '+ str(time.strftime('%H:%M:%S', time.localtime(time.time())))).start()
                    time.sleep(60)
                    print('{}模式终止时间：'.format(side), time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
                else:
                    time.sleep(300)
                    continue
                # while ma(5, '30m') - ma(3, '30m') > 0:
                #     close_price = bn.fetch_ohlcv(symbol, '15m', limit = 1)[0][4]
                #     ma_ch = ma(5, '30m') - ma(3, '30m')
                #     ma5 = ma(5, '15m')
                #     time.sleep(1200)
                #     if ma(3, '30m') - ma(5, '30m') > 90 and bn.fetch_ohlcv(symbol, '15m', limit = 1)[0][4] > close_price:
                #         side = 'LONG'
                #         # if len(bn.fetch_open_orders(symbol)) < 2 and side not in [ x['info']['positionSide'] for x in bn.fetch_open_orders(symbol) if x['type'] == 'limit']:
                #         if not pos_status(side):
                #             auto_order = auto_create(side)
                #             time.sleep(5)
                #     elif ma(5, '30m') - ma(3, '30m') > 90:
                #         if ma(5, '30m') - ma(3, '30m') > ma_ch and ma(5, '15m') < ma5:
                #             side = 'SHORT'
                #             if not pos_status(side):
                #                 auto_order = auto_create(side)
                #                 time.sleep(5)
                #         else:
                #             continue   
                #     else:
                #         continue
                #     if bn.fetch_order_status(auto_order, symbol) == 'closed':
                #         print('订单ID：', auto_order)
                #         threading.Thread(target = Autotrading, args = (side,), name = auto_order).start()
                #         # th_pos = threading.Thread(target = Autotrading, args = (side,))
                #         # th_pos.start()
                #         # th_pos.join()
                #         # pr_pos = Process(target = Autotrading, args = (side,))
                #         # pr_pos.start()
                #         # pr_pos.join()
                #         pprint(threading.enumerate())
                #         break
                #     else:
                #         bn.cancel_order(auto_order, symbol)
                #         continue
    print('程序退出！当前余额：{}'.format(bn.fetch_free_balance()['USDT']))
    return
            
        
def loop(function, fun_args = None):
    functions = ['Autocreate', 'Autotrading', 'push_message']
    if function not in functions:
        print('函数错误！')
        return
    else:
        if fun_args != None and function == 'Autotrading':
            th = threading.Thread(target = function, args = (fun_args,))
        else:
            th = threading.Thread(function)
    return th 
    
def main():
    order_check()
    th_order = threading.Thread(target = Autoorders)
    th_price = threading.Thread(target = price_now)
    while True:
        if bn.fetch_free_balance(symbol)['USDT'] <= 200:
            print('资金低于阈值！', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
            return
        if not th_order.is_alive():
            try:
                th_order.start()
                th_price.start()
                th_order.join()
                th_price.join()
            except:
                time.sleep(60)
                continue
        
if __name__ == '__main__':
    print('5m:',avg_ch('5m'))
    print('15m:',avg_ch('15m'))
    print('30m:',avg_ch('30m'))
    print('1h:',avg_ch('1h'))
    Autoorders()

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

#pprint(positions_info(fetch_positions(symbol)))
#pprint(bn.fetch_my_trades(symbol,limit=1))
#pprint(create_tpsl_order('TAKE_PROFIT', 0.2, 61000, 'LONG'))
#pprint(bn.fetch_open_orders(symbol))
#pprint(bn.fetch_orders(symbol,limit=4))
#pprint(len([x['id'] for x in bn.fetch_orders(symbol)]))
#print(order_check('17824277086'))
#print(bn.fetch_order_status('17748191220',symbol))
# order_find = order_col.find_one({'order_price': 61000, 'order_positionSide': 'LONG'},{'_id': 0, 'order_id': 1})
# print(order_find['order_id'])
# def autotd(side):
#     if check_positions():
#         try:
#             Autotrading(side)
#         except Exception as e:
#             if e != None:
#                 autotd(side)

# autotd('SHORT')
# pprint(bn.fapiPrivate_get_order({
#     'orderId': '20206699237',
#     'symbol': 'BTCUSDT'
#     }))
# ol = bn.fetch_ohlcv(symbol, '30m', limit = 48)
# # for i in range(0,4):
# #     print(ma(3, '15m') - ma(5, '15m'))
# #     time.sleep(900)
# def mab(ma1, ma2, data):
#     max_ma = max(ma1, ma2)
#     ma_ch = []
#     sum = 0
#     for i in range(max_ma, len(data)):
#         ma1sum = 0
#         ma2sum = 0
#         for a in data[(i - ma1): i]:
#             ma1sum += a[4]
#         for b in data[(i - ma2): i]:
#             ma2sum += b[4]
#         ma_ch.append(ma1sum / ma1 - ma2sum / ma2)
#     for j in ma_ch:
#         sum += abs(j)
#     return sum / len(data)

# print(mab(3,5,ol))