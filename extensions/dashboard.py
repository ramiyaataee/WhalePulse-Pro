import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from strategy_backtester import backtest_strategy
from ai_detector import detect_anomalies

st.title("?? WhalePulse-Pro Dashboard")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
if uploaded_file:
    data = pd.read_csv(uploaded_file)
    st.subheader("Raw Data")
    st.write(data.tail())

    data = detect_anomalies(data)
    cumulative_return = backtest_strategy(data)

    st.subheader("Cumulative Strategy Return")
    st.line_chart(cumulative_return)

    st.subheader("Anomaly Detection")
    st.write(data[data["anomaly"] == -1])
