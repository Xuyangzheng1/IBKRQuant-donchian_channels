

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
# import logging

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

# class DonchianStrategy:
#     def __init__(self, symbol, capital=100000, period=20, num_tranches=3, alert_threshold=0.002):
#         """
#         初始化唐奇安通道策略
#         symbol: 股票代码
#         capital: 总资金
#         period: 通道周期
#         num_tranches: 分批次数
#         alert_threshold: 触发阈值
#         """
#         #=====================
#         self.trades = []
#         self.current_position_size = 0
#         self.total_cost_basis = 0
#         self.realized_pnl = 0
#         self.trade_history = []
#         #=====================
#         self.symbol = symbol
#         self.capital = capital
#         self.period = period
#         self.num_tranches = num_tranches
#         self.alert_threshold = alert_threshold
#         self.position = 0
#         self.last_trade_time = None
#         self.min_trade_interval = 300
#         self.bot = TradingBot()
#         self.logger = self._setup_logger()

#     def _setup_logger(self):
#         """设置日志"""
#         logger = logging.getLogger(f'DonchianStrategy_{self.symbol}')
#         logger.setLevel(logging.INFO)
#         fh = logging.FileHandler(f'donchian_{self.symbol}.log')
#         fh.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
#         logger.addHandler(fh)
#         return logger

#     def get_market_data(self):
#         """获取市场数据"""
#         try:
#             stock = yf.Ticker(self.symbol)
#             end = datetime.now()
#             start = end - timedelta(days=5)
#             df = stock.history(start=start, end=end, interval='1m')
#             if df.empty:
#                 raise ValueError("No data received")
#             return df
#         except Exception as e:
#             self.logger.error(f"获取市场数据错误: {str(e)}")
#             raise

#     def is_near_channel(self, price, upper, lower):
#         """检查价格是否接近通道"""
#         try:
#             upper_dist = abs(price - upper) / upper
#             lower_dist = abs(price - lower) / lower
            
#             if upper_dist <= self.alert_threshold:
#                 return "UPPER"
#             elif lower_dist <= self.alert_threshold:
#                 return "LOWER"
#             return None
#         except Exception as e:
#             self.logger.error(f"检查通道位置错误: {str(e)}")
#             return None

#     def can_trade(self):
#         """检查是否可以交易"""
#         if not self.last_trade_time:
#             return True
#         time_passed = (datetime.now() - self.last_trade_time).seconds
#         return time_passed > self.min_trade_interval
#     def execute_trade(self, action, price, upper, lower):
#         """执行交易"""
#         try:
#             if not self.can_trade():
#                 self.logger.info("交易间隔时间未到")
#                 return False
            
#             base_position = 100
#             max_capital_per_trade = 50000
            
#             total_cost = base_position * self.num_tranches * price
#             if total_cost > max_capital_per_trade:
#                 base_position = int(max_capital_per_trade / (price * self.num_tranches))
            
#             contract = Contract()
#             contract.symbol = self.symbol
#             contract.secType = "STK"
#             contract.exchange = "SMART"
#             contract.currency = "USD"
#             contract.primaryExchange = "NASDAQ"
            
#             total_shares = 0
#             total_trade_cost = 0
            
#             for i in range(self.num_tranches):
#                 df = self.get_market_data()
#                 df = get_donchian_channels(df, self.period)
#                 latest = df.iloc[-1]
#                 current_price = latest['Close']
#                 current_upper = latest['upper_channel']
#                 current_lower = latest['lower_channel']
                
#                 channel_position = self.is_near_channel(current_price, current_upper, current_lower)
                
#                 print(f"批次 {i+1} - 价格: ${current_price:.2f}, 上轨: ${current_upper:.2f}, 下轨: ${current_lower:.2f}")
#                 self.logger.info(f"批次 {i+1} - 价格: ${current_price:.2f}, 上轨: ${current_upper:.2f}, 下轨: ${current_lower:.2f}")
                
#                 if action == "SELL" and channel_position != "UPPER":
#                     print("价格已离开上轨区域，停止交易")
#                     self.logger.info("价格已离开上轨区域，停止交易")
#                     break
#                 elif action == "BUY" and channel_position != "LOWER":
#                     print("价格已离开下轨区域，停止交易")
#                     self.logger.info("价格已离开下轨区域，停止交易")
#                     break
                
