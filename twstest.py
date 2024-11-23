# import sys
# from ibapi.client import EClient
# from ibapi.wrapper import EWrapper
# from ibapi.contract import Contract
# from ibapi.order import Order
# import yfinance as yf
# import pandas as pd
# import numpy as np
# import time
# from datetime import datetime, timedelta
# from pytz import timezone
# import pytz

# class TradingBot(EWrapper, EClient):
#     def __init__(self):
#         EClient.__init__(self, self)
#         self.nextorderId = None
#         self.position = 0
#         self.initial_capital = 10000
#         self.risk_per_trade = 0.02
#         self.last_price = None
#         self.last_trade_price = None
#         self.profit_loss = 0
#         self.proximity_threshold = 0.002  # 改为0.2%更精确
#         self.connected = False

#     def connect_and_wait(self, max_attempts=3):
#         attempt = 0
#         while attempt < max_attempts:
#             try:
#                 if not self.connected:
#                     self.connect('127.0.0.1', 7497, 1)
#                     timeout = time.time() + 10
#                     while time.time() < timeout and not self.connected:
#                         self.run()
#                         time.sleep(0.1)
                    
#                     if not self.connected:
#                         print("连接超时，重试...")
#                         attempt += 1
#                         continue
#                     return True
#             except Exception as e:
#                 print(f"连接错误: {str(e)}")
#                 attempt += 1
#                 time.sleep(2)
#         return False
        
#     def error(self, reqId:int, errorCode:int, errorString:str, advancedOrderRejectJson=""):
#         if errorCode == 502:
#             self.connected = False
#             print("TWS未连接")
#         elif errorCode != 2104 and errorCode != 2106 and errorCode != 2158:  # 忽略正常连接消息
#             print(f'Error {errorCode}: {errorString}')
    
#     def nextValidId(self, orderId):
#         self.nextorderId = orderId
#         self.connected = True
#         print('成功连接到IBKR')

#     def connectionClosed(self):
#         self.connected = False
#         print("TWS连接关闭")

#     def get_current_times(self):
#         et_tz = timezone('US/Eastern')
#         cn_tz = timezone('Asia/Shanghai')
#         utc_now = datetime.now(pytz.UTC)
#         return utc_now.astimezone(et_tz), utc_now.astimezone(cn_tz)

#     def format_time_info(self, et_time, cn_time):
#         return f"""=== 当前时间 ===
# 美东时间: {et_time.strftime('%Y-%m-%d %H:%M:%S %A')}
# 中国时间: {cn_time.strftime('%Y-%m-%d %H:%M:%S %A')}"""

#     def is_market_hours(self):
#         et_time, cn_time = self.get_current_times()
#         if et_time.weekday() > 4:
#             return False, et_time, cn_time
#         market_open = et_time.replace(hour=9, minute=30, second=0)
#         market_close = et_time.replace(hour=16, minute=0, second=0)
#         return market_open <= et_time <= market_close, et_time, cn_time

#     def get_market_data(self, symbol):
#         try:
#             is_market_open, current_et, current_cn = self.is_market_hours()
#             if not is_market_open:
#                 next_open_et = current_et + timedelta(days=(7-current_et.weekday()) % 5)
#                 next_open_et = next_open_et.replace(hour=9, minute=30, second=0)
#                 next_open_cn = next_open_et.astimezone(timezone('Asia/Shanghai'))
#                 print(f"\n=== 市场状态: 休市 ===")
#                 print(f"下次开盘: 美东 {next_open_et.strftime('%H:%M:%S')} / 中国 {next_open_cn.strftime('%H:%M:%S')}")
#                 return None
            
#             end_time = datetime.now()
#             start_time = end_time - timedelta(days=1)
#             ticker = yf.Ticker(symbol)
#             print("正在获取数据...")
#             data = ticker.history(start=start_time, end=end_time, interval='1m')
#             print(f"获取到 {len(data)} 条数据")
#             if len(data) == 0 or data.index[-1].date() < end_time.date():
#                 print("等待数据更新...")
#                 return None

