# 将所有仓位控制，订单操作模块化

#import ws
import time
import requests
from requests.api import request
import userapi
import hashlib
import hmac
from pprint import pprint
from enum import Enum, unique
from urllib.parse import urlencode

# 基本变量设置
# bn = ccxt.binance({
#     'enableRateLimit': True,
#     'options': {
#         'defaultType': 'future',
#         'adjustForTimeDifference': True
#     },
#     'apiKey': userapi.apiKey,
#     'secret': userapi.secret
# })

@unique
class RequestMethod(Enum):
    GET = "get"
    POST = "post"
    DELETE = "delete"
    PUT = "put"

class Interval(Enum):
    MINUTE_1 = '1m'
    MINUTE_3 = '3m'
    MINUTE_5 = '5m'
    MINUTE_15 = '15m'
    MINUTE_30 = '30m'
    HOUR_1 = '1h'
    HOUR_2 = '2h'
    HOUR_4 = '4h'
    HOUR_6 = '6h'
    HOUR_8 = '8h'
    HOUR_12 = '12h'
    DAY_1 = '1d'
    DAY_3 = '3d'
    WEEK_1 = '1w'
    MOUTH_1 = '1M'

class OrderType(Enum):
    LIMIT = 'LIMIT'
    MARKET = 'MARKET'
    STOP = 'STOP'
    TAKE_PROFIT = 'TAKE_PROFIT'
    STOP_MARKET = 'STOP_MARKET'
    TAKE_PROFIT_MARKET = 'TAKE_PROFIT_MARKET'

class Bn:
    base_url = 'https://fapi.binance.com'
    interval_list = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
    def __init__(self, symbol, api_key = None, secret = None, timeout = 5):
        self.symbol = symbol
        self.api_key = api_key
        self.secret = secret
        self.timeout = timeout
        self.headers = {'X-MBX-APIKEY': self.api_key}
    
    def  _generate_signature(self, params: dict):
        query_str = urlencode(params)
        return hmac.new(self.secret.encode('utf-8'), query_str.encode('utf-8'), hashlib.sha256).hexdigest()
    
    def _requests(self, Method: RequestMethod, url, headers: bool = False, params: dict = None, private: bool = False):
        if private:
            if params:
                url += '?' + urlencode(params)
            url = url + '&signature=' + self._generate_signature(params)
        else:
            if params:
                url += '?' + urlencode(params)
        if headers:
            return requests.request(Method.value, url, headers = self.headers, timeout = self.timeout)
        else:
            return requests.request(Method.value, url, timeout = self.timeout)

    def fetch_ticker(self, symbol = None):
        path = '/fapi/v1/ticker/price'
        url = self.base_url + path
        if symbol:
            sym = symbol
        else:
            sym = self.symbol
        params = {'symbol': sym}
        #requests_data = requests.get(url, timeout=self.timeout).json()
        requests_data = self._requests(RequestMethod.GET, url, params = params).json()
        return float(requests_data['price'])
        
    def fetchOHLCV(self, symbol, interval: str, since = None, limit: int = None):
        if interval not in self.interval_list:
            return
        else:
            path = '/fapi/v1/klines'
            url = self.base_url + path
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            if since:
                params['startTime'] = since
            requests_data = self._requests(RequestMethod.GET, url, False, params).json()
            return [[ohl[i] for i in range(0,6)] for ohl in requests_data]
    
    # Private API
    def get_timestamp(self):
        return int(time.time() * 1000)

    def listenKey(self, Method: RequestMethod):
        path = '/fapi/v1/listenKey'
        url = self.base_url + path
        if Method.value != 'delete':
            requests_data = self._requests(Method, url, True, private = False)
            if Method.value == 'put':
                return
            else:
                return requests_data.json()['listenKey']
        else:
            self._requests(Method, url, True, private = False)
            return

    def fetch_open_orders(self, symbol = None, since = None, limit = None):
        path = '/fapi/v1/openOrders'
        url = self.base_url + path
        params = {
            'timestamp': self.get_timestamp()
        }
        if symbol:
            params['symbol'] = symbol
        return self._requests(RequestMethod.GET, url, True, params, True).json()

    def fetch_orders(self, symbol = None, since = None, limit = None):
        path = '/fapi/v1/allOrders'
        url = self.base_url + path
        params = {
            'timestamp': self.get_timestamp()
        }
        if symbol:
            params['symbol'] = symbol
        else:
            params['symbol'] = self.symbol
        if since:
            params['startTime'] = since
        if limit:
            params['limit'] = limit
        return self._requests(RequestMethod.GET, url, True, params, True).json()

    def fetch_order_status(self, id, symbol = None):
        path = '/fapi/v1/order'
        url = self.base_url + path
        statuses = {
            'NEW': 'open',
            'PARTIALLY_FILLED': 'open',
            'FILLED': 'closed',
            'CANCELED': 'canceled',
            'PENDING_CANCEL': 'canceling',  # currently unused
            'REJECTED': 'rejected',
            'EXPIRED': 'expired',
        }
        params = {
            'orderId': id,
            'timestamp': self.get_timestamp()
        }
        if symbol:
            params['symbol'] = symbol
        else:
            params['symbol'] = self.symbol
        return statuses[self._requests(RequestMethod.GET, url, True, params, True).json()['status']]

    def fetch_my_trades(self, symbol = None, since = None, limit = None):
        path = '/fapi/v1/userTrades'
        url = self.base_url + path
        params = {
            'timestamp': self.get_timestamp()
        }
        if symbol:
            params['symbol'] = symbol
        else:
            params['symbol'] = self.symbol
        if since:
            params['startTime'] = since
        if limit:
            params['limit'] = limit
        return self._requests(RequestMethod.GET, url, True, params, True).json()

    def fetch_total_balance(self):
        path = '/fapi/v2/balance'
        url = self.base_url + path
        params = {
            'timestamp': self.get_timestamp()
        }
        requests_data = self._requests(RequestMethod.GET, url, True, params, True).json()
        return {i['asset']:float(i['balance']) for i in requests_data}
            

    def fetch_free_balance(self):
        path = '/fapi/v2/balance'
        url = self.base_url + path
        params = {
            'timestamp': self.get_timestamp()
        }
        requests_data = self._requests(RequestMethod.GET, url, True, params, True).json()
        return {i['asset']:float(i['availableBalance']) for i in requests_data}

    def create_order(self, symbol, positionSide, type):
        
        pass

    def cancel_order(self):
        pass

    def fetch_positions(self):
        path = '/fapi/v2/positionRisk'
        url = self.base_url + path
        params = {
            'symbol': self.symbol,
            'timestamp': self.get_timestamp()
        }
        return self._requests(RequestMethod.GET, url, True, params, True)
            
