# Bitso Liquidity Dashboard using Streamlit
# Run this with: streamlit run bitso_dashboard.py

import streamlit as st
import pandas as pd
import os
from datetime import datetime

CSV_LOG_FILE = 'bitso_trades.csv'

st.set_page_config(page_title="Bitso Liquidity Bot Dashboard", layout="wide")
st.title("📊 Bitso Liquidity Bot Dashboard")

# Load CSV
if os.path.exists(CSV_LOG_FILE):
    df = pd.read_csv(CSV_LOG_FILE, parse_dates=['timestamp'])
    df = df.sort_values(by='timestamp', ascending=False)

    # Summary metrics
    total_trades = len(df)
    total_volume = df['amount'].sum()
    avg_price = df['price'].mean()
    sell_trades = df[df['side'] == 'sell']
    buy_trades = df[df['side'] == 'buy']

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Trades", total_trades)
    col2.metric("Total Volume (MXN or USD)", f"{total_volume:,.2f}")
    col3.metric("Avg Price", f"{avg_price:.4f}")
    col4.metric("Sell:Buy Ratio", f"{len(sell_trades)}:{len(buy_trades)}")

    # Trade Log Table
    st.subheader("📄 Trade Log")
    st.dataframe(df[['timestamp', 'side', 'price', 'amount', 'order_id']])

    # Trade Volume Over Time
    st.subheader("📈 Trade Volume Over Time")
    df['date'] = df['timestamp'].dt.date
    volume_by_day = df.groupby(['date', 'side'])['amount'].sum().unstack().fillna(0)
    st.line_chart(volume_by_day)
else:
    st.warning(f"Trade log file '{CSV_LOG_FILE}' not found.")
    st.info("Run the bot first to generate trade logs.")