#             data['upper'] = data['High'].rolling(window=20).max()
#             data['lower'] = data['Low'].rolling(window=20).min()
#             data['middle'] = (data['upper'] + data['lower']) / 2
            
#             current_price = data['Close'].iloc[-1]
#             self.last_price = current_price
            
#             # 计算距离并显示状态
#             distance_to_upper = abs(current_price - data['upper'].iloc[-1]) / data['upper'].iloc[-1]
#             distance_to_middle = abs(current_price - data['middle'].iloc[-1]) / data['middle'].iloc[-1]
#             distance_to_lower = abs(current_price - data['lower'].iloc[-1]) / data['lower'].iloc[-1]
            
#             print(f"\n=== 市场状态: {symbol} ===")
#             print(f"时间: {data.index[-1].strftime('%H:%M:%S')}")
#             print(f"价格: ${current_price:.2f}")
#             print(f"上轨: ${data['upper'].iloc[-1]:.2f} (距离: {distance_to_upper:.2%})")
#             print(f"中轨: ${data['middle'].iloc[-1]:.2f} (距离: {distance_to_middle:.2%})")
#             print(f"下轨: ${data['lower'].iloc[-1]:.2f} (距离: {distance_to_lower:.2%})")
#             print(f"持仓: {self.position}股")
            
#             if self.position > 0 and self.last_trade_price:
#                 unrealized_pl = self.position * (current_price - self.last_trade_price)
#                 print(f"未实现盈亏: ${unrealized_pl:.2f}")
            
#             return data
                
#         except Exception as e:
#             print(f"获取数据失败: {str(e)}")
#             return None
    
#     def check_signals(self, data):
#         if data is None or len(data) < 2:
#             return False, False
        
#         current_price = data['Close'].iloc[-1]
#         upper_band = data['upper'].iloc[-1]
#         middle_band = data['middle'].iloc[-1]
        
#         distance_to_upper = abs(current_price - upper_band) / upper_band
#         distance_to_middle = abs(current_price - middle_band) / middle_band
        
#         buy_signal = distance_to_upper <= self.proximity_threshold
#         sell_signal = distance_to_middle <= self.proximity_threshold
        
#         if buy_signal or sell_signal:
#             print("\n=== 信号详情 ===")
#             if buy_signal:
#                 print(f"价格接近上轨: {distance_to_upper:.2%} <= {self.proximity_threshold:.2%}")
#             if sell_signal:
#                 print(f"价格接近中轨: {distance_to_middle:.2%} <= {self.proximity_threshold:.2%}")
        
#         return buy_signal, sell_signal
    
#     def calculate_position_size(self, current_price):
#         max_risk = self.initial_capital * self.risk_per_trade
#         position_size = int(max_risk / current_price)
#         return max(1, position_size)
    
#     def place_order(self, action, quantity, symbol):
#         if not self.connected or quantity <= 0:
#             print(f"下单失败: {'未连接' if not self.connected else '数量无效'}")
#             return
            
#         try:
#             contract = Contract()
#             contract.symbol = symbol
#             contract.secType = "STK"
#             contract.exchange = "SMART"
#             contract.currency = "USD"
            
#             order = Order()
#             order.action = action
#             order.totalQuantity = quantity
#             order.orderType = "MKT"
            
#             current_price = self.last_price
            
#             if action == "SELL" and self.last_trade_price is not None:
#                 trade_pl = quantity * (current_price - self.last_trade_price)
#                 self.profit_loss += trade_pl
#                 print(f"\n=== 交易结算 ===")
#                 print(f"本次交易盈亏: ${trade_pl:.2f}")
            
#             if action == "BUY":
#                 self.last_trade_price = current_price
            
