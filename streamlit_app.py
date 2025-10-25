"""
blooming cash - Family Portfolio Tracker
Track stocks across multiple accounts - FREE!
"""

import streamlit as st
import json
import os
import requests
import pandas as pd
from datetime import datetime

# ----------------- Page Config -----------------
st.set_page_config(
    page_title="blooming cash 🌸",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ----------------- CSS Styling -----------------
st.markdown("""
<style>
.stApp { background: #0a0e1a; }
header[data-testid="stHeader"] { background: #0a0e1a !important; }
#MainMenu, footer, .stDeployButton {visibility: hidden;}
.welcome-text { font-size: 36px; font-weight: 600; color: #ffffff; text-align: center; margin-bottom: 10px; }
.balance-bar { background: rgba(255,255,255,0.08); border-radius: 10px; padding: 15px; text-align: center; margin: 20px auto; max-width: 900px; color: white; font-size: 18px; border: 1px solid rgba(255,255,255,0.1); }
.stButton>button { width: 100%; background: rgba(255,255,255,0.08); color: white; border: 1px solid rgba(255,255,255,0.15); border-radius: 10px; padding: 15px; font-size: 16px; transition: all 0.3s; margin: 5px 0; }
.stButton>button:hover { background: rgba(255,255,255,0.15); border-color: rgba(255,255,255,0.3); transform: translateX(5px); }
.stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div { background: rgba(255,255,255,0.08); color: white; border: 1px solid rgba(255,255,255,0.15); border-radius: 8px; }
.result-box { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 20px; color: white; margin-top: 20px; min-height: 400px; font-family: 'Courier New', monospace; white-space: pre-wrap; font-size: 14px; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

# ----------------- Config -----------------
CONFIG_FILE = "config.json"

if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []
if 'selected_service' not in st.session_state:
    st.session_state.selected_service = "dashboard"

# ----------------- Config Load/Save -----------------
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                st.session_state.portfolio = data.get('portfolio', [])
        except:
            pass

def save_config():
    data = {
        'portfolio': st.session_state.portfolio,
        'last_updated': datetime.now().isoformat()
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# ----------------- NSE Price Fetch -----------------
@st.cache_data(ttl=300)
def get_stock_price(symbol):
    """
    Fetch the last available NSE closing price, even if market is closed.
    """
    try:
        symbol = symbol.upper()
        headers = {"User-Agent": "Mozilla/5.0"}
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers)

        # Quote API
        url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
        resp = session.get(url, headers=headers)
        data = resp.json()

        last_price = data.get("priceInfo", {}).get("lastPrice")
        if last_price:
            return float(last_price.replace(",", ""))

        # Fallback to historical data (most recent close)
        hist_url = f"https://www.nseindia.com/api/historical/cm/equity?symbol={symbol}&series=[\"EQ\"]&from=01-01-2020&to={datetime.today().strftime('%d-%m-%Y')}"
        hist_resp = session.get(hist_url, headers=headers)
        hist_data = hist_resp.json()
        if "data" in hist_data and hist_data["data"]:
            for day in reversed(hist_data["data"]):
                if day.get("closePrice"):
                    return float(day["closePrice"].replace(",", ""))
        return None
    except:
        return None

# ----------------- Portfolio Calculations -----------------
def calculate_total_pl():
    total = 0
    for stock in st.session_state.portfolio:
        current_price = get_stock_price(stock['symbol'])
        if current_price:
            total += (current_price - stock['avg_price']) * stock['quantity']
    return total

def buy_stock(symbol, quantity, avg_price, portfolio_name, account_name):
    symbol = symbol.upper()
    quantity = round(quantity)  # remove fractional shares
    existing_idx = next((i for i, s in enumerate(st.session_state.portfolio)
                         if s['symbol']==symbol and s['portfolio']==portfolio_name and s['account']==account_name), None)
    if existing_idx is not None:
        old = st.session_state.portfolio[existing_idx]
        new_qty = old['quantity'] + quantity
        new_avg = ((old['avg_price']*old['quantity']) + (avg_price*quantity)) / new_qty
        st.session_state.portfolio[existing_idx] = {'symbol': symbol, 'quantity': new_qty, 'avg_price': new_avg, 'portfolio': portfolio_name, 'account': account_name}
    else:
        st.session_state.portfolio.append({'symbol': symbol, 'quantity': quantity, 'avg_price': avg_price, 'portfolio': portfolio_name, 'account': account_name})
    save_config()

def sell_stock(symbol, quantity, portfolio_name, account_name):
    symbol = symbol.upper()
    quantity = round(quantity)
    idx = next((i for i, s in enumerate(st.session_state.portfolio)
                if s['symbol']==symbol and s['portfolio']==portfolio_name and s['account']==account_name), None)
    if idx is None:
        return False, f"You don't own {symbol} in {portfolio_name}'s {account_name}"
    stock = st.session_state.portfolio[idx]
    if quantity > stock['quantity']:
        return False, f"You only own {stock['quantity']} shares of {symbol}"
    if quantity == stock['quantity']:
        st.session_state.portfolio.pop(idx)
    else:
        st.session_state.portfolio[idx]['quantity'] -= quantity
    save_config()
    return True, f"Sold {quantity} shares of {symbol}"

# ----------------- Load Data -----------------
load_config()

# ----------------- UI Header -----------------
st.markdown('<h1 class="welcome-text">blooming cash 🌸</h1>', unsafe_allow_html=True)

# ----------------- Summary Bar -----------------
total_pl = calculate_total_pl()
pl_color = "#10b981" if total_pl >= 0 else "#ef4444"
pl_sign = "+" if total_pl >= 0 else ""
last_updated = datetime.now().strftime("%d %b %Y, %I:%M %p")
accounts = list(set([s['account'] for s in st.session_state.portfolio]))
portfolios = list(set([s['portfolio'] for s in st.session_state.portfolio]))

st.markdown(f'''
<div class="balance-bar">
📊 Total P/L: <span style="color: {pl_color}; font-weight: bold; font-size: 24px;">{pl_sign}₹{total_pl:.2f}</span> |
💼 Holdings: {len(st.session_state.portfolio)} stocks |
👥 Portfolios: {len(portfolios)} |
🕒 Last Updated: {last_updated}
</div>
''', unsafe_allow_html=True)

# ----------------- Layout -----------------
col_left, col_right = st.columns([1, 3])
with col_left:
    st.markdown("### Services")
    if st.button("📊 Dashboard"): st.session_state.selected_service="dashboard"; st.rerun()
    if st.button("📈 Buy Stock"): st.session_state.selected_service="buy"; st.rerun()
    if st.button("📉 Sell Stock"): st.session_state.selected_service="sell"; st.rerun()
    if st.button("🔄 Refresh Prices"): st.cache_data.clear(); st.rerun()

with col_right:
    if st.session_state.selected_service=="dashboard":
        st.markdown("### 📊 Family Portfolio Dashboard")
        if not st.session_state.portfolio:
            st.markdown('<div class="result-box">No stocks in portfolio yet! 🌸 Use "📈 Buy Stock" to add holdings.</div>', unsafe_allow_html=True)
        else:
            rows=[]
            for s in st.session_state.portfolio:
                price = get_stock_price(s['symbol'])
                if price:
                    pl_val = (price - s['avg_price'])*s['quantity']
                    pl_pct = ((price - s['avg_price'])/s['avg_price'])*100
                    rows.append({'Portfolio': s['portfolio'],'Account': s['account'],'Symbol': s['symbol'],'Quantity': s['quantity'],'Avg Price': f"₹{s['avg_price']:.2f}",'Current Price': f"₹{price:.2f}",'Total P/L': f"₹{pl_val:.2f}",'P/L %': f"{pl_pct:+.2f}%"})
                else:
                    rows.append({'Portfolio': s['portfolio'],'Account': s['account'],'Symbol': s['symbol'],'Quantity': s['quantity'],'Avg Price': f"₹{s['avg_price']:.2f}",'Current Price':'Unavailable','Total P/L':'N/A','P/L %':'N/A'})
            df=pd.DataFrame(rows)
            st.dataframe(df,use_container_width=True,hide_index=True)

    elif st.session_state.selected_service=="buy":
        st.markdown("### 📈 Buy Stock")
        with st.form("buy_form"):
            portfolio_name = st.text_input("Portfolio (e.g., Dad, Mom, Self)")
            account_name = st.text_input("Account (e.g., Zerodha, Groww)")
            symbol = st.text_input("Stock Symbol (e.g., RELIANCE, TCS, INFY)")
            quantity = st.number_input("Quantity", min_value=1, step=1)
            avg_price = st.number_input("Average Price (₹)", min_value=1.0, step=1.0)
            submitted = st.form_submit_button("✅ Buy Stock")
            if submitted:
                if not all([portfolio_name, account_name, symbol]):
                    st.error("Please fill all fields.")
                else:
                    price = get_stock_price(symbol)
                    if price is None:
                        st.error("❌ Invalid stock symbol or no price data available.")
                    else:
                        buy_stock(symbol, quantity, avg_price, portfolio_name, account_name)
                        st.success(f"✅ Bought {quantity} shares of {symbol.upper()} at ₹{avg_price}")
                        st.balloons()

    elif st.session_state.selected_service=="sell":
        st.markdown("### 📉 Sell Stock")
        if not st.session_state.portfolio:
            st.info("No stocks in portfolio to sell.")
        else:
            with st.form("sell_form"):
                portfolios_list = list(set([s['portfolio'] for s in st.session_state.portfolio]))
                portfolio_name = st.selectbox("Portfolio", portfolios_list)
                accounts_list = list(set([s['account'] for s in st.session_state.portfolio if s['portfolio']==portfolio_name]))
                account_name = st.selectbox("Account", accounts_list)
                stocks_list = [s['symbol'] for s in st.session_state.portfolio if s['portfolio']==portfolio_name and s['account']==account_name]
                symbol = st.selectbox("Stock Symbol", stocks_list)
                current_qty = next((s['quantity'] for s in st.session_state.portfolio if s['symbol']==symbol and s['portfolio']==portfolio_name and s['account']==account_name),0)
                st.info(f"You own {current_qty} shares of {symbol}")
                quantity = st.number_input("Quantity to Sell", min_value=1, max_value=current_qty, step=1)
                submitted = st.form_submit_button("✅ Sell Stock")
                if submitted:
                    success,message=sell_stock(symbol,quantity,portfolio_name,account_name)
                    if success:
                        st.success(f"✅ {message}")
                        st.balloons()
                    else:
                        st.error(f"❌ {message}")