#                 order = Order()
#                 order.action = action
#                 order.totalQuantity = base_position
#                 order.orderType = "MKT"
#                 order.eTradeOnly = False
#                 order.firmQuoteOnly = False
                
#                 self.bot.placeOrder(self.bot.order_id, contract, order)
#                 self.bot.order_id += 1
                
#                 # 更新持仓和盈亏信息
#                 if action == "BUY":
#                     total_shares += base_position
#                     trade_cost = base_position * current_price
#                     total_trade_cost += trade_cost
#                     self.current_position_size += base_position
#                     self.total_cost_basis += trade_cost
#                     print(f"买入: {base_position}股 @ ${current_price:.2f}")
#                 else:  # SELL
#                     total_shares -= base_position
#                     if self.current_position_size > 0:
#                         avg_cost = self.total_cost_basis / self.current_position_size
#                         realized_pnl = base_position * (current_price - avg_cost)
#                         self.realized_pnl += realized_pnl
#                         self.current_position_size -= base_position
#                         self.total_cost_basis = avg_cost * self.current_position_size
#                         print(f"卖出: {base_position}股 @ ${current_price:.2f}")
#                         print(f"实现盈亏: ${realized_pnl:.2f}")
                
#                 self.logger.info(f"执行{action}: {base_position}股 @ ${current_price:.2f}")
                
#                 if i < self.num_tranches - 1:
#                     time.sleep(20)
            
#             # 交易摘要
#             print(f"\n=== 交易摘要 ===")
#             print(f"交易方向: {action}")
#             print(f"交易股数: {abs(total_shares)}")
#             print(f"当前持仓: {self.current_position_size}")
#             if self.current_position_size > 0:
#                 print(f"平均成本: ${self.total_cost_basis/self.current_position_size:.2f}")
#             print(f"总实现盈亏: ${self.realized_pnl:.2f}")
            
#             self.logger.info(f"\n=== 交易摘要 ===")
#             self.logger.info(f"交易方向: {action}")
#             self.logger.info(f"交易股数: {abs(total_shares)}")
#             self.logger.info(f"当前持仓: {self.current_position_size}")
#             if self.current_position_size > 0:
#                 self.logger.info(f"平均成本: ${self.total_cost_basis/self.current_position_size:.2f}")
#             self.logger.info(f"总实现盈亏: ${self.realized_pnl:.2f}")
            
#             return True
            
#         except Exception as e:
#             self.logger.error(f"执行交易错误: {str(e)}")
#             return False

#     def run_strategy(self):
#         """运行策略"""
#         try:
#             self.bot.connect("127.0.0.1", 7497, 1)
#             self.bot_thread = threading.Thread(target=self.bot.run)
#             self.bot_thread.daemon = True
#             self.bot_thread.start()
#             time.sleep(1)
            
#             while True:
#                 try:
#                     df = self.get_market_data()
#                     df = get_donchian_channels(df, self.period)
#                     latest = df.iloc[-1]
#                     current_price = latest['Close']
#                     upper_channel = latest['upper_channel']
#                     lower_channel = latest['lower_channel']
                    
#                     channel_position = self.is_near_channel(
#                         current_price,
#                         upper_channel,
#                         lower_channel
#                     )
                    
#                     print(f"\n=== {datetime.now().strftime('%H:%M:%S')} 策略状态 ===")
#                     print(f"当前价格: ${current_price:.2f}")
#                     print(f"上轨: ${upper_channel:.2f}")
#                     print(f"下轨: ${lower_channel:.2f}")
#                     print(f"持仓数量: {self.current_position_size}")
#                     if self.current_position_size > 0:
#                         print(f"平均成本: ${self.total_cost_basis/self.current_position_size:.2f}")
#                         unrealized_pnl = self.current_position_size * (current_price - self.total_cost_basis/self.current_position_size)
#                         print(f"未实现盈亏: ${unrealized_pnl:.2f}")
#                     print(f"已实现盈亏: ${self.realized_pnl:.2f}")
                    
#                     # 修改交易逻辑
#                     if channel_position == "UPPER" and self.current_position_size > 0:
#                         print("\n接近上轨 - 准备卖出")
#                         if self.execute_trade("SELL", current_price, upper_channel, lower_channel):
#                             self.position = -1
#                             self.last_trade_time = datetime.now()
                            
