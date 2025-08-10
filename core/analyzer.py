import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta
import statistics

class SmartAnalyzer:
    """تحلیل‌گر هوشمند بازار"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.historical_data = {}
        self.logger = logging.getLogger(__name__)
    
    async def analyze_market(self, market_data: Dict) -> Dict:
        """تحلیل کامل بازار"""
        analysis = {}
        
        for symbol, data in market_data.items():
            try:
                # ذخیره داده‌های تاریخی
                self.store_historical_data(symbol, data)
                
                # محاسبه شاخص‌های تحلیل
                analysis[symbol] = {
                    'price': data['price'],
                    'volume': data['volume'],
                    'price_change': data['price_change_percent'],
                    'volume_change': self.calculate_volume_change(symbol, data['volume']),
                    'volatility': self.calculate_volatility(symbol),
                    'trend': self.detect_trend(symbol),
                    'momentum': self.calculate_momentum(symbol),
                    'support_resistance': self.find_support_resistance(symbol),
                    'timestamp': datetime.now()
                }
                
            except Exception as e:
                self.logger.error(f"خطا در تحلیل {symbol}: {e}")
        
        return analysis
    
    def store_historical_data(self, symbol: str, data: Dict):
        """ذخیره داده‌های تاریخی"""
        if symbol not in self.historical_data:
            self.historical_data[symbol] = []
        
        self.historical_data[symbol].append({
            'timestamp': datetime.now(),
            'price': data['price'],
            'volume': data['volume'],
            'price_change': data['price_change_percent']
        })
        
        # نگهداری فقط 1000 رکورد آخر
        if len(self.historical_data[symbol]) > 1000:
            self.historical_data[symbol] = self.historical_data[symbol][-1000:]
    
    def calculate_volume_change(self, symbol: str, current_volume: float) -> float:
        """محاسبه درصد تغییر حجم"""
        if symbol not in self.historical_data or len(self.historical_data[symbol]) < 2:
            return 0.0
        
        # محاسبه میانگین حجم در 24 ساعت گذشته
        recent_data = self.historical_data[symbol][-1440:]  # 24 ساعت * 60 دقیقه
        if not recent_data:
            return 0.0
        
        avg_volume = statistics.mean([d['volume'] for d in recent_data])
        if avg_volume == 0:
            return 0.0
        
        return ((current_volume - avg_volume) / avg_volume) * 100
    
    def calculate_volatility(self, symbol: str, period: int = 20) -> float:
        """محاسبه نوسانات"""
        if symbol not in self.historical_data or len(self.historical_data[symbol]) < period:
            return 0.0
        
        prices = [d['price'] for d in self.historical_data[symbol][-period:]]
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        
        return statistics.stdev(returns) * 100 if returns else 0.0
    
    def detect_trend(self, symbol: str, period: int = 20) -> str:
        """تشخیص روند"""
        if symbol not in self.historical_data or len(self.historical_data[symbol]) < period:
            return "نامشخص"
        
        prices = [d['price'] for d in self.historical_data[symbol][-period:]]
        
        # محاسبه خط روند ساده
        x = list(range(len(prices)))
        slope = self.calculate_slope(x, prices)
        
        if slope > 0.01:
            return "صعودی"
        elif slope < -0.01:
            return "نزولی"
        else:
            return "خنثی"
    
    def calculate_slope(self, x: List, y: List) -> float:
        """محاسبه شیب خط روند"""
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(xi ** 2 for xi in x)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        return slope
    
    def calculate_momentum(self, symbol: str, period: int = 10) -> float:
        """محاسبه مومنتوم"""
        if symbol not in self.historical_data or len(self.historical_data[symbol]) < period + 1:
            return 0.0
        
        prices = [d['price'] for d in self.historical_data[symbol]]
        current_price = prices[-1]
        past_price = prices[-(period + 1)]
        
        return ((current_price - past_price) / past_price) * 100
    
    def find_support_resistance(self, symbol: str) -> Dict:
        """یافتن سطوح حمایت و مقاومت"""
        if symbol not in self.historical_data or len(self.historical_data[symbol]) < 50:
            return {'support': 0, 'resistance': 0}
        
        prices = [d['price'] for d in self.historical_data[symbol][-100:]]
        
        # یافتن سطوح با استفاده از پیوت پوینت‌ها
        pivot_high = max(prices[-20:])
        pivot_low = min(prices[-20:])
        
        return {
            'support': pivot_low,
            'resistance': pivot_high
        }
