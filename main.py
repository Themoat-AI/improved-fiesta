import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.stats import linregress

# --- PAGE CONFIG ---
st.set_page_config(page_title="Chaos Stock Terminal", layout="wide")

st.title("🌀 Advanced Chaos & Mathematical Stock Terminal")
st.markdown("Analyzing market entropy, fractals, and trend dynamics.")

# --- SIDEBAR CONTROLS ---
ticker = st.sidebar.text_input("Enter Ticker (e.g., AAPL, TSLA, BTC-USD)", value="AAPL")
period = st.sidebar.selectbox("Data Period", ["6mo", "1y", "2y", "5y"], index=1)
interval = st.sidebar.selectbox("Interval", ["1d", "1wk"], index=0)

# --- MATH FUNCTIONS ---

def calculate_fractal_chaos_oscillator(df, period=5):
    """
    Calculates the Fractal Chaos Oscillator.
    Values near 1 = Trending, Values near -1 = Chaotic/Random.
    """
    close = df['Close']
    # Difference between current price and price 'n' periods ago
    price_diff = close.diff(period)
    
    # Sum of absolute differences (path length)
    path_length = close.diff().abs().rolling(window=period).sum()
    
    fco = price_diff / path_length
    return fco

def calculate_hurst_exponent(series):
    """
    Calculates the Hurst Exponent to identify mean-reverting vs trending series.
    H < 0.5: Mean-reverting
    H = 0.5: Random Walk (Brownian Motion)
    H > 0.5: Trending (Persistent)
    """
    lags = range(2, 20)
    tau = [np.sqrt(np.std(np.subtract(series[lag:], series[:-lag]))) for lag in lags]
    poly = np.polyfit(np.log(lags), np.log(tau), 1)
    return poly[0] * 2.0

# --- DATA FETCHING ---
@st.cache_data
def load_data(symbol, p, i):
    data = yf.download(symbol, period=p, interval=i)
    return data

data = load_data(ticker, period, interval)

if not data.empty:
    # --- CALCULATIONS ---
    data['FCO'] = calculate_fractal_chaos_oscillator(data)
    data['SMA_20'] = data['Close'].rolling(window=20).mean()
    data['Volatility'] = data['Close'].pct_change().rolling(window=20).std() * np.sqrt(252)
    
    # Calculate Hurst on the full downloaded close price
    hurst = calculate_hurst_exponent(data['Close'].values.flatten())

    # --- TOP METRICS ---
    col1, col2, col3, col4 = st.columns(4)
    current_price = data['Close'].iloc[-1].iloc[0]
    price_chg = (data['Close'].iloc[-1].iloc[0] - data['Close'].iloc[-2].iloc[0]) if len(data) > 1 else 0.0
    
    col1.metric("Current Price", f"${current_price:,.2f}", f"{price_chg:,.2f}")
    col2.metric("Hurst Exponent", f"{hurst:.2f}", "Trend Strength")
    col3.metric("Chaos Level (FCO)", f"{data['FCO'].iloc[-1]:.2f}", "Trending" if data['FCO'].iloc[-1] > 0 else "Chaotic")
    col4.metric("Ann. Volatility", f"{data['Volatility'].iloc[-1]*100:.1f}%")

    # --- VISUALIZATION ---
    tab1, tab2 = st.tabs(["📈 Price & Fractals", "🧮 Math Lab"])

    with tab1:
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'],
                                   low=data['Low'], close=data['Close'], name="Price"))
        fig.add_trace(go.Scatter(x=data.index, y=data['SMA_20'], line=dict(color='orange', width=1), name="SMA 20"))
        fig.update_layout(title=f"{ticker} Fractal Analysis", yaxis_title="Price", height=600)
        st.plotly_chart(fig, width='stretch')

        # FCO Chart
        fig_fco = go.Figure()
        fig_fco.add_trace(go.Scatter(x=data.index, y=data['FCO'], fill='tozeroy', name="Fractal Chaos Oscillator"))
        fig_fco.add_hline(y=0, line_dash="dash", line_color="gray")
        fig_fco.update_layout(title="Chaos Signal (FCO)", height=300)
        st.plotly_chart(fig_fco, width='stretch')

    with tab2:
        st.subheader("Advanced Statistical Summary")
        stats_col1, stats_col2 = st.columns(2)
        
        with stats_col1:
            st.write("**Chaos Theory Metrics**")
            st.write(f"- **Hurst Exponent:** {hurst:.4f}")
            if hurst > 0.5:
                st.info("The market is currently showing 'Persistent' behavior (Trending).")
            elif hurst < 0.5:
                st.warning("The market is 'Anti-persistent' (Mean-reverting/Chaotic).")
            else:
                st.write("The market is a Random Walk.")

        with stats_col2:
            st.write("**Risk Metrics**")
            sharpe = (data['Close'].pct_change().mean() / data['Close'].pct_change().std()) * np.sqrt(252)
            st.write(f"- **Estimated Sharpe Ratio:** {sharpe.iloc[0]:.2f}")

    st.dataframe(data.tail(10))
else:
    st.error("Could not find data for that ticker. Please try again.")