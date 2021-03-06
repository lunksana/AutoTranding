# AutoTranding
自动化交易系统

# 声明
本人作死行为，对造成的损失不负任何责任

# 历史
* **2021-03-19** 建立此项目
* **2021-03-24** 总结一些想法

# 想法

---

* 如何进行有效的交易才能保证稳定的赚钱，或者说即使不赚钱也能保证不亏损本金
* 合约交易重在仓位控制，将自己的所有资金划分成多份，每次使用其中的一份进行交易，即使此次交易全亏也只是一份资金，不会造成较大的损失
* 每次交易之后及时设置止损位，避免不必要的资金损失，同样的及时止盈也很重要，见好就收才不会越陷越深
* 多空双开，依据走势进行比例调整，分别设置止损位，并同时进行价格追踪，可行性暂时无法确定
  

# 观察

1. MA3 MA5一旦相交，走向就会发生变化，但是之间的差值如果太小就会出现震荡的情况，如果短时间内差值能突破100以上应该会有较大的走向变化，虽然能确定大致的走势，但短时间内较大的波动亦会导致强制平仓的发生
2. 四小时走势能较准确的反应变化，斐波那契通道也可以作为参照
3. 需要有一个合理的对冲方式来解决较大的波动导致的损失
4. RSI背离感觉好像还是有点用处的

# 大致运行流程

---
> 输入必要的参数进行初始化（币安api，仓位控制，止损幅度，价格追踪范围，杠杆数……）；
> 函数会自动将输入的内容写入mongodb数据库方便后续的调用（数据库的地址信息保存在config目录下的cfg.json文件中，软件会通过检测此文件判断是否已经进行了数据库初始化配置）；
> 自动化进行行情分析，当符合设定的要求之后进行订单操作；

# 止盈止损订单参数

---
|参数|是否必须|STOP|TAKE_PROFIT|STOP_MARKET|TAKE_PROFIT_MARKET|TRAILING_STOP_MARKET|
|:------:|:------:|:------:|:------:|:------:|:------:|:------:|
|symbol|YES|BTCUSDT|BTCUSDT|BTCUSDT|BTCUSDT|BTCUSDT|
|side|YES|BUY/SELL|BUY/SELL|BUY/SELL|BUY/SELL|BUY/SELL|
|positionSide|YES|LONG/SHORT|LONG/SHORT|LONG/SHORT|LONG/SHORT|LONG/SHORT|
|reduceOnly|NO|true/false|true/false|||true/false|
|quantity|NO|||||0|
|price|NO||||||
|newClientOrderId|NO||||||
|stopPrice|NO|0|0|0|0||
|closePosition|NO|||true/false|true/false||
|activationPrice|NO|||||0|
|callbackRate|NO|||||[0.1,5]|
|timeInForce|NO||||||
|workingType|NO|MARK_PRICE/CONTRACT_PRICE|MARK_PRICE/CONTRACT_PRICE|MARK_PRICE/CONTRACT_PRICE|MARK_PRICE/CONTRACT_PRICE|MARK_PRICE/CONTRACT_PRICE|
|priceProtect|NO|TRUE/FALSE|TRUE/FALSE|TRUE/FALSE|TRUE/FALSE||
|newOrderRespType|NO||||||
|recvWindow|NO||||||