#                     elif channel_position == "LOWER" and self.current_position_size == 0:
#                         print("\n接近下轨 - 准备买入")
#                         if self.execute_trade("BUY", current_price, upper_channel, lower_channel):
#                             self.position = 1
#                             self.last_trade_time = datetime.now()
                    
#                     time.sleep(5)
                    
#                 except Exception as e:
#                     self.logger.error(f"策略运行错误: {str(e)}")
#                     time.sleep(5)
#                     continue
                    
#         except KeyboardInterrupt:
#             self.logger.info("策略已停止")
#             self.bot.disconnect()
            
#         except Exception as e:
#             self.logger.error(f"严重错误: {str(e)}")
#             self.bot.disconnect()
  

# def get_donchian_channels(df, period=20):
#     """计算唐奇安通道"""
#     df['upper_channel'] = df['High'].rolling(window=period).max()
#     df['lower_channel'] = df['Low'].rolling(window=period).min()
#     df['middle_channel'] = (df['upper_channel'] + df['lower_channel']) / 2
#     return df
# def main():
#     # 策略参数设置
#     config = {
#         'symbol': 'TSLA',        # 股票代码
#         'capital': 50000,        # 总资金
#         'period': 20,           # 通道周期
#         'num_tranches': 3,      # 分批次数
#         'alert_threshold': 0.002 # 触发阈值 0.2%
#     }
    
#     # 初始化策略
#     strategy = DonchianStrategy(**config)
    
#     try:
#         print(f"\n=== 策略启动 ===")
#         print(f"股票: {config['symbol']}")
#         print(f"资金: ${config['capital']:,}")
#         print(f"通道周期: {config['period']}分钟")
#         print(f"分批次数: {config['num_tranches']}")
#         print(f"触发阈值: {config['alert_threshold']*100}%")
        
#         strategy.run_strategy()
        
#     except KeyboardInterrupt:
#         print("\n策略已手动停止")
#     except Exception as e:
#         print(f"\n策略运行错误: {str(e)}")
#     finally:
#         if hasattr(strategy, 'bot'):
#             strategy.bot.disconnect()

# if __name__ == "__main__":
#     main()



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
        self.market_depth = {}
        
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
            
    def marketDepth(self, reqId, position, operation, side, price, size):
        if reqId not in self.market_depth:
            self.market_depth[reqId] = {'bids': [], 'asks': []}
        
        depth_side = 'bids' if side == 0 else 'asks'
        
        if operation == 0:  # Insert
            self.market_depth[reqId][depth_side].append({'price': price, 'size': size})
        elif operation == 1:  # Update
            if position < len(self.market_depth[reqId][depth_side]):
                self.market_depth[reqId][depth_side][position] = {'price': price, 'size': size}
        elif operation == 2:  # Delete
            if position < len(self.market_depth[reqId][depth_side]):
                del self.market_depth[reqId][depth_side][position]

