# 注意点：
# 1.常见的挂单状态有open，closed，expired，canceled，在订单取消或者创建过程中都需要考虑这些状态
# 2.成交额与手续费之间的关系
# 3.设置一个检测函数，每次订单操作之前和之后都进行一次检测，同时设置一个定时任务，定期进行必要的订单检测
# 4.合理使用mongodb的查询功能

import ccxt
import time
from pkg_resources import register_namespace_handler
import pymongo
#import schedule
# import pandas as pd
import threading
import userapi
import requests
import json
import re
import datetime
#import logging
#from concurrent.futures import ThreadPoolExecutor, as_completed
#from multiprocessing import Process 
from pprint import pprint
from queue import Queue
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor

# 初始化变量及数据库
symbol = 'BTC/USDT'
executors = {
      'default': ThreadPoolExecutor(4)
}
schebg = BackgroundScheduler(executors = executors)
positions_split = 90
leverage = 20
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
id_col = db['id']
pos_col = db['pos']

# FORMAT = '%(asctime)s %(levename)s %(message)s'
# DATEFMT = '%Y-%m-%d %H:%M:%S'
# logging.basicConfig(level = logging.ERROR, filename = 'btc_script.log', filemode = 'a', format = FORMAT, datefmt = DATEFMT)


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
def avg_ch(interval):
    time_list = ["5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d"]
    limit_list = [2016, 672, 336, 168, 84, 28, 14, 7]
    if interval not in time_list:
        print('时间错误！')
        return
    else:
        localimit = limit_list[time_list.index(interval)]            
    ohlcv = bn.fetchOHLCV(symbol, interval, limit = localimit)
    ch_sum = 0
    for i in ohlcv:
        ch_sum += abs(i[2] - i[3])
    return int(ch_sum / len(ohlcv))

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
    if isinstance(data_info, dict) and 'clientOrderId' in data_info.keys():
        col = order_col
        col_dict = {
            'order_id': data_info['id'],
            'order_status': data_info['status'],
            'order_type': data_info['info']['type'],
            'order_price': data_info['stopPrice'],
            'order_amount': data_info['amount'],
            'order_side': data_info['side'],
            'order_positionSide': data_info['info']['positionSide'],
            'uptime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(data_info['info']['updateTime']) / 1000))
        }
    elif isinstance(data_info, float):
        month = time.strftime('%m',time.localtime(time.time()))
        col = price_db[month]
        col_dict = {
            'btc_price': data_info,
            'uptime': time.strftime('%d-%H:%M:%S',time.localtime(time.time()))
        }
    elif isinstance(data_info, str) and data_info.isdigit():
        col = id_col
        order_info = bn.fetch_order(data_info, symbol)
        col_dict = {
            'main_id': data_info,
            'start_price': order_info['average'],
            'pos_price': order_info['average'],
            'amount': order_info['amount'],
            'pos_side': order_info['info']['positionSide'],
            'defense_price': {
                'trigger_price': 0,
                'limit_price': 0
            },
            'close_price': 0,
            'order_count': -3,
            'trade_count': 0,
            'makepos_price_list': [],
            'makepos_id_list': [],
            'order_price_list': list(),
            'order_id_list': list(),
            'P&L': 0,
            'uptime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(order_info['timestamp'] / 1000))
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
            'uptime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(data_info['timestamp']) / 1000))
        }
    col.insert_one(col_dict)
    return

# 基于订单价格进行搜索
def db_search(side, price):
    if order_col.count_documents({'order_status': 'open', 'order_price': price, 'order_positionSide': side}) > 0:
        return True
    else:
        return False
    

# 判断挂单是否成交
'''
也可以通过closed订单判断，成交的订单自动会进入closed订单中，fetch_closed_orders 'id' == fetch_my_traders 'order'
如果输入的是没有参数的情况，那将自动遍历订单，自动对已经发生变化的订单进行数据库操作
'''
def order_check(order_id = None):
    if db.list_collection_names():
        db_order_list = list(order_col.find({},{'_id': 0, 'order_id': 1}).sort([('uptime', -1)]).limit(16))
        start_time = order_col.find_one({'order_id': db_order_list[-1]['order_id']})['uptime']
        # mongodb查询生成的列表需要先进行赋值，之后再通过列表生成式生成需要的列表
        order_id_list = [x['order_id'] for x in db_order_list]
        trade_id_list = [x['trade_id'] for x in trade_col.find({'uptime': {'$gte': start_time}})]
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
                order_check()
            return
        elif order_id.isdigit(): #判断输入的内容能否转换成数字
            order_status = bn.fetch_order_status(order_id, symbol)    # 基于id获取订单状态
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
    else:
        return

