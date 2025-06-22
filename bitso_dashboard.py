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
autonomous_mode = st.sidebar.toggle("🤖 Autonomous Trading Mode", value=False)
next_trade_time = st.sidebar.time_input("Next Trade Time (estimate)", value=datetime.now().time())
st.sidebar.title("Trading Controls")
mxn_exposure_limit = st.sidebar.number_input("Max MXN Exposure (MXN)", min_value=0.0, value=8000000.0, format="%.2f", help="e.g. 8,000,000.00")
usd_exposure_limit = st.sidebar.number_input("Max USD Exposure (USD)", min_value=0.0, value=450000.0, format="%.2f", help="e.g. 450,000.00")
target_sell_mxn = st.sidebar.number_input("Target Sell MXN (MXN)", min_value=0.0, value=8000000.0, format="%.2f", help="e.g. 8,000,000.00")
target_sell_usd = st.sidebar.number_input("Target Sell USD (USD)", min_value=0.0, value=450000.0, format="%.2f", help="e.g. 450,000.00")
cost_basis = st.sidebar.number_input("USD/MXN Cost Basis", min_value=0.0, value=18.0000, format="%0.4f")
block_size = st.sidebar.number_input("Suggested Trade Block Size (MXN)", min_value=10000.0, value=500000.0, step=10000.0, format="%.2f", help="e.g. 500,000.00")

# Exposure logic
sell_mxn = data[data['side'] == 'sell']['amount'].sum()
buy_usd = (data[data['side'] == 'buy']['amount'] * data[data['side'] == 'buy']['price']).sum()

# Progress toward daily target
st.sidebar.markdown("### 📈 Trade Fulfillment")
sell_progress = min(sell_mxn / target_sell_mxn, 1.0)
buy_progress = min(buy_usd / target_sell_usd, 1.0)
sell_color = 'green' if sell_progress >= 0.8 else 'orange' if sell_progress >= 0.5 else 'red'
st.sidebar.markdown(f"<span style='color:{sell_color}; font-weight:bold;'>Sell MXN Progress: ${sell_mxn:,.0f} / ${target_sell_mxn:,.0f} MXN</span>", unsafe_allow_html=True)
st.sidebar.progress(sell_progress)
buy_color = 'green' if buy_progress >= 0.8 else 'orange' if buy_progress >= 0.5 else 'red'
st.sidebar.markdown(f"<span style='color:{buy_color}; font-weight:bold;'>Sell USD Progress: ${buy_usd:,.0f} / ${target_sell_usd:,.0f} USD</span>", unsafe_allow_html=True)
st.sidebar.progress(buy_progress)



# Alerts
if sell_mxn >= mxn_exposure_limit:
    st.warning(f"⚠️ MXN exposure limit reached: ${sell_mxn:,.2f} / ${mxn_exposure_limit:,.2f} MXN")
if buy_usd >= usd_exposure_limit:
    st.warning(f"⚠️ USD exposure limit reached: ${buy_usd:,.2f} / ${usd_exposure_limit:,.2f} USD")
if sell_mxn >= target_sell_mxn:
    st.success(f"✅ Target Sell MXN achieved: ${sell_mxn:,.2f} / ${target_sell_mxn:,.2f} MXN")
if buy_usd >= target_sell_usd:
    st.success(f"✅ Target Sell USD achieved: ${buy_usd:,.2f} / ${target_sell_usd:,.2f} USD")

# Bitso balance fetch (mocked API call)
st.subheader("📡 Bitso Account Balances (demo)")
def fetch_mock_balances():
    return {"MXN": 7284500.00, "USD": 312500.00}

balances = fetch_mock_balances()
st.metric("Available MXN", f"${balances['MXN']:,.2f} MXN")
st.metric("Available USD", f"${balances['USD']:,.2f} USD")

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
sell_pnl_color = 'green' if cost_basis_pnl >= 0 else 'red'
st.metric("Est. Sell P&L vs. Cost Basis", f"${cost_basis_pnl:,.2f} MXN", delta=f"${cost_basis_pnl:,.2f}", delta_color=sell_pnl_color)
buy_pnl_color = 'green' if cost_basis_buy_pnl >= 0 else 'red'
st.metric("Est. Buy P&L vs. Cost Basis", f"${cost_basis_buy_pnl:,.2f} MXN", delta=f"${cost_basis_buy_pnl:,.2f}", delta_color=buy_pnl_color)

# Cumulative P&L estimation (simplified model)
st.subheader("📊 Estimated Cumulative P&L")
est_pnl = (sell_avg - buy_avg) * sell_qty if not np.isnan(sell_avg) and not np.isnan(buy_avg) else 0.0
pnl_color = 'green' if est_pnl >= 0 else 'red'
st.metric("Estimated P&L (MXN)", f"${est_pnl:,.2f} MXN", delta=f"${est_pnl:,.2f}", delta_color=pnl_color)

# Dashboard header
st.title("📊 Bitso Liquidity Bot Dashboard")
st.metric("Total Sell MXN", f"${sell_mxn:,.2f} MXN")
st.metric("Total Sell USD", f"${buy_usd:,.2f} USD")

# Trade log chart
st.subheader("Trade Volume Over Time")
import altair as alt
volume_chart_reset = volume_chart.reset_index().melt(id_vars='timestamp', var_name='Side', value_name='Amount')
line_chart = alt.Chart(volume_chart_reset).mark_line().encode(
    x='timestamp:T',
    y=alt.Y('Amount:Q', title='Trade Volume'),
    color='Side:N',
    tooltip=['timestamp:T', 'Side:N', 'Amount:Q']
).interactive()

price_overlay = data['price'].resample('H').mean().reset_index()
price_line = alt.Chart(price_overlay).mark_line(color='gray', strokeDash=[5, 5]).encode(
    x='timestamp:T',
    y=alt.Y('price:Q', axis=alt.Axis(title='USD/MXN Rate'), scale=alt.Scale(zero=False)),
    tooltip=['timestamp:T', alt.Tooltip('price:Q', format='.4f')]
)

st.altair_chart((line_chart + price_line).resolve_scale(y='independent').properties(height=400), use_container_width=True)

# Hourly analysis
st.subheader("📅 Hourly Execution Overview")
data['hour'] = data['timestamp'].dt.hour
hourly = data.groupby(['hour', 'side'])['amount'].sum().unstack().fillna(0)
hourly = hourly.applymap(lambda x: round(x, 2))
st.bar_chart(hourly)

# Bot Activity Log (demo)
st.subheader("📝 Recent Bot Decisions (Demo)")
bot_logs = [
    {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "decision": "Sell 500,000 MXN", "reason": "Price > cost basis"},
    {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "decision": "Hold", "reason": "High volatility"},
    {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "decision": "Sell 250,000 MXN", "reason": "Mid-range price stability"},
]
st.table(pd.DataFrame(bot_logs))

# Show raw log
data.reset_index(inplace=True)
st.subheader("Recent Trades")
styled_data = data.sort_values("timestamp", ascending=False).copy()
styled_data["price"] = styled_data["price"].map("{:,.4f}".format)
styled_data["amount"] = styled_data["amount"].map("{:,.2f}".format)
st.dataframe(styled_data)
