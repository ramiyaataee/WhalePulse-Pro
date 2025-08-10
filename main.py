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
                TelegramPlugin(config['notifications']['telegram'])
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