# ایجاد ساختار پوشه‌بندی
$basePath = "C:\Users\Raman\Desktop\WhalePulse-Pro"
New-Item -ItemType Directory -Path $basePath -Force | Out-Null
New-Item -ItemType Directory -Path "$basePath\core" -Force | Out-Null
New-Item -ItemType Directory -Path "$basePath\plugins" -Force | Out-Null
New-Item -ItemType Directory -Path "$basePath\strategies" -Force | Out-Null
New-Item -ItemType Directory -Path "$basePath\config" -Force | Out-Null
New-Item -ItemType Directory -Path "$basePath\logs" -Force | Out-Null
New-Item -ItemType Directory -Path "$basePath\data" -Force | Out-Null

# ایجاد فایل اصلی اجرایی
$mainScript = @"
import asyncio
import yaml
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# اضافه کردن مسیر پوشه‌ها به sys.path
sys.path.append(str(Path(__file__).parent))

from core.monitor import WhaleMonitor
from core.analyzer import SmartAnalyzer
from core.notifier import NotificationManager
from plugins.binance import BinancePlugin
from plugins.telegram import TelegramPlugin

def setup_logging():
    """تنظیمات لاگینگ پیشرفته"""
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / f"whalepulse_{datetime.now().strftime('%Y%m%d')}.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

