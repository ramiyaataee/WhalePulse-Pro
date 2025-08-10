import pandas as pd

def calculate_ema(data, period):
    return data["close"].ewm(span=period, adjust=False).mean()

def calculate_rsi(data, period=14):
    delta = data["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi
