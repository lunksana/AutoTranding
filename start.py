'''
* 本程序现阶段只针对币安永续合约
* 参数配置：仓位控制（资金分割份数），止损比例，价格追踪，最大杠杆
* 基于上述参数，程序将自动基于行情进行多空操作，实现盈利
* 
'''

import ccxt
import time
import control
import db

class Autotranding():
    def __init__(self, position_control, sl_ratio, price_track, max_leverage):
        self.position_control = position_control
        self.sl_ratio = sl_ratio
        self.price_track = price_track
        self.max_leverage = max_leverage
    
    def start(self):
        pass
        
if __name__ = "__main__":
    position_control = input("请输入仓位划分数量：")
    sl_ratio = input("请输入止损比例：")
    price_track = input("请输入价格追踪：")
    max_leverage = input("请输入最大杠杆值：")
    autotranding = Autotranding()