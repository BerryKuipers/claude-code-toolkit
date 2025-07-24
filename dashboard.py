#!/usr/bin/env python3
"""
Streamlit dashboard for crypto portfolio analysis.
Run this file directly with: streamlit run dashboard.py
"""

import logging
import os
import sys
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st
from python_bitvavo_api.bitvavo import Bitvavo

# Import performance optimizations
from src.portfolio.ui.performance import (
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
        print(f"[WARN] Warning: Could not set up file logging: {e}")
        print("[INFO] Continuing with console logging only")

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
        force=True,  # Override any existing logging configuration
    )

    return logging.getLogger(__name__)


# Initialize logger
logger = setup_logging()


# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file."""
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()


# Load environment variables
load_env_file()

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.portfolio.ai_explanations import (
    format_currency,
    generate_coin_explanation,
    get_position_summary,
    get_price_format_details,
)
from src.portfolio.chat import render_chat_interface
from src.portfolio.chat.api_status import APIStatusChecker
from src.portfolio.chat.cost_tracker import CostTracker, render_cost_footer
from src.portfolio.core import (
    BitvavoAPIException,
    InvalidAPIKeyError,
    RateLimitExceededError,
    TransferSummary,
    _decimal,
    analyze_transfers,
    calculate_discrepancy_breakdown,
    calculate_pnl,
    fetch_trade_history,
    get_current_price,
    get_portfolio_assets,
    sync_time,
)
from src.portfolio.ui.components import get_current_tab, render_sticky_header

# Note: Removed old UI imports - now using TabManager for clean navigation
from src.portfolio.ui.tabs import AnalysisTab, PortfolioTab, SettingsTab