def db_del(db_col = None):
    Deadline_time = (datetime.datetime.now() - datetime.timedelta(days = 15)).strftime('%Y-%m-%d %H:%M:%S')
    if db_col:
        if db_col not in db.list_collection_names():
            print('集合名错误！')
            return
        else:
            del_data = db[db_col].delete_many({'uptime': {'$lte': Deadline_time}})
            return del_data.deleted_count
    else:
        del_count = 0
        for col in db.list_collection_names():
            del_data = db[col].delete_many({'uptime': {'$lte': Deadline_time}})
            del_count += del_data.deleted_count
        return del_count    
        
# 自动建立每个订单后续生成的订单
def id_db(main_id, order_id = None, order_price = None, order_id_list = None):
    if not re.match(r'^[0-9]+$', main_id):
    #if order_id != None and order_id_list != None:
        return
    elif id_col.find_one({'main_id': main_id}):
        id_list = id_col.find_one({'main_id': main_id})['order_id_list']
        price_list = id_col.find_one({'main_id': main_id})['order_price_list']
        if order_id != None and order_id not in id_list and re.match(r'^[0-9]+$', order_id):
            id_list.append(order_id)
            id_col.update_one({'main_id': main_id}, {'$set': {'order_id_list': id_list}})
            id_col.update_one({'main_id': main_id}, {'$inc': {'order_count': 1}})
        if order_price != None and order_price not in price_list and isinstance(order_price, int):
            price_list.append(order_price)
            id_col.update_one({'main_id': main_id}, {'$set': {'order_price_list': price_list}})
        if order_id_list != None and isinstance(order_id_list, list):
            id_col.update_one({'main_id': main_id}, {'$set': {'order_id_list': order_id_list}})
        else:
            return id_list
    else:
        db_insert(main_id)
        id_db(main_id, order_id, order_price, order_id_list)
    return

# 自动话操作数据库
def pos_db(main_id, makepos_id = None, order_id = None):
    if id_col.find_one({'main_id': main_id}):
        main_order_info = bn.fetch_order(main_id, symbol)
        pos_guard = id_col.find_one({'main_id': main_id})['defense_price']
        pos_side = id_col.find_one({'main_id': main_id})['pos_side']
        if pos_guard['trigger_price'] != 0 or pos_guard['limit_price'] != 0:
            if main_order_info['pos_side'] == 'LONG':
                pos_guard = {
                    'trigger_price': main_order_info['average'] * (1 - 0.25 / leverage),
                    'limit_price': main_order_info['average'] * (1 + 0.25 / leverage)
                }
            else:
                pos_guard = {
                    'trigger_price': main_order_info['average'] * (1 + 0.25 / leverage),
                    'limit_price': main_order_info['average'] * (1 - 0.25 /leverage),
                }
            id_col.update_one({'main_id': main_id}, {'$set': {'defense_price': pos_guard}})
        if makepos_id and isinstance(makepos_id, str):
            makepos_info = bn.fetch_order(makepos_id, symbol)
            new_pos = fetch_positions(pos_side)
            makepos_price_list = id_col.find_one({'main_id': main_id})['makepos_price_list'].append(new_pos['pos_price'])
            makepos_id_list = id_col.find_one({'main_id': main_id})['makepos_id_list'].append(makepos_id)
            id_col.update_one({'main_id': main_id}, {'$set': {'pos_price': new_pos['pos_price'], 'makepos_price_list': makepos_price_list, 'makepos_id_list': makepos_id_list}})
    else:
        db_insert(main_id)
        
pprint(bn.fetch_order('24929079957', symbol))
exit()

# 开单
def make_order(btc_price, amount):
    if amount > 0:
        new_order = bn.create_limit_buy_order(symbol, amount, btc_price, {'positionSide': 'LONG'})
    else:
        amount = abs(amount)
        new_order = bn.create_limit_sell_order(symbol, amount, btc_price, {'positionSide': 'SHORT'})
    db_insert(new_order)
    order_id = new_order['id']
    order_check(order_id)
    db_insert(order_id)
    return order_id

# MA计算
def ma(long, interval):
    ohlcv = bn.fetchOHLCV(symbol, interval, limit = long + 2)
    ohlcvsum = 0
    for i in range(0 - long, 0):
        ohlcvsum += ohlcv[i][4]
    return ohlcvsum / long

# 历史MA计算(测试阶段)
def hisma(long, span, interval):
    hisohl = bn.fetchOHLCV(symbol, interval, limit = long + span)
    ohlsum = 0
    for x in hisohl[0:long]:
        ohlsum += x[4]
    return ohlsum / long


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
# def fetch_positions(symbol):
#     bn_symbol = symbol.replace('/','')
#     positions_list = []
#     for i in bn.fapiPrivateV2GetPositionRisk({'symbol': bn_symbol}):
#         if i != None:
#             if i['symbol'] == bn_symbol and float(i['entryPrice']) > 0:
#                 positions_list.append(i)
#     return positions_list

