
# Elliott-Wave & Fibonacci Analysis – Web-App (Streamlit, Option 1)
# Login: USER=master, PASS=123 (oder via Env: APP_USER / APP_PASSWORD / APP_PWHASH)

import os, time, hashlib
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import argrelextrema

# --- Auth ---
def _hash(p: str) -> str:
    return hashlib.sha256(p.encode("utf-8")).hexdigest()

APP_USER = os.getenv("APP_USER", "master")
APP_PASSWORD = os.getenv("APP_PASSWORD", "123")  # Klartext, Standard 123
APP_PWHASH = os.getenv("APP_PWHASH", "")        # alternativ SHA256

def _check_login(user: str, pw: str) -> bool:
    if APP_PASSWORD:
        return user == APP_USER and pw == APP_PASSWORD
    if APP_PWHASH:
        return user == APP_USER and _hash(pw) == APP_PWHASH
    return False

def _ensure_login():
    if st.session_state.get("logged_in"):
        return
    st.title("Login")
    u = st.text_input("User", value="")
    p = st.text_input("Passwort", type="password", value="")
    if st.button("Einloggen", type="primary"):
        time.sleep(0.2)
        if _check_login(u, p):
            st.session_state["logged_in"] = True
            st.rerun()
        else:
            st.error("Login fehlgeschlagen.")
    st.stop()

# --- Data / Logic ---
@st.cache_data(show_spinner=False)
def fetch_data(symbol: str, period: str, interval: str) -> pd.DataFrame:
    df = yf.download(symbol, period=period, interval=interval, progress=False)
    if df is None or df.empty:
        return pd.DataFrame()
    df.dropna(inplace=True)
    return df

def find_wave_points(df: pd.DataFrame, order: int = 5):
    vals = df["Close"].values
    highs = argrelextrema(vals, np.greater, order=order)[0]
    lows  = argrelextrema(vals, np.less,    order=order)[0]
    return highs, lows

def fibonacci_levels(high_price: float, low_price: float):
    diff = high_price - low_price
    return {
        "0%": high_price,
        "23.6%": high_price - 0.236*diff,
        "38.2%": high_price - 0.382*diff,
        "50%": high_price - 0.5*diff,
        "61.8%": high_price - 0.618*diff,
        "78.6%": high_price - 0.786*diff,
        "100%": low_price,
        "161.8% Ext": high_price + 0.618*diff
    }

def plot_chart(df: pd.DataFrame, highs, lows, fib_levels):
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df.index, df["Close"], label="Close")
    if len(highs) > 0:
        ax.scatter(df.index[highs], df["Close"].iloc[highs], marker="^", s=80, label="Highs")
    if len(lows) > 0:
        ax.scatter(df.index[lows],  df["Close"].iloc[lows],  marker="v", s=80, label="Lows")
    for level, price in fib_levels.items():
        ax.axhline(price, linestyle="--", alpha=0.6, label=f"{level} {price:.2f}")
    ax.set_title("Elliott-Wave & Fibonacci Analysis")
    ax.grid(True)
    ax.legend(loc="best")
    return fig

# --- UI ---
st.set_page_config(page_title="Elliott/Fibo Tool", layout="wide")
_ensure_login()

st.sidebar.write(f"Eingeloggt als **{APP_USER}**")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

st.title("📈 Elliott-Wave & Fibonacci Analysis")
c1, c2, c3 = st.columns(3)
with c1:
    symbol = st.text_input("Ticker (z. B. BTC-USD, AAPL, TSLA)", "BTC-USD")
with c2:
    period = st.selectbox("Zeitraum", ["1mo","3mo","6mo","1y","2y","5y","10y","max"], index=3)
with c3:
    interval = st.selectbox("Intervall", ["1d","1wk","1mo"], index=0)

order = st.slider("Wellen-Sensitivitaet (order)", 3, 20, 5, 1)

if st.button("Analyse starten", type="primary"):
    with st.spinner("Lade Daten..."):
        df = fetch_data(symbol, period, interval)
        if df.empty:
            st.error("Keine Daten erhalten.")
        else:
            highs, lows = find_wave_points(df, order=order)
            if len(highs)==0 or len(lows)==0:
                st.warning("Zu wenig Wendepunkte gefunden. 'order' anpassen.")
            else:
                last_high = float(df['Close'].iloc[highs[-1]])
                last_low  = float(df['Close'].iloc[lows[-1]])
                fib = fibonacci_levels(last_high, last_low)
                fig = plot_chart(df, highs, lows, fib)
                st.pyplot(fig)
                st.subheader("Fibonacci-Level")
                st.write({k: round(v, 4) for k, v in fib.items()})
