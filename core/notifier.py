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
