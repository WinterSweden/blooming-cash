"""
blooming cash - Family Portfolio Tracker
Track stocks across multiple accounts - FREE!
"""

import streamlit as st
import json
import os
import yfinance as yf
import pandas as pd
from datetime import datetime

# Page config
st.set_page_config(
    page_title="blooming cash 🌸",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS (mirroring Literary Voice)
st.markdown("""
<style>
    .stApp { background: #0a0e1a; }
    header[data-testid="stHeader"] { background: #0a0e1a !important; }
    #MainMenu, footer, .stDeployButton {visibility: hidden;}
    .welcome-text {
        font-size: 36px;
        font-weight: 600;
        color: #ffffff;
        text-align: center;
        margin-bottom: 10px;
    }
    .balance-bar {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        margin: 20px auto;
        max-width: 900px;
        color: white;
        font-size: 18px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .stButton>button {
        width: 100%;
        background: rgba(255, 255, 255, 0.08);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 10px;
        padding: 15px;
        font-size: 16px;
        transition: all 0.3s;
        margin: 5px 0;
    }
    .stButton>button:hover {
        background: rgba(255, 255, 255, 0.15);
        border-color: rgba(255, 255, 255, 0.3);
        transform: translateX(5px);
    }
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
        background: rgba(255, 255, 255, 0.08);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 8px;
    }
    .result-box {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 20px;
        color: white;
        margin-top: 20px;
        min-height: 400px;
        font-family: 'Courier New', monospace;
        white-space: pre-wrap;
        font-size: 14px;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

CONFIG_FILE = "config.json"

# Initialize session state
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []
if 'selected_service' not in st.session_state:
    st.session_state.selected_service = "dashboard"

# Load config
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                st.session_state.portfolio = data.get('portfolio', [])
        except:
            pass

# Save config
def save_config():
    data = {
        'portfolio': st.session_state.portfolio,
        'last_updated': datetime.now().isoformat()
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# --- FIXED FUNCTION (with 5-day fallback and BSE check) ---
@st.cache_data(ttl=60)
def get_stock_price(symbol):
    """Get current or last close stock price from Yahoo Finance (NSE/BSE)."""
    try:
        symbol = symbol.upper()

        # Try NSE 1-day data first
        ticker = yf.Ticker(f"{symbol}.NS")
        data = ticker.history(period="1d")

        if not data.empty:
            return float(data['Close'].iloc[-1])

        # Fallback: try NSE 5-day data if market closed
        data = ticker.history(period="5d")
        if not data.empty:
            return float(data['Close'].iloc[-1])

        # Fallback: try BSE 5-day data
        ticker = yf.Ticker(f"{symbol}.BO")
        data = ticker.history(period="5d")
        if not data.empty:
            return float(data['Close'].iloc[-1])

        return None
    except Exception as e:
        st.warning(f"⚠️ Could not fetch {symbol}: {e}")
        return None

def calculate_total_pl():
    total = 0.0
    for stock in st.session_state.portfolio:
        current_price = get_stock_price(stock['symbol'])
        if current_price:
            total += (current_price - stock['avg_price']) * stock['quantity']
    return total

def buy_stock(symbol, quantity, avg_price, portfolio_name, account_name):
    symbol = symbol.upper()
    existing_idx = None
    for i, stock in enumerate(st.session_state.portfolio):
        if stock['symbol'] == symbol and stock['portfolio'] == portfolio_name and stock['account'] == account_name:
            existing_idx = i
            break
    if existing_idx is not None:
        old_stock = st.session_state.portfolio[existing_idx]
        new_qty = old_stock['quantity'] + quantity
        new_avg = ((old_stock['avg_price'] * old_stock['quantity']) + (avg_price * quantity)) / new_qty
        st.session_state.portfolio[existing_idx] = {
            'symbol': symbol,
            'quantity': new_qty,
            'avg_price': new_avg,
            'portfolio': portfolio_name,
            'account': account_name
        }
    else:
        st.session_state.portfolio.append({
            'symbol': symbol,
            'quantity': quantity,
            'avg_price': avg_price,
            'portfolio': portfolio_name,
            'account': account_name
        })
    save_config()

def sell_stock(symbol, quantity, portfolio_name, account_name):
    symbol = symbol.upper()
    stock_idx = None
    for i, stock in enumerate(st.session_state.portfolio):
        if stock['symbol'] == symbol and stock['portfolio'] == portfolio_name and stock['account'] == account_name:
            stock_idx = i
            break
    if stock_idx is None:
        return False, f"You don't own {symbol} in {portfolio_name}'s {account_name}"
    stock = st.session_state.portfolio[stock_idx]
    if quantity > stock['quantity']:
        return False, f"You only own {stock['quantity']} shares of {symbol}"
    if quantity == stock['quantity']:
        st.session_state.portfolio.pop(stock_idx)
    else:
        st.session_state.portfolio[stock_idx]['quantity'] -= quantity
    save_config()
    return True, f"Sold {quantity} shares of {symbol}"

# Load data
load_config()

# UI header
st.markdown('<h1 class="welcome-text">blooming cash 🌸</h1>', unsafe_allow_html=True)

# Summary bar
total_pl = calculate_total_pl()
pl_color = "#10b981" if total_pl >= 0 else "#ef4444"
pl_sign = "+" if total_pl >= 0 else ""
last_updated = datetime.now().strftime("%d %b %Y, %I:%M %p")

accounts = list(set([stock['account'] for stock in st.session_state.portfolio]))
portfolios = list(set([stock['portfolio'] for stock in st.session_state.portfolio]))

st.markdown(f'''
<div class="balance-bar">
📊 Total P/L: <span style="color: {pl_color}; font-weight: bold; font-size: 24px;">{pl_sign}₹{total_pl:.2f}</span> |
💼 Holdings: {len(st.session_state.portfolio)} stocks |
👥 Portfolios: {len(portfolios)} |
🕒 Last Updated: {last_updated}
</div>
''', unsafe_allow_html=True)

# Layout
col_left, col_right = st.columns([1, 3])

with col_left:
    st.markdown("### Services")
    if st.button("📊 Dashboard"): st.session_state.selected_service = "dashboard"; st.rerun()
    if st.button("📈 Buy Stock"): st.session_state.selected_service = "buy"; st.rerun()
    if st.button("📉 Sell Stock"): st.session_state.selected_service = "sell"; st.rerun()
    if st.button("🔄 Refresh Prices"):
        st.cache_data.clear()
        st.rerun()

with col_right:
    if st.session_state.selected_service == "dashboard":
        st.markdown("### 📊 Family Portfolio Dashboard")

        if not st.session_state.portfolio:
            st.markdown("""
            <div class="result-box">
No stocks in portfolio yet! 🌸  
Use "📈 Buy Stock" to add holdings.
            </div>
            """, unsafe_allow_html=True)
        else:
            portfolio_data = []
            for stock in st.session_state.portfolio:
                current_price = get_stock_price(stock['symbol'])
                if current_price:
                    total_pl = (current_price - stock['avg_price']) * stock['quantity']
                    pl_pct = ((current_price - stock['avg_price']) / stock['avg_price']) * 100
                    portfolio_data.append({
                        'Portfolio': stock['portfolio'],
                        'Account': stock['account'],
                        'Symbol': stock['symbol'],
                        'Quantity': stock['quantity'],
                        'Avg Price': f"₹{stock['avg_price']:.2f}",
                        'Current Price': f"₹{current_price:.2f}",
                        'Total P/L': f"₹{total_pl:.2f}",
                        'P/L %': f"{pl_pct:+.2f}%"
                    })
                else:
                    portfolio_data.append({
                        'Portfolio': stock['portfolio'],
                        'Account': stock['account'],
                        'Symbol': stock['symbol'],
                        'Quantity': stock['quantity'],
                        'Avg Price': f"₹{stock['avg_price']:.2f}",
                        'Current Price': 'Unavailable',
                        'Total P/L': 'N/A',
                        'P/L %': 'N/A'
                    })

            df = pd.DataFrame(portfolio_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

    elif st.session_state.selected_service == "buy":
        st.markdown("### 📈 Buy Stock")
        with st.form("buy_form"):
            portfolio_name = st.text_input("Portfolio (e.g., Dad, Mom, Self)")
            account_name = st.text_input("Account (e.g., Zerodha, Groww)")
            symbol = st.text_input("Stock Symbol (e.g., RELIANCE, TCS, INFY)")
            quantity = st.number_input("Quantity", min_value=0.01, step=0.01, format="%.2f")
            avg_price = st.number_input("Average Price (₹)", min_value=0.01, step=0.01, format="%.2f")
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

    elif st.session_state.selected_service == "sell":
        st.markdown("### 📉 Sell Stock")
        if not st.session_state.portfolio:
            st.info("No stocks in portfolio to sell.")
        else:
            with st.form("sell_form"):
                portfolios_list = list(set([s['portfolio'] for s in st.session_state.portfolio]))
                portfolio_name = st.selectbox("Portfolio", portfolios_list)
                accounts_in_portfolio = list(set([s['account'] for s in st.session_state.portfolio if s['portfolio'] == portfolio_name]))
                account_name = st.selectbox("Account", accounts_in_portfolio)
                stocks_in_selection = [s['symbol'] for s in st.session_state.portfolio if s['portfolio'] == portfolio_name and s['account'] == account_name]
                symbol = st.selectbox("Stock Symbol", stocks_in_selection)
                current_qty = next((s['quantity'] for s in st.session_state.portfolio if s['symbol'] == symbol and s['portfolio'] == portfolio_name and s['account'] == account_name), 0)
                st.info(f"You own {current_qty} shares of {symbol}")
                quantity = st.number_input("Quantity to Sell", min_value=0.01, max_value=float(current_qty), step=0.01, format="%.2f")
                submitted = st.form_submit_button("✅ Sell Stock")
                if submitted:
                    success, message = sell_stock(symbol, quantity, portfolio_name, account_name)
                    if success:
                        st.success(f"✅ {message}")
                        st.balloons()
                    else:
                        st.error(f"❌ {message}")