if __name__ == '__main__':
    print(Bn.base_url)
    bn = Bn('BTCUSDT', userapi.apiKey, userapi.secret)
    pprint(bn.fetch_free_balance())
    
exit()

class Posctl:
    def __init__(self, sym = None):
        if sym:
            self.sym = sym
        else:
            self.sym = 'BTCUSDT'
    
    def place_order(self, param):
        return bn.fapiPrivate_post_order(param)
    
    def get_pos(self, pos_side):
        pos_list = bn.fapiPrivateV2GetPositionRisk({'symbol': self.sym})
        for i in pos_list:
            if i['positionSide'] == pos_side:
                return i

    def create_pos(self, btc_price, btc_amt, order_type):
        if btc_amt > 0:
            side = 'BUY'
            pos_side = 'LONG'
        else:
            side = 'SELL'
            pos_side = 'SHORT'
            btc_amt = abs(btc_amt)
        if order_type not in ['LIMIT', 'MARKET']:
            return
        param = {
            'symbol': self.sym,
            'side': side,
            'positionSide': pos_side,
            'type': order_type,
            'quantity': btc_amt
        }
        if order_type == 'LIMIT':
            param['timeInForce'] = 'GTC'
            param['price'] = btc_price
        order_res = self.place_order(param)
        if order_res['order_id']:
            return order_res['order_id']
    
    def stop_pos(self):
        pass

    def cancel_order(self):
        pass
    
    def create_stop_order(self, btc_price, pos_side, order_type):
        if order_type not in ['STOP', 'STOP_MARKET']:
            return
        else:
            param = {
                'symbol': self.sym,
                'positionSide': pos_side,
                'type': order_type, 
                'stopPrice': btc_price,
                'workingType': 'MARK_PRICE'
            }
        if order_type == 'STOP_MARKET':
            param['closePosition'] = True
        else:
            param['quantity'] = None
        if pos_side == 'LONG':
            side = 'SELL'
        else:
            side = 'BUY'
        param['side'] = side

    def create_pfhl_order(self):
        pass

# def create_pos():
#         def create_pos(self, data):
#         sym = data['symbol']
#         if data['price'] == '市价':
#             res = brkrs.fetch_symbol_price(sym)
#             price = float(res['price'])
#             order_type = 'MARKET'
#         else:
#             price = float(data['price']) #fix price
#             order_type = 'LIMIT'
#         for an in data['vas']:
#             self._set_lev(an, data)
#             acct_equ = brkrs.all_equ[an]
#             margin_rate = float(data['mr'][:-1])/100
#             margin = acct_equ*margin_rate
#             quote = margin*float(data['lev'])
#             qp = brkrs.sym_infos[sym]['qp']
#             qty = round(quote/price,qp)
#             qty = max(qty,1/pow(10,qp))

#             rstr = base62.encode(int(datetime.now().timestamp()))
#             param = {
#                 'symbol': sym,
#                 'side': data['side'],
#                 'positionSide': data['positionSide'],
#                 'type': order_type,
#                 'quantity': qty,
#                 'newClientOrderId': f"{app}_{data['op']}_{rstr}", 
#             }
#             if order_type == 'LIMIT': 
#                 param['price'] = price
#                 param['timeInForce'] = 'GTC'
#             res = brkrs.place_order(an, param)
#             if res['orderId']:
#                 op_ch = get_op(data['op'])
#                 Lgr.log(data['op'],f"账户:{an} {op_ch}: {param}")
#             else:
#                 Lgr.log('ERROR','place order has error')

