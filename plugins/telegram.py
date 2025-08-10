import asyncio
import logging
from typing import Dict, Any
try:
    from telegram import Bot
    from telegram.constants import ParseMode
except ImportError:
    Bot = None
    ParseMode = None

class TelegramPlugin:
    """پلاگین تلگرام"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        if Bot is None:
            self.logger.error("telegram library not installed")
            self.bot = None
        else:
            self.bot = Bot(token=config['token'])
        self.chat_id = config['chat_id']
    
    async def get_market_data(self):
        """دریافت داده‌های بازار (برای سازگاری)"""
        return {}
    
    async def send_message(self, message: str):
        """ارسال پیام به تلگرام"""
        if self.bot is None:
            self.logger.error("Telegram bot not initialized")
            return
            
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.HTML if ParseMode else None,
                disable_web_page_preview=True
            )
            self.logger.info("پیام به تلگرام ارسال شد")
            
        except Exception as e:
            self.logger.error(f"خطا در ارسال پیام به تلگرام: {e}")

class TelegramNotifier:
    """نوتیفایر تلگرام"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        if Bot is None:
            self.logger.error("telegram library not installed")
            self.bot = None
        else:
            self.bot = Bot(token=config['token'])
        self.chat_id = config['chat_id']
    
    async def send_message(self, message: str):
        """ارسال پیام به تلگرام"""
        if self.bot is None:
            self.logger.error("Telegram bot not initialized")
            return
            
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.HTML if ParseMode else None,
                disable_web_page_preview=True
            )
            self.logger.info("پیام به تلگرام ارسال شد")
            
        except Exception as e:
            self.logger.error(f"خطا در ارسال پیام به تلگرام: {e}")
    
    async def send_alert(self, alert: Dict):
        """ارسال هشدار"""
        message = f"🚨 <b>هشدار WhalePulse Pro</b>\n\n{alert['message']}"
        await self.send_message(message)