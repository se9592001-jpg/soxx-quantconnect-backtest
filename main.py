# region imports
from AlgorithmImports import *

class BasicTemplateAlgorithm(QCAlgorithm):

    def initialize(self):
        fast_period = self.get_parameter("fast_period", 20)
        slow_period = self.get_parameter("slow_period", 60)
        
        self.set_start_date(2021, 8, 2)
        self.set_end_date(2026, 7, 30)
        self.set_cash(100000)
        self.set_benchmark("SOXX")
        
        self.soxx = self.add_equity("SOXX", Resolution.DAILY).symbol
        self.sma_fast = self.sma(self.soxx, fast_period, Resolution.DAILY)
        self.sma_slow = self.sma(self.soxx, slow_period, Resolution.DAILY)
        self.set_warm_up(slow_period)
        self.is_holding = None
        self.initial_soxx_price = None
    
    def on_data(self, data):
        if self.initial_soxx_price is None and self.securities[self.soxx].price > 0:
            self.initial_soxx_price = self.securities[self.soxx].price
            self.log(f"Initial SOXX price set on {self.time}: {self.initial_soxx_price}")

        if self.is_warming_up:
            return 
        if not (self.sma_fast.is_ready and self.sma_slow.is_ready):
            return
        
        self.price_fast = self.sma_fast.current.value
        self.price_slow = self.sma_slow.current.value
        
        if (self.is_holding == None) and ( self.price_slow < self.price_fast): # Golden Cross
            self.is_holding = True
            self.set_holdings(self.soxx, 1)
            self.log(f"Golden Cross on {self.time} with SMA 60:{self.price_slow}, SMA 20:{self.price_fast}")

        if (self.is_holding == True) and (self.price_slow > self.price_fast): # Dead Cross
            self.is_holding = None
            self.liquidate(self.soxx)
            self.log(f"Dead Cross on {self.time} with SMA 60:{self.price_slow}, SMA 20:{self.price_fast}")

        if self.initial_soxx_price is not None:
            current_price = self.securities[self.soxx].price
            baseline_equity = 100000 * (current_price / self.initial_soxx_price)
            self.plot("Baseline VS Strategy", "Baseline (Buy & Hold)", baseline_equity)
            self.plot("Baseline VS Strategy", "Strategy Equity", self.portfolio.total_portfolio_value)





