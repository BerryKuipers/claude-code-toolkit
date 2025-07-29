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

import pandas as pd
import streamlit as st

# Add frontend to path for API client
sys.path.append("frontend")

from frontend.api_client import APIException, SyncCryptoPortfolioAPIClient

# No old dependencies - using only Clean Architecture backend


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

# Clean Architecture - no global optimizations needed


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
        st.sidebar.markdown(
            """
        **Backend not available**

        Please ensure the backend is running:
        ```bash
        .\\scripts\\start-backend.ps1
        ```
        """
        )


def display_asset_filters():
    """Display asset selection filters in sidebar."""
    st.sidebar.markdown("## 🎯 Asset Filters")

    # Initialize session state for asset filters
    if "selected_assets" not in st.session_state:
        st.session_state.selected_assets = "all"

    # Asset selection options
    filter_option = st.sidebar.radio(
        "Select Assets to Display:",
        ["all", "custom", "top_performers", "losers"],
        format_func=lambda x: {
            "all": "📊 All Assets",
            "custom": "🎯 Custom Selection",
            "top_performers": "🏆 Top Performers",
            "losers": "📉 Underperformers",
        }[x],
        key="asset_filter_option",
    )

    st.session_state.selected_assets = filter_option

    # Custom asset selection
    if filter_option == "custom":
        st.sidebar.markdown("**Select specific assets:**")
        # This would be populated with actual assets from the portfolio
        # For now, show common crypto assets
        common_assets = ["BTC", "ETH", "ADA", "DOT", "LINK", "UNI", "AAVE", "SUSHI"]
        selected_custom = st.sidebar.multiselect(
            "Choose assets:",
            common_assets,
            default=common_assets[:3],
            key="custom_asset_selection",
        )
        st.session_state.custom_assets = selected_custom

    return st.session_state.selected_assets


def display_ai_model_selector():
    """Display AI model selection in sidebar."""
    st.sidebar.markdown("## 🤖 AI Model Settings")

    # Model selection
    model_options = {
        "": "🤖 Auto (Backend Default) - Recommended",
        "gpt-4o": "💎 GPT-4o (OpenAI, $5/1M tokens)",
        "claude-sonnet-4": "🧠 Claude Sonnet 4 (Anthropic, $3/1M tokens)",
        "gpt-4o-mini": "⚡ GPT-4o Mini (Budget, $0.15/1M tokens)",
        "claude-opus-4": "🚀 Claude Opus 4 (Premium, $15/1M tokens)",
        "gpt-4-turbo": "🔧 GPT-4 Turbo (Reliable, $10/1M tokens)",
    }

    selected_model = st.sidebar.selectbox(
        "Choose AI Model:",
        list(model_options.keys()),
        format_func=lambda x: model_options[x],
        key="selected_ai_model",
        help="Different models have different capabilities and costs",
    )

    # Temperature setting
    temperature = st.sidebar.slider(
        "Response Creativity:",
        min_value=0.0,
        max_value=1.0,
        value=0.1,
        step=0.1,
        key="ai_temperature",
        help="Lower = more focused, Higher = more creative",
    )

    # Function calling toggle
    use_functions = st.sidebar.checkbox(
        "🔧 Enable Function Calling",
        value=True,
        key="use_function_calling",
        help="Allow AI to call portfolio functions for accurate data",
    )

    return {
        "model": selected_model,
        "temperature": temperature,
        "use_functions": use_functions,
    }


def display_cost_tracker():
    """Display AI usage cost tracking."""
    st.sidebar.markdown("## 💰 AI Cost Tracker")

    # Initialize cost tracking in session state
    if "ai_costs" not in st.session_state:
        st.session_state.ai_costs = {
            "total_tokens": 0,
            "total_cost": 0.0,
            "queries_count": 0,
        }

    costs = st.session_state.ai_costs

    # Display current session costs
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("Queries", costs["queries_count"])
        st.metric("Tokens", f"{costs['total_tokens']:,}")
    with col2:
        st.metric("Cost", f"${costs['total_cost']:.4f}")

    # Reset button
    if st.sidebar.button("🔄 Reset Costs", help="Reset cost tracking for this session"):
        st.session_state.ai_costs = {
            "total_tokens": 0,
            "total_cost": 0.0,
            "queries_count": 0,
        }
        st.rerun()


