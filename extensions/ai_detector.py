import pandas as pd
from sklearn.ensemble import IsolationForest

def detect_anomalies(data):
    model = IsolationForest(contamination=0.01, random_state=42)
    features = data[["close", "volume"]].fillna(method="ffill")
    data["anomaly"] = model.fit_predict(features)
    return data
