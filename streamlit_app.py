import streamlit as st
import json
import os
import requests
import pandas as pd
from datetime import datetime

# Page config
st.set_page_config(
    page_title="blooming cash 🌸",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
.stApp { background: #0a0e1a; }
header[data-testid="stHeader"] { background: #0a0e1a !important; }
#MainMenu, footer, .stDeployButton {visibility: hidden;}
.welcome-text { font-size:36px; font-weight:600; color:#fff; text-align:center; margin-bottom:10px; }
.balance-bar { background: rgba(255,255,255,0.08); border-radius:10px; padding:15px; text-align:center; margin:20px auto; max-width:900px; color:white; font-size:18px; border:1px solid rgba(255,255,255,0.1);}
.stButton>button { width:100%; background:rgba(255,255,255,0.08); color:white; border:1px solid rgba(255,255,255,0.15); border-radius:10px; padding:15px; font-size:16px; margin:5px 0; transition: all 0.3s; }
.stButton>button:hover { background: rgba(255,255,255,0.15); border-color: rgba(255,255,255,0.3); transform:translateX(5px); }
.stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div { background: rgba(255,255,255,0.08); color:white; border:1px solid rgba(255,255,255,0.15); border-radius:8px; }
.result-box { background: rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); border-radius:10px; padding:20px; color:white; margin-top:20px; min-height:400px; font-family:'Courier New', monospace; white-space: pre-wrap; font-size:14px; line-height:1.6; }
</style>
""", unsafe_allow_html=True)

CONFIG_FILE = "config.json"

# Session state
if 'portfolio' not in st.session_state: st.session_state.portfolio = []
if 'selected_service' not in st.session_state: st.session_state.selected_service = "dashboard"

# Load/save config
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE,'r') as f:
                data=json.load(f)
                st.session_state.portfolio = data.get('portfolio',[])
        except: pass

def save_config():
    data = {'portfolio': st.session_state.portfolio, 'last_updated': datetime.now().isoformat()}
    with open(CONFIG_FILE,'w') as f:
        json.dump(data,f,indent=2)

# NSE price fetch
@st.cache_data(ttl=60)
def get_stock_price(symbol):
    try:
        symbol = symbol.upper()
        url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
        headers = {"User-Agent":"Mozilla/5.0"}
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers)  # initial request for cookies
        r = session.get(url, headers=headers, timeout=5)
        data = r.json()
        price = data['priceInfo'].get('lastPrice') or data['priceInfo'].get('closePrice')
        if price: return float(price)
        return None
    except: return None

# Total P/L
def calculate_total_pl():
    total=0
    for s in st.session_state.portfolio:
        price = get_stock_price(s['symbol'])
        if price: total += (price - s['avg_price'])*s['quantity']
    return total

# Buy/Sell
def buy_stock(symbol, quantity, avg_price, portfolio_name, account_name):
    symbol = symbol.upper()
    idx = next((i for i,s in enumerate(st.session_state.portfolio) 
                if s['symbol']==symbol and s['portfolio']==portfolio_name and s['account']==account_name), None)
    if idx is not None:
        old = st.session_state.portfolio[idx]
        new_qty = old['quantity'] + quantity
        new_avg = ((old['avg_price']*old['quantity']) + (avg_price*quantity))/new_qty
        st.session_state.portfolio[idx] = {'symbol':symbol,'quantity':new_qty,'avg_price':new_avg,'portfolio':portfolio_name,'account':account_name}
    else:
        st.session_state.portfolio.append({'symbol':symbol,'quantity':quantity,'avg_price':avg_price,'portfolio':portfolio_name,'account':account_name})
    save_config()

def sell_stock(symbol, quantity, portfolio_name, account_name):
    symbol = symbol.upper()
    idx = next((i for i,s in enumerate(st.session_state.portfolio) 
                if s['symbol']==symbol and s['portfolio']==portfolio_name and s['account']==account_name), None)
    if idx is None: return False, f"You don't own {symbol}"
    stock = st.session_state.portfolio[idx]
    if quantity > stock['quantity']: return False, f"You only own {stock['quantity']} shares"
    if quantity == stock['quantity']: st.session_state.portfolio.pop(idx)
    else: st.session_state.portfolio[idx]['quantity'] -= quantity
    save_config()
    return True, f"Sold {quantity} shares of {symbol}"

# Load config & round fractionals
load_config()
for s in st.session_state.portfolio:
    s['quantity'] = int(round(s['quantity']))
save_config()

# --- UI ---
st.markdown('<h1 class="welcome-text">blooming cash 🌸</h1>', unsafe_allow_html=True)

total_pl = calculate_total_pl()
pl_color = "#10b981" if total_pl>=0 else "#ef4444"
pl_sign = "+" if total_pl>=0 else ""
last_updated = datetime.now().strftime("%d %b %Y, %I:%M %p")
accounts = list(set([s['account'] for s in st.session_state.portfolio]))
portfolios = list(set([s['portfolio'] for s in st.session_state.portfolio]))

st.markdown(f'''
<div class="balance-bar">
📊 Total P/L: <span style="color:{pl_color}; font-weight:bold; font-size:24px;">{pl_sign}₹{total_pl:.2f}</span> |
💼 Holdings: {len(st.session_state.portfolio)} stocks |
👥 Portfolios: {len(portfolios)} |
🕒 Last Updated: {last_updated}
</div>
''', unsafe_allow_html=True)

# Layout
col_left, col_right = st.columns([1,3])
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
            st.markdown('<div class="result-box">No stocks in portfolio yet! 🌸</div>', unsafe_allow_html=True)
        else:
            data_list=[]
            for s in st.session_state.portfolio:
                price = get_stock_price(s['symbol'])
                if price:
                    total = (price-s['avg_price'])*s['quantity']
                    pct = ((price-s['avg_price'])/s['avg_price'])*100
                    data_list.append({'Portfolio':s['portfolio'],'Account':s['account'],'Symbol':s['symbol'],'Quantity':s['quantity'],
                                      'Avg Price':f"₹{s['avg_price']:.2f}",'Current Price':f"₹{price:.2f}",
                                      'Total P/L':f"₹{total:.2f}",'P/L %':f"{pct:+.2f}%"})
                else:
                    data_list.append({'Portfolio':s['portfolio'],'Account':s['account'],'Symbol':s['symbol'],'Quantity':s['quantity'],
                                      'Avg Price':f"₹{s['avg_price']:.2f}",'Current Price':'Unavailable','Total P/L':'N/A','P/L %':'N/A'})
            st.dataframe(pd.DataFrame(data_list), use_container_width=True, hide_index=True)

    elif st.session_state.selected_service=="buy":
        st.markdown("### 📈 Buy Stock")
        with st.form("buy_form"):
            portfolio_name = st.text_input("Portfolio (e.g., Dad, Mom)")
            account_name = st.text_input("Account (e.g., Zerodha)")
            symbol = st.text_input("Stock Symbol (e.g., RELIANCE)")
            quantity = st.number_input("Quantity", min_value=1, step=1, format="%d")
            avg_price = st.number_input("Average Price (₹)", min_value=0.01, step=0.01, format="%.2f")
            if st.form_submit_button("✅ Buy Stock"):
                if not all([portfolio_name, account_name, symbol]):
                    st.error("Please fill all fields.")
                else:
                    price = get_stock_price(symbol)
                    if price is None: st.error("❌ Invalid symbol or price unavailable.")
                    else:
                        buy_stock(symbol, quantity, avg_price, portfolio_name, account_name)
                        st.success(f"✅ Bought {quantity} shares of {symbol.upper()} at ₹{avg_price}")
                        st.balloons()

    elif st.session_state.selected_service=="sell":
        st.markdown("### 📉 Sell Stock")
        if not st.session_state.portfolio: st.info("No stocks to sell.")
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
                quantity = st.number_input("Quantity to Sell", min_value=1, max_value=current_qty, step=1, format="%d")
                if st.form_submit_button("✅ Sell Stock"):
                    success, msg = sell_stock(symbol, quantity, portfolio_name, account_name)
                    if success: st.success(f"✅ {msg}"); st.balloons()
                    else: st.error(f"❌ {msg}")