class ImprovedDonchianStrategy:
    def __init__(self, symbol, capital=100000, period=20, base_tranches=3, 
                 alert_threshold=0.004, max_capital_per_trade=50000):
        """
        改进的唐奇安通道策略
        
        Parameters:
        -----------
        symbol : str
            交易品种代码
        capital : float
            总资金
        period : int
            通道周期
        base_tranches : int
            基础分批数量
        alert_threshold : float
            触发阈值
        max_capital_per_trade : float
            单次交易最大资金
        """
        # 基础参数
        self.symbol = symbol
        self.capital = capital
        self.period = period
        self.base_tranches = base_tranches
        self.alert_threshold = alert_threshold
        self.max_capital_per_trade = max_capital_per_trade
        
        # 交易相关
        self.position = 0
        self.current_position_size = 0
        self.total_cost_basis = 0
        self.realized_pnl = 0
        self.last_trade_time = None
        self.min_trade_interval = 300
        
        # 风控参数
        self.baseline_volatility = 0.01  # 1%基准波动率
        self.max_allowed_volatility = 0.03  # 3%最大允许波动率
        self.max_allowed_spread = 0.002  # 0.2%最大允许价差
        self.min_required_volume = 1000  # 最小需求成交量
        
        # 初始化交易接口和日志
        self.bot = TradingBot()
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """设置日志系统"""
        logger = logging.getLogger(f'ImprovedDonchianStrategy_{self.symbol}')
        logger.setLevel(logging.INFO)
        fh = logging.FileHandler(f'improved_donchian_{self.symbol}.log')
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

    def calculate_volatility(self):
        """计算当前波动率"""
        try:
            df = self.get_market_data()
            returns = df['Close'].pct_change().dropna()
            return returns.std()
        except Exception as e:
            self.logger.error(f"计算波动率错误: {str(e)}")
            return self.baseline_volatility

    def get_volume_data(self):
        """获取成交量数据"""
        try:
            df = self.get_market_data()
            return {
                'current_volume': df['Volume'].iloc[-1],
                'avg_volume': df['Volume'].mean()
            }
        except Exception as e:
            self.logger.error(f"获取成交量数据错误: {str(e)}")
            return {'current_volume': 0, 'avg_volume': 0}

    def get_current_spread(self):
        """获取当前买卖价差"""
        try:
            depth = self.bot.market_depth.get(1, {'bids': [], 'asks': []})
            if depth['bids'] and depth['asks']:
                best_bid = max(level['price'] for level in depth['bids'])
                best_ask = min(level['price'] for level in depth['asks'])
                return (best_ask - best_bid) / best_bid
            return 0
        except Exception as e:
            self.logger.error(f"获取价差数据错误: {str(e)}")
            return 0

    def calculate_tranches(self, price, volatility):
        """计算动态分批参数"""
        try:
            # 根据波动率调整批次
            vol_multiplier = min(max(volatility / self.baseline_volatility, 0.5), 2)
            adjusted_tranches = int(self.base_tranches * vol_multiplier)
            
            # 计算每批次的位置大小
            total_value = self.current_position_size * price
            if total_value > self.max_capital_per_trade:
                position_size = int(self.max_capital_per_trade / (price * adjusted_tranches))
            else:
                position_size = int(self.current_position_size / adjusted_tranches)
                
            return adjusted_tranches, max(position_size, 1)
        except Exception as e:
            self.logger.error(f"计算分批参数错误: {str(e)}")
            return self.base_tranches, 100

    def calculate_interval(self, volume, avg_volume):
        """计算批次间隔时间"""
        try:
            base_interval = 20
            volume_ratio = volume / avg_volume if avg_volume > 0 else 1
            
            if volume_ratio < 0.5:
                return min(base_interval * 2, 60)
            elif volume_ratio > 2:
                return max(base_interval / 2, 5)
            
            return base_interval
        except Exception as e:
            self.logger.error(f"计算间隔时间错误: {str(e)}")
            return 20

    def analyze_market_depth(self):
        """分析市场深度"""
        try:
            depth = self.bot.market_depth.get(1, {'bids': [], 'asks': []})
            
            bid_volume = sum(level['size'] for level in depth['bids'])
            ask_volume = sum(level['size'] for level in depth['asks'])
            
            if bid_volume + ask_volume == 0:
                return {
                    'reduce_size': False,
                    'increase_intervals': False,
                    'use_limit_orders': False
                }
            
            imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume)
            
            return {
                'reduce_size': abs(imbalance) > 0.3,
                'increase_intervals': abs(imbalance) > 0.3,
                'use_limit_orders': abs(imbalance) > 0.3
            }
        except Exception as e:
            self.logger.error(f"分析市场深度错误: {str(e)}")
            return {
                'reduce_size': False,
                'increase_intervals': False,
                'use_limit_orders': False
            }

    def check_market_conditions(self):
        """检查市场条件"""
        try:
            # 检查波动率
            current_vol = self.calculate_volatility()
            if current_vol > self.max_allowed_volatility:
                self.logger.info(f"当前波动率({current_vol:.4f})过高")
                return False
            
            # 检查价差
            current_spread = self.get_current_spread()
            if current_spread > self.max_allowed_spread:
                self.logger.info(f"当前价差({current_spread:.4f})过大")
                return False
            
            # 检查成交量
            volume_data = self.get_volume_data()
            if volume_data['current_volume'] < self.min_required_volume:
                self.logger.info(f"当前成交量({volume_data['current_volume']})过低")
                return False
            
            return True
        except Exception as e:
            self.logger.error(f"检查市场条件错误: {str(e)}")
            return False

    def execute_tranche(self, action, position_size, price_threshold):
        """执行单个批次交易"""
        try:
            contract = Contract()
            contract.symbol = self.symbol
            contract.secType = "STK"
            contract.exchange = "SMART"
            contract.currency = "USD"
            contract.primaryExchange = "NASDAQ"
            
            order = Order()
            order.action = action
            
            # 根据价格偏离度调整交易量
            current_price = self.bot.current_price or price_threshold
            price_deviation = abs(current_price - price_threshold) / price_threshold
            
            if price_deviation > 0.001:
                adjusted_position = int(position_size * (1 - price_deviation * 10))
                order.totalQuantity = max(adjusted_position, 1)
            else:
                order.totalQuantity = position_size
            
            # 根据市场深度选择订单类型
            market_state = self.analyze_market_depth()
            if market_state['use_limit_orders']:
                order.orderType = "LMT"
                order.lmtPrice = current_price * (0.9999 if action == "BUY" else 1.0001)
            else:
                order.orderType = "MKT"
            
            self.bot.placeOrder(self.bot.order_id, contract, order)
            self.bot.order_id += 1
            
            return order.totalQuantity
            
        except Exception as e:
            self.logger.error(f"执行批次交易错误: {str(e)}")
            return 0

    def update_position_info(self, action, filled_quantity, price):
        """更新持仓信息"""
        try:
            if action == "BUY":
                self.current_position_size += filled_quantity
                self.total_cost_basis += filled_quantity * price
            else:  # SELL
                if self.current_position_size > 0:
                    avg_cost = self.total_cost_basis / self.current_position_size
                    realized_pnl = filled_quantity * (price - avg_cost)
                    self.realized_pnl += realized_pnl
                    self.current_position_size -= filled_quantity
                    if self.current_position_size > 0:
                        self.total_cost_basis = avg_cost * self.current_position_size
                    else:
                        self.total_cost_basis = 0
        except Exception as e:
            self.logger.error(f"更新持仓信息错误: {str(e)}")

    def execute_trade(self, action, price, upper, lower):
        """执行完整交易"""
        try:
            if not self.can_trade():
                self.logger.info("交易间隔时间未到")
                return False
            
            # 计算波动率和分批参数
            volatility = self.calculate_volatility()
            num_tranches, position_size = self.calculate_tranches(price, volatility)
            
            # 获取市场状态
            market_state = self.analyze_market_depth()
            volume_data = self.get_volume_data()
            
            total_filled = 0
            
            # 执行分批交易
            for i in range(num_tranches):
                # 检查市场条件
                if not self.check_market_conditions():
                    self.logger.info("市场条件不适合继续交易")
                    break
                
                # 计算本批次间隔
                interval = self.calculate_interval(
                    volume_data['current_volume'],
                    volume_data['avg_volume']
                )
                
                # 根据市场深度调整仓位
                current_position = (
                    int(position_size * 0.7)
                    if market_state['reduce_size']
                    else position_size
                )
                
                # 执行交易
                filled = self.execute_tranche(
                    action,
                    current_position,
                    price
                )
                
                if filled:
                    total_filled += filled
                    self.update_position_info(action, filled, price)
                    print(f"完成第 {i+1}/{num_tranches} 批交易: {filled}股 @ ${price:.2f}")
                
                # 等待下一批次
                if i < num_tranches - 1:
                    adjusted_interval = (
                        interval * 1.5
                        if market_state['increase_intervals']
                        else interval
                    )
                    time.sleep(adjusted_interval)
            
            if total_filled > 0:
                self.last_trade_time = datetime.now()
                print(f"\n=== 交易摘要 ===")
                print(f"交易方向: {action}")
                print(f"总成交: {total_filled}股")
                print(f"当前持仓: {self.current_position_size}")
                if self.current_position_size > 0:
                    print(f"平均成本: ${self.total_cost_basis/self.current_position_size:.2f}")
                print(f"总实现盈亏: ${self.realized_pnl:.2f}")
                
            return total_filled > 0
            
        except Exception as e:
            self.logger.error(f"执行交易错误: {str(e)}")
            return False

    def can_trade(self):
        """检查是否可以交易"""
        if not self.last_trade_time:
            return True
        time_passed = (datetime.now() - self.last_trade_time).seconds
        return time_passed > self.min_trade_interval

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

    def get_donchian_channels(self, df):
        """计算唐奇安通道"""
        try:
            df = df.copy()
            df['upper_channel'] = df['High'].rolling(window=self.period).max()
            df['lower_channel'] = df['Low'].rolling(window=self.period).min()
            df['middle_channel'] = (df['upper_channel'] + df['lower_channel']) / 2
            return df
        except Exception as e:
            self.logger.error(f"计算通道错误: {str(e)}")
            return df

    def run_strategy(self):
        """运行策略"""
        try:
            self.logger.info("策略启动")
            print("\n=== 策略启动 ===")
            print(f"交易品种: {self.symbol}")
            print(f"初始资金: ${self.capital:,}")
            print(f"通道周期: {self.period}分钟")
            
            # 连接交易接口
            self.bot.connect("127.0.0.1", 7497, 1)
            
            # 启动交易线程
            api_thread = threading.Thread(target=self.bot.run)
            api_thread.daemon = True
            api_thread.start()
            
            # 等待连接
            time.sleep(1)
            
            while True:
                try:
                    # 获取市场数据
                    df = self.get_market_data()
                    df = self.get_donchian_channels(df)
                    latest = df.iloc[-1]
                    
                    # 获取当前价格和通道值
                    current_price = latest['Close']
                    upper_channel = latest['upper_channel']
                    lower_channel = latest['lower_channel']
                    
                    # 检查价格位置
                    channel_position = self.is_near_channel(
                        current_price,
                        upper_channel,
                        lower_channel
                    )
                    
                    # 输出状态信息
                    print(f"\n=== {datetime.now().strftime('%H:%M:%S')} 策略状态 ===")
                    print(f"当前价格: ${current_price:.2f}")
                    print(f"上轨: ${upper_channel:.2f}")
                    print(f"下轨: ${lower_channel:.2f}")
                    print(f"持仓数量: {self.current_position_size}")
                    
                    if self.current_position_size > 0:
                        avg_cost = self.total_cost_basis / self.current_position_size
                        print(f"平均成本: ${avg_cost:.2f}")
                        unrealized_pnl = self.current_position_size * (current_price - avg_cost)
                        print(f"未实现盈亏: ${unrealized_pnl:.2f}")
                    print(f"已实现盈亏: ${self.realized_pnl:.2f}")
                    
                    # 交易逻辑
                    if channel_position == "UPPER" and self.current_position_size > 0:
                        print("\n接近上轨 - 准备卖出")
                        if self.execute_trade("SELL", current_price, upper_channel, lower_channel):
                            self.position = -1
                            
                    elif channel_position == "LOWER" and self.current_position_size == 0:
                        print("\n接近下轨 - 准备买入")
                        if self.execute_trade("BUY", current_price, upper_channel, lower_channel):
                            self.position = 1
                    
                    # 策略监控
                    volatility = self.calculate_volatility()
                    print(f"\n市场状态:")
                    print(f"当前波动率: {volatility:.4f}")
                    print(f"当前价差: {self.get_current_spread():.4f}")
                    
                    volume_data = self.get_volume_data()
                    print(f"当前成交量: {volume_data['current_volume']}")
                    print(f"平均成交量: {volume_data['avg_volume']:.0f}")
                    
                    time.sleep(5)
                    
                except KeyboardInterrupt:
                    print("\n策略手动停止")
                    self.logger.info("策略手动停止")
                    break
                    
                except Exception as e:
                    self.logger.error(f"策略运行错误: {str(e)}")
                    time.sleep(5)
                    continue
                    
        except Exception as e:
            self.logger.error(f"严重错误: {str(e)}")
        finally:
            if hasattr(self, 'bot'):
                self.bot.disconnect()

def main():
    # 策略参数设置
    config = {
        'symbol': 'TSLA',        # 交易品种
        'capital': 100000,       # 总资金
        'period': 20,           # 通道周期
        'base_tranches': 3,     # 基础分批数量
        'alert_threshold': 0.002, # 触发阈值 0.2%
        'max_capital_per_trade': 50000  # 单次交易最大资金
    }
    
    # 初始化策略
    strategy = ImprovedDonchianStrategy(**config)
    
    try:
        strategy.run_strategy()
    except KeyboardInterrupt:
        print("\n程序手动停止")
    except Exception as e:
        print(f"\n程序运行错误: {str(e)}")
    finally:
        if hasattr(strategy, 'bot'):
            strategy.bot.disconnect()

if __name__ == "__main__":
    main()