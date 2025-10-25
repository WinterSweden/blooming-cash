import streamlit as st
import json
import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time

# Page config
st.set_page_config(
    page_title="blooming cash 🌸",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

CONFIG_FILE = "config.json"

# --- SESSION STATE ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []
if 'selected_service' not in st.session_state:
    st.session_state.selected_service = "dashboard"

# --- LOAD / SAVE ---
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

# --- GET STOCK PRICE FROM NSE ---
def get_stock_price(symbol):
    """Scrape NSE Market Pulse to get last price"""
    symbol = symbol.upper()
    url = f"https://www.nseindia.com/get-quotes/equity?symbol={symbol}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    }
    session = requests.Session()
    session.headers.update(headers)

    # Get cookies
    session.get("https://www.nseindia.com")
    time.sleep(0.5)  # small delay

    # Get stock page
    try:
        response = session.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        # NSE Market Pulse uses this class/id for last price
        price_tag = soup.find("div", {"id": "lastPrice"}) or soup.find("span", {"id": "lastPrice"})
        if price_tag:
            price_str = price_tag.text.strip().replace(",", "")
            return float(price_str)
        else:
            # fallback: try last 5 days history from Yahoo Finance
            import yfinance as yf
            ticker = yf.Ticker(f"{symbol}.NS")
            hist = ticker.history(period="5d")
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
    except Exception as e:
        st.warning(f"⚠️ Could not fetch {symbol}: {e}")
    return None

# --- PORTFOLIO CALCULATIONS ---
def calculate_total_pl():
    total = 0
    for s in st.session_state.portfolio:
        current_price = get_stock_price(s['symbol'])
        if current_price:
            total += (current_price - s['avg_price']) * s['quantity']
    return total

# --- BUY / SELL ---
def buy_stock(symbol, quantity, avg_price, portfolio_name, account_name):
    symbol = symbol.upper()
    quantity = round(quantity)
    idx = None
    for i, s in enumerate(st.session_state.portfolio):
        if s['symbol'] == symbol and s['portfolio'] == portfolio_name and s['account'] == account_name:
            idx = i
            break
    if idx is not None:
        old = st.session_state.portfolio[idx]
        new_qty = old['quantity'] + quantity
        new_avg = ((old['avg_price']*old['quantity']) + (avg_price*quantity)) / new_qty
        st.session_state.portfolio[idx] = {
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
    quantity = round(quantity)
    idx = None
    for i, s in enumerate(st.session_state.portfolio):
        if s['symbol'] == symbol and s['portfolio'] == portfolio_name and s['account'] == account_name:
            idx = i
            break
    if idx is None:
        return False, f"You don't own {symbol}"
    stock = st.session_state.portfolio[idx]
    if quantity > stock['quantity']:
        return False, f"You only own {stock['quantity']} shares"
    if quantity == stock['quantity']:
        st.session_state.portfolio.pop(idx)
    else:
        st.session_state.portfolio[idx]['quantity'] -= quantity
    save_config()
    return True, f"Sold {quantity} shares of {symbol}"

# --- LOAD DATA ---
load_config()

# --- UI HEADER ---
st.markdown('<h1 style="text-align:center;color:white;">blooming cash 🌸</h1>', unsafe_allow_html=True)
total_pl = calculate_total_pl()
pl_color = "#10b981" if total_pl >= 0 else "#ef4444"
pl_sign = "+" if total_pl >= 0 else ""
last_updated = datetime.now().strftime("%d %b %Y, %I:%M %p")
accounts = list(set([s['account'] for s in st.session_state.portfolio]))
portfolios = list(set([s['portfolio'] for s in st.session_state.portfolio]))

st.markdown(f'''
<div style="background:rgba(255,255,255,0.08);border-radius:10px;padding:15px;text-align:center;color:white;font-size:18px;">
📊 Total P/L: <span style="color:{pl_color};font-weight:bold;font-size:24px;">{pl_sign}₹{total_pl:.2f}</span> |
💼 Holdings: {len(st.session_state.portfolio)} stocks |
👥 Portfolios: {len(portfolios)} |
🕒 Last Updated: {last_updated}
</div>
''', unsafe_allow_html=True)

# --- LAYOUT ---
col_left, col_right = st.columns([1,3])
with col_left:
    st.markdown("### Services")
    if st.button("📊 Dashboard"): st.session_state.selected_service="dashboard"; st.rerun()
    if st.button("📈 Buy Stock"): st.session_state.selected_service="buy"; st.rerun()
    if st.button("📉 Sell Stock"): st.session_state.selected_service="sell"; st.rerun()
    if st.button("🔄 Refresh Prices"): st.rerun()

# --- DASHBOARD ---
with col_right:
    if st.session_state.selected_service=="dashboard":
        st.markdown("### 📊 Family Portfolio Dashboard")
        if not st.session_state.portfolio:
            st.info("No stocks yet! Buy to get started 🌸")
        else:
            data=[]
            for s in st.session_state.portfolio:
                price = get_stock_price(s['symbol'])
                if price:
                    pl = (price - s['avg_price'])*s['quantity']
                    pl_pct = ((price - s['avg_price'])/s['avg_price'])*100
                    data.append({
                        'Portfolio':s['portfolio'],
                        'Account':s['account'],
                        'Symbol':s['symbol'],
                        'Quantity':s['quantity'],
                        'Avg Price':f"₹{s['avg_price']:.2f}",
                        'Current Price':f"₹{price:.2f}",
                        'Total P/L':f"₹{pl:.2f}",
                        'P/L %':f"{pl_pct:+.2f}%"
                    })
                else:
                    data.append({
                        'Portfolio':s['portfolio'],
                        'Account':s['account'],
                        'Symbol':s['symbol'],
                        'Quantity':s['quantity'],
                        'Avg Price':f"₹{s['avg_price']:.2f}",
                        'Current Price':'Unavailable',
                        'Total P/L':'N/A',
                        'P/L %':'N/A'
                    })
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)

# --- BUY ---
    elif st.session_state.selected_service=="buy":
        st.markdown("### 📈 Buy Stock")
        with st.form("buy_form"):
            portfolio_name = st.text_input("Portfolio (Dad, Mom, Self)")
            account_name = st.text_input("Account (Zerodha, Groww)")
            symbol = st.text_input("Stock Symbol (RELIANCE, TCS)")
            quantity = st.number_input("Quantity", min_value=1, step=1)
            avg_price = st.number_input("Average Price (₹)", min_value=1.0, step=1.0)
            submitted = st.form_submit_button("✅ Buy Stock")
            if submitted:
                if not all([portfolio_name, account_name, symbol]):
                    st.error("Fill all fields")
                else:
                    buy_stock(symbol, quantity, avg_price)
                    st.success(f"Bought {quantity} shares of {symbol.upper()} at ₹{avg_price}")
                    st.balloons()

# --- SELL ---
    elif st.session_state.selected_service=="sell":
        st.markdown("### 📉 Sell Stock")
        if not st.session_state.portfolio:
            st.info("No stocks to sell")
        else:
            with st.form("sell_form"):
                portfolios_list = list(set([s['portfolio'] for s in st.session_state.portfolio]))
                portfolio_name = st.selectbox("Portfolio", portfolios_list)
                accounts_list = list(set([s['account'] for s in st.session_state.portfolio if s['portfolio']==portfolio_name]))
                account_name = st.selectbox("Account", accounts_list)
                stocks_list = [s['symbol'] for s in st.session_state.portfolio if s['portfolio']==portfolio_name and s['account']==account_name]
                symbol = st.selectbox("Stock Symbol", stocks_list)
                current_qty = next((s['quantity'] for s in st.session_state.portfolio if s['symbol']==symbol and s['portfolio']==portfolio_name and s['account']==account_name), 0)
                st.info(f"You own {current_qty} shares")
                quantity = st.number_input("Quantity to Sell", min_value=1, max_value=current_qty, step=1)
                submitted = st.form_submit_button("✅ Sell Stock")
                if submitted:
                    success, msg = sell_stock(symbol, quantity, portfolio_name, account_name)
                    if success:
                        st.success(msg)
                        st.balloons()
                    else:
                        st.error(msg)