def init_bitvavo_client() -> Optional[Bitvavo]:
    """Initialize Bitvavo client with error handling."""
    logger.info("Initializing Bitvavo client...")

    api_key = os.getenv("BITVAVO_API_KEY")
    api_secret = os.getenv("BITVAVO_API_SECRET")

    logger.info(f"API Key found: {'Yes' if api_key else 'No'}")
    logger.info(f"API Secret found: {'Yes' if api_secret else 'No'}")

    if not api_key or not api_secret:
        error_msg = (
            "⚠️ Please set BITVAVO_API_KEY and BITVAVO_API_SECRET environment variables"
        )
        logger.error(error_msg)
        st.error(error_msg)
        st.info("Add these to your .env file or system environment")
        return None

    try:
        logger.info("Creating Bitvavo client instance...")
        client = Bitvavo({"APIKEY": api_key, "APISECRET": api_secret})

        logger.info("Attempting to sync time with Bitvavo servers...")
        sync_time(client)

        logger.info("Bitvavo client initialized successfully")
        return client
    except BitvavoAPIException as exc:
        error_msg = f"❌ Error connecting to Bitvavo API: {exc}"
        logger.error(error_msg)
        st.error(error_msg)
        return None
    except Exception as exc:
        error_msg = f"❌ Unexpected error initializing Bitvavo client: {exc}"
        logger.error(error_msg)
        st.error(error_msg)
        return None


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_current_prices(assets: List[str]) -> Dict[str, float]:
    """Fetch current prices for all assets with caching."""
    logger.info(f"Fetching current prices for {len(assets)} assets: {assets}")

    client = init_bitvavo_client()
    if not client:
        logger.error("Failed to initialize Bitvavo client for price fetching")
        return {}

    prices = {}
    for asset in assets:
        try:
            price_eur = get_current_price(client, asset)
            if price_eur > 0:
                prices[asset] = float(price_eur)
                logger.info(f"Current price for {asset}: €{price_eur}")
            else:
                logger.warning(f"No valid EUR price found for {asset}")
        except Exception as e:
            logger.error(f"Error fetching price for {asset}: {e}")

    return prices


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_portfolio_data(
    assets: List[str],
    price_overrides: Dict[str, float],
    current_prices: Dict[str, float],
) -> pd.DataFrame:
    """Fetch and calculate portfolio data with caching."""
    logger.info(f"Getting portfolio data for {len(assets)} assets: {assets}")
    logger.info(f"Price overrides: {price_overrides}")

    client = init_bitvavo_client()
    if not client:
        logger.error("Failed to initialize Bitvavo client")
        st.error("❌ Failed to initialize Bitvavo client")
        return pd.DataFrame()

    # Get actual account balances for comparison
    try:
        actual_balances = {
            b["symbol"]: float(b["available"]) + float(b["inOrder"])
            for b in client.balance({})
        }
        logger.info(f"Retrieved actual balances for {len(actual_balances)} assets")
    except Exception as exc:
        logger.error(f"Failed to get actual balances: {exc}")
        actual_balances = {}

    data = []
    skipped_assets = []

    for asset in assets:
        try:
            logger.info(f"Processing asset: {asset}")
            trades = fetch_trade_history(client, asset)
            logger.info(f"Found {len(trades) if trades else 0} trades for {asset}")

            if not trades:
                logger.warning(f"No trades found for {asset}")
                skipped_assets.append(f"{asset} (no trades)")
                continue

            # Use override price if provided, otherwise use cached current price
            if asset in price_overrides:
                price_eur = _decimal(str(price_overrides[asset]))
                logger.info(f"Using override price for {asset}: €{price_eur}")
            else:
                # Use the current price from the cached prices
                current_price = current_prices.get(asset, 0.0)
                if current_price > 0:
                    price_eur = _decimal(str(current_price))
                    logger.info(f"Using cached price for {asset}: €{price_eur}")
                else:
                    logger.warning(f"No cached price found for {asset}")
                    skipped_assets.append(f"{asset} (no EUR pair)")
                    continue

            pnl = calculate_pnl(trades, price_eur)
            invested = pnl["total_buys_eur"]

            # Calculate total return percentage
            total_return_pct = (
                ((pnl["value_eur"] + pnl["realised_eur"]) - invested) / invested * 100
                if invested != 0
                else Decimal("0")
            )

            # Get actual balance for comparison
            actual_amount = _decimal(str(actual_balances.get(asset, 0.0)))
            fifo_amount = pnl["amount"]  # This is already a Decimal from calculate_pnl

            # Calculate values based on actual balance
            actual_value_eur = float(actual_amount) * float(price_eur)

            # Analyze transfers (deposits/withdrawals) for this asset
            try:
                logger.info(f"Analyzing transfers for {asset}")
                transfer_summary = analyze_transfers(client, asset)
                logger.info(
                    f"Transfer analysis for {asset}: {transfer_summary.deposit_count} deposits, {transfer_summary.withdrawal_count} withdrawals"
                )
            except Exception as exc:
                logger.warning(f"Failed to analyze transfers for {asset}: {exc}")
                # Create empty transfer summary if analysis fails
                transfer_summary = TransferSummary(
                    total_deposits=_decimal("0"),
                    total_withdrawals=_decimal("0"),
                    net_transfers=_decimal("0"),
                    deposit_count=0,
                    withdrawal_count=0,
                    potential_rewards=_decimal("0"),
                )

            # Calculate discrepancy breakdown
            discrepancy_breakdown = calculate_discrepancy_breakdown(
                fifo_amount, actual_amount, transfer_summary
            )

            data.append(
                {
                    "Asset": asset,
                    "FIFO Amount": float(fifo_amount),
                    "Actual Amount": float(actual_amount),
                    "Amount Diff": float(actual_amount - fifo_amount),
                    "Cost €": float(pnl["cost_eur"]),
                    "FIFO Value €": float(pnl["value_eur"]),
                    "Actual Value €": actual_value_eur,
                    "Realised €": float(pnl["realised_eur"]),
                    "Unrealised €": float(pnl["unrealised_eur"]),
                    "Total Return %": float(total_return_pct),
                    "Current Price €": format_currency(float(price_eur)),
                    "Total Invested €": float(
                        invested
                    ),  # Add the correct total investment amount
                    # Transfer data
                    "Net Transfers": float(transfer_summary.net_transfers),
                    "Total Deposits": float(transfer_summary.total_deposits),
                    "Total Withdrawals": float(transfer_summary.total_withdrawals),
                    "Deposit Count": transfer_summary.deposit_count,
                    "Withdrawal Count": transfer_summary.withdrawal_count,
                    "Potential Rewards": float(transfer_summary.potential_rewards),
                    # Discrepancy breakdown
                    "Transfer Explained": float(
                        discrepancy_breakdown["transfer_explained"]
                    ),
                    "Rewards Explained": float(
                        discrepancy_breakdown["rewards_explained"]
                    ),
                    "Unexplained Diff": float(discrepancy_breakdown["unexplained"]),
                    "Explanation %": float(
                        discrepancy_breakdown["explanation_percentage"]
                    ),
                }
            )

        except (BitvavoAPIException, InvalidAPIKeyError, RateLimitExceededError) as exc:
            error_msg = f"API error processing {asset}: {exc}"
            logger.error(error_msg)
            st.warning(f"⚠️ Error processing {asset}: {exc}")
            skipped_assets.append(f"{asset} (API error)")
            continue
        except Exception as exc:
            error_msg = f"Unexpected error processing {asset}: {exc}"
            logger.error(error_msg)
            st.warning(f"⚠️ Unexpected error processing {asset}: {exc}")
            skipped_assets.append(f"{asset} (unexpected error)")
            continue

    # Show debugging info
    logger.info(f"Successfully processed {len(data)} assets")
    if skipped_assets:
        logger.warning(f"Skipped {len(skipped_assets)} assets: {skipped_assets}")
        st.info(f"ℹ️ Skipped assets: {', '.join(skipped_assets)}")

    if not data:
        logger.warning("No valid data found for any selected assets")
        st.warning("⚠️ No valid data found for any selected assets")
    else:
        logger.info(f"Returning DataFrame with {len(data)} rows")

    return pd.DataFrame(data)


