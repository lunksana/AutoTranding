# 测试交易所使用Websocket获取交易信息



import websocket
import time
import json
import userapi
from pprint import pprint

def on_open(ws):
    print('on open')
    # data = {}
    # ws.send(json.dumps(data))

def on_close(ws):
    print('On close')

def on_message(ws, msg):
    pprint(msg)

def on_error(ws, error):
    print(f'on error: {error}')

stream = 'btcusdt@kline_15m/btcusdt@markPrice@1s'
# {
#     'method': 'SUBSCRIBE',
#     'params': [
#         'btcusdt@kline_15m',
#         'btcusdt@markPrice@1s'
#     ],
#     'id': 123
# }
wss_url = 'wss://fstream.binance.com/ws/btcusdt@kline_15m' # 15分钟K线
wss_url = 'wss://fstream.binance.com/ws/btcusdt@markPrice@1s' # 标记价格
wss_url = 'wss://fstream.binance.com/ws/btcusdt@miniTicker' # 精简ticker
wss_url = 'wss://fstream.binance.com/ws/FbIDMnfvr0fLszyZ4Q7nQHyiGrhqXIMv3i3DovSMudvI5QlvFqOCeSHGyeDD83jZ' # 用户账户信息订阅
wss_url = f'wss://fstream.binance.com/stream?streams={stream}'
ws = websocket.WebSocketApp(
    wss_url,
    on_open = on_open,
    on_close = on_close,
    on_message = on_message,
    on_error = on_error
)

ws.run_forever(ping_interval = 15)

{
    "stream":"btcusdt@kline_15m",
    "data":{
        "e":"kline",
        "E":1624689539855,
        "s":"BTCUSDT",
        "k":{
            "t":1624689000000,
            "T":1624689899999,
            "s":"BTCUSDT",
            "i":"15m",
            "f":1090335797,
            "L":1090361112,
            "o":"32292.17",
            "c":"32155.01",
            "h":"32328.70",
            "l":"32155.00",
            "v":"3078.657",
            "n":25316,
            "x":false,
            "q":"99218494.36846",
            "V":"1361.091",
            "Q":"43869450.17767",
            "B":"0"
        }
    }
}