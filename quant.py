import ccxt
import time
import db
import control

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

get_info = control.Json_ctr.json_file()
user_api = get_info[]