#             self.placeOrder(self.nextorderId, contract, order)
#             print(f"下单: {action} {quantity}股 {symbol} @ {current_price:.2f}")
#             self.nextorderId += 1
            
#         except Exception as e:
#             print(f"下单失败: {str(e)}")

# def main():
#     app = TradingBot()
#     et_time, cn_time = app.get_current_times()
    
#     print("\n=== 交易机器人启动 ===")
#     print(app.format_time_info(et_time, cn_time))
#     print("\n策略说明：")
#     print(f"1. 使用20周期唐奇安通道")
#     print(f"2. 买入条件: 价格接近上轨(距离 <= {app.proximity_threshold:.2%})")
#     print(f"3. 卖出条件: 价格接近中轨(距离 <= {app.proximity_threshold:.2%})")
#     print(f"4. 风险控制: 每次交易风险限制在账户的2%")
#     print("5. 交易时间: 美东时间 9:30 AM - 4:00 PM (工作日)")
#     print("          对应中国时间 21:30 - 04:00 (工作日)")
    
#     if not app.connect_and_wait():
#         print("连接失败，请检查TWS设置")
#         return

#     symbol = 'TSLA'
    
#     while True:
#         try:
#             app.run()
            
#             if not app.connected:
#                 print("连接断开，尝试重连...")
#                 if not app.connect_and_wait():
#                     break
#                 continue
            
#             data = app.get_market_data(symbol)
#             sys.stdout.flush()  # 强制刷新输出
            
#             if data is not None:
#                 buy_signal, sell_signal = app.check_signals(data)
                
#                 if buy_signal and app.position <= 0:
#                     quantity = app.calculate_position_size(app.last_price)
#                     app.place_order("BUY", quantity, symbol)
#                     app.position = quantity
#                 elif sell_signal and app.position > 0:
#                     app.place_order("SELL", app.position, symbol)
#                     app.position = 0
#                 else:
#                     print("\n未触发交易信号")
                    
#                 time.sleep(60)  # 交易时间内每分钟检查
#             else:
#                 time.sleep(300)  # 休市时间每5分钟检查
            
#         except KeyboardInterrupt:
#             print("\n程序手动终止")
#             break
#         except Exception as e:
#             print(f"Error: {str(e)}")
#             time.sleep(5)

# if __name__ == "__main__":
#     main()



# from ibapi.client import EClient
# from ibapi.wrapper import EWrapper
# import time

# class IBConnection(EWrapper, EClient):
#     def __init__(self):
#         EClient.__init__(self, self)
#         self.connected = False
    
#     def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
#         if errorCode == 502:
#             print("TWS未连接")
#         else:
#             print(f'错误 {errorCode}: {errorString}')
    
#     def nextValidId(self, orderId):
#         self.connected = True
#         print('连接成功')

# def main():
#     app = IBConnection()
#     app.connect('127.0.0.1', 7497, 1)
    
#     while not app.connected:
#         app.run()
#         time.sleep(1)
#         print("等待连接...")

# if __name__ == "__main__":
#     main()
#================================================================
# import yfinance as yf
# from ibapi.client import EClient
# from ibapi.wrapper import EWrapper
# from ibapi.contract import Contract
# from ibapi.order import Order
# import pandas as pd
# import numpy as np
# from datetime import datetime, timedelta
# import threading
# import time

# class TradingBot(EWrapper, EClient):
#     def __init__(self):
#         EClient.__init__(self, self)
#         self.positions = {}
#         self.current_price = None
#         self.order_id = 0
        
#     def error(self, reqId, errorCode, errorString):
#         print(f'Error {errorCode}: {errorString}')
        
#     def nextValidId(self, orderId):
#         self.order_id = orderId
#         print("\n=== TWS连接状态 ===")
#         print("✓ 成功连接到TWS")
#         print(f"✓ 初始订单ID: {orderId}")
        
