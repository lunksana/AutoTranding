# take_profit_market 止盈

import ccxt
import time
import db
import control

# 开始量化
class Startquant():
    def __init__(self):
        bn = ccxt.binance({
            
        })

    def new_order():
        pass

bn = ccxt.binance({
    'enableRateLimit': True,
    'options': {'defaultType': 'future'},
    'apiKey': user_api,
    "secret": user_secret
})

# get_info = control.Json_ctr.json_file()
# user_api = get_info[]

# 订单处理
class Orderprocessing():
    def def __init__(self, symbol):
      self.symbol = symbol
      
    def new_order(self, order):
        neworder = {
        'symbol': 'BTCUSDT',
        'side': 'BUY',
        'type': "TAKE_PROFIT",
        'quantity': 0.03,
        'price': 58200,
        'stopPrice': 58200,
        'positionSide': 'SHORT'
    }

# 创建行情分析
class Marketjudgment():
    def __init__(self, exchange):
        self.exchange = exchange

    def klines(self, interval):
        kline = self.exchange.fetchOHLCV('BTC/USDT',interval)
        print(kline)
        
