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
                     f" ({data['price_change']:+.2f}%)\n"
        
        if alerts:
            report += f"\n🚨 <b>تعداد هشدارها: {len(alerts)}</b>"
        
        return report
    
    def console_display(self, analysis: Dict):
        """نمایش وضعیت در کنسول"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        for symbol, data in analysis.items():
            print(f"[{timestamp}] {symbol}:  | "
                  f"حجم: {data['volume']:,.0f} | "
                  f"تغییر: {data['price_change']:+.2f}%")
