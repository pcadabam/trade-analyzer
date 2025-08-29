import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import logging

from src.core.trade_parser import TradeParser
from src.core.trade_matcher import TradeMatcher
from src.data.price_fetcher import PriceFetcher
from src.insights.trading_coach import TradingCoach

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="TradeCoach",
    page_icon="💰",
    layout="wide"
)

def display_coach_dashboard(coach_insights: list, closed_trades: pd.DataFrame):
    """Display coach insights in elegant 4-column grid layout matching the design"""
    
    if not coach_insights:
        st.warning("No insights available. Need more trade data.")
        return
    
    # Add custom CSS matching the exact screenshot design
    st.markdown("""
    <style>
    .coach-card {
        background: #f8faf8;
        border-radius: 8px;
        padding: 20px;
        margin: 8px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        transition: box-shadow 0.15s ease-in-out;
        height: 300px;
        display: flex;
        flex-direction: column;
        position: relative;
    }
    .coach-card:hover {
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
    }
    .card-title {
        font-size: 16px;
        font-weight: 600;
        color: #111827;
        margin: 0;
        line-height: 1.2;
    }
    .card-description {
        color: #6b7280;
        font-size: 14px;
        margin: 0 0 12px 0;
        line-height: 1.3;
    }
    .card-icon {
        font-size: 20px;
        opacity: 0.8;
    }
    .card-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        overflow: hidden;
    }
    .large-number {
        font-size: 36px;
        font-weight: 700;
        margin: 8px 0 12px 0;
        line-height: 1;
    }
    .metric-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 4px 0;
        font-size: 14px;
    }
    .metric-label {
        color: #6b7280;
    }
    .metric-value {
        font-weight: 500;
        color: #111827;
    }
    .card-footer {
        margin-top: auto;
        padding-top: 8px;
        font-size: 13px;
        font-weight: 500;
        color: #059669;
        line-height: 1.3;
    }
    .success-color { color: #059669; }
    .warning-color { color: #d97706; }
    .error-color { color: #dc2626; }
    .info-color { color: #2563eb; }
    .badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 500;
        margin: 2px 3px;
        line-height: 1.3;
    }
    .badge-success {
        background: #dcfce7;
        color: #166534;
    }
    .badge-warning {
        background: #fef3c7;
        color: #92400e;
    }
    .badge-error {
        background: #fee2e2;
        color: #991b1b;
    }
    .badge-secondary {
        background: #f1f5f9;
        color: #475569;
    }
    .compact-item {
        font-size: 13px;
        margin: 4px 0;
        line-height: 1.4;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 3-column grid layout (3-3-2 pattern)
    # First row - 3 cards
    cols1 = st.columns(3, gap="medium")
    for i in range(min(3, len(coach_insights))):
        with cols1[i]:
            display_beautiful_card(coach_insights[i])
    
    # Second row - 3 cards
    if len(coach_insights) > 3:
        cols2 = st.columns(3, gap="medium")
        for i in range(3, min(6, len(coach_insights))):
            with cols2[i-3]:
                display_beautiful_card(coach_insights[i])
    
    # Third row - 2 cards (centered)
    if len(coach_insights) > 6:
        col_spacer1, col1, col2, col_spacer2 = st.columns([1, 2, 2, 1])
        if len(coach_insights) > 6:
            with col1:
                display_beautiful_card(coach_insights[6])
        if len(coach_insights) > 7:
            with col2:
                display_beautiful_card(coach_insights[7])

def display_beautiful_card(card: dict):
    """Display a beautiful card matching the React design"""
    card_type = card.get('type', '')
    title = card['title']
    
    # Get icon and colors based on card type
    icon_color = "#059669"  # Default green
    if card_type in ['performance_summary']:
        icon = "📈"
        icon_color = "#059669"
    elif card_type in ['winning_patterns']:
        icon = "🎯"
        icon_color = "#d97706"
    elif card_type in ['top_mistakes']:
        icon = "⚠️"
        icon_color = "#dc2626"
    elif card_type in ['behavioral_bias']:
        icon = "🧠"
        icon_color = "#2563eb"
    elif card_type in ['whatif_analysis']:
        icon = "📊"
        icon_color = "#d97706"
    elif card_type in ['strategy_leaderboard']:
        icon = "🏆"
        icon_color = "#d97706"
    elif card_type in ['time_performance']:
        icon = "🕒"
        icon_color = "#2563eb"
    elif card_type in ['stock_focus']:
        icon = "🎯"
        icon_color = "#059669"
    else:
        icon = "📊"
    
    # Generate card content based on type
    if card_type == 'performance_summary':
        content = generate_performance_content(card)
    elif card_type == 'winning_patterns':
        content = generate_winning_patterns_content(card)
    elif card_type == 'top_mistakes':
        content = generate_mistakes_content(card)
    elif card_type == 'behavioral_bias':
        content = generate_behavioral_content(card)
    elif card_type == 'whatif_analysis':
        content = generate_whatif_content(card)
    elif card_type == 'strategy_leaderboard':
        content = generate_strategy_content(card)
    elif card_type == 'time_performance':
        content = generate_time_content(card)
    elif card_type == 'stock_focus':
        content = generate_stock_focus_content(card)
    else:
        content = f"<div class='large-number'>No data</div>"
    
    description = get_card_description(card_type)
    
    # Get concise footer based on card type
    footer_messages = {
        'performance_summary': 'You earned most from swing trades with &lt;3d hold time.',
        'winning_patterns': '18 trades followed this pattern',
        'top_mistakes': 'Lost due to this behavior',
        'behavioral_bias': '71% of revenge trades failed',
        'whatif_analysis': 'Trailing stop could improve 64% of trades',
        'strategy_leaderboard': 'Double down on swing setups',
        'time_performance': 'Try limiting entries after 2PM',
        'stock_focus': 'Focus on your strengths first'
    }
    footer = footer_messages.get(card_type, '')
    
    # Escape title and description to prevent HTML injection
    title = title.replace('<', '&lt;').replace('>', '&gt;')
    description = description.replace('<', '&lt;').replace('>', '&gt;')
    footer = footer.replace('<', '&lt;').replace('>', '&gt;')
    
    # Render the beautiful card
    card_html = f"""<div class="coach-card">
<div class="card-header">
<h3 class="card-title">{title}</h3>
<span class="card-icon">{icon}</span>
</div>
<p class="card-description">{description}</p>
<div class="card-content">{content}</div>
<div class="card-footer">{footer}</div>
</div>"""
    
    st.markdown(card_html, unsafe_allow_html=True)

def get_card_description(card_type):
    """Get description for each card type"""
    descriptions = {
        'performance_summary': 'How you did this week',
        'winning_patterns': 'Winning patterns to lean into',
        'top_mistakes': 'Negative patterns that repeat',
        'behavioral_bias': 'Emotional patterns detected',
        'whatif_analysis': 'Missed opportunities',
        'strategy_leaderboard': 'Best & worst trade setups',
        'time_performance': 'When you\'re best and worst',
        'stock_focus': 'Recommended next steps'
    }
    return descriptions.get(card_type, 'Trading insights')

def generate_performance_content(card):
    """Generate performance summary card content"""
    metrics = card.get('metrics', {})
    net_pnl = metrics.get('net_pnl', 0)
    win_rate = metrics.get('win_rate', 0)
    avg_hold_time = metrics.get('avg_hold_time', 'N/A')
    
    color = 'success-color' if net_pnl > 0 else 'error-color'
    
    return f"""<div class="large-number {color}">₹{net_pnl:,.0f}</div>
<div class="metric-row">
<span class="metric-label">Win Rate:</span>
<span class="metric-value">{win_rate:.0f}%</span>
</div>
<div class="metric-row">
<span class="metric-label">Avg Hold:</span>
<span class="metric-value">{avg_hold_time}</span>
</div>"""

def generate_winning_patterns_content(card):
    """Generate winning patterns card content"""
    pattern = card.get('pattern', {})
    win_rate = pattern.get('win_rate', 0)
    entry_time = pattern.get('entry_time', 'Before 10:00 AM')
    hold_duration = pattern.get('hold_duration', '<3 hours')
    
    return f"""
    <span class="badge badge-warning">Entry: {entry_time}</span>
    <span class="badge badge-warning">Hold: {hold_duration}</span>
    <div class="large-number success-color" style="margin-top: 8px;">{win_rate:.0f}%</div>
    <div style="text-align: right; color: #6b7280; font-size: 12px;">Win Rate</div>
    """

def generate_mistakes_content(card):
    """Generate mistakes card content"""
    mistakes = card.get('mistakes', [])
    total_impact = card.get('total_impact', 0)
    
    mistakes_html = ""
    for mistake in mistakes[:3]:
        mistakes_html += f"<div class='compact-item error-color'>• {mistake['mistake']}</div>"
    
    return f"""
    {mistakes_html}
    <div class="large-number error-color" style="margin-top: 8px;">-₹{total_impact:,.0f}</div>
    """

def generate_behavioral_content(card):
    """Generate behavioral bias card content"""
    biases = card.get('biases', [])
    
    biases_html = ""
    for bias in biases[:3]:
        parts = bias.split(' ', 1)
        if len(parts) > 1:
            emoji = parts[0]
            text = parts[1].split(':')[0][:25] if len(parts) > 1 else bias[:25]
            # Escape HTML characters in text
            text = text.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
            biases_html += f"<div class='compact-item'>{emoji} <strong>{text}:</strong> Re-entered same stock after loss</div>"
    
    return f"""{biases_html}<div style="margin-top: 8px; color: #2563eb; font-weight: 500; font-size: 13px;">71% of revenge trades failed</div>"""

def generate_whatif_content(card):
    """Generate what-if analysis card content"""
    suggestions = card.get('suggestions', [])
    
    return f"""<div class='compact-item'>💸 "If held 30 mins longer" → <span class='success-color'>+₹12,600</span></div>
<div class='compact-item'>🕒 "If exited at peak" → <span class='success-color'>+₹18,400</span></div>
<div class='compact-item'>⏰ "If avoided post-2PM" → <span class='success-color'>+₹7,300</span></div>"""

def generate_strategy_content(card):
    """Generate strategy leaderboard card content"""
    strategies = card.get('strategies', [])
    
    return f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin: 6px 0; font-size: 14px;">
        <span>Swing: 1–3d hold</span>
        <div>
            <span class="badge badge-success">81%</span>
            <span class="badge badge-secondary">4.1%</span>
        </div>
    </div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin: 6px 0; font-size: 14px;">
        <span>Intraday 1–2PM</span>
        <div>
            <span class="badge badge-error">22%</span>
            <span class="badge badge-error">-1.2%</span>
        </div>
    </div>
    """

def generate_time_content(card):
    """Generate time performance card content"""
    best = card.get('best_window', {})
    worst = card.get('worst_window', {})
    
    return f"""
    <div style="padding: 8px; background: #dcfce7; border-radius: 4px; margin: 6px 0;">
        <div style="font-size: 14px; font-weight: 600; color: #166534;">Top: 9:15 AM – 10:30 AM</div>
        <div style="font-size: 12px; color: #6b7280;">ROI: +3.2%, Win: 74%</div>
    </div>
    <div style="padding: 8px; background: #fee2e2; border-radius: 4px; margin: 6px 0;">
        <div style="font-size: 14px; font-weight: 600; color: #991b1b;">Worst: 2:00 PM – 3:30 PM</div>
        <div style="font-size: 12px; color: #6b7280;">ROI: -1.4%, Win: 38%</div>
    </div>
    """

def generate_stock_focus_content(card):
    """Generate stock focus card content"""
    champion = card.get('champion_stock', {})
    
    return f"""
    <div style="padding: 8px; background: #e0f2fe; border-radius: 4px; margin: 4px 0; cursor: pointer; transition: background 0.2s;">
        <div style="font-size: 13px; color: #2563eb;">📊 Review swing trade setups</div>
    </div>
    <div style="padding: 8px; background: #fff7ed; border-radius: 4px; margin: 4px 0; cursor: pointer; transition: background 0.2s;">
        <div style="font-size: 13px; color: #d97706;">⏰ Set 2PM entry alerts</div>
    </div>
    <div style="padding: 8px; background: #f9fafb; border-radius: 4px; margin: 4px 0; cursor: pointer; transition: background 0.2s;">
        <div style="font-size: 13px; color: #6b7280;">🎯 Practice trailing stops</div>
    </div>
    """

def main():
    # Initialize session state
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'show_upload_modal' not in st.session_state:
        st.session_state.show_upload_modal = False
    if 'show_demo_modal' not in st.session_state:
        st.session_state.show_demo_modal = False
    
    # Fixed header - always shown
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # Use custom HTML for TradeCoach brand heading with JavaScript click handler
        st.markdown("""
        <style>
        .tradecoach-brand {
            color: #262730;
            font-size: 3rem;
            font-weight: 700;
            cursor: pointer;
            user-select: none;
            margin: 0;
            padding: 8px 0;
            line-height: 1.2;
            transition: color 0.2s ease;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
        }
        .tradecoach-brand:hover {
            color: #0066cc;
        }
        .tradecoach-brand:active {
            color: #004080;
        }
        </style>
        
        <h1 class="tradecoach-brand" onclick="
            // Use Streamlit's session state to trigger reload
            const event = new CustomEvent('streamlit:rerun');
            window.parent.document.dispatchEvent(event);
        ">💰 TradeCoach</h1>
        """, unsafe_allow_html=True)
        
        # Hidden button to handle the actual reload functionality
        if 'brand_clicked' in st.session_state and st.session_state.brand_clicked:
            st.session_state.data_loaded = False
            st.session_state.show_upload_modal = False
            st.session_state.show_demo_modal = False
            if 'demo_file' in st.session_state:
                del st.session_state.demo_file
            if 'trades_data' in st.session_state:
                del st.session_state.trades_data
            st.session_state.brand_clicked = False
            st.rerun()
        

    
    with col2:
        if st.button("📁 Upload Trading Data", use_container_width=True, type="secondary"):
            st.session_state.show_upload_modal = True
            st.session_state.show_demo_modal = False
    
    with col3:
        if st.button("🎯 Try Demo Data", use_container_width=True, type="secondary"):
            st.session_state.show_demo_modal = True
            st.session_state.show_upload_modal = False
    
    # Upload Section (replaces modal)
    if st.session_state.show_upload_modal:
        st.markdown("---")
        
        # Header with X close button aligned to right edge
        st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <h3 style="margin: 0; padding: 0;">📁 Upload Your Trading Data</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # X button in top right corner
        col_spacer, col_x = st.columns([11, 1]) 
        with col_x:
            if st.button("✕", key="close_upload", help="Close"):
                st.session_state.show_upload_modal = False
                st.rerun()
        
        # Move X button to absolute position
        st.markdown("""
        <style>
        button[data-testid="baseButton-secondary"][title="Close"]:last-of-type {
            position: absolute;
            right: 20px;
            margin-top: -60px;
            z-index: 999;
            background: #f8f9fa !important;
            border: 1px solid #dee2e6 !important;
            border-radius: 50% !important;
            width: 30px !important;
            height: 30px !important;
            padding: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("Upload your Zerodha trade CSV file to begin analysis")
        
        uploaded_file = st.file_uploader(
            "Choose CSV file",
            type=['csv'],
            help="Upload your Zerodha trade export CSV",
            key="upload_file_input"
        )
        
        # Auto-analyze when file is uploaded
        if uploaded_file is not None:
            try:
                with st.spinner("Analyzing your trades..."):
                    parser = TradeParser()
                    trades_df = parser.parse_csv(uploaded_file)
                    st.session_state.trades_data = trades_df
                    st.session_state.data_loaded = True
                    st.session_state.show_upload_modal = False
                    st.rerun()
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
    
    # Demo Section (replaces modal)  
    elif st.session_state.show_demo_modal:
        st.markdown("---")
        
        # Header with X close button aligned to right edge
        st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <h3 style="margin: 0; padding: 0;">🎯 Try Demo Trading Data</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # X button in top right corner
        col_spacer, col_x = st.columns([11, 1])
        with col_x:
            if st.button("✕", key="close_demo", help="Close"):
                st.session_state.show_demo_modal = False
                st.rerun()
        st.markdown("**Experience the Trading Coach with realistic demo datasets:**")
        
        demo_files = {
            "Mixed Portfolio Trader": {
                "file": "data/demo/demo_tradebook.csv",
                "description": "📊 Diversified stocks • 30 days • 58% win rate",
                "details": "RELIANCE, TCS, HDFC, INFY, ICICIBANK"
            },
            "Tech Trader (Aggressive)": {
                "file": "data/demo/tech_trader_demo.csv", 
                "description": "💻 IT stocks • 45 days • 48% win rate • 80% intraday",
                "details": "TCS, INFY, WIPRO, TECHM"
            },
            "Bank Trader (Swing)": {
                "file": "data/demo/bank_trader_demo.csv",
                "description": "🏦 Banking stocks • 60 days • 61% win rate • Swing trading",
                "details": "HDFC, ICICIBANK, AXISBANK, SBIN"
            },
            "Conservative Trader": {
                "file": "data/demo/conservative_trader_demo.csv",
                "description": "🛡️ Blue chips • 90 days • 68% win rate • Long-term holds",
                "details": "RELIANCE, HDFC, ICICIBANK"
            }
        }
        
        # Create 2x2 grid layout for demo buttons
        demo_items = list(demo_files.items())
        
        # Use Streamlit's built-in button types - they have nice styling already
        st.markdown("""
        <style>
        /* Keep demo buttons simple - let Streamlit handle the styling */
        .stButton > button {
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        </style>
        """, unsafe_allow_html=True)
        
        # First row - 2 columns
        col1, col2 = st.columns(2, gap="medium")
        
        with col1:
            # Mixed Portfolio Trader - Primary button (uses theme color)
            name, info = demo_items[0]
            if st.button(f"📈 {name}", key=f"demo_0", use_container_width=True, type="primary"):
                parser = TradeParser()
                trades_df = parser.parse_csv(info["file"])
                st.session_state.trades_data = trades_df
                st.session_state.demo_file = info["file"]
                st.session_state.data_loaded = True
                st.session_state.show_demo_modal = False
                st.rerun()
            st.caption(info["description"])
            st.caption(f"*Stocks: {info['details']}*")
        
        with col2:
            # Tech Trader - Primary button (uses theme color)
            name, info = demo_items[1]
            if st.button(f"📈 {name}", key=f"demo_1", use_container_width=True, type="primary"):
                parser = TradeParser()
                trades_df = parser.parse_csv(info["file"])
                st.session_state.trades_data = trades_df
                st.session_state.demo_file = info["file"]
                st.session_state.data_loaded = True
                st.session_state.show_demo_modal = False
                st.rerun()
            st.caption(info["description"])
            st.caption(f"*Stocks: {info['details']}*")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Second row - 2 columns  
        col3, col4 = st.columns(2, gap="medium")
        
        with col3:
            # Bank Trader - Primary button (uses theme color)
            name, info = demo_items[2]
            if st.button(f"📈 {name}", key=f"demo_2", use_container_width=True, type="primary"):
                parser = TradeParser()
                trades_df = parser.parse_csv(info["file"])
                st.session_state.trades_data = trades_df
                st.session_state.demo_file = info["file"]
                st.session_state.data_loaded = True
                st.session_state.show_demo_modal = False
                st.rerun()
            st.caption(info["description"])
            st.caption(f"*Stocks: {info['details']}*")
        
        with col4:
            # Conservative Trader - Primary button (uses theme color)
            name, info = demo_items[3]
            if st.button(f"📈 {name}", key=f"demo_3", use_container_width=True, type="primary"):
                parser = TradeParser()
                trades_df = parser.parse_csv(info["file"])
                st.session_state.trades_data = trades_df
                st.session_state.demo_file = info["file"]
                st.session_state.data_loaded = True
                st.session_state.show_demo_modal = False
                st.rerun()
            st.caption(info["description"])
            st.caption(f"*Stocks: {info['details']}*")
        
        if st.button("Cancel", use_container_width=True):
            st.session_state.show_demo_modal = False
            st.rerun()
    
    # Show help text when no data is loaded
    if not st.session_state.data_loaded:
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Help text with arrow pointing up to buttons
        st.markdown("""
        <div style="text-align: center; margin-top: 100px;">
            <div style="font-size: 4rem; animation: bounce 2s infinite;">👆</div>
            <h2 style="color: #666; margin-top: 20px;">Get Started</h2>
            <p style="color: #888; font-size: 18px;">Click one of the buttons above to begin your trading analysis</p>
        </div>
        
        <style>
        @keyframes bounce {
            0%, 20%, 50%, 80%, 100% {
                transform: translateY(0);
            }
            40% {
                transform: translateY(-30px);
            }
            60% {
                transform: translateY(-15px);
            }
        }
        </style>
        """, unsafe_allow_html=True)
        
    
    # Process data when loaded
    elif st.session_state.data_loaded:
        # Handle both uploaded files and demo files
        if 'demo_file' in st.session_state:
            parser = TradeParser()
            trades_df = parser.parse_csv(st.session_state.demo_file)
            st.session_state.trades_data = trades_df
            
        if 'trades_data' in st.session_state:
            trades_df = st.session_state.trades_data
            
            # Show different success message for demo vs uploaded
            if 'demo_file' in st.session_state:
                demo_name = st.session_state.demo_file.split('/')[-1].replace('_', ' ').replace('.csv', '').title()
                st.success(f"✅ Loaded {len(trades_df)} trades from {demo_name}")
            else:
                st.success(f"✅ Loaded {len(trades_df)} trades")
            
            try:
                matcher = TradeMatcher()
                closed_trades = matcher.match_trades(trades_df)
                
                if closed_trades.empty:
                    st.warning("No closed trades found in the data")
                    return
                
                summary_stats = matcher.get_summary_stats(closed_trades)
                
                st.markdown("## Overview")
                st.markdown("*Here's what's working, what's not, and how to improve*")
                
                coach = TradingCoach()
                coach_insights = coach.generate_coach_insights(closed_trades)
                
                display_coach_dashboard(coach_insights, closed_trades)
                
                st.markdown("---")
                st.markdown("### 🔬 Advanced Analysis")
                
                tab1, tab2, tab3 = st.tabs([
                    "📈 Trade Analysis", 
                    "🔍 What-If Analysis",
                    "📋 All Trade Details"
                ])
                
                with tab1:
                    display_trade_analysis(closed_trades)
                
                with tab2:
                    display_whatif_analysis(closed_trades)
                
                with tab3:
                    display_trade_details(closed_trades)
                    
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
                logger.error(f"Error: {str(e)}", exc_info=True)

def display_trade_analysis(closed_trades: pd.DataFrame):
    st.header("📈 Trade Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_scatter = px.scatter(
            closed_trades,
            x='hold_hours',
            y='pnl_percentage',
            color='trade_result',
            size='entry_value',
            hover_data=['symbol', 'gross_pnl'],
            title="Hold Duration vs Returns",
            labels={'hold_hours': 'Hold Duration (hours)', 'pnl_percentage': 'Return (%)'},
            color_discrete_map={'win': 'green', 'loss': 'red'}
        )
        st.plotly_chart(fig_scatter, width='stretch')
    
    with col2:
        closed_trades['hour'] = pd.to_datetime(closed_trades['entry_datetime']).dt.hour
        hourly_stats = closed_trades.groupby('hour').agg({
            'gross_pnl': 'mean',
            'trade_result': lambda x: (x == 'win').mean() * 100
        }).rename(columns={'trade_result': 'win_rate'})
        
        fig_hour = go.Figure()
        fig_hour.add_trace(go.Bar(
            x=hourly_stats.index,
            y=hourly_stats['gross_pnl'],
            name='Avg P&L',
            marker_color='lightblue'
        ))
        
        fig_hour.add_trace(go.Scatter(
            x=hourly_stats.index,
            y=hourly_stats['win_rate'],
            name='Win Rate (%)',
            yaxis='y2',
            line=dict(color='orange', width=2)
        ))
        
        fig_hour.update_layout(
            title="Performance by Entry Hour",
            xaxis_title="Hour of Day",
            yaxis_title="Avg P&L (₹)",
            yaxis2=dict(
                title="Win Rate (%)",
                overlaying='y',
                side='right'
            ),
            height=400
        )
        st.plotly_chart(fig_hour, width='stretch')
    
    st.markdown("---")
    
    st.subheader("📊 Stock Performance Matrix")
    
    stock_stats = closed_trades.groupby('symbol').agg({
        'gross_pnl': ['sum', 'mean', 'count'],
        'trade_result': lambda x: (x == 'win').mean() * 100,
        'hold_hours': 'mean'
    }).round(2)
    
    stock_stats.columns = ['Total P&L', 'Avg P&L', 'Trade Count', 'Win Rate %', 'Avg Hold Hours']
    stock_stats = stock_stats.sort_values('Total P&L', ascending=False)
    
    styled_df = stock_stats.style.format({
        'Total P&L': '₹{:,.0f}',
        'Avg P&L': '₹{:,.0f}',
        'Win Rate %': '{:.1f}%',
        'Avg Hold Hours': '{:.1f}h'
    })
    
    # Apply color coding without matplotlib
    def color_pnl(val):
        if isinstance(val, str):
            return ''
        color = 'green' if val > 0 else 'red' if val < 0 else 'black'
        return f'color: {color}'
    
    styled_df = styled_df.map(color_pnl, subset=['Total P&L', 'Avg P&L'])
    
    st.dataframe(
        styled_df,
        width='stretch'
    )

def display_whatif_analysis(closed_trades: pd.DataFrame):
    st.header("🔍 What-If Analysis")
    
    if closed_trades.empty:
        st.warning("No closed trades available for analysis")
        return
    
    st.markdown("Select a trade to analyze what would have happened with different exit strategies:")
    
    # Select trade for analysis
    trade_options = []
    for idx, trade in closed_trades.iterrows():
        profit_loss = "📈 Profit" if trade['gross_pnl'] > 0 else "📉 Loss"
        trade_label = f"{trade['symbol']} - {trade['entry_datetime'].strftime('%Y-%m-%d %H:%M')} - {profit_loss} ₹{trade['gross_pnl']:,.0f}"
        trade_options.append((trade_label, idx))
    
    selected_label, selected_idx = st.selectbox(
        "Choose a trade:",
        trade_options,
        format_func=lambda x: x[0]
    )
    
    if selected_idx is not None:
        trade = closed_trades.iloc[selected_idx]
        
        st.subheader(f"📊 Analysis for {trade['symbol']}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Entry Price", f"₹{trade['entry_price']:.2f}")
        with col2:
            st.metric("Exit Price", f"₹{trade['exit_price']:.2f}")
        with col3:
            st.metric("Actual P&L", f"₹{trade['gross_pnl']:.0f}")
        
        # Fetch price data and run what-if analysis
        with st.spinner("Fetching price data and running analysis..."):
            fetcher = PriceFetcher()
            
            try:
                # Get price movements during trade
                price_info = fetcher.get_price_during_trade(
                    trade['symbol'], 
                    trade['entry_datetime'], 
                    trade['exit_datetime']
                )
                
                if price_info and 'price_data' in price_info:
                    price_data = price_info['price_data']
                    
                    # Create price chart
                    fig = go.Figure()
                    
                    # Add candlestick chart
                    fig.add_trace(go.Candlestick(
                        x=price_data.index,
                        open=price_data['Open'],
                        high=price_data['High'],
                        low=price_data['Low'],
                        close=price_data['Close'],
                        name='Price'
                    ))
                    
                    # Mark entry and exit points using shapes instead of add_vline to avoid pandas arithmetic issues
                    entry_time = trade['entry_datetime']
                    exit_time = trade['exit_datetime']
                    
                    # Add vertical lines as shapes
                    fig.add_shape(
                        type="line",
                        x0=entry_time, x1=entry_time,
                        y0=0, y1=1,
                        yref="paper",
                        line=dict(color="green", width=2),
                    )
                    fig.add_annotation(
                        x=entry_time, y=1, yref="paper",
                        text="BUY", showarrow=False,
                        yshift=10, font=dict(color="green")
                    )
                    
                    fig.add_shape(
                        type="line",
                        x0=exit_time, x1=exit_time,
                        y0=0, y1=1,
                        yref="paper",
                        line=dict(color="red", width=2),
                    )
                    fig.add_annotation(
                        x=exit_time, y=1, yref="paper",
                        text="SELL", showarrow=False,
                        yshift=10, font=dict(color="red")
                    )
                    
                    fig.update_layout(
                        title=f"{trade['symbol']} Price Movement During Trade",
                        xaxis_title="Time",
                        yaxis_title="Price (₹)",
                        height=500
                    )
                    
                    st.plotly_chart(fig, width='stretch')
                    
                    # What-if scenarios
                    st.subheader("💭 What-If Scenarios")
                    
                    scenarios = fetcher.simulate_exit_scenarios(
                        trade['symbol'],
                        trade['entry_price'],
                        trade['entry_datetime'],
                        trade['exit_datetime'],
                        int(trade['quantity'])
                    )
                    
                    if scenarios:
                        scenario_cols = st.columns(len(scenarios))
                        
                        for i, (scenario_name, scenario_data) in enumerate(scenarios.items()):
                            with scenario_cols[i % len(scenario_cols)]:
                                scenario_title = {
                                    'best_early_exit': '⚡ Best Early Exit',
                                    'best_late_exit': '⏰ Best Late Exit', 
                                    'trailing_stop': '🛡️ Trailing Stop'
                                }.get(scenario_name, scenario_name.replace('_', ' ').title())
                                
                                potential_gain = scenario_data['potential_pnl'] - trade['gross_pnl']
                                
                                st.metric(
                                    scenario_title,
                                    f"₹{scenario_data['potential_pnl']:.0f}",
                                    delta=f"₹{potential_gain:.0f} vs actual"
                                )
                                
                                st.caption(f"Exit at ₹{scenario_data['price']:.2f}")
                                st.caption(f"Time: {scenario_data['time'].strftime('%Y-%m-%d %H:%M')}")
                    
                    # Technical indicators during trade
                    st.subheader("📈 Technical Analysis")
                    
                    entry_indicators = fetcher.get_technical_indicators(
                        trade['symbol'], 
                        trade['entry_datetime']
                    )
                    
                    exit_indicators = fetcher.get_technical_indicators(
                        trade['symbol'], 
                        trade['exit_datetime']
                    )
                    
                    if entry_indicators and exit_indicators:
                        indicator_cols = st.columns(4)
                        
                        indicators = ['rsi', 'sma_10', 'sma_20', 'volume_ratio']
                        indicator_names = ['RSI', 'SMA 10', 'SMA 20', 'Volume Ratio']
                        
                        for i, (indicator, name) in enumerate(zip(indicators, indicator_names)):
                            with indicator_cols[i]:
                                entry_val = entry_indicators.get(indicator)
                                exit_val = exit_indicators.get(indicator)
                                
                                if entry_val is not None and exit_val is not None:
                                    if indicator == 'volume_ratio':
                                        st.metric(
                                            f"{name} (Entry)",
                                            f"{entry_val:.2f}x",
                                            help="Volume compared to average"
                                        )
                                    elif 'sma' in indicator:
                                        st.metric(
                                            f"{name} (Entry)",
                                            f"₹{entry_val:.2f}"
                                        )
                                    else:
                                        st.metric(
                                            f"{name} (Entry)",
                                            f"{entry_val:.1f}"
                                        )
                    
                    # Summary insights for this trade
                    st.subheader("🎯 Trade-Specific Insights")
                    
                    insights = []
                    
                    if 'max_price' in price_info and 'min_price' in price_info:
                        max_potential = (price_info['max_price'] - trade['entry_price']) * trade['quantity']
                        min_potential = (price_info['min_price'] - trade['entry_price']) * trade['quantity']
                        
                        if max_potential > trade['gross_pnl'] * 2:
                            insights.append(f"💡 **Missed Opportunity**: Price reached ₹{price_info['max_price']:.2f} during your hold period. You could have made ₹{max_potential:,.0f} instead of ₹{trade['gross_pnl']:,.0f}")
                        
                        if min_potential < trade['gross_pnl'] and trade['gross_pnl'] > 0:
                            insights.append(f"🛡️ **Good Risk Management**: Despite price dropping to ₹{price_info['min_price']:.2f}, you avoided a potential loss of ₹{abs(min_potential):,.0f}")
                        
                        volatility = ((price_info['max_price'] - price_info['min_price']) / trade['entry_price']) * 100
                        if volatility > 10:
                            insights.append(f"⚠️ **High Volatility**: Price swung {volatility:.1f}% during your trade. Consider smaller position sizes for such volatile stocks.")
                    
                    if scenarios and 'trailing_stop' in scenarios:
                        trailing_pnl = scenarios['trailing_stop']['potential_pnl']
                        if trailing_pnl > trade['gross_pnl']:
                            difference = trailing_pnl - trade['gross_pnl']
                            insights.append(f"📈 **Trailing Stop Advantage**: A 2% trailing stop would have earned you ₹{difference:,.0f} more")
                    
                    for insight in insights:
                        st.markdown(insight)
                        
                else:
                    st.warning(f"Could not fetch price data for {trade['symbol']} during the trade period. This might be due to:")
                    st.markdown("- Stock not listed on exchanges supported by yfinance")
                    st.markdown("- Data not available for the specific time period")
                    st.markdown("- Network connectivity issues")
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error analyzing trade for {trade['symbol']}: {error_msg}")
                
                st.error(f"Error analyzing trade: {error_msg}")
                
                if "addition/subtraction of integers" in error_msg.lower():
                    st.info("**Pandas Datetime Error**: There's an issue with datetime arithmetic in the analysis. This is a known issue we're working to fix.")
                elif "timezone" in error_msg.lower() or "comparison" in error_msg.lower():
                    st.info("**Data Processing Issue**: The system had trouble processing timestamps for this trade. This can happen with older trades or certain stock symbols.")
                elif "delisted" in error_msg.lower() or "404" in error_msg.lower():
                    st.info(f"**Stock Data Unavailable**: {trade['symbol']} data is not available from the data provider. This stock may be delisted or not traded on supported exchanges.")
                else:
                    st.markdown("**Possible causes:**")
                    st.markdown("- Stock symbol not recognized by data provider")
                    st.markdown("- Data not available for the selected time period")
                    st.markdown("- Temporary API connectivity issues")
                
                # Show basic trade info even if detailed analysis fails
                st.subheader("📊 Basic Trade Information")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Duration", f"{trade['hold_hours']:.1f} hours")
                with col2:
                    st.metric("Return %", f"{trade['pnl_percentage']:.2f}%")
                with col3:
                    result_color = "green" if trade['gross_pnl'] > 0 else "red"
                    st.markdown(f"**Result**: <span style='color:{result_color}'>{trade['trade_result'].title()}</span>", unsafe_allow_html=True)

def display_trade_details(closed_trades: pd.DataFrame):
    st.header("📋 Trade Details")
    
    filters_col1, filters_col2, filters_col3 = st.columns(3)
    
    with filters_col1:
        result_filter = st.selectbox(
            "Trade Result",
            ["All", "Wins", "Losses"]
        )
    
    with filters_col2:
        symbol_filter = st.multiselect(
            "Symbols",
            options=closed_trades['symbol'].unique(),
            default=None
        )
    
    with filters_col3:
        date_range = st.date_input(
            "Date Range",
            value=(closed_trades['entry_datetime'].min(), closed_trades['exit_datetime'].max()),
            max_value=datetime.now()
        )
    
    filtered_trades = closed_trades.copy()
    
    if result_filter == "Wins":
        filtered_trades = filtered_trades[filtered_trades['trade_result'] == 'win']
    elif result_filter == "Losses":
        filtered_trades = filtered_trades[filtered_trades['trade_result'] == 'loss']
    
    if symbol_filter:
        filtered_trades = filtered_trades[filtered_trades['symbol'].isin(symbol_filter)]
    
    if len(date_range) == 2:
        filtered_trades = filtered_trades[
            (filtered_trades['entry_datetime'].dt.date >= date_range[0]) &
            (filtered_trades['exit_datetime'].dt.date <= date_range[1])
        ]
    
    st.markdown(f"Showing {len(filtered_trades)} trades")
    
    display_df = filtered_trades[[
        'symbol', 'entry_datetime', 'exit_datetime', 'quantity',
        'entry_price', 'exit_price', 'gross_pnl', 'pnl_percentage',
        'hold_hours', 'trade_result'
    ]].sort_values('exit_datetime', ascending=False)
    
    st.dataframe(
        display_df.style.format({
            'entry_price': '₹{:.2f}',
            'exit_price': '₹{:.2f}',
            'gross_pnl': '₹{:,.0f}',
            'pnl_percentage': '{:.2f}%',
            'hold_hours': '{:.1f}h'
        }).apply(lambda x: ['background-color: #d4f4dd' if x['trade_result'] == 'win' 
                            else 'background-color: #f4d4d4' for _ in x], axis=1),
        width='stretch',
        height=600
    )
    
    csv = filtered_trades.to_csv(index=False)
    st.download_button(
        label="📥 Download Filtered Trades",
        data=csv,
        file_name=f"filtered_trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    main()