#     def position(self, account, contract, pos, avgCost):
#         self.positions[contract.symbol] = pos
#         print(f"\n当前持仓: {contract.symbol} - {pos}股")
        
#     def tickPrice(self, reqId, tickType, price, attrib):
#         if tickType == 4:
#             self.current_price = price
#             print(f"\n当前价格更新: ${price:.2f}")

# def get_donchian_channels(df, period=20):
#     df['upper_channel'] = df['High'].rolling(window=period).max()
#     df['lower_channel'] = df['Low'].rolling(window=period).min()
#     df['middle_channel'] = (df['upper_channel'] + df['lower_channel']) / 2
#     return df

# class DonchianStrategy:
#     def __init__(self, symbol, capital=100000, period=20, num_tranches=3):
#         self.symbol = symbol
#         self.capital = capital
#         self.period = period
#         self.num_tranches = num_tranches
#         self.bot = TradingBot()
#         self.position = 0
        
#     def connect_tws(self):
#         print("\n=== 初始化策略 ===")
#         print(f"股票: {self.symbol}")
#         print(f"资金: ${self.capital:,.2f}")
#         print(f"通道周期: {self.period}分钟")
#         print(f"分批数量: {self.num_tranches}")
        
#         self.bot.connect("127.0.0.1", 7497, 1)
#         self.bot_thread = threading.Thread(target=self.bot.run)
#         self.bot_thread.start()
#         time.sleep(1)
        
#     def get_minute_data(self):
#         print("\n=== 获取市场数据 ===")
#         stock = yf.Ticker(self.symbol)
#         end = datetime.now()
#         start = end - timedelta(days=5)
#         df = stock.history(start=start, end=end, interval='1m')
#         print(f"获取到 {len(df)} 条分钟数据")
#         return df
        
#     def run_strategy(self):
#         self.connect_tws()
        
#         while True:
#             try:
#                 df = self.get_minute_data()
#                 df = get_donchian_channels(df, self.period)
                
#                 latest = df.iloc[-1]
#                 print("\n=== 策略状态 ===")
#                 print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
#                 print(f"当前价格: ${latest['Close']:.2f}")
#                 print(f"上轨: ${latest['upper_channel']:.2f}")
#                 print(f"下轨: ${latest['lower_channel']:.2f}")
#                 print(f"当前持仓: {self.position}")
                
#                 if latest['Close'] > latest['upper_channel'] and self.position <= 0:
#                     print("\n▲ 突破上轨 - 买入信号")
#                 elif latest['Close'] < latest['lower_channel'] and self.position >= 0:
#                     print("\n▼ 突破下轨 - 卖出信号")
#                 else:
#                     print("\n● 区间震荡 - 持仓不变")
                    
#                 time.sleep(60)
                
#             except Exception as e:
#                 print(f"\n*** 错误 ***\n{str(e)}")
#                 time.sleep(60)
#                 continue

# def main():
#     strategy = DonchianStrategy(
#         symbol="TSLA",
#         capital=100000,
#         period=20,
#         num_tranches=3
#     )
    
#     try:
#         strategy.run_strategy()
#     except KeyboardInterrupt:
#         print("\n=== 策略已停止 ===")
#         strategy.bot.disconnect()

# if __name__ == "__main__":
#     main()




# import yfinance as yf
# from ibapi.client import EClient
# from ibapi.wrapper import EWrapper
# from ibapi.contract import Contract
# from ibapi.order import Order
# import pandas as pd
# import numpy as np
# from datetime import datetime, timedelta
# import threading
# import time

# class TradingBot(EWrapper, EClient):
#     def __init__(self):
#         EClient.__init__(self, self)
#         self.positions = {}
#         self.current_price = None
#         self.order_id = 0
        
#     def error(self, reqId, errorCode, errorString):
#         print(f'Error {errorCode}: {errorString}')
        
#     def nextValidId(self, orderId):
#         self.order_id = orderId
#         print("Connected to TWS")
        
