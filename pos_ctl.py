# 将所有仓位控制，订单操作模块化

import ws
import time
import ccxt
import requests
import userapi

# 基本变量设置
bn = ccxt.binance({
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
        'adjustForTimeDifference': True
    },
    'apiKey': userapi.apiKey,
    'secret': userapi.secret
})

class Posctl:
    sym = 'BTCUSDT'
    def __init__(self):
        pass
    
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
        elif order_type == 'STOP_MARKET': 
            param = {
                'symbol': self.sym,
                'side': data['side'],
                'positionSide': pos_side,
                'type': order_type, 
                'stopPrice': data['price'],
                'closePosition': True,
                'workingType': 'MARK_PRICE'
            }

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