def update_cost_tracking(model, tokens_used):
    """Update cost tracking with new usage."""
    if "ai_costs" not in st.session_state:
        st.session_state.ai_costs = {
            "total_tokens": 0,
            "total_cost": 0.0,
            "queries_count": 0,
        }

    # Cost per 1M tokens (approximate)
    cost_per_token = {
        "": 5.0 / 1_000_000,  # Auto mode - assume GPT-4o default
        "claude-sonnet-4": 3.0 / 1_000_000,
        "gpt-4o": 5.0 / 1_000_000,
        "gpt-4o-mini": 0.15 / 1_000_000,
        "claude-opus-4": 15.0 / 1_000_000,
        "gpt-4-turbo": 10.0 / 1_000_000,
    }

    token_cost = cost_per_token.get(model, 5.0 / 1_000_000)
    query_cost = tokens_used * token_cost

    st.session_state.ai_costs["total_tokens"] += tokens_used
    st.session_state.ai_costs["total_cost"] += query_cost
    st.session_state.ai_costs["queries_count"] += 1


def export_chat_history():
    """Export chat history to downloadable file."""
    if "chat_history" not in st.session_state or not st.session_state.chat_history:
        st.warning("No chat history to export")
        return

    # Create export content
    export_content = "# Crypto Portfolio AI Chat History\n\n"
    for user_msg, ai_msg, timestamp in st.session_state.chat_history:
        export_content += f"## {timestamp}\n\n"
        export_content += f"**User:** {user_msg}\n\n"
        export_content += f"**AI:** {ai_msg}\n\n"
        export_content += "---\n\n"

    # Offer download
    st.download_button(
        label="📥 Download Chat History",
        data=export_content,
        file_name=f"portfolio_chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown",
        key="download_chat_history",
    )


def filter_holdings_by_selection(holdings, filter_type):
    """Filter holdings based on user selection."""
    if not holdings or filter_type == "all":
        return holdings

    if filter_type == "custom":
        if "custom_assets" in st.session_state and st.session_state.custom_assets:
            return [h for h in holdings if h.asset in st.session_state.custom_assets]
        return holdings

    elif filter_type == "top_performers":
        # Sort by total return percentage and take top 5
        sorted_holdings = sorted(
            holdings, key=lambda h: float(h.total_return_percentage), reverse=True
        )
        return sorted_holdings[:5]

    elif filter_type == "losers":
        # Sort by total return percentage and take bottom 5
        sorted_holdings = sorted(
            holdings, key=lambda h: float(h.total_return_percentage)
        )
        return sorted_holdings[:5]

    return holdings


@st.cache_data(ttl=300)  # Cache for 5 minutes
def _fetch_portfolio_data():
    """Internal function to fetch portfolio data from API backend."""
    try:
        client = get_api_client()
        logger.info("Fetching fresh portfolio data from API...")

        # Load data sequentially to avoid threading issues with asyncio
        summary = client.get_portfolio_summary()
        holdings = client.get_current_holdings()

        logger.info("Portfolio data fetched successfully")
        return summary, holdings

    except APIException as e:
        logger.error(f"API Error: {e.message}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error loading portfolio data: {e}")
        raise e


def load_portfolio_data(show_progress=True):
    """Load portfolio data with optional progress indicators."""
    # Check if we should show progress (only for first load or explicit refresh)
    if show_progress and not st.session_state.get("_portfolio_data_loaded", False):
        progress_placeholder = st.empty()

        try:
            with progress_placeholder:
                st.info(
                    "🔄 Step 1/2: Loading portfolio summary (may take 20-30 seconds)..."
                )

            # This will either fetch from cache or make API call
            summary, holdings = _fetch_portfolio_data()

            with progress_placeholder:
                st.info(
                    "🔄 Step 2/2: Loading current holdings (may take 10-15 seconds)..."
                )

            # Clear progress indicator
            progress_placeholder.empty()
            return summary, holdings

        except Exception as e:
            progress_placeholder.empty()
            if isinstance(e, APIException):
                st.error(f"API Error: {e.message}")
                if e.status_code:
                    st.error(f"Status Code: {e.status_code}")
            else:
                st.error(f"Unexpected error loading portfolio data: {e}")
            return None, None
    else:
        # Load silently (from cache or fresh)
        try:
            return _fetch_portfolio_data()
        except Exception as e:
            if isinstance(e, APIException):
                st.error(f"API Error: {e.message}")
                if e.status_code:
                    st.error(f"Status Code: {e.status_code}")
            else:
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
            delta=f"€{summary.total_pnl:,.2f}",
        )

    with col2:
        st.metric(
            "Total Return",
            f"{summary.total_return_percentage:.2f}%",
            delta=f"€{summary.unrealized_pnl:,.2f}",
        )

    with col3:
        st.metric("Realized P&L", f"€{summary.realized_pnl:,.2f}", delta=None)

    with col4:
        st.metric("Assets", f"{summary.asset_count}", delta=None)

    # Additional metrics in expandable section
    with st.expander("📈 Detailed Metrics"):
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total Cost Basis", f"€{summary.total_cost:,.2f}")
            st.metric("Unrealized P&L", f"€{summary.unrealized_pnl:,.2f}")

        with col2:
            st.metric("Total P&L", f"€{summary.total_pnl:,.2f}")
            st.write(
                f"**Last Updated:** {summary.last_updated.strftime('%Y-%m-%d %H:%M:%S')}"
            )