#     def position(self, account, contract, pos, avgCost):
#         self.positions[contract.symbol] = pos
        
#     def tickPrice(self, reqId, tickType, price, attrib):
#         if tickType == 4:
#             self.current_price = price
#             print(f"Current Price: ${price:.2f}")

# def get_donchian_channels(df, period=20):
#     df['upper_channel'] = df['High'].rolling(window=period).max()
#     df['lower_channel'] = df['Low'].rolling(window=period).min()
#     df['middle_channel'] = (df['upper_channel'] + df['lower_channel']) / 2
#     return df


import yfinance as yf
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import threading
import time
import logging

class TradingBot(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.positions = {}
        self.current_price = None
        self.order_id = 0
        
    def error(self, reqId, errorCode, errorString):
        print(f'Error {errorCode}: {errorString}')
        
    def nextValidId(self, orderId):
        self.order_id = orderId
        print("Connected to TWS")
        
    def position(self, account, contract, pos, avgCost):
        self.positions[contract.symbol] = pos
        
    def tickPrice(self, reqId, tickType, price, attrib):
        if tickType == 4:
            self.current_price = price
            print(f"Current Price: ${price:.2f}")

class DonchianStrategy:
    def __init__(self, symbol, capital=100000, period=20, num_tranches=3, alert_threshold=0.002):
        """
        初始化唐奇安通道策略
        symbol: 股票代码
        capital: 总资金
        period: 通道周期
        num_tranches: 分批次数
        alert_threshold: 触发阈值
        """
        #=====================
        self.trades = []
        self.current_position_size = 0
        self.total_cost_basis = 0
        self.realized_pnl = 0
        self.trade_history = []
        #=====================
        self.symbol = symbol
        self.capital = capital
        self.period = period
        self.num_tranches = num_tranches
        self.alert_threshold = alert_threshold
        self.position = 0
        self.last_trade_time = None
        self.min_trade_interval = 300
        self.bot = TradingBot()
        self.logger = self._setup_logger()

    def _setup_logger(self):
        """设置日志"""
        logger = logging.getLogger(f'DonchianStrategy_{self.symbol}')
        logger.setLevel(logging.INFO)
        fh = logging.FileHandler(f'donchian_{self.symbol}.log')
        fh.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        logger.addHandler(fh)
        return logger

    def get_market_data(self):
        """获取市场数据"""
        try:
            stock = yf.Ticker(self.symbol)
            end = datetime.now()
            start = end - timedelta(days=5)
            df = stock.history(start=start, end=end, interval='1m')
            if df.empty:
                raise ValueError("No data received")
            return df
        except Exception as e:
            self.logger.error(f"获取市场数据错误: {str(e)}")
            raise

    def is_near_channel(self, price, upper, lower):
        """检查价格是否接近通道"""
        try:
            upper_dist = abs(price - upper) / upper
            lower_dist = abs(price - lower) / lower
            
            if upper_dist <= self.alert_threshold:
                return "UPPER"
            elif lower_dist <= self.alert_threshold:
                return "LOWER"
            return None
        except Exception as e:
            self.logger.error(f"检查通道位置错误: {str(e)}")
            return None

    def can_trade(self):
        """检查是否可以交易"""
        if not self.last_trade_time:
            return True
        time_passed = (datetime.now() - self.last_trade_time).seconds
        return time_passed > self.min_trade_interval
    def execute_trade(self, action, price, upper, lower):
        """执行交易"""
        try:
            if not self.can_trade():
                self.logger.info("交易间隔时间未到")
                return False
            
            base_position = 100
            max_capital_per_trade = 50000
            
            total_cost = base_position * self.num_tranches * price
            if total_cost > max_capital_per_trade:
                base_position = int(max_capital_per_trade / (price * self.num_tranches))
            
            contract = Contract()
            contract.symbol = self.symbol
            contract.secType = "STK"
            contract.exchange = "SMART"
            contract.currency = "USD"
            contract.primaryExchange = "NASDAQ"
            
            total_shares = 0
            total_trade_cost = 0
            
            for i in range(self.num_tranches):
                df = self.get_market_data()
                df = get_donchian_channels(df, self.period)
                latest = df.iloc[-1]
                current_price = latest['Close']
                current_upper = latest['upper_channel']
                current_lower = latest['lower_channel']
                
                channel_position = self.is_near_channel(current_price, current_upper, current_lower)
                
                print(f"批次 {i+1} - 价格: ${current_price:.2f}, 上轨: ${current_upper:.2f}, 下轨: ${current_lower:.2f}")
                self.logger.info(f"批次 {i+1} - 价格: ${current_price:.2f}, 上轨: ${current_upper:.2f}, 下轨: ${current_lower:.2f}")
                
                if action == "SELL" and channel_position != "UPPER":
                    print("价格已离开上轨区域，停止交易")
                    self.logger.info("价格已离开上轨区域，停止交易")
                    break
                elif action == "BUY" and channel_position != "LOWER":
                    print("价格已离开下轨区域，停止交易")
                    self.logger.info("价格已离开下轨区域，停止交易")
                    break
                
                order = Order()
                order.action = action
                order.totalQuantity = base_position
                order.orderType = "MKT"
                order.eTradeOnly = False
                order.firmQuoteOnly = False
                
                self.bot.placeOrder(self.bot.order_id, contract, order)
                self.bot.order_id += 1
                
                # 更新持仓和盈亏信息
                if action == "BUY":
                    total_shares += base_position
                    trade_cost = base_position * current_price
                    total_trade_cost += trade_cost
                    self.current_position_size += base_position
                    self.total_cost_basis += trade_cost
                    print(f"买入: {base_position}股 @ ${current_price:.2f}")
                else:  # SELL
                    total_shares -= base_position
                    if self.current_position_size > 0:
                        avg_cost = self.total_cost_basis / self.current_position_size
                        realized_pnl = base_position * (current_price - avg_cost)
                        self.realized_pnl += realized_pnl
                        self.current_position_size -= base_position
                        self.total_cost_basis = avg_cost * self.current_position_size
                        print(f"卖出: {base_position}股 @ ${current_price:.2f}")
                        print(f"实现盈亏: ${realized_pnl:.2f}")
                
                self.logger.info(f"执行{action}: {base_position}股 @ ${current_price:.2f}")
                
                if i < self.num_tranches - 1:
                    time.sleep(20)
            
            # 交易摘要
            print(f"\n=== 交易摘要 ===")
            print(f"交易方向: {action}")
            print(f"交易股数: {abs(total_shares)}")
            print(f"当前持仓: {self.current_position_size}")
            if self.current_position_size > 0:
                print(f"平均成本: ${self.total_cost_basis/self.current_position_size:.2f}")
            print(f"总实现盈亏: ${self.realized_pnl:.2f}")
            
            self.logger.info(f"\n=== 交易摘要 ===")
            self.logger.info(f"交易方向: {action}")
            self.logger.info(f"交易股数: {abs(total_shares)}")
            self.logger.info(f"当前持仓: {self.current_position_size}")
            if self.current_position_size > 0:
                self.logger.info(f"平均成本: ${self.total_cost_basis/self.current_position_size:.2f}")
            self.logger.info(f"总实现盈亏: ${self.realized_pnl:.2f}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"执行交易错误: {str(e)}")
            return False
    # def execute_trade(self, action, price, upper, lower):
    #     """执行交易"""
    #     try:
    #         if not self.can_trade():
    #             self.logger.info("交易间隔时间未到")
    #             return False

    #         base_position = 100
    #         max_capital_per_trade = 50000
            
    #         total_cost = base_position * self.num_tranches * price
    #         if total_cost > max_capital_per_trade:
    #             base_position = int(max_capital_per_trade / (price * self.num_tranches))
            
    #         contract = Contract()
    #         contract.symbol = self.symbol
    #         contract.secType = "STK"
    #         contract.exchange = "SMART"
    #         contract.currency = "USD"
    #         contract.primaryExchange = "NASDAQ"  # 添加主交易所
            
    #         for i in range(self.num_tranches):
    #             df = self.get_market_data()
    #             df = get_donchian_channels(df, self.period)
    #             latest = df.iloc[-1]
    #             current_price = latest['Close']
    #             current_upper = latest['upper_channel']
    #             current_lower = latest['lower_channel']
                
    #             channel_position = self.is_near_channel(current_price, current_upper, current_lower)
                
    #             self.logger.info(f"批次 {i+1} - 价格: ${current_price:.2f}, 上轨: ${current_upper:.2f}, 下轨: ${current_lower:.2f}")
                
    #             if action == "SELL" and channel_position != "UPPER":
    #                 self.logger.info("价格已离开上轨区域，停止交易")
    #                 break
    #             elif action == "BUY" and channel_position != "LOWER":
    #                 self.logger.info("价格已离开下轨区域，停止交易")
    #                 break
                    
    #             order = Order()
    #             order.action = action
    #             order.totalQuantity = base_position
    #             order.orderType = "MKT"
    #             order.eTradeOnly = False  # 添加这行
    #             order.firmQuoteOnly = False  # 添加这行
                
    #             self.bot.placeOrder(self.bot.order_id, contract, order)
    #             self.bot.order_id += 1
    #             self.logger.info(f"执行{action}: {base_position}股")
                
    #             if i < self.num_tranches - 1:
    #                 time.sleep(20)
            
    #         return True
                
    #     except Exception as e:
    #         self.logger.error(f"执行交易错误: {str(e)}")
    #         return False
    def run_strategy(self):
        """运行策略"""
        try:
            self.bot.connect("127.0.0.1", 7497, 1)
            self.bot_thread = threading.Thread(target=self.bot.run)
            self.bot_thread.daemon = True
            self.bot_thread.start()
            time.sleep(1)
            
            while True:
                try:
                    df = self.get_market_data()
                    df = get_donchian_channels(df, self.period)
                    latest = df.iloc[-1]
                    current_price = latest['Close']
                    upper_channel = latest['upper_channel']
                    lower_channel = latest['lower_channel']
                    
                    channel_position = self.is_near_channel(
                        current_price,
                        upper_channel,
                        lower_channel
                    )
                    
                    print(f"\n=== {datetime.now().strftime('%H:%M:%S')} 策略状态 ===")
                    print(f"当前价格: ${current_price:.2f}")
                    print(f"上轨: ${upper_channel:.2f}")
                    print(f"下轨: ${lower_channel:.2f}")
                    print(f"持仓数量: {self.current_position_size}")
                    if self.current_position_size > 0:
                        print(f"平均成本: ${self.total_cost_basis/self.current_position_size:.2f}")
                        unrealized_pnl = self.current_position_size * (current_price - self.total_cost_basis/self.current_position_size)
                        print(f"未实现盈亏: ${unrealized_pnl:.2f}")
                    print(f"已实现盈亏: ${self.realized_pnl:.2f}")
                    
                    # 修改交易逻辑
                    if channel_position == "UPPER" and self.current_position_size > 0:
                        print("\n接近上轨 - 准备卖出")
                        if self.execute_trade("SELL", current_price, upper_channel, lower_channel):
                            self.position = -1
                            self.last_trade_time = datetime.now()
                            
                    elif channel_position == "LOWER" and self.current_position_size == 0:
                        print("\n接近下轨 - 准备买入")
                        if self.execute_trade("BUY", current_price, upper_channel, lower_channel):
                            self.position = 1
                            self.last_trade_time = datetime.now()
                    
                    time.sleep(5)
                    
                except Exception as e:
                    self.logger.error(f"策略运行错误: {str(e)}")
                    time.sleep(5)
                    continue
                    
        except KeyboardInterrupt:
            self.logger.info("策略已停止")
            self.bot.disconnect()
            
        except Exception as e:
            self.logger.error(f"严重错误: {str(e)}")
            self.bot.disconnect()
    # def run_strategy(self):
    #     """运行策略"""
    #     try:
    #         self.bot.connect("127.0.0.1", 7497, 1)
    #         self.bot_thread = threading.Thread(target=self.bot.run)
    #         self.bot_thread.daemon = True
    #         self.bot_thread.start()
    #         time.sleep(1)
            
    #         while True:
    #             try:
    #                 df = self.get_market_data()
    #                 df = get_donchian_channels(df, self.period)
    #                 latest = df.iloc[-1]
    #                 current_price = latest['Close']
    #                 upper_channel = latest['upper_channel']
    #                 lower_channel = latest['lower_channel']
                    
    #                 channel_position = self.is_near_channel(
    #                     current_price,
    #                     upper_channel,
    #                     lower_channel
    #                 )
                    
    #                 print(f"\nTime: {datetime.now().strftime('%H:%M:%S')}")
    #                 print(f"Price: ${current_price:.2f}")
    #                 print(f"Upper: ${upper_channel:.2f}")
    #                 print(f"Lower: ${lower_channel:.2f}")
    #                 print(f"Position: {self.position}")
                    
    #                 if channel_position == "UPPER" and self.position >= 0:
    #                     print("接近上轨 - 准备卖出")
    #                     if self.execute_trade("SELL", current_price, upper_channel, lower_channel):
    #                         self.position = -1
    #                         self.last_trade_time = datetime.now()
                            
    #                 elif channel_position == "LOWER" and self.position <= 0:
    #                     print("接近下轨 - 准备买入")
    #                     if self.execute_trade("BUY", current_price, upper_channel, lower_channel):
    #                         self.position = 1
    #                         self.last_trade_time = datetime.now()
                    
    #                 time.sleep(5)
                    
    #             except Exception as e:
    #                 self.logger.error(f"策略运行错误: {str(e)}")
    #                 time.sleep(5)
    #                 continue
                    
    #     except KeyboardInterrupt:
    #         self.logger.info("策略已停止")
    #         self.bot.disconnect()
            
    #     except Exception as e:
    #         self.logger.error(f"严重错误: {str(e)}")
    #         self.bot.disconnect()

def get_donchian_channels(df, period=20):
    """计算唐奇安通道"""
    df['upper_channel'] = df['High'].rolling(window=period).max()
    df['lower_channel'] = df['Low'].rolling(window=period).min()
    df['middle_channel'] = (df['upper_channel'] + df['lower_channel']) / 2
    return df
def main():
    # 策略参数设置
    config = {
        'symbol': 'TSLA',        # 股票代码
        'capital': 50000,        # 总资金
        'period': 20,           # 通道周期
        'num_tranches': 3,      # 分批次数
        'alert_threshold': 0.002 # 触发阈值 0.2%
    }
    
    # 初始化策略
    strategy = DonchianStrategy(**config)
    
    try:
        print(f"\n=== 策略启动 ===")
        print(f"股票: {config['symbol']}")
        print(f"资金: ${config['capital']:,}")
        print(f"通道周期: {config['period']}分钟")
        print(f"分批次数: {config['num_tranches']}")
        print(f"触发阈值: {config['alert_threshold']*100}%")
        
        strategy.run_strategy()
        
    except KeyboardInterrupt:
        print("\n策略已手动停止")
    except Exception as e:
        print(f"\n策略运行错误: {str(e)}")
    finally:
        if hasattr(strategy, 'bot'):
            strategy.bot.disconnect()

if __name__ == "__main__":
    main()