@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_available_assets() -> List[str]:
    """Get list of available assets with caching."""
    client = init_bitvavo_client()
    if not client:
        return []

    try:
        all_assets = get_portfolio_assets(client)
        # Filter to only assets that have trade history
        assets_with_trades = []
        for asset in all_assets:
            try:
                trades = fetch_trade_history(client, asset)
                if trades:  # Only include assets with actual trades
                    assets_with_trades.append(asset)
            except Exception as e:
                logger.warning(f"Error processing asset {asset}: {e}")
                continue  # Skip assets that cause errors
        return assets_with_trades
    except BitvavoAPIException:
        return []


def render_sticky_chat_interface(df: pd.DataFrame):
    """Render a chat interface that's accessible from all tabs."""
    # Add some spacing before the chat
    st.markdown("---")
    st.markdown("### 💬 AI Portfolio Assistant")
    st.markdown("*Ask questions about your portfolio from any tab*")

    # Create a collapsible chat section that's always visible
    with st.expander("🤖 Chat with AI about your portfolio", expanded=False):
        # Import here to avoid circular imports
        from src.portfolio.chat import render_chat_interface

        render_chat_interface(df)


def main():
    """Main Streamlit application."""
    # Apply global performance optimizations
    apply_global_optimizations()

    # Get sidebar state from session state (persisted across refreshes)
    sidebar_state = st.session_state.get("sidebar_state", "expanded")

    st.set_page_config(
        page_title="Crypto Portfolio Dashboard",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state=sidebar_state,
    )

    # Initialize session state objects FIRST
    if "api_status_checker" not in st.session_state:
        st.session_state.api_status_checker = APIStatusChecker()

    # Initialize cost tracker
    if "cost_tracker" not in st.session_state:
        st.session_state.cost_tracker = CostTracker()

    # Initialize other required session state objects
    if "selected_model" not in st.session_state:
        from src.portfolio.chat.base_llm_client import LLMClientFactory

        st.session_state.selected_model = LLMClientFactory.get_default_model()

    # Initialize sidebar state with persistence
    if "sidebar_state" not in st.session_state:
        st.session_state.sidebar_state = "expanded"

    if "total_cost" not in st.session_state:
        st.session_state.total_cost = 0.0

    # Initialize tab selection in session state
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = 0  # Default to Portfolio tab

    # Note: Removed old sticky navigation - now using TabManager for clean tab navigation

    # Render sticky header at the very top
    render_sticky_header()

    # Sidebar for controls
    st.sidebar.header("🎛️ Controls")
    st.sidebar.caption(
        "💡 Note: Changing settings will refresh the dashboard to update data"
    )

    # Get available assets
    with st.spinner("Loading available assets..."):
        # Clear cache if we have issues
        if st.sidebar.button("🔄 Clear Cache & Reload"):
            st.cache_data.clear()
            st.rerun()

        available_assets = get_available_assets()

        # Temporary fallback for debugging
        if not available_assets:
            st.warning("⚠️ Using fallback asset list for debugging")
            available_assets = ["BTC", "ETH", "XRP", "ADA", "DOT"]  # Common assets

    if not available_assets:
        st.error("❌ No assets found or API connection failed")
        st.info("Make sure your API credentials are set and you have crypto balances")

        # Debug information
        with st.expander("🔍 Debug Information"):
            st.write("Checking Bitvavo client initialization...")
            client = init_bitvavo_client()
            if client:
                st.success("✅ Bitvavo client initialized successfully")
                try:
                    # Try to get portfolio assets directly
                    portfolio_assets = get_portfolio_assets(client)
                    st.write(
                        f"Found {len(portfolio_assets)} portfolio assets: {portfolio_assets}"
                    )
                except Exception as e:
                    st.error(f"Error getting portfolio assets: {e}")
            else:
                st.error("❌ Failed to initialize Bitvavo client")
        return

    # Asset selection
    selected_assets = st.sidebar.multiselect(
        "Select Assets",
        options=available_assets,
        default=available_assets,
        help="Choose which assets to include in the analysis",
        key="asset_selector",  # Stable key to reduce unnecessary reruns
    )

    if not selected_assets:
        st.warning("⚠️ Please select at least one asset")
        return

    # Price overrides section
    st.sidebar.subheader("💰 Price Overrides")
    st.sidebar.markdown("*Override live prices for what-if scenarios*")

    # Get current prices for all selected assets
    with st.spinner("Fetching current prices..."):
        current_prices = get_current_prices(selected_assets)

    price_overrides = {}
    for asset in selected_assets:
        # Use current price as default, or 0.0 if not available
        current_price = current_prices.get(asset, 0.0)

        # Show current price in the label if available with proper formatting
        if current_price > 0:
            # Use dynamic formatting for small prices
            price_display = format_currency(current_price)

            # Set appropriate step and format based on price magnitude
            step_value, format_str = get_price_format_details(current_price)

            label = f"{asset} Price (€) - Current: {price_display}"
            help_text = (
                f"Current live price: {price_display}. Modify to run what-if scenarios."
            )
        else:
            label = f"{asset} Price (€) - No EUR pair"
            help_text = f"No EUR trading pair available for {asset}"
            step_value = 0.01
            format_str = "%.2f"

        override_value = st.sidebar.number_input(
            label,
            min_value=0.0,
            value=current_price,
            step=step_value,
            format=format_str,
            help=help_text,
            key=f"price_override_{asset}",  # Unique key to prevent conflicts
        )

        # Only consider it an override if it's different from current price
        if override_value != current_price and override_value > 0:
            price_overrides[asset] = override_value

    # Refresh button
    if st.sidebar.button("🔄 Refresh Data", type="primary", key="refresh_data_btn"):
        st.cache_data.clear()
        st.rerun()

    # Get portfolio data using cached prices
    with st.spinner("Fetching portfolio data..."):
        df = get_portfolio_data(selected_assets, price_overrides, current_prices)

    if df.empty:
        st.error("❌ No data available")
        return

    # Render content based on selected tab
    current_tab = get_current_tab()

    if current_tab == "Portfolio":
        PortfolioTab().render(df, price_overrides)
    elif current_tab == "Analysis":
        AnalysisTab().render(df)
    elif current_tab == "Settings":
        SettingsTab().render(selected_assets, current_prices, price_overrides)

    # Render sticky chat interface at the bottom (outside of tabs)
    # Note: Chat is available in dedicated Chat tab and doesn't need to be sticky
    # render_sticky_chat_interface(df)

    # Footer (outside of tabs)
    st.markdown("---")
    st.markdown("*Data refreshed every 5 minutes. Price overrides update immediately.*")
    st.markdown(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

    # Render cost footer for LLM usage tracking
    render_cost_footer()


if __name__ == "__main__":
    main()
