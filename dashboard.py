#!/usr/bin/env python3
"""
Streamlit dashboard for crypto portfolio analysis.
Run this file directly with: streamlit run dashboard.py
"""

import os
import sys
import logging
from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime

import streamlit as st
import pandas as pd
from python_bitvavo_api.bitvavo import Bitvavo

# Set up logging
def setup_logging():
    """Set up comprehensive logging to file and console."""
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f'dashboard_{datetime.now().strftime("%Y%m%d")}.log')

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    return logging.getLogger(__name__)

# Initialize logger
logger = setup_logging()

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file."""
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Load environment variables
load_env_file()

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.portfolio.core import (
    sync_time,
    fetch_trade_history,
    calculate_pnl,
    analyze_transfers,
    calculate_discrepancy_breakdown,
    TransferSummary,
    get_current_price,
    get_portfolio_assets,
    _decimal,
    BitvavoAPIException,
    InvalidAPIKeyError,
    RateLimitExceededError,
)


def init_bitvavo_client() -> Optional[Bitvavo]:
    """Initialize Bitvavo client with error handling."""
    logger.info("Initializing Bitvavo client...")

    api_key = os.getenv("BITVAVO_API_KEY")
    api_secret = os.getenv("BITVAVO_API_SECRET")

    logger.info(f"API Key found: {'Yes' if api_key else 'No'}")
    logger.info(f"API Secret found: {'Yes' if api_secret else 'No'}")

    if not api_key or not api_secret:
        error_msg = "⚠️ Please set BITVAVO_API_KEY and BITVAVO_API_SECRET environment variables"
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
def get_portfolio_data(assets: List[str], price_overrides: Dict[str, float]) -> pd.DataFrame:
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
        actual_balances = {b['symbol']: float(b['available']) + float(b['inOrder'])
                          for b in client.balance({})}
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

            # Use override price if provided, otherwise get live price
            if asset in price_overrides:
                price_eur = _decimal(str(price_overrides[asset]))
                logger.info(f"Using override price for {asset}: €{price_eur}")
            else:
                logger.info(f"Fetching live price for {asset}")
                price_eur = get_current_price(client, asset)
                logger.info(f"Live price for {asset}: €{price_eur}")

                # Skip assets with no valid price (no EUR trading pair)
                if price_eur == 0:
                    logger.warning(f"No valid EUR price found for {asset}")
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
                logger.info(f"Transfer analysis for {asset}: {transfer_summary.deposit_count} deposits, {transfer_summary.withdrawal_count} withdrawals")
            except Exception as exc:
                logger.warning(f"Failed to analyze transfers for {asset}: {exc}")
                # Create empty transfer summary if analysis fails
                transfer_summary = TransferSummary(
                    total_deposits=_decimal("0"),
                    total_withdrawals=_decimal("0"),
                    net_transfers=_decimal("0"),
                    deposit_count=0,
                    withdrawal_count=0,
                    potential_rewards=_decimal("0")
                )

            # Calculate discrepancy breakdown
            discrepancy_breakdown = calculate_discrepancy_breakdown(
                fifo_amount, actual_amount, transfer_summary
            )

            data.append({
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
                "Current Price €": float(price_eur),
                # Transfer data
                "Net Transfers": float(transfer_summary.net_transfers),
                "Total Deposits": float(transfer_summary.total_deposits),
                "Total Withdrawals": float(transfer_summary.total_withdrawals),
                "Deposit Count": transfer_summary.deposit_count,
                "Withdrawal Count": transfer_summary.withdrawal_count,
                "Potential Rewards": float(transfer_summary.potential_rewards),
                # Discrepancy breakdown
                "Transfer Explained": float(discrepancy_breakdown["transfer_explained"]),
                "Rewards Explained": float(discrepancy_breakdown["rewards_explained"]),
                "Unexplained Diff": float(discrepancy_breakdown["unexplained"]),
                "Explanation %": float(discrepancy_breakdown["explanation_percentage"]),
            })
            
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
            except Exception:
                continue  # Skip assets that cause errors
        return assets_with_trades
    except BitvavoAPIException:
        return []


def create_pnl_chart(df: pd.DataFrame) -> None:
    """Create enhanced P&L visualizations."""
    if df.empty:
        return

    # Create tabs for different visualizations
    tab1, tab2, tab3, tab4 = st.tabs(["📊 P&L Overview", "🥧 Portfolio Allocation", "📈 Top Performers", "🔄 Transfer Analysis"])

    with tab1:
        st.markdown("**💰 Profit & Loss by Asset**")
        st.markdown("*Green = Profit if sold now | Red = Loss if sold now*")

        # Filter out assets with zero unrealized P&L for cleaner chart
        chart_df = df[df["Unrealised €"] != 0].copy()
        if not chart_df.empty:
            # Sort by unrealized P&L for better visualization
            chart_df = chart_df.sort_values("Unrealised €", ascending=True)

            # Create the chart data
            chart_data = pd.DataFrame({
                "Asset": chart_df["Asset"],
                "Unrealised P&L €": chart_df["Unrealised €"],
                "Realised P&L €": chart_df["Realised €"],
            })

            st.bar_chart(chart_data.set_index("Asset"), height=400)
        else:
            st.info("No unrealized P&L to display")

    with tab2:
        st.markdown("**🎯 Portfolio Value Distribution**")
        st.markdown("*Shows how your money is distributed across assets*")

        # Create pie chart data for portfolio allocation
        portfolio_df = df[df["Actual Value €"] > 0].copy()
        if not portfolio_df.empty:
            # Only show top 10 holdings for clarity
            portfolio_df = portfolio_df.nlargest(10, "Actual Value €")

            # Create pie chart using plotly
            try:
                import plotly.express as px
                fig = px.pie(
                    portfolio_df,
                    values="Actual Value €",
                    names="Asset",
                    title="Portfolio Allocation by Value",
                    height=500
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            except ImportError:
                # Fallback to simple bar chart if plotly not available
                st.bar_chart(portfolio_df.set_index("Asset")["Actual Value €"], height=400)
        else:
            st.info("No portfolio data to display")

    with tab3:
        st.markdown("**🚀 Performance Rankings**")
        st.markdown("*Assets ranked by percentage return*")

        # Show top and bottom performers
        perf_df = df[df["Total Return %"] != 0].copy()
        if not perf_df.empty:
            perf_df = perf_df.sort_values("Total Return %", ascending=False)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**🏆 Top 5 Performers**")
                top_5 = perf_df.head(5)
                for _, row in top_5.iterrows():
                    delta_color = "normal" if row["Total Return %"] >= 0 else "inverse"
                    st.metric(
                        row["Asset"],
                        f"€{row['Actual Value €']:.0f}",
                        f"{row['Total Return %']:.1f}%",
                        delta_color=delta_color
                    )

            with col2:
                st.markdown("**📉 Bottom 5 Performers**")
                bottom_5 = perf_df.tail(5)
                for _, row in bottom_5.iterrows():
                    delta_color = "normal" if row["Total Return %"] >= 0 else "inverse"
                    st.metric(
                        row["Asset"],
                        f"€{row['Actual Value €']:.0f}",
                        f"{row['Total Return %']:.1f}%",
                        delta_color=delta_color
                    )
        else:
            st.info("No performance data to display")

    with tab4:
        st.markdown("**🔄 Transfer Flow Analysis**")

        # Check if we have transfer data
        has_transfer_data = any([
            "Net Transfers" in df.columns,
            "Total Deposits" in df.columns,
            "Total Withdrawals" in df.columns
        ])

        if not has_transfer_data:
            st.info("Transfer analysis data not available. This feature requires deposit/withdrawal history.")
            return

        # Create transfer flow chart
        transfer_data = df[df["Net Transfers"] != 0].copy()
        if not transfer_data.empty:
            try:
                import plotly.express as px
                fig_transfers = px.bar(
                    transfer_data,
                    x="Asset",
                    y=["Total Deposits", "Total Withdrawals"],
                    title="Deposits vs Withdrawals by Asset",
                    barmode="group",
                    color_discrete_map={"Total Deposits": "green", "Total Withdrawals": "red"},
                    height=400
                )
                fig_transfers.update_layout(
                    xaxis_title="Asset",
                    yaxis_title="Amount",
                )
                st.plotly_chart(fig_transfers, use_container_width=True)
            except ImportError:
                # Fallback without plotly
                st.bar_chart(transfer_data.set_index("Asset")[["Total Deposits", "Total Withdrawals"]])
        else:
            st.info("No transfer activity detected for visualization.")

        # Discrepancy explanation chart
        st.markdown("**🔍 Discrepancy Explanation Breakdown**")
        discrepancy_data = df[abs(df["Amount Diff"]) > 0.000001].copy()
        if not discrepancy_data.empty:
            try:
                import plotly.express as px
                # Prepare data for stacked bar chart
                explanation_cols = ["Transfer Explained", "Rewards Explained", "Unexplained Diff"]
                fig_discrepancy = px.bar(
                    discrepancy_data,
                    x="Asset",
                    y=explanation_cols,
                    title="How Discrepancies Are Explained",
                    barmode="stack",
                    color_discrete_map={
                        "Transfer Explained": "lightblue",
                        "Rewards Explained": "lightgreen",
                        "Unexplained Diff": "orange"
                    },
                    height=400
                )
                fig_discrepancy.update_layout(
                    xaxis_title="Asset",
                    yaxis_title="Amount Difference",
                )
                st.plotly_chart(fig_discrepancy, use_container_width=True)
            except ImportError:
                # Fallback without plotly
                st.bar_chart(discrepancy_data.set_index("Asset")[explanation_cols])
        else:
            st.info("No significant discrepancies to analyze.")

        # Transfer activity summary table
        st.markdown("**📊 Transfer Activity Summary**")
        activity_data = df[["Asset", "Deposit Count", "Withdrawal Count", "Potential Rewards"]].copy()
        activity_data = activity_data[
            (activity_data["Deposit Count"] > 0) |
            (activity_data["Withdrawal Count"] > 0) |
            (activity_data["Potential Rewards"] > 0)
        ]

        if not activity_data.empty:
            st.dataframe(
                activity_data,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Asset": st.column_config.TextColumn("Asset", width="small"),
                    "Deposit Count": st.column_config.NumberColumn("Deposits", format="%d", width="small"),
                    "Withdrawal Count": st.column_config.NumberColumn("Withdrawals", format="%d", width="small"),
                    "Potential Rewards": st.column_config.NumberColumn("Est. Rewards", format="%.6f", width="small"),
                }
            )
        else:
            st.info("No transfer activity detected.")


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Crypto Portfolio Dashboard",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Add mobile-responsive CSS
    st.markdown("""
    <style>
    /* Mobile-responsive adjustments */
    @media (max-width: 768px) {
        .stDataFrame {
            font-size: 12px;
        }
        .metric-container {
            margin-bottom: 1rem;
        }
        .stColumns > div {
            padding: 0.5rem;
        }
    }

    /* Better spacing for metrics */
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }

    /* Improved table styling */
    .stDataFrame {
        border-radius: 0.5rem;
        overflow: hidden;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("📈 Crypto Portfolio FIFO P&L Dashboard")
    st.markdown("*Real-time portfolio analysis with FIFO accounting*")
    
    # Sidebar for controls
    st.sidebar.header("🎛️ Controls")
    
    # Get available assets
    available_assets = get_available_assets()
    
    if not available_assets:
        st.error("❌ No assets found or API connection failed")
        st.info("Make sure your API credentials are set and you have crypto balances")
        return
    
    # Asset selection
    selected_assets = st.sidebar.multiselect(
        "Select Assets",
        options=available_assets,
        default=available_assets,
        help="Choose which assets to include in the analysis"
    )
    
    if not selected_assets:
        st.warning("⚠️ Please select at least one asset")
        return
    
    # Price overrides section
    st.sidebar.subheader("💰 Price Overrides")
    st.sidebar.markdown("*Override live prices for what-if scenarios*")
    
    price_overrides = {}
    for asset in selected_assets:
        override_value = st.sidebar.number_input(
            f"{asset} Price (€)",
            min_value=0.0,
            value=0.0,
            step=0.01,
            format="%.2f",
            help=f"Leave at 0 to use live {asset} price"
        )
        if override_value > 0:
            price_overrides[asset] = override_value
    
    # Refresh button
    if st.sidebar.button("🔄 Refresh Data", type="primary"):
        st.cache_data.clear()
        st.rerun()
    
    # Get portfolio data first
    with st.spinner("Fetching portfolio data..."):
        df = get_portfolio_data(selected_assets, price_overrides)

    if df.empty:
        st.error("❌ No data available")
        return

    # Portfolio Overview Section
    st.subheader("📊 Portfolio Overview")

    # Add column explanations
    with st.expander("📋 Column Explanations - Click to understand what each column means"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **📊 Holdings & Values:**
            - **FIFO Amt**: Amount calculated from trade history
            - **Actual Amt**: Your real current balance on Bitvavo
            - **Diff**: Difference between FIFO and actual amounts
            - **Cost €**: Total money you spent on this coin
            - **FIFO €**: Value based on FIFO calculation
            - **Actual €**: Value based on your real holdings
            """)
        with col2:
            st.markdown("""
            **💰 Profit & Loss:**
            - **Realised €**: Profit/loss from completed trades
            - **Unrealised €**: Profit/loss if you sell NOW
              - ✅ **Positive = Profit** if sold now
              - ❌ **Negative = Loss** if sold now
            - **Return %**: Overall performance percentage
            - **Price €**: Current market price per coin
            """)

        # Add a third section for transfer analysis
        st.markdown("**🔄 Transfer & Discrepancy Analysis:**")
        col3, col4 = st.columns(2)
        with col3:
            st.markdown("""
            **📥 Deposits & Withdrawals:**
            - **Net Transfers**: Deposits minus withdrawals
            - **Total Deposits**: Amount deposited from external sources
            - **Total Withdrawals**: Amount withdrawn to external wallets
            - **Deposit Count**: Number of deposit transactions
            - **Withdrawal Count**: Number of withdrawal transactions
            """)
        with col4:
            st.markdown("""
            **🎁 Rewards & Explanations:**
            - **Potential Rewards**: Estimated staking rewards/airdrops
            - **Transfer Explained**: Difference explained by transfers
            - **Rewards Explained**: Difference explained by rewards
            - **Unexplained Diff**: Remaining unexplained discrepancy
            - **Explanation %**: How much is explained (higher = better)
            """)

    # Display the main table with mobile-friendly formatting
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Asset": st.column_config.TextColumn("Asset", width="small"),
            "FIFO Amount": st.column_config.NumberColumn("FIFO Amt", format="%.6f", width="small", help="Amount calculated from trade history"),
            "Actual Amount": st.column_config.NumberColumn("Actual Amt", format="%.6f", width="small", help="Your real current balance on Bitvavo"),
            "Amount Diff": st.column_config.NumberColumn("Diff", format="%.6f", width="small", help="Difference between FIFO and actual amounts"),
            "Cost €": st.column_config.NumberColumn("Cost €", format="€%.0f", width="small", help="Total money you spent on this coin"),
            "FIFO Value €": st.column_config.NumberColumn("FIFO €", format="€%.0f", width="small", help="Value based on FIFO calculation"),
            "Actual Value €": st.column_config.NumberColumn("Actual €", format="€%.0f", width="small", help="Value based on your real holdings"),
            "Realised €": st.column_config.NumberColumn("Realised €", format="€%.0f", width="small", help="Profit/loss from completed trades"),
            "Unrealised €": st.column_config.NumberColumn("Unrealised €", format="€%.0f", width="small", help="Profit/loss if you sell NOW - Positive=Profit, Negative=Loss"),
            "Total Return %": st.column_config.NumberColumn("Return %", format="%.1f%%", width="small", help="Overall performance percentage"),
            "Current Price €": st.column_config.NumberColumn("Price €", format="€%.2f", width="small", help="Current market price per coin"),
            # Transfer columns
            "Net Transfers": st.column_config.NumberColumn("Net Transfers", format="%.6f", width="small", help="Net amount transferred (deposits - withdrawals)"),
            "Total Deposits": st.column_config.NumberColumn("Deposits", format="%.6f", width="small", help="Total amount deposited from external sources"),
            "Total Withdrawals": st.column_config.NumberColumn("Withdrawals", format="%.6f", width="small", help="Total amount withdrawn to external wallets"),
            "Deposit Count": st.column_config.NumberColumn("Dep#", format="%d", width="small", help="Number of deposit transactions"),
            "Withdrawal Count": st.column_config.NumberColumn("With#", format="%d", width="small", help="Number of withdrawal transactions"),
            "Potential Rewards": st.column_config.NumberColumn("Rewards", format="%.6f", width="small", help="Estimated staking rewards/airdrops"),
            "Transfer Explained": st.column_config.NumberColumn("Trans Exp", format="%.6f", width="small", help="Amount difference explained by transfers"),
            "Rewards Explained": st.column_config.NumberColumn("Rew Exp", format="%.6f", width="small", help="Amount difference explained by rewards"),
            "Unexplained Diff": st.column_config.NumberColumn("Unexplained", format="%.6f", width="small", help="Remaining unexplained discrepancy"),
            "Explanation %": st.column_config.NumberColumn("Expl %", format="%.1f%%", width="small", help="Percentage of discrepancy explained"),
        }
    )

    # Calculate and display totals
    fifo_totals = {
        "Total Cost": df["Cost €"].sum(),
        "FIFO Value": df["FIFO Value €"].sum(),
        "Actual Value": df["Actual Value €"].sum(),
        "Total Realised": df["Realised €"].sum(),
        "Total Unrealised": df["Unrealised €"].sum(),
    }

    total_invested = df["Cost €"].sum() + abs(df["Realised €"].sum())
    fifo_return = ((fifo_totals["FIFO Value"] + fifo_totals["Total Realised"]) - total_invested) / total_invested * 100 if total_invested > 0 else 0

    # Portfolio Summary Section
    st.subheader("💼 Portfolio Summary")

    # Mobile-responsive metrics layout
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("FIFO Value", f"€{fifo_totals['FIFO Value']:.0f}")
        st.metric("Total Cost", f"€{fifo_totals['Total Cost']:.0f}")
        st.metric("Realised P&L", f"€{fifo_totals['Total Realised']:.0f}")
    with col_b:
        st.metric("Actual Value", f"€{fifo_totals['Actual Value']:.0f}",
                 delta=f"€{fifo_totals['Actual Value'] - fifo_totals['FIFO Value']:.0f}")
        st.metric("Unrealised P&L", f"€{fifo_totals['Total Unrealised']:.0f}")
        st.metric("📈 FIFO Return", f"{fifo_return:.1f}%")

    # Show discrepancy warning if significant differences
    value_diff = abs(fifo_totals['Actual Value'] - fifo_totals['FIFO Value'])
    if value_diff > 100:  # More than €100 difference
        st.warning(f"⚠️ **Significant discrepancy detected!** "
                  f"Your actual portfolio value differs from FIFO calculation by €{value_diff:.0f}. "
                  f"This may be due to deposits/withdrawals not captured in trade history.")

    # Transfer Analysis Section
    st.subheader("🔄 Transfer & Discrepancy Analysis")

    # Calculate totals for transfer analysis
    total_transfers = df["Net Transfers"].sum()
    total_deposits = df["Total Deposits"].sum()
    total_withdrawals = df["Total Withdrawals"].sum()
    total_rewards = df["Potential Rewards"].sum()
    total_transfer_explained = df["Transfer Explained"].sum()
    total_rewards_explained = df["Rewards Explained"].sum()
    total_unexplained = df["Unexplained Diff"].sum()

    # Create columns for transfer metrics
    trans_col1, trans_col2, trans_col3 = st.columns(3)

    with trans_col1:
        st.markdown("**📥 Deposit/Withdrawal Summary**")
        st.metric("Total Deposits", f"{total_deposits:.6f}")
        st.metric("Total Withdrawals", f"{total_withdrawals:.6f}")
        st.metric("Net Transfers", f"{total_transfers:.6f}")

    with trans_col2:
        st.markdown("**🎁 Rewards & Airdrops**")
        st.metric("Potential Rewards", f"{total_rewards:.6f}")
        deposit_count = df["Deposit Count"].sum()
        withdrawal_count = df["Withdrawal Count"].sum()
        st.metric("Total Transactions", f"{deposit_count + withdrawal_count}")
        st.metric("Deposits vs Withdrawals", f"{deposit_count}D / {withdrawal_count}W")

    with trans_col3:
        st.markdown("**🔍 Discrepancy Breakdown**")
        st.metric("Transfer Explained", f"{total_transfer_explained:.6f}")
        st.metric("Rewards Explained", f"{total_rewards_explained:.6f}")
        st.metric("Still Unexplained", f"{total_unexplained:.6f}")

    # Show explanation percentage
    total_amount_diff = df["Amount Diff"].sum()
    if abs(total_amount_diff) > 0:
        explanation_pct = abs(total_transfer_explained + total_rewards_explained) / abs(total_amount_diff) * 100
        if explanation_pct > 80:
            st.success(f"✅ **{explanation_pct:.1f}%** of discrepancies explained by transfers and rewards!")
        elif explanation_pct > 50:
            st.info(f"ℹ️ **{explanation_pct:.1f}%** of discrepancies explained by transfers and rewards.")
        else:
            st.warning(f"⚠️ Only **{explanation_pct:.1f}%** of discrepancies explained. Remaining differences may be due to missing data.")

    # Assets with significant unexplained differences
    unexplained_assets = df[abs(df["Unexplained Diff"]) > 0.001].copy()
    if not unexplained_assets.empty:
        st.markdown("**🔍 Assets with Unexplained Discrepancies:**")
        unexplained_display = unexplained_assets[["Asset", "Amount Diff", "Transfer Explained", "Rewards Explained", "Unexplained Diff"]].copy()
        st.dataframe(unexplained_display, use_container_width=True, hide_index=True)

    # P&L Visualization Section
    st.subheader("📈 P&L Visualization")

    if not df.empty:
        create_pnl_chart(df)

        # Key Metrics Section with better explanations
        st.subheader("🎯 Key Metrics")

        # Create two columns for metrics
        met_col1, met_col2 = st.columns(2)

        with met_col1:
            st.markdown("**📊 Performance Leaders**")
            best_performer = df.loc[df["Total Return %"].idxmax()]
            worst_performer = df.loc[df["Total Return %"].idxmin()]

            st.metric("🚀 Best Performer",
                     f"{best_performer['Asset']}",
                     f"{best_performer['Total Return %']:.1f}%")
            st.metric("📉 Worst Performer",
                     f"{worst_performer['Asset']}",
                     f"{worst_performer['Total Return %']:.1f}%")

        with met_col2:
            st.markdown("**🎯 Portfolio Composition**")
            # Use actual values for portfolio composition
            total_actual_value = df["Actual Value €"].sum()
            if total_actual_value > 0:
                largest_holding = df.loc[df["Actual Value €"].idxmax()]
                largest_pct = (largest_holding["Actual Value €"] / total_actual_value) * 100
                st.metric("💎 Largest Holding",
                         f"{largest_holding['Asset']}",
                         f"{largest_pct:.1f}% of portfolio")

                # Count of profitable positions
                profitable_count = len(df[df["Total Return %"] > 0])
                total_positions = len(df)
                st.metric("📈 Profitable Positions",
                         f"{profitable_count}/{total_positions}",
                         f"{(profitable_count/total_positions*100):.0f}%")

        # Show price overrides if any
        if price_overrides:
            st.subheader("⚙️ Active Price Overrides")
            for asset, price in price_overrides.items():
                st.info(f"{asset}: €{price:.2f}")

    # Explanation section
    with st.expander("ℹ️ What do these metrics mean?"):
        st.markdown("""
        **FIFO vs Actual Values:**
        - **FIFO Amount**: Holdings calculated from your trade history using First-In-First-Out accounting
        - **Actual Amount**: Your real current balance on Bitvavo
        - **Difference**: Shows deposits/withdrawals not captured in trade history

        **Financial Metrics:**
        - **Cost €**: Total amount invested (purchases minus sales)
        - **FIFO Value €**: Value based on FIFO calculation from trades
        - **Actual Value €**: Value based on your real current holdings
        - **Realised €**: Profit/loss from completed trades
        - **Unrealised €**: Current profit/loss on holdings
        - **Total Return %**: Overall performance including both realised and unrealised gains

        **Why might FIFO and Actual differ?**
        - Direct deposits to Bitvavo (not through trades)
        - Withdrawals from other exchanges
        - Staking rewards or airdrops
        - Manual transfers between accounts
        """)

    # Footer
    st.markdown("---")
    st.markdown("*Data refreshed every 5 minutes. Price overrides update immediately.*")
    st.markdown(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")


if __name__ == "__main__":
    main()