def display_holdings_table(holdings):
    """Display holdings in an optimized table."""
    st.markdown("## 💰 Current Holdings")

    if not holdings:
        st.warning("No holdings found")
        return

    # Convert holdings to DataFrame
    holdings_data = []
    for holding in holdings:
        holdings_data.append(
            {
                "Asset": holding.asset,
                "Quantity": float(holding.quantity),
                "Current Price €": float(holding.current_price),
                "Value €": float(holding.value_eur),
                "Cost Basis €": float(holding.cost_basis),
                "Unrealized P&L €": float(holding.unrealized_pnl),
                "Realized P&L €": float(holding.realized_pnl),
                "Portfolio %": float(holding.portfolio_percentage),
                "Total Return %": float(holding.total_return_percentage),
            }
        )

    df = pd.DataFrame(holdings_data)

    # Display the table with row selection enabled for AI analysis
    selected_rows = st.dataframe(
        df,
        key="holdings_table",
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Asset": st.column_config.TextColumn("Asset", width="small"),
            "Quantity": st.column_config.NumberColumn("Quantity", format="%.6f"),
            "Current Price €": st.column_config.NumberColumn(
                "Current Price €", format="€%.4f"
            ),
            "Value €": st.column_config.NumberColumn("Value €", format="€%.2f"),
            "Cost Basis €": st.column_config.NumberColumn(
                "Cost Basis €", format="€%.2f"
            ),
            "Unrealized P&L €": st.column_config.NumberColumn(
                "Unrealized P&L €", format="€%.2f"
            ),
            "Realized P&L €": st.column_config.NumberColumn(
                "Realized P&L €", format="€%.2f"
            ),
            "Portfolio %": st.column_config.NumberColumn(
                "Portfolio %", format="%.2f%%"
            ),
            "Total Return %": st.column_config.NumberColumn(
                "Total Return %", format="%.2f%%"
            ),
        },
    )

    # Handle row selection for AI analysis
    handle_asset_selection(selected_rows, df)


def handle_asset_selection(selected_rows, df):
    """Handle row selection and display AI analysis."""
    if (
        selected_rows
        and hasattr(selected_rows, "selection")
        and len(selected_rows.selection.rows) > 0
    ):
        selected_idx = selected_rows.selection.rows[0]
        selected_asset = df.iloc[selected_idx]

        # Generate AI analysis for the selected asset
        try:
            explanation = generate_asset_explanation(selected_asset.to_dict())

            # Display the explanation in an info box
            st.info(f"💡 **{selected_asset['Asset']} Analysis**\n\n{explanation}")

        except Exception as e:
            st.error(f"❌ Error generating analysis: {str(e)}")


def generate_asset_explanation(asset_data):
    """Generate AI explanation for an asset (simplified version)."""
    asset = asset_data.get("Asset", "Unknown")
    value = asset_data.get("Value €", 0)
    pnl = asset_data.get("Unrealized P&L €", 0)
    return_pct = asset_data.get("Total Return %", 0)

    if return_pct > 0:
        performance = "profitable"
        emoji = "📈"
    elif return_pct < 0:
        performance = "at a loss"
        emoji = "📉"
    else:
        performance = "breaking even"
        emoji = "➡️"

    return f"""{emoji} **{asset}** is currently {performance} in your portfolio.

**Current Position:**
- Value: €{value:,.2f}
- Unrealized P&L: €{pnl:,.2f}
- Total Return: {return_pct:.2f}%

This represents {asset_data.get('Portfolio %', 0):.1f}% of your total portfolio value."""


