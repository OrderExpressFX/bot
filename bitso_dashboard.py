import streamlit as st
import pandas as pd
from datetime import datetime

# Load trade log
@st.cache_data(ttl=60)
def load_data():
    try:
        return pd.read_csv("bitso_trades.csv", parse_dates=['timestamp'])
    except FileNotFoundError:
        return pd.DataFrame(columns=["timestamp", "side", "price", "amount", "order_id"])

# Load and process data
data = load_data()
data['timestamp'] = pd.to_datetime(data['timestamp'])
data['amount'] = pd.to_numeric(data['amount'], errors='coerce')
data['price'] = pd.to_numeric(data['price'], errors='coerce')
data = data.dropna()

# Dashboard controls
st.sidebar.title("Trading Controls")
mxn_exposure_limit = st.sidebar.number_input("Max MXN Exposure", min_value=0.0, value=50000.0)
usd_exposure_limit = st.sidebar.number_input("Max USD Exposure", min_value=0.0, value=5000.0)
target_sell_mxn = st.sidebar.number_input("Target Sell MXN", min_value=0.0, value=10000.0)
target_buy_usd = st.sidebar.number_input("Target Buy USD", min_value=0.0, value=1000.0)

# Exposure logic
sell_mxn = data[data['side'] == 'sell']['amount'].sum()
buy_usd = (data[data['side'] == 'buy']['amount'] * data[data['side'] == 'buy']['price']).sum()

# Alerts
if sell_mxn >= mxn_exposure_limit:
    st.warning(f"⚠️ MXN exposure limit reached: {sell_mxn:.2f} / {mxn_exposure_limit:.2f}")
if buy_usd >= usd_exposure_limit:
    st.warning(f"⚠️ USD exposure limit reached: {buy_usd:.2f} / {usd_exposure_limit:.2f}")
if sell_mxn >= target_sell_mxn:
    st.success(f"✅ Target Sell MXN achieved: {sell_mxn:.2f} / {target_sell_mxn:.2f}")
if buy_usd >= target_buy_usd:
    st.success(f"✅ Target Buy USD achieved: {buy_usd:.2f} / {target_buy_usd:.2f}")

# Display metrics
st.title("📊 Bitso Liquidity Bot Dashboard")
st.metric("Total Sell MXN", f"{sell_mxn:,.2f}")
st.metric("Total Buy USD", f"{buy_usd:,.2f}")

# Trade log chart
st.subheader("Trade Volume Over Time")
data.set_index("timestamp", inplace=True)
volume_chart = data.groupby([pd.Grouper(freq='H'), 'side'])['amount'].sum().unstack().fillna(0)
st.line_chart(volume_chart)

# Show raw log
data.reset_index(inplace=True)
st.subheader("Recent Trades")
st.dataframe(data.sort_values("timestamp", ascending=False))
