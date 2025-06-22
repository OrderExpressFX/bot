import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np
import requests

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
mxn_exposure_limit = st.sidebar.number_input("Max MXN Exposure", min_value=0.0, value=8000000.0)
usd_exposure_limit = st.sidebar.number_input("Max USD Exposure", min_value=0.0, value=450000.0)
target_sell_mxn = st.sidebar.number_input("Target Sell MXN", min_value=0.0, value=8000000.0)
target_buy_usd = st.sidebar.number_input("Target Buy USD", min_value=0.0, value=450000.0)
cost_basis = st.sidebar.number_input("USD/MXN Cost Basis", min_value=0.0, value=18.0000, format="%0.4f")
block_size = st.sidebar.number_input("Suggested Trade Block Size (MXN)", min_value=10000.0, value=500000.0, step=10000.0)

# Exposure logic
sell_mxn = data[data['side'] == 'sell']['amount'].sum()
buy_usd = (data[data['side'] == 'buy']['amount'] * data[data['side'] == 'buy']['price']).sum()

# Progress toward daily target
st.sidebar.markdown("### 📈 Trade Fulfillment")
sell_progress = min(sell_mxn / target_sell_mxn, 1.0)
buy_progress = min(buy_usd / target_buy_usd, 1.0)
st.sidebar.progress(sell_progress, text=f"Sell MXN Progress: {sell_mxn:,.0f} / {target_sell_mxn:,.0f}")
st.sidebar.progress(buy_progress, text=f"Buy USD Progress: {buy_usd:,.0f} / {target_buy_usd:,.0f}")

# Alerts
if sell_mxn >= mxn_exposure_limit:
    st.warning(f"⚠️ MXN exposure limit reached: {sell_mxn:.2f} / {mxn_exposure_limit:.2f}")
if buy_usd >= usd_exposure_limit:
    st.warning(f"⚠️ USD exposure limit reached: {buy_usd:.2f} / {usd_exposure_limit:.2f}")
if sell_mxn >= target_sell_mxn:
    st.success(f"✅ Target Sell MXN achieved: {sell_mxn:.2f} / {target_sell_mxn:.2f}")
if buy_usd >= target_buy_usd:
    st.success(f"✅ Target Buy USD achieved: {buy_usd:.2f} / {target_buy_usd:.2f}")

# Bitso balance fetch (mocked API call)
st.subheader("📡 Bitso Account Balances (demo)")
def fetch_mock_balances():
    return {"MXN": 7284500.00, "USD": 312500.00}

balances = fetch_mock_balances()
st.metric("Available MXN", f"{balances['MXN']:,.2f}")
st.metric("Available USD", f"{balances['USD']:,.2f}")

# Volatility monitoring
st.subheader("📉 Volatility Monitor")
data['rolling_vol'] = data['price'].rolling(window=10).std()
latest_vol = data['rolling_vol'].iloc[-1] if not data['rolling_vol'].isna().all() else 0.0
st.metric("Recent Volatility (10 trades)", f"{latest_vol:.6f}")

# Recommended action
st.subheader("🧠 Trade Suggestion Engine")
if latest_vol > 0.04:
    st.info("Market is volatile. Suggest: Reduce block size or delay next trade.")
elif sell_price_deviation < 0:
    st.info("Sell price below cost basis. Suggest: Wait or reduce size.")
else:
    st.success(f"Suggest: SELL {block_size:,.0f} MXN at current market price")

# Cost basis analysis
st.subheader("📉 Trade vs. Cost Basis Analysis")
buy_avg = data[data['side'] == 'buy']['price'].mean()
sell_avg = data[data['side'] == 'sell']['price'].mean()
sell_qty = data[data['side'] == 'sell']['amount'].sum()

st.metric("Cost Basis (USD/MXN)", f"{cost_basis:.4f}")
sell_price_deviation = sell_avg - cost_basis if not np.isnan(sell_avg) else 0.0
st.metric("Avg Sell vs. Cost Basis", f"{sell_price_deviation:.4f}")
buy_price_deviation = cost_basis - buy_avg if not np.isnan(buy_avg) else 0.0
st.metric("Avg Buy vs. Cost Basis", f"{buy_price_deviation:.4f}")

# Profit/loss using cost basis
cost_basis_pnl = (sell_avg - cost_basis) * sell_qty if not np.isnan(sell_avg) else 0.0
cost_basis_buy_pnl = (cost_basis - buy_avg) * data[data['side'] == 'buy']['amount'].sum() if not np.isnan(buy_avg) else 0.0
st.metric("Est. Sell P&L vs. Cost Basis", f"{cost_basis_pnl:,.2f}")
st.metric("Est. Buy P&L vs. Cost Basis", f"{cost_basis_buy_pnl:,.2f}")

# Cumulative P&L estimation (simplified model)
st.subheader("📊 Estimated Cumulative P&L")
est_pnl = (sell_avg - buy_avg) * sell_qty if not np.isnan(sell_avg) and not np.isnan(buy_avg) else 0.0
st.metric("Estimated P&L (MXN)", f"{est_pnl:,.2f}")

# Dashboard header
st.title("📊 Bitso Liquidity Bot Dashboard")
st.metric("Total Sell MXN", f"{sell_mxn:,.2f}")
st.metric("Total Buy USD", f"{buy_usd:,.2f}")

# Trade log chart
st.subheader("Trade Volume Over Time")
data.set_index("timestamp", inplace=True)
volume_chart = data.groupby([pd.Grouper(freq='H'), 'side'])['amount'].sum().unstack().fillna(0)
st.line_chart(volume_chart)

# Hourly analysis
st.subheader("📅 Hourly Execution Overview")
data['hour'] = data['timestamp'].dt.hour
hourly = data.groupby(['hour', 'side'])['amount'].sum().unstack().fillna(0)
st.bar_chart(hourly)

# Show raw log
data.reset_index(inplace=True)
st.subheader("Recent Trades")
st.dataframe(data.sort_values("timestamp", ascending=False))