def render_sticky_chat(df):
    """Render sticky chat interface at bottom of portfolio page."""
    # Initialize chat state - CLOSED by default
    if "sticky_chat_open" not in st.session_state:
        st.session_state.sticky_chat_open = False

    # Render the sticky chat interface
    render_sticky_chat_interface(df)


def render_sticky_chat_interface(df=None):
    """Render a working chat interface with history and persistence."""
    # Initialize unique session ID for button keys
    if "session_id" not in st.session_state:
        import time

        st.session_state.session_id = str(int(time.time()))

    if st.session_state.sticky_chat_open:
        # Initialize chat history
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        # Show chat interface at bottom of page
        st.markdown("---")

        # Chat header with controls
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            st.markdown("### 💬 AI Portfolio Assistant")
        with col2:
            if st.button(
                "📋 Export",
                key=f"export_chat_{st.session_state.session_id}",
                help="Export Chat History",
            ):
                export_chat_history()
        with col3:
            if st.button(
                "🗑️ Clear",
                key=f"clear_chat_{st.session_state.session_id}",
                help="Clear Chat History",
            ):
                st.session_state.chat_history = []
                st.rerun()
        with col4:
            if st.button(
                "✕",
                key=f"close_sticky_chat_{st.session_state.session_id}",
                help="Close Chat",
            ):
                st.session_state.sticky_chat_open = False
                st.rerun()

        # Show chat history
        if st.session_state.chat_history:
            st.markdown("#### 📜 Chat History")
            chat_container = st.container()
            with chat_container:
                for i, (user_msg, ai_msg, timestamp) in enumerate(
                    st.session_state.chat_history
                ):
                    with st.expander(
                        f"💬 {timestamp} - {user_msg[:50]}...",
                        expanded=(i == len(st.session_state.chat_history) - 1),
                    ):
                        st.markdown(f"**👤 You:** {user_msg}")
                        st.markdown(f"**🤖 AI:** {ai_msg}")
        else:
            st.info(
                "💡 **AI Assistant Ready!** Ask me about your portfolio, market analysis, or crypto insights."
            )

        # Advanced AI function buttons
        st.markdown("#### 🚀 Quick Analysis")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button(
                "📊 Technical Analysis",
                key=f"tech_analysis_{st.session_state.session_id}",
            ):
                user_input = "Perform technical analysis on my top 3 holdings with price trends, support/resistance levels, and trading signals"
                st.session_state[
                    f"portfolio_chat_input_{st.session_state.session_id}"
                ] = user_input
                st.rerun()

        with col2:
            if st.button(
                "⚠️ Risk Assessment",
                key=f"risk_assessment_{st.session_state.session_id}",
            ):
                user_input = "Analyze the risk profile of my portfolio including diversification, volatility, and correlation analysis"
                st.session_state[
                    f"portfolio_chat_input_{st.session_state.session_id}"
                ] = user_input
                st.rerun()

        with col3:
            if st.button(
                "🔮 Price Predictions",
                key=f"price_predictions_{st.session_state.session_id}",
            ):
                user_input = "Provide price predictions for my holdings based on technical indicators and market sentiment"
                st.session_state[
                    f"portfolio_chat_input_{st.session_state.session_id}"
                ] = user_input
                st.rerun()

        with col4:
            if st.button(
                "📰 Market Research",
                key=f"market_research_{st.session_state.session_id}",
            ):
                user_input = "Research latest news and developments for my portfolio assets and their potential impact"
                st.session_state[
                    f"portfolio_chat_input_{st.session_state.session_id}"
                ] = user_input
                st.rerun()

        # Chat input - available immediately
        user_input = st.text_input(
            "Ask about your portfolio",
            placeholder="Ask about your portfolio performance, holdings, or get analysis...",
            key=f"portfolio_chat_input_{st.session_state.session_id}",
        )

        # Ask button
        ask_button = st.button(
            "Ask AI",
            key=f"portfolio_chat_ask_{st.session_state.session_id}",
            type="primary",
        )

        # Process the question
        if ask_button and user_input:
            with st.spinner("🤖 Analyzing your portfolio..."):
                try:
                    # Use the backend AI chat service with user-selected settings
                    client = get_api_client()

                    # Get AI settings from session state
                    model = st.session_state.get(
                        "selected_ai_model", None
                    )  # Let backend choose default
                    temperature = st.session_state.get("ai_temperature", 0.1)
                    use_functions = st.session_state.get("use_function_calling", True)

                    # Only pass model if user explicitly selected one
                    chat_params = {
                        "message": user_input,
                        "use_function_calling": use_functions,
                        "temperature": temperature,
                    }
                    if model:  # Only add model if explicitly selected
                        chat_params["model"] = model

                    response = client.chat_query(**chat_params)

                    # Display the AI response
                    st.success(f"🤖 **AI Response:**\n\n{response.message}")

                    # Save to chat history
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.session_state.chat_history.append(
                        (user_input, response.message, timestamp)
                    )

                    # Update cost tracking (estimate tokens)
                    estimated_tokens = (
                        len(user_input.split()) * 1.3
                        + len(response.message.split()) * 1.3
                    )
                    update_cost_tracking(model, int(estimated_tokens))

                    # Show function calls if any
                    if hasattr(response, "function_calls") and response.function_calls:
                        with st.expander("🔧 Function Calls Used", expanded=False):
                            for func_call in response.function_calls:
                                # Handle both dict and object formats
                                if isinstance(func_call, dict):
                                    func_name = func_call.get(
                                        "function_name", "unknown"
                                    )
                                    success = func_call.get("success", False)
                                    exec_time = func_call.get("execution_time_ms", 0.0)
                                    error_msg = func_call.get("error_message", "")
                                else:
                                    func_name = getattr(
                                        func_call, "function_name", "unknown"
                                    )
                                    success = getattr(func_call, "success", False)
                                    exec_time = getattr(
                                        func_call, "execution_time_ms", 0.0
                                    )
                                    error_msg = getattr(func_call, "error_message", "")

                                st.code(f"Called: {func_name}")
                                if success:
                                    st.success(f"✅ Success ({exec_time:.1f}ms)")
                                else:
                                    st.error(f"❌ Error: {error_msg}")

                    # Show cost info
                    costs = st.session_state.ai_costs
                    st.info(
                        f"💰 Query cost: ~${estimated_tokens * 15.0 / 1_000_000:.6f} | Session total: ${costs['total_cost']:.4f}"
                    )

                    # Clear input for next question
                    st.session_state[
                        f"portfolio_chat_input_{st.session_state.session_id}"
                    ] = ""

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.info(
                        "💡 Make sure your API keys are configured and backend is running"
                    )

    else:
        # Show simple button to open chat
        st.markdown("---")
        st.markdown("### 💬 Need help with your portfolio?")
        if st.button(
            "Open AI Portfolio Assistant",
            key=f"open_sticky_chat_{st.session_state.session_id}",
            type="primary",
        ):
            st.session_state.sticky_chat_open = True
            st.rerun()


