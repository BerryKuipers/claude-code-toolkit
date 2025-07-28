#!/usr/bin/env python3
"""
Streamlit dashboard for crypto portfolio analysis using the new strongly typed API backend.

This version communicates with the FastAPI backend instead of making direct Bitvavo API calls,
providing faster development cycles and better separation of concerns.
"""

import logging
import os
import sys
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st

# Add frontend to path for API client
sys.path.append("frontend")
sys.path.append("src")

from frontend.api_client import SyncCryptoPortfolioAPIClient, APIException

# Import UI components
from portfolio.ui.performance import (
    PerformanceOptimizer,
    apply_global_optimizations,
    render_optimized_dataframe,
)


# Set up logging
def setup_logging():
    """Set up comprehensive logging to file and console with fallback for permission issues."""
    handlers = [logging.StreamHandler()]  # Always include console logging

    # Try to set up file logging, but fall back gracefully if permissions fail
    try:
        log_dir = os.path.join(os.path.dirname(__file__), "logs")
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(
            log_dir, f'dashboard_{datetime.now().strftime("%Y%m%d")}.log'
        )

        # Test if we can write to the log file
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"# Log started at {datetime.now()}\n")

        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
        print(f"[OK] Logging to file: {log_file}")

    except (PermissionError, OSError) as e:
        print(f"[WARNING] Could not set up file logging: {e}")
        print("[INFO] Continuing with console logging only")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
        force=True,
    )


# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# Apply global performance optimizations
apply_global_optimizations()


def get_api_client() -> SyncCryptoPortfolioAPIClient:
    """Get API client with backend URL from environment or default."""
    backend_url = os.getenv("BACKEND_API_URL", "http://localhost:8000")
    return SyncCryptoPortfolioAPIClient(base_url=backend_url)


def check_backend_connection() -> bool:
    """Check if backend is available and healthy."""
    try:
        client = get_api_client()
        health = client.health_check()
        return health.get("status") == "healthy"
    except Exception as e:
        logger.error(f"Backend connection failed: {e}")
        return False


def display_connection_status():
    """Display backend connection status in sidebar."""
    st.sidebar.markdown("### 🔗 Backend Status")
    
    if check_backend_connection():
        st.sidebar.success("✅ Backend Connected")
        if st.sidebar.button("🔄 Refresh Data"):
            try:
                client = get_api_client()
                success = client.refresh_portfolio_data()
                if success:
                    st.sidebar.success("✅ Data refreshed!")
                    st.rerun()
                else:
                    st.sidebar.error("❌ Refresh failed")
            except Exception as e:
                st.sidebar.error(f"❌ Refresh error: {e}")
    else:
        st.sidebar.error("❌ Backend Disconnected")
        st.sidebar.markdown("""
        **Backend not available**
        
        Please ensure the backend is running:
        ```bash
        .\\scripts\\start-backend.ps1
        ```
        """)


def load_portfolio_data():
    """Load portfolio data from API backend."""
    try:
        client = get_api_client()
        
        # Get portfolio summary and holdings
        summary = client.get_portfolio_summary()
        holdings = client.get_current_holdings()
        
        return summary, holdings
        
    except APIException as e:
        st.error(f"API Error: {e.message}")
        if e.status_code:
            st.error(f"Status Code: {e.status_code}")
        return None, None
    except Exception as e:
        st.error(f"Unexpected error loading portfolio data: {e}")
        return None, None