#     def close_pos(self, data):
#         sym = data['symbol']
#         if data['price'] == '市价':
#             res = brkrs.fetch_symbol_price(sym)
#             price = float(res['price'])
#             order_type = 'MARKET'
#         else:
#             price = float(data['price']) #fix price
#             order_type = 'LIMIT'
#         for an in data['vas']:
#             qp = brkrs.sym_infos[sym]['qp']
#             close_rate = float(data['cr'][:-1])/100
#             pos_amt = 0
#             for pos in brkrs.all_valid_pos[an]:
#                 if pos['symbol'] == sym and pos['positionSide'] == data['positionSide']:
#                     pos_amt = float(pos['positionAmt'])
#             if not pos_amt:
#                 Lgr.log('bnews', f'账户 {an} 没有找到对应仓位')
#                 return
#             qty = round(abs(pos_amt)*close_rate,qp)
#             qty = max(qty,1/pow(10,qp))
#             rstr = base62.encode(int(datetime.now().timestamp()))
#             param = {
#                 'symbol': sym,
#                 'side': data['side'],
#                 'positionSide': data['positionSide'],
#                 'type': order_type,
#                 'quantity': qty,
#                 'newClientOrderId': f"{app}_{data['op']}_{rstr}", 
#             }
#             if order_type == 'LIMIT': 
#                 param['price'] = price
#                 param['timeInForce'] = 'GTC'
#             res = brkrs.place_order(an, param)
#             if res['orderId']:
#                 op_ch = get_op(data['op'])
#                 Lgr.log(data['op'],f"账户:{an} {op_ch}: {param}")
#             else:
#                 Lgr.log('ERROR','place order has error')


#     def cancel_porders(self, porder_df, idxs):
#         for idx in idxs.split(' '):
#             order = porder_df.iloc[int(idx)]
#             param = {
#                 "symbol": order['symbol'],
#                 "orderId": order['orderId']
#             }
#             res = brkrs.cancel_porder(order['账户'],param)
#             if res and res['orderId']:
#                 Lgr.log('SUCCESS',f"撤销订单 {res['symbol']} {res['clientOrderId']} 成功")


#     def create_stop_order(self, data):
#         sym = data['symbol']
#         for an in data['vas']:
#             rstr = base62.encode(int(datetime.now().timestamp()))
#             param = {
#                 'symbol': sym,
#                 'side': data['side'],
#                 'positionSide': data['positionSide'],
#                 'type': 'STOP_MARKET',
#                 'newClientOrderId': f"{app}_stplos_{rstr}", 
#                 'stopPrice': data['price'],
#                 'closePosition': True,
#                 'workingType': 'MARK_PRICE'
#             }
#             res = brkrs.place_order(an, param)
#             if res['orderId']:
#                 op_ch = get_op(data['op'])
#                 Lgr.log(data['op'],f"账户:{an} {op_ch}: {param}")
#             else:
#                 Lgr.log('ERROR','place order has error')

#     # 下 LIMIT 止盈单
#     def create_pfhl_order(self, data):
#         stp_p = float(data['price'])
#         sym = data['symbol']
#         pside = data['positionSide']
        
#         for an in data['vas']:
#             pp = brkrs.sym_infos[sym]['pp']
#             qp = brkrs.sym_infos[sym]['qp']
#             close_rate = 0.5
#             pos_amt = 0
#             brkrs.fetch_postion(an)
#             for pos in brkrs.all_valid_pos[an]:
#                 if pos['symbol'] == sym and pos['positionSide'] == pside:
#                     pos_amt = float(pos['positionAmt'])
#                     entry_p = float(pos['entryPrice'])
#             if not pos_amt:
#                 Lgr.log('bnews', f"账户 {an} {sym} 没有 {pside} 仓位")
#                 continue
#             if pside == 'LONG':
#                 price = round(abs(entry_p-stp_p)+entry_p*(1+Settings['slippage']),pp)
#             else:
#                 price = round(entry_p*(1-Settings['slippage'])-abs(entry_p-stp_p),pp)
#             qty = round(abs(pos_amt)*close_rate,qp)
#             qty = max(qty,1/pow(10,qp))
#             rstr = base62.encode(int(datetime.now().timestamp()))
#             param = {
#                 'symbol': sym,
#                 'side': data['side'],
#                 'positionSide': pside,
#                 'price': price,
#                 'type': 'LIMIT',
#                 'timeInForce': 'GTC',
#                 'quantity': qty,
#                 'newClientOrderId': f"{app}_{data['op']}_{rstr}", 
#             }
#             res = brkrs.place_order(an, param)
#             if res['orderId']:
#                 op_ch = get_op(data['op'])
#                 Lgr.log(data['op'],f"账户:{an} {op_ch}: {param}")
#             else:
#                 Lgr.log('ERROR','place order has error')
