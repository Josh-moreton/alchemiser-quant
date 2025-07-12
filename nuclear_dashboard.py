#!/usr/bin/env python3
"""
Nuclear Energy Trading Bot Dashboard
Interactive Streamlit dashboard for monitoring the Nuclear Energy strategy
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Import our Nuclear strategy
from nuclear_trading_bot import NuclearTradingBot, NuclearStrategyEngine
from nuclear_backtest import NuclearBacktester

# Page config
st.set_page_config(
    page_title="Nuclear Energy Trading Dashboard",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #007bff;
        margin-bottom: 1rem;
    }
    .signal-buy {
        background: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 8px;
    }
    .signal-hold {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 8px;
    }
    .signal-sell {
        background: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_current_signal():
    """Get current trading signal"""
    try:
        bot = NuclearTradingBot()
        alert = bot.run_analysis()
        return alert
    except Exception as e:
        st.error(f"Error getting signal: {e}")
        return None

@st.cache_data(ttl=3600)  # Cache for 1 hour
def run_backtest(start_date, end_date=None):
    """Run backtest with caching"""
    try:
        backtester = NuclearBacktester(start_date=start_date, end_date=end_date)
        results = backtester.run_backtest()
        return results
    except Exception as e:
        st.error(f"Error running backtest: {e}")
        return None

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_market_data():
    """Get current market data for key symbols"""
    try:
        strategy = NuclearStrategyEngine()
        market_data = strategy.get_market_data()
        indicators = strategy.calculate_indicators(market_data)
        return indicators
    except Exception as e:
        st.error(f"Error getting market data: {e}")
        return None

def create_portfolio_chart(df_results):
    """Create interactive portfolio performance chart"""
    if df_results is None or df_results.empty:
        return None
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Portfolio Value', 'Cumulative Returns', 'Drawdown', 'Position Distribution'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"type": "domain"}]]
    )
    
    # Portfolio value
    fig.add_trace(
        go.Scatter(
            x=df_results['date'],
            y=df_results['portfolio_value'],
            name='Portfolio Value',
            line=dict(color='#007bff', width=2)
        ),
        row=1, col=1
    )
    
    # Returns
    fig.add_trace(
        go.Scatter(
            x=df_results['date'],
            y=df_results['return_pct'],
            name='Returns (%)',
            line=dict(color='#28a745', width=2)
        ),
        row=1, col=2
    )
    
    # Drawdown
    running_max = df_results['portfolio_value'].expanding().max()
    drawdown = (df_results['portfolio_value'] - running_max) / running_max * 100
    
    fig.add_trace(
        go.Scatter(
            x=df_results['date'],
            y=drawdown,
            name='Drawdown (%)',
            fill='tonexty',
            fillcolor='rgba(255, 0, 0, 0.3)',
            line=dict(color='red', width=1)
        ),
        row=2, col=1
    )
    
    # Position distribution pie chart
    positions = df_results['position'].value_counts()
    fig.add_trace(
        go.Pie(
            labels=positions.index,
            values=positions.values,
            name="Position Distribution"
        ),
        row=2, col=2
    )
    
    fig.update_layout(
        height=600,
        showlegend=True,
        title_text="Nuclear Energy Strategy Performance"
    )
    
    return fig

def create_indicators_chart(indicators):
    """Create indicators overview chart"""
    if not indicators:
        return None
    
    # Key symbols to display
    key_symbols = ['SPY', 'QQQ', 'TQQQ', 'UVXY', 'SMR', 'BWXT']
    available_symbols = [s for s in key_symbols if s in indicators]
    
    if not available_symbols:
        return None
    
    # Create RSI chart
    rsi_data = []
    for symbol in available_symbols:
        rsi_data.append({
            'Symbol': symbol,
            'RSI_10': indicators[symbol]['rsi_10'],
            'RSI_20': indicators[symbol]['rsi_20'],
            'Price': indicators[symbol]['current_price']
        })
    
    df_rsi = pd.DataFrame(rsi_data)
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('RSI (10-day)', 'RSI (20-day)', 'Current Prices', 'MA Returns (90-day)'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # RSI 10
    fig.add_trace(
        go.Bar(
            x=df_rsi['Symbol'],
            y=df_rsi['RSI_10'],
            name='RSI 10',
            marker_color=['red' if x > 70 else 'green' if x < 30 else 'blue' for x in df_rsi['RSI_10']]
        ),
        row=1, col=1
    )
    
    # RSI 20
    fig.add_trace(
        go.Bar(
            x=df_rsi['Symbol'],
            y=df_rsi['RSI_20'],
            name='RSI 20',
            marker_color=['red' if x > 70 else 'green' if x < 30 else 'blue' for x in df_rsi['RSI_20']]
        ),
        row=1, col=2
    )
    
    # Current prices
    fig.add_trace(
        go.Bar(
            x=df_rsi['Symbol'],
            y=df_rsi['Price'],
            name='Current Price',
            marker_color='orange'
        ),
        row=2, col=1
    )
    
    # MA Returns
    ma_returns = [indicators[s]['ma_return_90'] for s in available_symbols if s in indicators]
    fig.add_trace(
        go.Bar(
            x=available_symbols,
            y=ma_returns,
            name='90-day MA Return',
            marker_color=['green' if x > 0 else 'red' for x in ma_returns]
        ),
        row=2, col=2
    )
    
    # Add RSI reference lines (plotly subplots don't support add_hline with row/col)
    # We'll add them as scatter traces instead
    for symbol_idx, symbol in enumerate(available_symbols):
        # Add horizontal lines at RSI 70 and 30 for visual reference
        pass  # Skip for now, can add annotations if needed
    
    fig.update_layout(
        height=600,
        showlegend=False,
        title_text="Market Indicators Overview"
    )
    
    return fig

def display_signal_card(alert):
    """Display trading signal in a card format"""
    if not alert:
        st.error("No trading signal available")
        return
    
    # Determine card style based on action
    if alert.action == 'BUY':
        card_class = "signal-buy"
        icon = "📈"
        color = "green"
    elif alert.action == 'SELL':
        card_class = "signal-sell"
        icon = "📉"
        color = "red"
    else:
        card_class = "signal-hold"
        icon = "⏸️"
        color = "orange"
    
    # Create the signal card
    st.markdown(f"""
    <div class="{card_class}">
        <h3>{icon} {alert.action} {alert.symbol}</h3>
        <p><strong>Price:</strong> ${alert.price:.2f}</p>
        <p><strong>Reason:</strong> {alert.reason}</p>
        <p><strong>Time:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><em>Deterministic Strategy - No Confidence Scoring</em></p>
    </div>
    """, unsafe_allow_html=True)

def load_alert_history():
    """Load historical alerts from JSON file"""
    try:
        alerts = []
        with open('nuclear_alerts.json', 'r') as f:
            for line in f:
                try:
                    alert = json.loads(line.strip())
                    alerts.append(alert)
                except:
                    continue
        return pd.DataFrame(alerts)
    except FileNotFoundError:
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading alert history: {e}")
        return pd.DataFrame()

def main():
    """Main dashboard function"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>⚛️ Nuclear Energy Trading Dashboard</h1>
        <p>Real-time monitoring and backtesting for the Nuclear Energy Strategy</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.header("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["🏠 Overview", "📊 Live Signal", "📈 Backtest", "📋 Alert History", "🔍 Market Data"]
    )
    
    if page == "🏠 Overview":
        st.header("Strategy Overview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### Nuclear Energy Strategy
            
            This strategy is based on the "Nuclear Energy with Feaver Frontrunner V5" 
            from Composer.trade, backtested from 2022-03-24.
            
            **Key Features:**
            - Market regime detection via RSI levels
            - Volatility protection with UVXY
            - Nuclear energy stocks in bull markets
            - Tech/bond dynamics in bear markets
            
            **Nuclear Stocks:**
            - SMR (Small Modular Reactor)
            - BWXT (BWX Technologies)
            - LEU (Centrus Energy)
            - EXC (Exelon Corporation)
            - NLR (VanEck Uranium+Nuclear Energy ETF)
            - OKLO (Oklo Inc.)
            """)
        
        with col2:
            st.markdown("""
            ### Strategy Logic
            
            1. **Overbought Protection**: When SPY RSI > 79, switch to UVXY for volatility protection
            2. **Extreme Overbought**: When any major index RSI > 81, full UVXY allocation
            3. **Oversold Opportunities**: Buy TQQQ when RSI < 30, UPRO when SPY RSI < 30
            4. **Bull Market**: When SPY > 200-day MA, invest in top nuclear energy stocks
            5. **Bear Market**: Complex logic involving bonds vs tech shorts
            
            ### Risk Management
            - Daily rebalancing
            - Deterministic rules (no subjective decisions)
            - Multi-asset diversification
            - Volatility protection in extreme conditions
            """)
        
        # Quick stats
        st.header("Quick Stats")
        col1, col2, col3, col4 = st.columns(4)
        
        # Get current signal
        current_signal = get_current_signal()
        
        with col1:
            if current_signal:
                st.metric("Current Signal", f"{current_signal.action} {current_signal.symbol}")
            else:
                st.metric("Current Signal", "Loading...")
        
        with col2:
            # Get market data
            indicators = get_market_data()
            if indicators and 'SPY' in indicators:
                spy_rsi = indicators['SPY']['rsi_10']
                st.metric("SPY RSI (10)", f"{spy_rsi:.1f}")
            else:
                st.metric("SPY RSI (10)", "Loading...")
        
        with col3:
            if indicators and 'SPY' in indicators:
                spy_price = indicators['SPY']['current_price']
                spy_ma = indicators['SPY']['ma_200']
                trend = "Bull" if spy_price > spy_ma else "Bear"
                st.metric("Market Trend", trend)
            else:
                st.metric("Market Trend", "Loading...")
        
        with col4:
            # Count nuclear stocks in bull territory
            if indicators:
                nuclear_symbols = ['SMR', 'BWXT', 'LEU', 'EXC', 'NLR', 'OKLO']
                bullish_count = sum(1 for s in nuclear_symbols 
                                  if s in indicators and indicators[s]['ma_return_90'] > 0)
                st.metric("Bullish Nuclear Stocks", f"{bullish_count}/{len(nuclear_symbols)}")
            else:
                st.metric("Bullish Nuclear Stocks", "Loading...")
    
    elif page == "📊 Live Signal":
        st.header("Live Trading Signal")
        
        # Get current signal
        if st.button("🔄 Refresh Signal"):
            st.cache_data.clear()
        
        current_signal = get_current_signal()
        
        if current_signal:
            display_signal_card(current_signal)
            
            # Show market conditions
            st.subheader("Current Market Conditions")
            indicators = get_market_data()
            
            if indicators:
                # Create indicators chart
                fig = create_indicators_chart(indicators)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                
                # Key metrics table
                st.subheader("Key Metrics")
                key_symbols = ['SPY', 'QQQ', 'TQQQ', 'UVXY', 'SMR', 'BWXT']
                metrics_data = []
                
                for symbol in key_symbols:
                    if symbol in indicators:
                        metrics_data.append({
                            'Symbol': symbol,
                            'Price': f"${indicators[symbol]['current_price']:.2f}",
                            'RSI (10)': f"{indicators[symbol]['rsi_10']:.1f}",
                            'RSI (20)': f"{indicators[symbol]['rsi_20']:.1f}",
                            'MA Return (90d)': f"{indicators[symbol]['ma_return_90']:.2f}%"
                        })
                
                if metrics_data:
                    df_metrics = pd.DataFrame(metrics_data)
                    st.dataframe(df_metrics, use_container_width=True)
        else:
            st.error("Unable to get current trading signal")
    
    elif page == "📈 Backtest":
        st.header("Strategy Backtesting")
        
        # Backtest parameters
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=datetime(2022, 3, 24),
                min_value=datetime(2020, 1, 1),
                max_value=datetime.now()
            )
        
        with col2:
            end_date = st.date_input(
                "End Date",
                value=datetime.now(),
                min_value=datetime(2020, 1, 1),
                max_value=datetime.now()
            )
        
        if st.button("🚀 Run Backtest"):
            with st.spinner("Running backtest... This may take a few minutes."):
                results = run_backtest(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
                
                if results is not None and not results.empty:
                    # Performance metrics
                    st.subheader("Performance Summary")
                    
                    initial_value = 100000
                    final_value = results['portfolio_value'].iloc[-1]
                    total_return = ((final_value - initial_value) / initial_value) * 100
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Return", f"{total_return:.2f}%")
                    
                    with col2:
                        days = (results['date'].iloc[-1] - results['date'].iloc[0]).days
                        years = days / 365.25
                        annualized_return = (final_value / initial_value) ** (1/years) - 1
                        st.metric("Annualized Return", f"{annualized_return:.2f}%")
                    
                    with col3:
                        daily_returns = results['portfolio_value'].pct_change().dropna()
                        volatility = daily_returns.std() * np.sqrt(252)
                        st.metric("Volatility", f"{volatility:.2f}%")
                    
                    with col4:
                        running_max = results['portfolio_value'].expanding().max()
                        drawdown = (results['portfolio_value'] - running_max) / running_max
                        max_drawdown = drawdown.min() * 100
                        st.metric("Max Drawdown", f"{max_drawdown:.2f}%")
                    
                    # Charts
                    st.subheader("Performance Charts")
                    fig = create_portfolio_chart(results)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Position analysis
                    st.subheader("Position Analysis")
                    positions = results['position'].value_counts()
                    st.bar_chart(positions)
                    
                    # Download results
                    csv = results.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Results CSV",
                        data=csv,
                        file_name=f"nuclear_backtest_{start_date}_{end_date}.csv",
                        mime="text/csv"
                    )
                else:
                    st.error("Backtest failed or returned no results")
    
    elif page == "📋 Alert History":
        st.header("Alert History")
        
        # Load alert history
        df_alerts = load_alert_history()
        
        if not df_alerts.empty:
            # Convert timestamp
            df_alerts['timestamp'] = pd.to_datetime(df_alerts['timestamp'])
            df_alerts = df_alerts.sort_values('timestamp', ascending=False)
            
            # Filters
            col1, col2 = st.columns(2)
            
            with col1:
                days_back = st.selectbox("Show alerts from last:", [7, 30, 90, 365], index=1)
            
            with col2:
                action_filter = st.selectbox("Filter by action:", ['All', 'BUY', 'SELL', 'HOLD'])
            
            # Filter data
            cutoff_date = datetime.now() - timedelta(days=days_back)
            filtered_alerts = df_alerts[df_alerts['timestamp'] >= cutoff_date]
            
            if action_filter != 'All':
                filtered_alerts = filtered_alerts[filtered_alerts['action'] == action_filter]
            
            # Display alerts
            st.subheader(f"Recent Alerts ({len(filtered_alerts)} total)")
            
            for _, alert in filtered_alerts.head(20).iterrows():
                with st.expander(f"{alert['timestamp'].strftime('%Y-%m-%d %H:%M')} - {alert['action']} {alert['symbol']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Price:** ${alert['price']:.2f}")
                        st.write(f"**Action:** {alert['action']}")
                    with col2:
                        st.write(f"**Symbol:** {alert['symbol']}")
                        st.write(f"**Reason:** {alert['reason']}")
        else:
            st.info("No alert history found. Run the trading bot to generate alerts.")
    
    elif page == "🔍 Market Data":
        st.header("Market Data Analysis")
        
        # Get market data
        indicators = get_market_data()
        
        if indicators:
            # Create indicators chart
            fig = create_indicators_chart(indicators)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            
            # Detailed table
            st.subheader("Detailed Market Data")
            
            detailed_data = []
            for symbol, data in indicators.items():
                detailed_data.append({
                    'Symbol': symbol,
                    'Current Price': f"${data['current_price']:.2f}",
                    'RSI (10)': f"{data['rsi_10']:.1f}",
                    'RSI (20)': f"{data['rsi_20']:.1f}",
                    'MA (200)': f"${data['ma_200']:.2f}",
                    'MA (20)': f"${data['ma_20']:.2f}",
                    'MA Return (90d)': f"{data['ma_return_90']:.2f}%",
                    'Cum Return (60d)': f"{data['cum_return_60']:.2f}%"
                })
            
            df_detailed = pd.DataFrame(detailed_data)
            st.dataframe(df_detailed, use_container_width=True)
            
            # Nuclear stocks analysis
            st.subheader("Nuclear Stocks Analysis")
            nuclear_symbols = ['SMR', 'BWXT', 'LEU', 'EXC', 'NLR', 'OKLO']
            nuclear_data = []
            
            for symbol in nuclear_symbols:
                if symbol in indicators:
                    data = indicators[symbol]
                    nuclear_data.append({
                        'Symbol': symbol,
                        'Price': data['current_price'],
                        'MA Return (90d)': data['ma_return_90'],
                        'RSI (10)': data['rsi_10'],
                        'Trend': 'Bullish' if data['ma_return_90'] > 0 else 'Bearish'
                    })
            
            if nuclear_data:
                df_nuclear = pd.DataFrame(nuclear_data)
                df_nuclear = df_nuclear.sort_values('MA Return (90d)', ascending=False)
                
                # Color code the dataframe
                def highlight_trend(row):
                    if row['Trend'] == 'Bullish':
                        return ['background-color: #d4edda'] * len(row)
                    else:
                        return ['background-color: #f8d7da'] * len(row)
                
                styled_df = df_nuclear.style.apply(highlight_trend, axis=1)
                st.dataframe(styled_df, use_container_width=True)
        else:
            st.error("Unable to load market data")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.8em;">
        Nuclear Energy Trading Dashboard | Based on Composer.trade Strategy | 
        ⚠️ For educational purposes only. Not financial advice.
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