def display_portfolio_summary(summary):
    """Display portfolio summary metrics."""
    st.markdown("## 📊 Portfolio Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Value",
            f"€{summary.total_value:,.2f}",
            delta=f"€{summary.total_pnl:,.2f}"
        )
    
    with col2:
        st.metric(
            "Total Return",
            f"{summary.total_return_percentage:.2f}%",
            delta=f"€{summary.unrealized_pnl:,.2f}"
        )
    
    with col3:
        st.metric(
            "Realized P&L",
            f"€{summary.realized_pnl:,.2f}",
            delta=None
        )
    
    with col4:
        st.metric(
            "Assets",
            f"{summary.asset_count}",
            delta=None
        )
    
    # Additional metrics in expandable section
    with st.expander("📈 Detailed Metrics"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Cost Basis", f"€{summary.total_cost:,.2f}")
            st.metric("Unrealized P&L", f"€{summary.unrealized_pnl:,.2f}")
        
        with col2:
            st.metric("Total P&L", f"€{summary.total_pnl:,.2f}")
            st.write(f"**Last Updated:** {summary.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")


def display_holdings_table(holdings):
    """Display holdings in an optimized table."""
    st.markdown("## 💰 Current Holdings")
    
    if not holdings:
        st.warning("No holdings found")
        return
    
    # Convert holdings to DataFrame
    holdings_data = []
    for holding in holdings:
        holdings_data.append({
            "Asset": holding.asset,
            "Quantity": float(holding.quantity),
            "Current Price €": float(holding.current_price),
            "Value €": float(holding.value_eur),
            "Cost Basis €": float(holding.cost_basis),
            "Unrealized P&L €": float(holding.unrealized_pnl),
            "Realized P&L €": float(holding.realized_pnl),
            "Portfolio %": float(holding.portfolio_percentage),
            "Total Return %": float(holding.total_return_percentage),
        })
    
    df = pd.DataFrame(holdings_data)
    
    # Apply performance optimizations and display
    render_optimized_dataframe(
        df,
        title="Portfolio Holdings",
        key="holdings_table",
        format_config={
            "Current Price €": "{:.4f}",
            "Value €": "{:,.2f}",
            "Cost Basis €": "{:,.2f}",
            "Unrealized P&L €": "{:,.2f}",
            "Realized P&L €": "{:,.2f}",
            "Portfolio %": "{:.2f}%",
            "Total Return %": "{:.2f}%",
        }
    )


def display_chat_interface():
    """Display AI chat interface using the backend."""
    st.markdown("## 🤖 AI Portfolio Assistant")
    
    # Initialize chat history in session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = None
    
    # Chat input
    user_message = st.chat_input("Ask about your portfolio...")
    
    if user_message:
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": user_message})
        
        try:
            client = get_api_client()
            
            # Send to backend
            with st.spinner("🤔 Thinking..."):
                response = client.chat_query(
                    message=user_message,
                    conversation_id=st.session_state.conversation_id,
                    use_function_calling=True
                )
            
            # Update conversation ID
            st.session_state.conversation_id = response.conversation_id
            
            # Add assistant response to history
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": response.message,
                "function_calls": response.function_calls,
                "cost": response.cost_estimate,
                "tokens": response.token_usage
            })
            
        except Exception as e:
            st.error(f"Chat error: {e}")
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            
            # Show function calls and metadata for assistant messages
            if message["role"] == "assistant" and "function_calls" in message:
                if message["function_calls"]:
                    with st.expander("🔧 Function Calls"):
                        for func_call in message["function_calls"]:
                            st.write(f"**{func_call['function_name']}** - {func_call['execution_time_ms']:.1f}ms")
                
                with st.expander("📊 Response Metadata"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Tokens:** {message.get('tokens', {})}")
                    with col2:
                        st.write(f"**Cost:** ${message.get('cost', 0):.4f}")


def main():
    """Main dashboard application."""
    st.set_page_config(
        page_title="Crypto Portfolio Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("📊 Crypto Portfolio Dashboard")
    st.markdown("*Powered by strongly typed FastAPI backend*")
    
    # Display connection status
    display_connection_status()
    
    # Check backend connection
    if not check_backend_connection():
        st.error("❌ Cannot connect to backend. Please start the backend service.")
        st.stop()
    
    # Load portfolio data
    with st.spinner("📊 Loading portfolio data..."):
        summary, holdings = load_portfolio_data()
    
    if summary is None or holdings is None:
        st.error("❌ Failed to load portfolio data")
        st.stop()
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "💰 Holdings", "🤖 AI Chat"])
    
    with tab1:
        display_portfolio_summary(summary)
    
    with tab2:
        display_holdings_table(holdings)
    
    with tab3:
        display_chat_interface()
    
    # Footer
    st.markdown("---")
    st.markdown("*Built with ❤️ using FastAPI + Streamlit + Strong Typing*")


if __name__ == "__main__":
    main()
