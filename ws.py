# 测试交易所使用Websocket获取交易信息
# a websocket client for binance 



import websocket
import time
import json
import threading

class Ws:
    def __init__(self, ws_url, symbol):
        self.ws_url = ws_url
        self.symbol = symbol
        self.isConnected = threading.Event()
        self._reCounect = threading.Event()
        self._disConnect = threading.Event()
        self._reConnects = 3
        self.ws = None


    def wsConnect(self):
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_close = self.on_close,
            on_message = self.on_message,
            on_error = self.on_error,
            on_ping = self.on_ping
        )
        self.ws.on_open = self.on_open
        self.ws.run_forever(ping_interval = 15)
        self.isConnected.set()
    
    def wsReconnect(self):
        if self.isConnected.is_set():
            pass

    def connectCheck(self):
        if self.ws:
            if self.isConnected.is_set():
                pass
    
    def on_open(self, ws):
        print('on open')

    def on_close(self, ws):
        print('On close')

    def on_message(self, ws, msg):
        msg = json.loads(msg)
        print(msg)
        print(len(msg))
        ws.close()
        
        #enumerate(msg)
            

    def on_error(self, ws, error):
        print(f'on error: {error}')
        
    def on_ping(self, ws, msg):
        print('get a ping!')
        #ws.pong()
        ws.send('pong', websocket.ABNF.OPCODE_PONG)
        time.sleep(10)
        ws.close()
    
    def sub_stream(self, stream):
        if self.isConnected.is_set():
            data = {
                'method': 'SUBSCRIBE',
                'params': [
                    'btcusdt@kline_15m',
                    'btcusdt@markPrice@1s',
                    'btcusdt@aggTrade',
                    'btcusdt@depth5@100ms',
                    'btcusdt@miniTicker',
                    'btcusdt_perpetual@continuousKline_15m'
                ],
                'id': 123
            }
            self.ws.send(json.dumps(data))
        else:
            self._recounect.set()

        


stream = 'btcusdt@kline_15m/btcusdt@markPrice@1s'
# {
#     'method': 'SUBSCRIBE',
#     'params': [
#         'btcusdt@kline_15m',
#         'btcusdt@markPrice@1s'
#     ],
#     'id': 123
# }
# wss_url = 'wss://fstream.binance.com/ws/btcusdt@kline_15m' # 15分钟K线
# wss_url = 'wss://fstream.binance.com/ws/btcusdt@markPrice@1s' # 标记价格
# wss_url = 'wss://fstream.binance.com/ws/btcusdt@miniTicker' # 精简ticker
# wss_url = 'wss://fstream.binance.com/ws/FbIDMnfvr0fLszyZ4Q7nQHyiGrhqXIMv3i3DovSMudvI5QlvFqOCeSHGyeDD83jZ' # 用户账户信息订阅
# wss_url = f'wss://fstream.binance.com/ws/'
# ws = websocket.WebSocketApp(
#     wss_url,
#     on_open = on_open,
#     on_close = on_close,
#     on_message = on_message,
#     on_error = on_error,
#     on_ping = on_ping
# )

# ws.run_forever(ping_interval = 15)

'''
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
'''
'''
{
    "e":"kline",
    "E":1624793687978,
    "s":"BTCUSDT",
    "k":{
        "t":1624793400000,
        "T":1624794299999,
        "s":"BTCUSDT",
        "i":"15m",
        "f":1100949467,
        "L":1101031665,
        "o":"32950.00",
        "c":"33142.87",
        "h":"33261.56",
        "l":"32932.37",
        "v":"10957.033",
        "n":82192,
        "x":false,
        "q":"362972470.64803",
        "V":"6048.611",
        "Q":"200385362.53320",
        "B":"0"
    }
}
{
    "e":"markPriceUpdate",
    "E":1624793688002,
    "s":"BTCUSDT",
    "p":"33139.82000000",
    "P":"32800.41714709",
    "i":"33178.63560092",
    "r":"-0.00044465",
    "T":1624809600000
}
'''