import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def generate_chart(symbol, data, save_path):
    """تولید چارت تحلیلی"""
    try:
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
        fig.suptitle(f'تحلیل تکنیکال {symbol}', fontsize=16, fontweight='bold')
        
        # استخراج داده‌ها
        times = [datetime.fromisoformat(d['timestamp'].replace('Z', '+00:00')) for d in data]
        prices = [d['price'] for d in data]
        volumes = [d['volume'] for d in data]
        
        # نمودار قیمت و حجم
        ax1.plot(times, prices, 'b-', linewidth=2, label='Price')
        ax1.set_ylabel('Price (USDT)', fontsize=10)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # نمودار حجم
        ax2.bar(times, volumes, color='green', alpha=0.7, label='Volume')
        ax2.set_ylabel('Volume', fontsize=10)
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        # نمودار RSI
        if len(data) > 14:
            rsi_values = calculate_rsi(prices)
            rsi_times = times[14:]
            ax3.plot(rsi_times, rsi_values, 'r-', linewidth=2, label='RSI')
            ax3.axhline(y=70, color='r', linestyle='--', alpha=0.5)
            ax3.axhline(y=30, color='g', linestyle='--', alpha=0.5)
            ax3.set_ylabel('RSI', fontsize=10)
            ax3.set_ylim(0, 100)
            ax3.grid(True, alpha=0.3)
            ax3.legend()
        
        # تنظیمات نمایش
        for ax in [ax1, ax2, ax3]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return True
    except Exception as e:
        print(f"Error generating chart: {e}")
        return False

def calculate_rsi(prices, period=14):
    """محاسبه RSI"""
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum()/period
    down = -seed[seed < 0].sum()/period
    rs = up/down
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - (100./(1.+rs))
    
    for i in range(period, len(prices)):
        delta = deltas[i-1]
        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta
            
        up = (up*(period-1) + upval)/period
        down = (down*(period-1) + downval)/period
        rs = up/down
        rsi[i] = 100. - (100./(1.+rs))
    
    return rsi[period:]

def create_sample_data(symbol="BTCUSDT"):
    """ایجاد داده‌های نمونه برای تست"""
    data = []
    base_price = 114000
    base_time = datetime.now() - timedelta(hours=24)
    
    for i in range(100):
        time_point = base_time + timedelta(minutes=i*15)
        price = base_price + np.random.normal(0, 500)
        volume = np.random.randint(8000, 12000)
        
        data.append({
            'timestamp': time_point.isoformat(),
            'price': price,
            'volume': volume
        })
    
    return data

if __name__ == "__main__":
    # ایجاد پوشه charts اگر وجود نداره
    if not os.path.exists('charts'):
        os.makedirs('charts')
    
    # تولید چارت برای BTCUSDT
    symbol = "BTCUSDT"
    data = create_sample_data(symbol)
    chart_path = f"charts/chart_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    
    if generate_chart(symbol, data, chart_path):
        print(f"Chart saved to: {chart_path}")
    else:
        print("Failed to generate chart")