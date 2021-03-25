'''
* 本程序现阶段只针对币安永续合约
* 参数配置：仓位控制（资金分割份数），止损比例，价格追踪，最大杠杆
* 基于上述参数，程序将自动基于行情进行多空操作，实现盈利
* 
'''

import control
import db
import quant

class Autotranding():
    def __init__(self):
        pass
    
    def firststart(self,user_input):
        sys_conf = user_input['sys_conf']
        bn_api = user_input['bn_api']
        addr = user_input['mongodb']['addr']
        port = user_input['mongodb']['port']
        insert_conf = {
            "db": "Binance",
            "mongodb": {
                "addr": addr,
                "port": port
            },    
            "collections": [
                "bn_api",
                "order_list",
                "kline_list",
                "sys_conf",
            ],
            "configured": True
        }
        control.Json_ctr().json_write(insert_conf)
        newdb = db.Newdb(insert_conf['mongodb'],insert_conf['db']).init_db()
        return db.Controldb(newdb,'bn_api').insert_one({
            'user_api': user_input['bn_api']['user_api'], 'user_secret': user_input['bn_api']['user_secret']
        })
    
    def normalstart():
        pass

if __name__ == '__main__':
    if control.Json_ctr().json_read()['configured']:
        position_control = input("请输入仓位划分数量：")
        sl_ratio = input("请输入止损比例：")
        price_track = input("请输入价格追踪：")
        max_leverage = input("请输入最大杠杆值：")
        addr = input("请输入MongoDB地址：")
        port = input("请输入MongoDB端口：")
        user_api = input("请输入币安API：")
        user_secret = input("请输入币安SECRET：")
        user_input = {
            "sys_conf": {
                "position_control": position_control,
                "sl_ratio": sl_ratio,
                "price_track": price_track,
                "max_leverage": max_leverage
            },
            "bn_api": {
                "user_api": user_api,
                "user_secret": user_secret
            },
            "mongodb": {
                "addr": addr,
                "port": port
            }
        }
        autotranding = Autotranding().firststart(user_input)
    else:
        autotranding = Autotranding().normalstart()