def generate_portfolio_response(question, df):
    """Generate a simple AI response about the portfolio."""
    question_lower = question.lower()

    if "total" in question_lower or "value" in question_lower:
        total_value = df["Value €"].sum()
        return f"Your total portfolio value is €{total_value:,.2f} across {len(df)} different assets."

    elif "best" in question_lower or "top" in question_lower:
        best_performer = df.loc[df["Total Return %"].idxmax()]
        return f"Your best performing asset is {best_performer['Asset']} with a {best_performer['Total Return %']:.2f}% return (€{best_performer['Unrealized P&L €']:,.2f} profit)."

    elif "worst" in question_lower or "loss" in question_lower:
        worst_performer = df.loc[df["Total Return %"].idxmin()]
        return f"Your worst performing asset is {worst_performer['Asset']} with a {worst_performer['Total Return %']:.2f}% return (€{worst_performer['Unrealized P&L €']:,.2f} loss)."

    else:
        return f"I can help you analyze your portfolio of {len(df)} assets worth €{df['Value €'].sum():,.2f}. Try asking about your total value, best performers, or worst performers!"


def display_portfolio_charts(holdings):
    """Display portfolio charts and visualizations."""
    st.markdown("## 📊 Portfolio Visualizations")

    # Convert holdings to DataFrame for charting
    holdings_data = []
    for holding in holdings:
        holdings_data.append(
            {
                "Asset": holding.asset,
                "Value €": float(holding.value_eur),
                "Unrealized P&L €": float(holding.unrealized_pnl),
                "Realized P&L €": float(holding.realized_pnl),
                "Portfolio %": float(holding.portfolio_percentage),
                "Total Return %": float(holding.total_return_percentage),
            }
        )

    df = pd.DataFrame(holdings_data)

    if df.empty:
        st.info("No data available for charts")
        return

    # Create tabs for different visualizations
    chart_tab1, chart_tab2, chart_tab3 = st.tabs(
        ["📊 P&L Overview", "🥧 Portfolio Allocation", "📈 Performance Analysis"]
    )

    with chart_tab1:
        st.markdown("**💰 Profit & Loss by Asset**")
        st.markdown("*Green = Profit if sold now | Red = Loss if sold now*")

        # Filter out assets with zero unrealized P&L for cleaner chart
        chart_df = df[df["Unrealized P&L €"] != 0].copy()
        if not chart_df.empty:
            # Sort by unrealized P&L for better visualization
            chart_df = chart_df.sort_values("Unrealized P&L €", ascending=True)

            # Create the chart data
            pnl_data = chart_df.set_index("Asset")[
                ["Unrealized P&L €", "Realized P&L €"]
            ]
            st.bar_chart(pnl_data, height=400)
        else:
            st.info("No unrealized P&L to display")

    with chart_tab2:
        st.markdown("**🥧 Portfolio Allocation by Value**")

        # Create pie chart data for portfolio allocation
        portfolio_df = df[df["Value €"] > 0].copy()
        if not portfolio_df.empty:
            # Only show top 10 holdings for clarity
            portfolio_df = portfolio_df.nlargest(10, "Value €")

            # Try to use plotly for better pie chart, fallback to bar chart
            try:
                import plotly.express as px

                fig = px.pie(
                    portfolio_df,
                    values="Value €",
                    names="Asset",
                    title="Portfolio Allocation by Value",
                    height=500,
                )
                fig.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig, use_container_width=True)
            except ImportError:
                # Fallback to bar chart if plotly not available
                st.bar_chart(portfolio_df.set_index("Asset")["Value €"], height=400)
        else:
            st.info("No portfolio data to display")

    with chart_tab3:
        st.markdown("**📈 Performance Analysis**")

        # Top and bottom performers
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**🏆 Top Performers**")
            top_performers = df.nlargest(5, "Total Return %")[
                ["Asset", "Total Return %", "Unrealized P&L €"]
            ]
            if not top_performers.empty:
                for _, row in top_performers.iterrows():
                    delta_color = "normal" if row["Total Return %"] >= 0 else "inverse"
                    st.metric(
                        row["Asset"],
                        f"{row['Total Return %']:.2f}%",
                        f"€{row['Unrealized P&L €']:,.2f}",
                        delta_color=delta_color,
                    )

        with col2:
            st.markdown("**📉 Bottom Performers**")
            bottom_performers = df.nsmallest(5, "Total Return %")[
                ["Asset", "Total Return %", "Unrealized P&L €"]
            ]
            if not bottom_performers.empty:
                for _, row in bottom_performers.iterrows():
                    delta_color = "normal" if row["Total Return %"] >= 0 else "inverse"
                    st.metric(
                        row["Asset"],
                        f"{row['Total Return %']:.2f}%",
                        f"€{row['Unrealized P&L €']:,.2f}",
                        delta_color=delta_color,
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
                    use_function_calling=True,
                )

            # Update conversation ID
            st.session_state.conversation_id = response.conversation_id

            # Add assistant response to history
            st.session_state.chat_history.append(
                {
                    "role": "assistant",
                    "content": response.message,
                    "function_calls": response.function_calls,
                    "cost": response.cost_estimate,
                    "tokens": response.token_usage,
                }
            )

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
                            # Handle both dict and object formats
                            if isinstance(func_call, dict):
                                func_name = func_call.get("function_name", "unknown")
                                exec_time = func_call.get("execution_time_ms", 0.0)
                            else:
                                func_name = getattr(
                                    func_call, "function_name", "unknown"
                                )
                                exec_time = getattr(func_call, "execution_time_ms", 0.0)

                            st.write(f"**{func_name}** - {exec_time:.1f}ms")

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
        initial_sidebar_state="expanded",
        menu_items={"Get Help": None, "Report a bug": None, "About": None},
    )

    # Hide Streamlit style elements
    hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    st.title("📊 Crypto Portfolio Dashboard")

    # Display connection status, asset filters, AI settings, and cost tracking
    display_connection_status()
    asset_filter = display_asset_filters()
    ai_settings = display_ai_model_selector()
    display_cost_tracker()

    # Add refresh button for portfolio data
    col1, col2, col3 = st.columns([1, 1, 8])
    with col1:
        if st.button(
            "🔄 Refresh Data",
            key="refresh_portfolio_data",
            help="Force refresh portfolio data",
        ):
            # Clear the cache and session state
            st.cache_data.clear()
            if hasattr(st.session_state, "_portfolio_data_loaded"):
                del st.session_state._portfolio_data_loaded
            if hasattr(st.session_state, "_portfolio_load_time"):
                del st.session_state._portfolio_load_time
            st.rerun()
    with col2:
        # Show last refresh time if data is loaded
        if hasattr(st.session_state, "_portfolio_data_loaded") and hasattr(
            st.session_state, "_portfolio_load_time"
        ):
            st.caption(f"📊 Data loaded at {st.session_state._portfolio_load_time}")
        else:
            st.caption("📊 No data loaded yet")

    # Check backend connection
    if not check_backend_connection():
        st.error("❌ Cannot connect to backend. Please start the backend service.")
        st.stop()

    # Load portfolio data with better UX
    summary, holdings = None, None

    # Check if data is likely cached (to avoid showing loading message unnecessarily)
    data_is_cached = hasattr(st.session_state, "_portfolio_data_loaded")

    # Show loading state only if data is not cached
    loading_placeholder = st.empty()
    if not data_is_cached:
        with loading_placeholder:
            st.info(
                "📊 Loading portfolio data... (This may take 30-45 seconds for fresh data)"
            )
            st.info(
                "⏳ The backend is processing all your trades and calculating FIFO P&L - please be patient!"
            )

    # Check if this is a row selection rerun (data already loaded)
    is_row_selection_rerun = (
        st.session_state.get("_portfolio_data_loaded", False)
        and "holdings_table" in st.session_state
        and hasattr(st.session_state.holdings_table, "selection")
    )

    try:
        # Only show progress indicators for initial load, not for row selection reruns
        show_progress = not is_row_selection_rerun
        summary, holdings = load_portfolio_data(show_progress=show_progress)

        loading_placeholder.empty()  # Clear loading message

        # Mark that data has been loaded at least once in this session
        if not st.session_state.get("_portfolio_data_loaded", False):
            from datetime import datetime

            st.session_state._portfolio_data_loaded = True
            st.session_state._portfolio_load_time = datetime.now().strftime("%H:%M:%S")

    except Exception as e:
        loading_placeholder.empty()
        st.error(f"❌ Failed to load portfolio data: {str(e)}")
        st.info(
            "💡 You can still use the AI chat below while we retry loading your portfolio data."
        )
        # Don't stop - allow chat to work even if portfolio fails

    # Use radio buttons instead of tabs to maintain state during reruns
    # This prevents the navigation jump when clicking on table rows
    selected_view = st.radio(
        "Select View:",
        ["📊 Overview", "💰 Holdings"],
        horizontal=True,
        key="main_view_selector",
    )

    st.markdown("---")  # Visual separator

    # Display content based on selected view
    if selected_view == "📊 Overview":
        if summary:
            display_portfolio_summary(summary)

            # Add portfolio visualizations
            if holdings:
                display_portfolio_charts(holdings)
        else:
            st.warning("Portfolio summary is loading...")

    elif selected_view == "💰 Holdings":
        if holdings:
            # Apply asset filters
            filtered_holdings = filter_holdings_by_selection(holdings, asset_filter)

            # Show filter info
            if asset_filter != "all":
                st.info(
                    f"📊 Showing {len(filtered_holdings)} of {len(holdings)} assets ({asset_filter.replace('_', ' ').title()})"
                )

            display_holdings_table(filtered_holdings)
        else:
            st.warning("Portfolio holdings are loading...")

    # Always show sticky chat - even if portfolio data is loading
    render_sticky_chat(holdings or [])


if __name__ == "__main__":
    main()