async def main():
    """تابع اصلی اجرای برنامه"""
    logger = setup_logging()
    logger.info("🚀 WhalePulse Pro در حال شروع...")
    
    try:
        # بارگذاری تنظیمات
        config_path = Path(__file__).parent / "config" / "settings.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        logger.info("⚙️ تنظیمات بارگذاری شد")
        
        # راه‌اندازی کامپوننت‌ها
        analyzer = SmartAnalyzer(config)
        notifier = NotificationManager(config)
        
        monitor = WhaleMonitor(
            config=config,
            analyzer=analyzer,
            notifier=notifier,
            plugins=[
                BinancePlugin(config),
                TelegramPlugin(config)
            ]
        )
        
        logger.info("🔧 کامپوننت‌ها راه‌اندازی شدند")
        
        # اجرای مانیتور
        await monitor.run()
        
    except Exception as e:
        logger.error(f"❌ خطای بحرانی: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
"@

Set-Content -Path "$basePath\main.py" -Value $mainScript -Encoding UTF8

# ایجاد فایل مانیتور
$monitorScript = @"
import asyncio
import time
import logging
from datetime import datetime
from typing import Dict, List, Any

class WhaleMonitor:
    """کلاس اصلی نظارت بر بازار"""
    
    def __init__(self, config: Dict, analyzer, notifier, plugins: List):
        self.config = config
        self.analyzer = analyzer
        self.notifier = notifier
        self.plugins = plugins
        self.running = True
        self.last_status_report = time.time()
        self.alert_cooldown = {}
        
    async def run(self):
        """اجرای اصلی مانیتور"""
        logger = logging.getLogger(__name__)
        
        logger.info("🐋 WhalePulse Pro شروع به کار کرد")
        logger.info("🔄 بررسی هر ثانیه - گزارش هر 15 دقیقه")
        
        # ارسال پیام شروع
        start_message = f"🚀 <b>WhalePulse Pro فعال شد!</b>\n" \
                      f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" \
                      f"🔄 بررسی هر ثانیه - گزارش هر 15 دقیقه"
        
        await self.notifier.send_message(start_message)
        
        while self.running:
            try:
                await self.check_market()
                
                # انتظار 1 ثانیه
                for _ in range(10):
                    if not self.running:
                        break
                    await asyncio.sleep(0.1)
                    
            except KeyboardInterrupt:
                logger.info("🛑 برنامه متوقف شد")
                self.running = False
                
                # ارسال پیام توقف
                stop_message = f"🛑 <b>WhalePulse Pro متوقف شد</b>\n" \
                               f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                await self.notifier.send_message(stop_message)
                break
                
            except Exception as e:
                logger.error(f"❌ خطا: {e}")
                await asyncio.sleep(1)
    
    async def check_market(self):
        """بررسی وضعیت بازار"""
        current_time = time.time()
        
        # دریافت داده‌ها از پلاگین‌ها
        market_data = {}
        for plugin in self.plugins:
            if hasattr(plugin, 'get_market_data'):
                data = await plugin.get_market_data()
                market_data.update(data)
        
        # تحلیل داده‌ها
        analysis = await self.analyzer.analyze_market(market_data)
        
        # بررسی هشدارها
        alerts = []
        for symbol, data in analysis.items():
            if data['volume_change'] > self.config['strategies']['volume_spike']['threshold']:
                alerts.append(self.create_alert(symbol, data))
        
        # ارسال گزارش وضعیت هر 15 دقیقه
        if current_time - self.last_status_report >= 900:  # 15 دقیقه
            status_report = self.create_status_report(analysis, alerts)
            await self.notifier.send_message(status_report)
            self.last_status_report = current_time
        
        # ارسال هشدارها
        for alert in alerts:
            cooldown_key = f"{alert['symbol']}_{int(current_time / 300)}"  # 5 دقیقه
            if cooldown_key not in self.alert_cooldown:
                self.alert_cooldown[cooldown_key] = True
                await self.notifier.send_message(alert['message'])
        
        # نمایش وضعیت در کنسول
        self.console_display(analysis)
    
    def create_alert(self, symbol: str, data: Dict) -> Dict:
        """ایجاد پیام هشدار"""
        return {
            'symbol': symbol,
            'message': f"""🚨 <b>هشدار فعالیت نهنگ!</b>
📊 <b>{symbol}</b>
💰 قیمت: <code>{data['price']:.4f}</code>
📈 تغییر: <code>{data['price_change']:+.2f}%</code>
🐋 حجم: <code>{data['volume']:,.0f}</code>
⚡ افزایش: <code>{data['volume_change']:+.2f}%</code>
⏰ {datetime.now().strftime('%H:%M:%S')}"""
        }
    
    def create_status_report(self, analysis: Dict, alerts: List) -> str:
        """ایجاد گزارش وضعیت"""
        report = f"📊 <b>گزارش وضعیت WhalePulse Pro</b>\n" \
                f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for symbol, data in analysis.items():
            report += f"{data.get('emoji', '📈')} <b>{symbol}</b>: " \
                     f"${data['price']:.4f} ({data['price_change']:+.2f}%)\n"
        
        if alerts:
            report += f"\n🚨 <b>تعداد هشدارها: {len(alerts)}</b>"
        
        return report
    
    def console_display(self, analysis: Dict):
        """نمایش وضعیت در کنسول"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        for symbol, data in analysis.items():
            print(f"[{timestamp}] {symbol}: ${data['price']:.4f} | "
                  f"حجم: {data['volume']:,.0f} | "
                  f"تغییر: {data['price_change']:+.2f}%")
"@

Set-Content -Path "$basePath\core\monitor.py" -Value $monitorScript -Encoding UTF8

# ایجاد فایل تحلیل‌گر
$analyzerScript = @"
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
"@

Set-Content -Path "$basePath\core\analyzer.py" -Value $analyzerScript -Encoding UTF8

# ایجاد فایل نوتیفایر
$notifierScript = @"
import asyncio
import logging
from typing import Dict, Any, List
from abc import ABC, abstractmethod

class NotificationManager:
    """مدیر اطلاع‌رسانی"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.notifiers = []
        
        # راه‌اندازی نوتیفایرها بر اساس تنظیمات
        if config['notifications']['telegram']['enabled']:
            from plugins.telegram import TelegramNotifier
            self.notifiers.append(TelegramNotifier(config['notifications']['telegram']))
    
    async def send_message(self, message: str):
        """ارسال پیام به تمام کانال‌های اطلاع‌رسانی"""
        tasks = []
        for notifier in self.notifiers:
            tasks.append(notifier.send_message(message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def send_alert(self, alert: Dict):
        """ارسال هشدار"""
        message = self.format_alert_message(alert)
        await self.send_message(message)
    
    def format_alert_message(self, alert: Dict) -> str:
        """قالب‌بندی پیام هشدار"""
        return f"🚨 <b>هشدار WhalePulse Pro</b>\n\n{alert['message']}"

class BaseNotifier(ABC):
    """کلاس پایه نوتیفایر"""
    
    @abstractmethod
    async def send_message(self, message: str):
        pass
"@

Set-Content -Path "$basePath\core\notifier.py" -Value $notifierScript -Encoding UTF8

# ایجاد پلاگین بایننس
$binancePlugin = @"
import asyncio
import aiohttp
import logging
from typing import Dict, Any
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
            symbols = self.config['symbols']
            market_data = {}
            
            async with self.session.get(f"{self.base_url}/ticker/24hr") as response:
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
            
            async with self.session.get(f"{self.base_url}/klines", params=params) as response:
                if response.status == 200:
                    return await response.json()
                return []
                
        except Exception as e:
            self.logger.error(f"خطا در دریافت کندل‌ها: {e}")
            return []
"@

Set-Content -Path "$basePath\plugins\binance.py" -Value $binancePlugin -Encoding UTF8

# ایجاد پلاگین تلگرام
$telegramPlugin = @"
import asyncio
import logging
from typing import Dict, Any
from telegram import Bot
from telegram.constants import ParseMode

class TelegramNotifier:
    """نوتیفایر تلگرام"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.bot = Bot(token=config['token'])
        self.chat_id = config['chat_id']
    
    async def send_message(self, message: str):
        """ارسال پیام به تلگرام"""
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            self.logger.info("پیام به تلگرام ارسال شد")
            
        except Exception as e:
            self.logger.error(f"خطا در ارسال پیام به تلگرام: {e}")
    
    async def send_alert(self, alert: Dict):
        """ارسال هشدار"""
        message = f"🚨 <b>هشدار WhalePulse Pro</b>\n\n{alert['message']}"
        await self.send_message(message)
"@

Set-Content -Path "$basePath\plugins\telegram.py" -Value $telegramPlugin -Encoding UTF8

# ایجاد فایل تنظیمات
$settingsYaml = @"
# تنظیمات WhalePulse Pro

# تنظیمات مانیتورینگ
monitor:
  check_interval: 1  # ثانیه
  report_interval: 900  # 15 دقیقه
  max_historical_records: 1000

# تنظیمات استراتژی‌ها
strategies:
  volume_spike:
    enabled: true
    threshold: 50  # درصد
    cooldown: 300  # ثانیه
  
  whale_alert:
    enabled: true
    min_volume: 1000000
    price_change_threshold: 2.0

# تنظیمات نوتیفیکیشن‌ها
notifications:
  telegram:
    enabled: true
    token: "8136421090:AAFrb8RI6BQ2tH49YXX_5S32_W0yWfT04Cg"
    chat_id: "570096331"
  
  discord:
    enabled: false
    webhook: ""

# تنظیمات ارزها
symbols:
  - "BTCUSDT"
  - "ETHUSDT"
  - "BNBUSDT"
  - "ADAUSDT"
  - "SOLUSDT"

# تنظیمات تحلیل
analysis:
  volatility_period: 20
  trend_period: 20
  momentum_period: 10
  support_resistance_period: 50

# تنظیمات لاگینگ
logging:
  level: INFO
  max_file_size: 10485760  # 10MB
  backup_count: 5
"@

Set-Content -Path "$basePath\config\settings.yaml" -Value $settingsYaml -Encoding UTF8

# ایجاد فایل اجرایی
$runnerScript = @"
@echo off
cd /d "%~dp0"
echo 🚀 WhalePulse Pro در حال راه‌اندازی...
python main.py
pause
"@

Set-Content -Path "$basePath\run.bat" -Value $runnerScript -Encoding ASCII

# ایجاد فایل نصب پکیج‌ها
$requirementsTxt = @"
aiohttp>=3.8.0
pyyaml>=6.0
python-telegram-bot>=20.0
requests>=2.28.0
asyncio
logging
"@

Set-Content -Path "$basePath\requirements.txt" -Value $requirementsTxt -Encoding UTF8

# ایجاد فایل README
$readmeContent = @"
# WhalePulse Pro 🐋

سیستم حرفه‌ای نظارت بر حجم معاملات و هشدار نهنگ‌ها

## ویژگی‌ها

- ✅ نظارت لحظه‌ای بر حجم معاملات
- ✅ تحلیل هوشمند بازار با الگوریتم‌های پیشرفته
- ✅ هشدارهای تلگرام در زمان واقعی
- ✅ گزارش‌های دوره‌ای وضعیت بازار
- ✅ ذخیره داده‌های تاریخی برای تحلیل
- ✅ رابط کاربری ساده و حرفه‌ای

## نصب و راه‌اندازی

1. نصب پکیج‌های مورد نیاز:
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

2. اجرای برنامه:
   \`\`\`bash
   run.bat
   \`\`\`

## ساختار پروژه

\`\`\`
WhalePulse-Pro/
├── core/           # هسته اصلی برنامه
├── plugins/        # پلاگین‌ها
├── strategies/     # استراتژی‌ها
├── config/         # تنظیمات
├── logs/           # لاگ‌ها
├── data/           # داده‌ها
├── main.py         # فایل اصلی
├── run.bat         # فایل اجرایی
└── requirements.txt # پکیج‌ها
\`\`\`

## تنظیمات

فایل \`config/settings.yaml\` را برای تنظیم پارامترها ویرایش کنید.

## پشتیبانی

برای گزارش مشکلات و پیشنهادات، با ما در تماس باشید.
"@

Set-Content -Path "$basePath\README.md" -Value $readmeContent -Encoding UTF8

# ایجاد اسکریپت نصب
$installScript = @"
@echo off
echo 🚀 در حال نصب WhalePulse Pro...
echo.

# نصب پکیج‌ها
echo 📦 نصب پکیج‌های مورد نیاز...
pip install -r requirements.txt

echo.
echo ✅ نصب با موفقیت انجام شد!
echo.
echo 🎯 برای اجرای برنامه، فایل run.bat را اجرا کنید.
echo.
pause
"@

Set-Content -Path "$basePath\install.bat" -Value $installScript -Encoding ASCII

Write-Host "✅ WhalePulse Pro با موفقیت ایجاد شد!"
Write-Host "📁 مسیر: $basePath"
Write-Host ""
Write-Host "🚀 مراحل نصب:"
Write-Host "1. به مسیر بالا بروید"
Write-Host "2. فایل install.bat را اجرا کنید"
Write-Host "3. پس از نصب، فایل run.bat را اجرا کنید"
Write-Host ""
Write-Host "📚 برای اطلاعات بیشتر، فایل README.md را مطالعه کنید"