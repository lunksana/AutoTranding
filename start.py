import json
import ccxt
import time
import db

class Autotranding():
    def __init__(self,order_symbol,order_type,order_price,order_side,num,exchange):
        self.order_symbol = order_symbol
        self.order_type = order_type
        self.order_price = order_price
        self.order_side = order_side
        self.num = num
        self.exchange = exchange
    
    def init_exchange(self):
        bn = ccxt.binance()
        return bn