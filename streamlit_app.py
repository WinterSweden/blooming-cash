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
    /* Main background - dark blue/black */
    .stApp {
        background: #0a0e1a;
    }
    
    /* Top bar dark */
    header[data-testid="stHeader"] {
        background: #0a0e1a !important;
    }
    
    /* Hide streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Welcome text */
    .welcome-text {
        font-size: 36px;
        font-weight: 600;
        color: #ffffff;
        text-align: center;
        margin-bottom: 10px;
        text-transform: none;
    }
    
    /* Balance bar */
    .balance-bar {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        margin: 20px auto;
        max-width: 800px;
        color: white;
        font-size: 18px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Service buttons */
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
    
    /* Input fields */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
        background: rgba(255, 255, 255, 0.08);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 8px;
    }
    
    .stTextInput>div>div>input:focus, .stNumberInput>div>div>input:focus {
        border-color: rgba(255, 255, 255, 0.3);
        box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.3);
    }
    
    /* Result box */
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
    
    /* Dataframe styling */
    .stDataFrame {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 10px;
    }
    
    /* Table header */
    .stDataFrame thead tr th {
        background: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    
    /* Table cells */
    .stDataFrame tbody tr td {
        background: rgba(255, 255, 255, 0.03) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
</style>
""", unsafe_allow_html=True)

# Config file path
CONFIG_FILE = "config.json"

# Initialize session state
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []
if 'selected_service' not in st.session_state:
    st.session_state.selected_service = "dashboard"

# Load config from file
def load_config():
    """Load portfolio from config.json"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                st.session_state.portfolio = data.get('portfolio', [])
        except:
            pass

# Save config to file
def save_config():
    """Save portfolio to config.json"""
    data = {
        'portfolio': st.session_state.portfolio,
        'last_updated': datetime.now().isoformat()
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# Fetch stock price from NSE
@st.cache_data(ttl=60)  # Cache for 1 minute
def get_stock_price(symbol):
    """Get current stock price from Yahoo Finance"""
    try:
        # Make sure symbol is uppercase and add .NS for NSE
        symbol = symbol.upper()
        ticker = yf.Ticker(f"{symbol}.NS")
        data = ticker.history(period="1d")
        if not data.empty:
            return data['Close'].iloc[-1]
        return None
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

# Calculate total P/L
def calculate_total_pl():
    """Calculate total portfolio P/L"""
    total = 0.0
    for stock in st.session_state.portfolio:
        current_price = get_stock_price(stock['symbol'])
        if current_price:
            pl = (current_price - stock['avg_price']) * stock['quantity']
            total += pl
    return total

# Buy stock
def buy_stock(symbol, quantity, avg_price, portfolio_name, account_name):
    """Add stock to portfolio with weighted average"""
    symbol = symbol.upper()
    
    # Check if stock already exists in same portfolio and account
    existing_idx = None
    for i, stock in enumerate(st.session_state.portfolio):
        if stock['symbol'] == symbol and stock['portfolio'] == portfolio_name and stock['account'] == account_name:
            existing_idx = i
            break
    
    if existing_idx is not None:
        # Update with weighted average
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

# Sell stock
def sell_stock(symbol, quantity, portfolio_name, account_name):
    """Sell stock from portfolio"""
    symbol = symbol.upper()
    
    # Find stock in portfolio and account
    stock_idx = None
    for i, stock in enumerate(st.session_state.portfolio):
        if stock['symbol'] == symbol and stock['portfolio'] == portfolio_name and stock['account'] == account_name:
            stock_idx = i
            break
    
    if stock_idx is None:
        return False, f"You don't own {symbol} in {portfolio_name}'s {account_name}"
    
    stock = st.session_state.portfolio[stock_idx]
    
    if quantity > stock['quantity']:
        return False, f"You only own {stock['quantity']} shares of {symbol} in {portfolio_name}'s {account_name}"
    
    if quantity == stock['quantity']:
        # Remove entirely
        st.session_state.portfolio.pop(stock_idx)
    else:
        # Reduce quantity
        st.session_state.portfolio[stock_idx]['quantity'] -= quantity
    
    save_config()
    return True, f"Sold {quantity} shares of {symbol} from {portfolio_name}'s {account_name}"

# Load config on startup
load_config()

# Main App Layout
st.markdown('<h1 class="welcome-text">blooming cash 🌸</h1>', unsafe_allow_html=True)

# Balance bar
total_pl = calculate_total_pl()
pl_color = "#10b981" if total_pl >= 0 else "#ef4444"
pl_sign = "+" if total_pl >= 0 else ""

# Get unique accounts
accounts = list(set([stock['account'] for stock in st.session_state.portfolio]))
portfolios = list(set([stock['portfolio'] for stock in st.session_state.portfolio]))

st.markdown(f'''
    <div class="balance-bar">
        📊 Total P/L: <span style="color: {pl_color}; font-weight: bold; font-size: 24px;">{pl_sign}₹{total_pl:.2f}</span> | 
        💼 Holdings: {len(st.session_state.portfolio)} stocks | 
        👥 Portfolios: {len(portfolios)}
    </div>
''', unsafe_allow_html=True)

# Layout: Services on left, content on right
col_left, col_right = st.columns([1, 3])

with col_left:
    st.markdown("### Services")
    
    if st.button("📊 Dashboard", use_container_width=True):
        st.session_state.selected_service = "dashboard"
        st.rerun()
    
    if st.button("📈 Buy Stock", use_container_width=True):
        st.session_state.selected_service = "buy"
        st.rerun()
    
    if st.button("📉 Sell Stock", use_container_width=True):
        st.session_state.selected_service = "sell"
        st.rerun()
    
    if st.button("🔄 Refresh Prices", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with col_right:
    # DASHBOARD
    if st.session_state.selected_service == "dashboard":
        st.markdown("### 📊 Family Portfolio Dashboard")
        
        if not st.session_state.portfolio:
            st.markdown("""
            <div class="result-box">
No stocks in portfolio yet! 🌸

Get started by:
• Click "📈 Buy Stock" to add holdings
• Track stocks from multiple accounts (Dad, Mom, Self, etc.)
• Your data is saved locally in config.json

Features:
✅ FREE - No API costs!
✅ Works with ANY broker (Zerodha, HDFC, Groww, Upstox, etc.)
✅ Real-time NSE price tracking
✅ Automatic P/L calculation
            </div>
            """, unsafe_allow_html=True)
        else:
            # Build portfolio table
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
                        'Current Price': 'Loading...',
                        'Total P/L': 'N/A',
                        'P/L %': 'N/A'
                    })
            
            df = pd.DataFrame(portfolio_data)
            
            # Display table
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Summary stats
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_stocks = len(st.session_state.portfolio)
                st.metric("Total Stocks", total_stocks)
            
            with col2:
                total_qty = sum(s['quantity'] for s in st.session_state.portfolio)
                st.metric("Total Shares", f"{total_qty:.0f}")
            
            with col3:
                total_invested = sum(s['quantity'] * s['avg_price'] for s in st.session_state.portfolio)
                st.metric("Total Invested", f"₹{total_invested:.2f}")
            
            with col4:
                st.metric("Portfolios", len(portfolios))
    
    # BUY STOCK
    elif st.session_state.selected_service == "buy":
        st.markdown("### 📈 Buy Stock")
        
        with st.form("buy_form"):
            portfolio_name = st.text_input("Portfolio (e.g., Dad, Mom, Self)")
            account_name = st.text_input("Account Name (e.g., Zerodha, HDFC, Groww)")
            symbol = st.text_input("Stock Symbol (e.g., RELIANCE, TCS, INFY)")
            quantity = st.number_input("Quantity", min_value=0.01, step=0.01, format="%.2f")
            avg_price = st.number_input("Average Price Bought At (₹)", min_value=0.01, step=0.01, format="%.2f")
            
            submitted = st.form_submit_button("✅ Buy Stock")
            
            if submitted:
                if not portfolio_name:
                    st.error("Please enter portfolio name")
                elif not account_name:
                    st.error("Please enter account name")
                elif not symbol:
                    st.error("Please enter stock symbol")
                elif quantity <= 0:
                    st.error("Quantity must be greater than 0")
                elif avg_price <= 0:
                    st.error("Price must be greater than 0")
                else:
                    buy_stock(symbol, quantity, avg_price, portfolio_name, account_name)
                    st.success(f"✅ Bought {quantity} shares of {symbol.upper()} at ₹{avg_price} in {portfolio_name}'s {account_name}")
                    st.balloons()

    
    # SELL STOCK
    elif st.session_state.selected_service == "sell":
        st.markdown("### 📉 Sell Stock")
        
        if not st.session_state.portfolio:
            st.info("No stocks in portfolio to sell. Buy some stocks first!")
        else:
            with st.form("sell_form"):
                # Get unique portfolios
                portfolios_list = list(set([stock['portfolio'] for stock in st.session_state.portfolio]))
                portfolio_name = st.selectbox("Portfolio", portfolios_list)
                
                # Get accounts in selected portfolio
                accounts_in_portfolio = list(set([stock['account'] for stock in st.session_state.portfolio if stock['portfolio'] == portfolio_name]))
                account_name = st.selectbox("Account Name", accounts_in_portfolio)
                
                # Get stocks in selected portfolio and account
                stocks_in_selection = [stock['symbol'] for stock in st.session_state.portfolio 
                                      if stock['portfolio'] == portfolio_name and stock['account'] == account_name]
                
                if stocks_in_selection:
                    symbol = st.selectbox("Stock Symbol", stocks_in_selection)
                    
                    # Get current quantity
                    current_qty = 0
                    for stock in st.session_state.portfolio:
                        if stock['symbol'] == symbol and stock['portfolio'] == portfolio_name and stock['account'] == account_name:
                            current_qty = stock['quantity']
                            break
                    
                    st.info(f"You own {current_qty} shares of {symbol} in {portfolio_name}'s {account_name}")
                    
                    quantity = st.number_input("Quantity to Sell", min_value=0.01, max_value=float(current_qty), step=0.01, format="%.2f")
                    
                    submitted = st.form_submit_button("✅ Sell Stock")
                    
                    if submitted:
                        if quantity <= 0:
                            st.error("Quantity must be greater than 0")
                        else:
                            success, message = sell_stock(symbol, quantity, portfolio_name, account_name)
                            if success:
                                st.success(f"✅ {message}")
                                st.balloons()
                            else:
                                st.error(f"❌ {message}")
                else:
                    st.warning(f"No stocks in {portfolio_name}'s {account_name}")
