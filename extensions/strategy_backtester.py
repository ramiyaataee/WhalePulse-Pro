import pandas as pd
from indicators import calculate_ema, calculate_rsi

def backtest_strategy(data):
    data["ema_fast"] = calculate_ema(data, 20)
    data["ema_slow"] = calculate_ema(data, 50)
    data["rsi"] = calculate_rsi(data)

    data["signal"] = 0
    data.loc[(data["ema_fast"] > data["ema_slow"]) & (data["rsi"] > 50), "signal"] = 1
    data.loc[(data["ema_fast"] < data["ema_slow"]) & (data["rsi"] < 50), "signal"] = -1

    data["returns"] = data["close"].pct_change()
    data["strategy_returns"] = data["signal"].shift(1) * data["returns"]

    cumulative_return = (1 + data["strategy_returns"].fillna(0)).cumprod()
    return cumulative_return