def pos_status(side = None):
    for pos in bn.fapiPrivateV2GetPositionRisk({'symbol': symbol.replace('/','')}):
        if side == None and float(pos['entryPrice']) > 0:
            return True
        elif float(pos['entryPrice']) > 0 and pos['positionSide'] == side:
            return True
    return False

def fetch_positions(side):
    format_pos = {}
    for pos in bn.fapiPrivateV2GetPositionRisk({'symbol': symbol.replace('/','')}):
        if float(pos['entryPrice']) > 0 and pos['positionSide'] == side:
            format_pos = {
                'pos_price': float(pos['entryPrice']),
                'pos_amt': float(pos['positionAmt']),
                'pos_lq_price': float(pos['liquidationPrice']),
                'pos_lev': int(pos['leverage']),
                'pos_unp': float(pos['unRealizedProfit']),
                'pos_wallet': float(pos['isolatedWallet'])
            }
    if format_pos:
        return format_pos
    else:
        return       
         
# 修改杠杆
def ch_lev(lev):
    if pos_status():
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

订单错误信息：binance {"code":-2021,"msg":"Order would immediately trigger."}
'''
def create_tpsl_order(type, ratio, price, poside):
    upperType = type.upper()
    quantityIsNeeded =False
    priceIsNeeded = False
    stoppriceIsNeeded = False
    positionsideIsNeeded = False
    closepositionIsNeeded = False
    try_count = 5
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
            workingType = 'CONTRACT_PRICE'
        elif upperType == 'STOP_MARKET' or upperType == 'TAKE_PROFIT_MARKET':
            stoppriceIsNeeded = True
            closepositionIsNeeded = True
            positionsideIsNeeded = True
            quantity = None
            workingType = 'MARK_PRICE'
    # 必要参数
    # amount,side,positionSide
    if positionsideIsNeeded:
        if poside not in ['LONG','SHORT']:
            print('持仓参数错误，请重新尝试！')
            return
        else:
            positionSide = poside
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
        elif pos_status(poside):
            quantity = abs(round((fetch_positions(poside)['pos_amt'] * ratio), 3)) #持仓取正
            # 保留三位小数
            if quantity == 0:
                print('数值太小！')
                return
        else:
            print('交易量异常！')
            return
    if priceIsNeeded or stoppriceIsNeeded:
        value = re.compile(r'^[0-9]+\.?[0-9]+$')
        if value.match(str(price)):
            stopPrice = price
        else:
            print('价格输入异常！')
            return
    if closepositionIsNeeded:
        closePosition = True
    else:
        closePosition = False
    while try_count > 0:
        try:
            print(stopPrice)  #调试输出
            the_order = bn.create_order(symbol, type, side, quantity, price, {
                'stopPrice': stopPrice,
                'positionSide': positionSide,
                'closePosition': closePosition,
                'workingType': workingType
            })
            print('订单成功执行！')
            db_insert(the_order)
            order_check(the_order['id'])
            break
        except Exception as a:
            print('订单执行异常，重试中！错误信息：{}'.format(a))
            if re.search('2021', str(a)):
                if poside == 'LONG':
                    stopPrice = price = int(0.999 * price)
                else:
                    stopPrice = price = int(1.001 * price)
            try_count -= 1
            if try_count == 0:
                return
            continue
    return the_order['id']


def cancel_my_order(order_id = None, price = None, side = None, type = None):
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
        'm8': 'MA5-MA15调转，MA30差值持续减小',
        'm9': '反向开单',
        'm10': 'K线调转'
    }
    order_mode = order_modes[mod]
    if side == 'SHORT':
        btc_price = bn.fetch_ticker(symbol)['last']
        order_price = btc_price - 10
        balance = bn.fetch_total_balance()['USDT']
        amount = 0 - round(balance / positions_split / btc_price * leverage, 3)
        auto_order = make_order(order_price, amount)
    else:
        btc_price = bn.fetch_ticker(symbol)['last']
        order_price = btc_price + 10
        balance = bn.fetch_total_balance()['USDT']
        amount = round(balance / positions_split / btc_price * leverage, 3)
        auto_order = make_order(order_price, amount)
    push_msg = {
        '标题：': '建立{}订单'.format(side),
        '订单ID：': auto_order,
        '成交价：': order_price,
        '成交量：': amount,
        '订单模式': order_mode,
        '订单成交时间：': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    }
    push_message(push_msg)
    return auto_order


# 追踪价格，按照阶梯方式进行订单生成和取消
# 价格低于持仓价格的时候，建立25%的止损单，当价格超越持仓价格之后，进行追踪，每触发一个价格自动取消上一个止损单，并建立
# 一个新的止损点，并最终建立合适的止盈单
def Autotrading(side):
    try:
        if pos_status(side):
            print('{}模式追踪函数启动时间：'.format(side), time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
            pos_lev = fetch_positions(side)['pos_lev']
            pos_price = fetch_positions(side)['pos_price'] 
            retry = 5           
            #defense_order_dict = {}
            # defense_order_list = []
            #order_cost = trade_col.find_one({'trade_id': list(order_col.find({'order_status': 'closed', 'order_positionSide': side}).sort([('uptime', -1)]).limit(1))[0]['order_id']})['trade_cost']
            if re.match(r'^[0-9]+$', threading.current_thread().name):
                th_name = threading.current_thread().name
            else:
                th_name = list(id_col.find({'pos_side': side}).sort([('uptime', -1)]).limit(1))[0]['main_id']
            print(th_name)
            order_cost = trade_col.find_one({'trade_id': th_name})['trade_cost']
            if side == 'LONG':
                price_step = int(pos_price * 0.05 / pos_lev)
                limit_price = int(pos_price + pos_price * 0.04 / pos_lev)
                trigger_price = pos_price
                while pos_status(side):
                    if bn.fetch_ticker(symbol)['last'] < pos_price - pos_price * 0.1 / pos_lev:
                        create_tpsl_order('STOP_MARKET', None, int(bn.fetch_ticker(symbol)['last']), side) #快速止损
                        break
                    else:
                        sl_price = int(pos_price - pos_price * 0.1 / pos_lev)
                        tp_price = int(pos_price + pos_price * 0.1 / pos_lev)
                        if not db_search(side, sl_price):
                            alert_order = create_tpsl_order('STOP_MARKET', None, sl_price, side) #12%止损单
                            id_db(th_name, alert_order)
                            if not db_search(side, tp_price):
                                id_db(th_name, create_tpsl_order('TAKE_PROFIT', 1, tp_price, side))
                        if bn.fetch_ticker(symbol)['last'] > trigger_price:
                            btc_price = bn.fetch_ticker(symbol)['last']
                            adj_value = max(id_col.find_one({'main_id': th_name})['order_count'], 0)
                            if btc_price < limit_price:
                                #adj_value = round((trigger_price - pos_price) / price_step) -1                                
                                #pt = 0.02 + 0.014 * adj_value * (adj_value + 1)
                                pt = (0.024 + (0.05 + 0.006 * adj_value) * adj_value) * 0.618
                                if trigger_price <= pos_price:
                                    defense_price = int(pos_price - pos_price * 0.06 / pos_lev)                                 
                                else:
                                    #defense_price = int(pos_price + ch_5m * 0.782 * adj_value * (0.6 + 0.2 * adj_value))
                                    #defense_price = int(pos_price * (1 + (0.06 + 0.03 * adj_value) / pos_lev))
                                    defense_price = int(pos_price + pos_price * pt / pos_lev)
                                    # if abs(defense_price - pos_price) < 1:
                                    #     defense_price = int(pos_price + pos_price * 0.03 / pos_lev)
                                if defense_price not in id_col.find_one({'main_id': th_name})['order_price_list']:
                                    if defense_price < pos_price:
                                        defense_order = create_tpsl_order('STOP_MARKET', None, defense_price, side) #防守订单
                                    else:
                                        defense_order = create_tpsl_order('TAKE_PROFIT', 1, defense_price, side)
                                    if not defense_order:
                                        continue
                                    # defense_order_list.append(defense_order)
                                    id_db(th_name, defense_order, defense_price)
                                    #defense_order_dict[trigger_price] = defense_order
                                    if len(id_db(th_name)) > 4:
                                        id_list = id_db(th_name)
                                        bn.cancel_order(id_list[2], symbol)
                                        print('挂单{}已被取消！'.format(id_list[2]))
                                        del id_list[2]
                                        id_db(th_name, order_id_list = id_list)
                                else:
                                    time.sleep(1)
                                    continue                            
                                print(defense_price, id_db(th_name))
                            else:
                                if btc_price - limit_price > price_step:
                                    limit_price = limit_price + ((btc_price - limit_price) // price_step + 1) * price_step
                                    trigger_price = limit_price - price_step
                                else:
                                    trigger_price = limit_price
                                    limit_price += price_step
                                if int(pos_price + pos_price * 0.04 / pos_lev + adj_value * price_step) < trigger_price:
                                    right_order_count = (trigger_price - int(pos_price * (0.04 / pos_lev + 1))) / price_step
                                    test_price = int(pos_price + pos_price * (0.024 + (0.05 + 0.006 * right_order_count) * right_order_count) * 0.618 / pos_lev)
                                    if test_price not in id_col.find_one({'main_id': th_name})['order_price_list']:
                                        stress_order = create_tpsl_order('TAKE_PROFIT', 1, test_price, side)
                                        if not stress_order:
                                            continue
                                        else:
                                            id_db(th_name, stress_order, test_price)
                                            id_col.update_one({'main_id': th_name}, {'$set': {'order_count': right_order_count + 1}})
                        # elif bn.fetch_ticker(symbol)['last'] < int(pos_price - pos_price * 0.06 / pos_lev) and len(id_col.find_one({'main_id': th_name})['order_price_list']) < 2 and not pos_status('SHORT'):
                        #     reverse_order = auto_create('SHORT', 'm10')
                        #     threading.Thread(target = Autotrading, args = ('SHORT',), name = reverse_order).start()
                        # elif bn.fetch_ticker(symbol)['last'] < int(pos_price - pos_price * 0.12 / pos_lev) and len(defense_order_list) < 1:
                        #     if not pos_status('SHORT'):
                        #         order_id = auto_create('SHORT', 'm9')
                        #         time.sleep(5)
                        #         threading.Thread(target = Autotrading, args = ('SHORT',), name = order_id).start()
                        #     else:
                        #         create_tpsl_order('STOP_MARKET', None, int(bn.fetch_ticker(symbol)['last']), side) #快速止损
                        #         break
                        # elif bn.fetch_ticker(symbol)['last'] < pos_price and time.time() - create_time > 600 and not db_search(side, int(pos_price - pos_price * 0.12 / pos_lev)):
                        #     safe_order_list.append(create_tpsl_order('STOP', 1, round(pos_price - pos_price * (0.24 - 0.02 * safe_nu) / pos_lev, 2)))
                        #     safe_nu += 1
                        #     create_time = time.time()
                    print(f'线程ID: {th_name}, 价格情况: ', trigger_price, limit_price, bn.fetch_ticker(symbol)['last'])
                    if retry == 0:
                        time.sleep(2)
                        print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
                        retry = 5
                    else:
                        time.sleep(1)
                        retry -= 1
            else:
                price_step = int(pos_price / 1.05 * 0.05 / pos_lev)
                limit_price = pos_price - int(pos_price / 1.04 * 0.04 / pos_lev)
                trigger_price = pos_price
                while pos_status(side):
                    if bn.fetch_ticker(symbol)['last'] > pos_price / (1 - 0.1 / pos_lev):
                        create_tpsl_order('STOP_MARKET', None, int(bn.fetch_ticker(symbol)['last']), side) #快速止损
                        break
                    else:
                        sl_price = int(pos_price / (1 - 0.1 / pos_lev))
                        tp_price = int(pos_price / (1 + 0.1 / pos_lev))
                        if not db_search(side, sl_price):
                            alert_order = create_tpsl_order('STOP_MARKET', None, sl_price, side) #12%止损单
                            id_db(th_name, alert_order)
                            if not db_search(side, tp_price):
                                id_db(th_name, create_tpsl_order('TAKE_PROFIT', 1, tp_price, side))
                        if bn.fetch_ticker(symbol)['last'] < trigger_price:
                            btc_price = bn.fetch_ticker(symbol)['last']
                            adj_value = max(id_col.find_one({'main_id': th_name})['order_count'], 0)
                            if btc_price > limit_price:
                                #adj_value = round((pos_price - trigger_price) / price_step) - 1
                                #pt = 0.02 + 0.014 * adj_value * (adj_value + 1)
                                pt = (0.024 + (0.05 + 0.006 * adj_value) * adj_value) * 0.618
                                if trigger_price >= pos_price:
                                    defense_price = int(pos_price / (1 - 0.06 / pos_lev))                                 
                                else:
                                    defense_price = int(pos_price / ( 1 + pt / pos_lev))
                                    # defense_price = int(pos_price - ch_5m * 0.782 * adj_value * (0.6 + 0.2 * adj_value))
                                    # if abs(defense_price - pos_price) < 1:
                                    #     defense_price = int(pos_price / (1 + 0.03 / pos_lev))                               
                                if defense_price not in id_col.find_one({'main_id': th_name})['order_price_list']:
                                    if defense_price > pos_price:
                                        defense_order = create_tpsl_order('STOP_MARKET', None, defense_price, side) #防守订单
                                    else:
                                        defense_order = create_tpsl_order('TAKE_PROFIT', 1, defense_price, side)
                                    if not defense_order:
                                        continue
                                    # defense_order_list.append(defense_order)
                                    id_db(th_name, defense_order, defense_price)
                                    #defense_order_dict[trigger_price] = defense_order
                                    if len(id_db(th_name)) > 4:
                                        id_list = id_db(th_name)
                                        bn.cancel_order(id_list[2], symbol)
                                        print('挂单{}已被取消！'.format(id_list[2]))
                                        del id_list[2]
                                        id_db(th_name, order_id_list = id_list)
                                else:
                                    time.sleep(1)
                                    continue
                                print(defense_price, id_db(th_name))
                            else:
                                if limit_price - btc_price > price_step:
                                    limit_price = limit_price - ((limit_price - btc_price) // price_step + 1) * price_step
                                    trigger_price = limit_price + price_step
                                else:
                                    trigger_price = limit_price
                                    limit_price -= price_step
                                if int(pos_price - pos_price / 1.04 * 0.04 / pos_lev - price_step * adj_value) > trigger_price:
                                    right_order_count = (pos_price - int(pos_price / 1.04 * 0.04 / pos_lev) - trigger_price) / price_step 
                                    test_price = int(pos_price / ( 1 + (0.024 + (0.05 + 0.006 * right_order_count) * right_order_count) * 0.618 / pos_lev))
                                    if test_price not in id_col.find_one({'main_id': th_name})['order_price_list']:
                                        stress_order = create_tpsl_order('TAKE_PROFIT', 1, test_price, side)
                                        if not stress_order:
                                            continue
                                        else:
                                            id_db(th_name, stress_order, test_price)
                                            id_col.update_one({'main_id': th_name}, {'$set': {'order_count': right_order_count + 1}})
                        # elif bn.fetch_ticker(symbol)['last'] > int(pos_price / (1 - 0.06 / pos_lev)) and len(id_col.find_one({'main_id': th_name})['order_price_list']) < 2 and not pos_status('LONG'):
                        #     reverse_order = auto_create('LONG', 'm10')
                        #     threading.Thread(target = Autotrading, args = ('LONG',), name = reverse_order).start()
                        # elif bn.fetch_ticker(symbol)['last'] > int(pos_price / (1 - 0.12 / pos_lev)) and len(defense_order_list) < 1:
                        #     if not pos_status('LONG'):
                        #         order_id= auto_ycreate('LONG', 'm9')
                        #         time.sleep(5)
                        #         threading.Thread(target = Autotrading, args = ('LONG',), name = order_id).start()
                        #     else:
                        #         create_tpsl_order('STOP_MARKET', None, int(bn.fetch_ticker(symbol)['last']), side) #快速止损
                        #         break
                    print(f'线程ID: {th_name}, 价格情况: ', trigger_price, limit_price, bn.fetch_ticker(symbol)['last'])
                    if retry == 0:
                        time.sleep(2)
                        print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
                        retry = 5
                    else:
                        time.sleep(1)
                        retry -= 1
            for the_id in id_db(th_name):
                try:
                    bn.cancel_order(the_id, symbol)
                except Exception as c:
                    print(c)
                    pass
            order_check()
            trade_info = list(trade_col.find({'trade_P&L': {'$ne': 0}, 'trade_positionSide': side}).sort([('uptime', -1)]).limit(1))[0]
            PL = trade_info['trade_P&L'] - trade_info['trade_cost'] - order_cost           
            push_msg = {
                '标题：': '{}订单已终止'.format(side),
                '持仓价格：': pos_price,
                '成交价格：': trade_info['trade_price'],
                '盈亏情况：': PL,
                '账户余额：': bn.fetch_total_balance()['USDT'],
                '成交时间：': trade_info['uptime']
            }
            push_message(push_msg)
            id_col.update_one({'main_id': th_name}, {'$set': {'P&L': PL, 'close_price': trade_info['trade_price']}})
            print('函数运行结束时间：', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        else:
            order_check()
            print('无持仓！')
    except Exception as e:
        print(e)
        Autotrading(side)

# 尝试新的策略，建立上下价格限制，之后在基础价格上进行多次建仓，低于标准值就买入。高于持仓均价就按比例建立止盈订单
def autolimit(side):
    if pos_status(side):
        if re.match(r'^[0-9]+$', threading.current_thread().name):
            th_id = threading.current_thread().name
        else:
            #th_id = list(order_col.find({'order_positionSide': side, 'order_status': 'closed', 'order_type': 'LIMIT'}).sort([('uptime', -1)]).limit(1))[0]['order_id']
            th_id = list(id_col.find({'pos_side': side}).sort([('uptime', -1)]).limit(1))[0]['main_id']
        pos_price = id_col.find_one({'main_id': th_id})['pos_price']
        if side == 'LONG':
            trigger_price = pos_price * (1 - 0.25 / leverage)
            limit_price = pos_price * (1 + 0.25 / leverage)
            if len(id_col.find({'main_id': th_id})['order_price_list']) < 2 and trigger_price < bn.fetch_ticker(symbol)['last'] < limit_price:
                if not db_search(side, trigger_price):
                    trigger_order = create_tpsl_order('STOP_MARKET', None, trigger_price, side)
                    id_db(th_id, trigger_order)
                elif not db_search(side, limit_price):
                    limit_order = create_tpsl_order('TAKE_PROFIT_MARKT', None, limit_price, side)
                    id_db(th_id, limit_order)
            else:
                pass   
            



def th_create(q_in):
    order_id, side, event = q_in.get()
    event.wait()
    if side != None and order_id not in [nu.getName() for nu in threading.enumerate()]:
        threading.Thread(target = Autotrading, args = (side,), name = order_id).start()
    else:
        threading.Thread(target = th_create, args = (que,), name = 'thread-' + str(int(time.time()))).start()
        return

# 获取方向
def get_side(q_out):
    ohl = bn.fetch_ohlcv(symbol, '15m', limit = 3)
    side = None
    for x, y, z in zip(range(0, len(ohl) - 2), range(1, len(ohl) - 1), range(2, len(ohl))):
        mid_price = int((max(ohl[x][2], ohl[y][2], ohl[z][2]) + min(ohl[x][3], ohl[y][3], ohl[z][3])) / 2)
        if ohl[x][4] > ohl[x][1] and ohl[y][1] > ohl[y][4] and abs(ohl[x][4] - ohl[y][1]) < 1 and ohl[z][4] < ma(3, '15m') * (1 - 0.01 / leverage) and hisma(3, 2, '15m') < ohl[x][4]:
            side = 'SHORT'
            mode = 'm10'
            # print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ohl[z][0] / 1000)), side, ohl[z][2] - ohl[z][1], ohl[z][1] - ohl[z][3])
        elif ohl[x][1] > ohl[x][4] and ohl[y][4] > ohl[y][1] and abs(ohl[x][4] - ohl[y][1]) < 1 and ohl[z][4] > ma(3, '15m') * (1 + 0.01 / leverage) and hisma(3, 2, '15m') > ohl[x][4]:
            side = 'LONG' 
            mode = 'm10'
            # print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ohl[z][0] / 1000)), side, ohl[z][2] - ohl[z][1], ohl[z][1] - ohl[z][3])
        # elif ohl[x][3] < ohl[y][3] < ohl[z][3] and ohl[x][1] < ohl[z][4]:
        #     pass
        print(mid_price, ohl[z][4])
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

def pos_monitoring(q_out):
    if pos_status():
        time.sleep(3)
        if len([nu for nu in threading.enumerate() if re.match(r'^[0-9]+$', nu.getName()) or re.match(r'^Thread-*', nu.getName())]) <= 0:
            if pos_status('LONG'):
                th_side = 'LONG'
            else:
                th_side = 'SHORT'
            trade_price = fetch_positions(th_side)['pos_price']
            for tra in bn.fetch_my_trades(symbol, limit = 5):
                if tra['price'] == trade_price:
                    order_id = tra['order']
                    event = threading.Event()
                    q_out.put((order_id, th_side, event))
                    event.set()
        else:
            return
    else:
        return

# 主函数    
def main():
    print('主函数启动时间：', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    ch_lev(leverage)
    order_check()
    schebg.start()
    try:
        while 1:
            if bn.fetch_total_balance()['USDT'] <= 200:
                print('资金低于阈值！', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
                pus_msg = {
                    '标题：': '资金已经低于阈值，结束程序！',
                    '资金：': bn.fetch_total_balance()['USDT']
                }
                push_message(pus_msg)
                schebg.remove_all_jobs()
                break
            else:
                if not schebg.get_jobs():
                    schebg.add_job(get_side, 'cron', args = [que], minute = '1/15', name = 'sched')
                    schebg.add_job(db_del, 'cron', day = '*/15', name = 'del_expired_db')
                    #schebg.add_job(pos_monitoring, 'cron', args = [que], minute = '*/1', name = 'position_monitoring')
                th_value = re.compile(r'^thread\-[0-9]+$')
                th_names = [nm.getName() for nm in threading.enumerate()]
                if len([x for x in th_names if th_value.match(x)]) < 1:
                    threading.Thread(target = th_create, args = (que,), name = 'thread-' + str(int(time.time()))).start()
                time.sleep(10)
            pprint(threading.enumerate())
            print(bn.fetch_free_balance()['USDT'], time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())))
            pprint(schebg.get_jobs())
            time.sleep(300)
    except Exception as d:
        schebg.remove_all_jobs()
        msg = {
            '标题': '主程序异常退出',
            '错误信息': str(d),
            '触发时间': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        }
        push_message(msg)
        main()

if __name__ == '__main__':
    # print('5m:',avg_ch('5m'))
    print('15m:',avg_ch('15m'))
    print('30m:',avg_ch('30m'))
    main()    

#bn.fapiPrivate_post_listenkey() 此命令可获取账户的推送订阅key
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
#pprint(create_tpsl_order('STOP', 1, 34900, 'LONG'))
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

#print(mab(3,5,ol))
# ohl = bn.fetch_ohlcv(symbol, '15m', limit = 3)
# for i,j in zip(range(0, len(ohl) - 1), range(1, len(ohl))):
#     if ohl[i][4] > ohl[i][1] and ohl[j][1] > ohl[j][4] and abs(ohl[i][4] - ohl[j][1]) < 1:
#         side = 'SHORT'
#         print(i,j,time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ohl[i][0] / 1000)), side)
#     elif ohl[i][1] > ohl[i][4] and ohl[j][4] > ohl[j][1] and abs(ohl[i][4] - ohl[j][1]) < 1:
#         side = 'LONG'
#         print(i,j,time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ohl[i][0] / 1000)), side)
# for i in ohl:
#     if i[1] > i[4]:
#         high_ch = i[2] - i[1]
#         low_ch = i[4] - i[3]
#         side = 'SHORT'
#     else:
#         high_ch = i[2] - i[4]
#         low_ch = i[1] - i[3]
#         side = 'LONG'
#     k_list.append([high_ch, low_ch, side])

# 计划，每隔十五分钟运行一次，如果出现一个long和一个short的组合，并且存在比较长的引线，之后再根据后续的实时价格进行开单操作，开单之后调整止损比例，初始止盈比例及价格差逐步
# 上升，初始建议为0.6



# ohl = bn.fetch_ohlcv(symbol, '15m',since = 1622649600000)
# list1 = []
# list2 = []
# for x, y, z in zip(range(0, len(ohl) - 2), range(1, len(ohl) - 1), range(2, len(ohl))):
#     side = None
#     if ohl[x][4] > ohl[x][1] and ohl[y][1] > ohl[y][4] and abs(ohl[x][4] - ohl[y][1]) < 1 and ohl[z][4] < ohl[z][1]:
#         side = 'SHORT'
#     elif ohl[x][1] > ohl[x][4] and ohl[y][4] > ohl[y][1] and abs(ohl[x][4] - ohl[y][1]) < 1 and ohl[z][4] > ohl[z][1]:
#         side = 'LONG'
#     high_ch = ohl[z][2] - ohl[z][1]
#     low_ch = ohl[z][1] - ohl[z][3]
#     if side != None:
#         if side == 'LONG' and high_ch > low_ch >= 0:
#             price_ch = high_ch - low_ch
#         elif side == 'SHORT' and low_ch > high_ch >= 0:
#             price_ch = low_ch - high_ch
#         list1.append([time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ohl[z][0] / 1000)), side, price_ch])
#     if ohl[x][4] > ohl[x][1] and ohl[y][1] > ohl[y][4] and abs(ohl[x][4] - ohl[y][1]) < 1:
#         side = 'SHORT'
#         list2.append([time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ohl[z][0] / 1000)), side])
#     elif ohl[x][1] > ohl[x][4] and ohl[y][4] > ohl[y][1] and abs(ohl[x][4] - ohl[y][1]) < 1:
#         side = 'LONG'
#         list2.append([time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ohl[z][0] / 1000)), side])
# print(len(list1), len(list2))
# def sched_test():
#     print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

# sched.add_job(sched_test, 'cron', second = '5/10')
# sched.start()
# sched.get_jobs()
# def test_k(k_time):
#     ohl = bn.fetch_ohlcv(symbol, k_time, limit = 3)
#     for x, y, z in zip(range(0, len(ohl) - 2), range(1, len(ohl) - 1), range(2, len(ohl))):
#         if ohl[x][4] > ohl[x][1] and ohl[y][1] > ohl[y][4] and abs(ohl[x][4] - ohl[y][1]) < 1 and ohl[z][4] < ohl[z][1]:
#             side = 'SHORT'
#             if ohl[x][2] - ohl[x][4] > ohl[x][4] - ohl[x][1] or ohl[y][2] - ohl[y][1] > ohl[y][1] - ohl[y][4]:
#                 print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ohl[z][0] / 1000)), side)
#         elif ohl[x][1] > ohl[x][4] and ohl[y][4] > ohl[y][1] and abs(ohl[x][4] - ohl[y][1]) < 1 and ohl[z][4] > ohl[z][1]:
#             side = 'LONG'
#             if ohl[x][4] - ohl[x][3] > ohl[x][1] - ohl[x][4] or ohl[y][1] - ohl[y][3] > ohl[y][4] - ohl[y][1]:
#                 print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ohl[z][0] / 1000)), side)
#     print('无符合要求K线！', time.time())

# schebl.add_job(test_k, 'cron', minute = '1/15', args = ['15m'])
# schebl.start()

