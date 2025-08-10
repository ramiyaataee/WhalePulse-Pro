import asyncio
import aiohttp
import logging
from typing import Dict, Any, List
from datetime import datetime

class BinancePlugin:
    """پلاگین اتصال به بایننس"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://api.binance.com/api/v3"
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_market_data(self) -> Dict[str, Any]:
        """دریافت داده‌های بازار از بایننس"""
        try:
            symbols = self.config.get('symbols', ['BTCUSDT'])
            market_data = {}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/ticker/24hr") as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for item in data:
                            if item['symbol'] in symbols:
                                market_data[item['symbol']] = {
                                    'price': float(item['lastPrice']),
                                    'volume': float(item['volume']),
                                    'price_change_percent': float(item['priceChangePercent']),
                                    'timestamp': datetime.now()
                                }
            
            return market_data
            
        except Exception as e:
            self.logger.error(f"خطا در دریافت داده‌ها از بایننس: {e}")
            return {}
    
    async def get_klines(self, symbol: str, interval: str = "1m", limit: int = 100) -> List:
        """دریافت داده‌های کندلی"""
        try:
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/klines", params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    return []
                
        except Exception as e:
            self.logger.error(f"خطا در دریافت کندل‌ها: {e}")
            return []