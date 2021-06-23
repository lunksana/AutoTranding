# 测试交易所使用Websocket获取交易信息



import websocket
import time
import json
import userapi

def on_open(ws):
    print('on open')
    # data = {}
    # ws.send(json.dumps(data))

def on_close(ws):
    print('On close')

def on_message(ws, msg):
    print(msg)

def on_error(ws, error):
    print(f'on error: {error}')

wss_url = 'wss://fstream.binance.com/ws/btcusdt@kline_15m' # 15分钟K线
wss_url = 'wss://fstream.binance.com/ws/btcusdt@markPrice@1s' # 标记价格
wss_url = 'wss://fstream.binance.com/ws/btcusdt@miniTicker' # 精简ticker
wss_url = 'wss://fstream.binance.com/ws/FbIDMnfvr0fLszyZ4Q7nQHyiGrhqXIMv3i3DovSMudvI5QlvFqOCeSHGyeDD83jZ' # 用户账户信息订阅
ws = websocket.WebSocketApp(
    wss_url,
    on_open = on_open,
    on_close = on_close,
    on_message = on_message,
    on_error = on_error
)

ws.run_forever(ping_interval = 15)