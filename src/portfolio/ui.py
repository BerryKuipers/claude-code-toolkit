"""Streamlit dashboard for interactive crypto portfolio analysis.

Provides a web-based interface for FIFO P&L analysis with real-time filtering,
price overrides, and visualization of portfolio performance over time.
"""

import os
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import streamlit as st
import pandas as pd
from python_bitvavo_api.bitvavo import Bitvavo

try:
    from .core import (
        sync_time,
        fetch_trade_history,
        calculate_pnl,
        get_current_price,
        get_portfolio_assets,
        _decimal,
        BitvavoAPIException,
        InvalidAPIKeyError,
        RateLimitExceededError,
    )
except ImportError:
    # When running directly with streamlit, use absolute imports
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from src.portfolio.core import (
        sync_time,
        fetch_trade_history,
        calculate_pnl,
        get_current_price,
        get_portfolio_assets,
        _decimal,
        BitvavoAPIException,
        InvalidAPIKeyError,
        RateLimitExceededError,
    )


def init_bitvavo_client() -> Optional[Bitvavo]:
    """Initialize Bitvavo client with error handling."""
    api_key = os.getenv("BITVAVO_API_KEY")
    api_secret = os.getenv("BITVAVO_API_SECRET")
    
    if not api_key or not api_secret:
        st.error("⚠️ Please set BITVAVO_API_KEY and BITVAVO_API_SECRET environment variables")
        st.info("Add these to your .env file or system environment")
        return None
    
    try:
        client = Bitvavo({"APIKEY": api_key, "APISECRET": api_secret})
        sync_time(client)
        return client
    except BitvavoAPIException as exc:
        st.error(f"❌ Error connecting to Bitvavo API: {exc}")
        return None


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_current_prices(assets: List[str]) -> Dict[str, float]:
    """Fetch current prices for all assets with caching."""
    client = init_bitvavo_client()
    if not client:
        return {}

    prices = {}
    for asset in assets:
        try:
            price_eur = get_current_price(client, asset)
            if price_eur > 0:
                prices[asset] = float(price_eur)
        except Exception:
            pass  # Skip assets with errors

    return prices


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_portfolio_data(assets: List[str], price_overrides: Dict[str, float]) -> pd.DataFrame:
    """Fetch and calculate portfolio data with caching."""
    client = init_bitvavo_client()
    if not client:
        return pd.DataFrame()
    
    data = []
    
    for asset in assets:
        try:
            trades = fetch_trade_history(client, asset)
            if not trades:
                continue
            
            # Use override price if provided, otherwise get live price
            if asset in price_overrides:
                price_eur = _decimal(str(price_overrides[asset]))
            else:
                price_eur = get_current_price(client, asset)
            
            pnl = calculate_pnl(trades, price_eur)
            invested = pnl["total_buys_eur"]
            
            # Calculate total return percentage
            total_return_pct = (
                ((pnl["value_eur"] + pnl["realised_eur"]) - invested) / invested * 100
                if invested != 0
                else Decimal("0")
            )
            
            data.append({
                "Asset": asset,
                "Amount": float(pnl["amount"]),
                "Cost €": float(pnl["cost_eur"]),
                "Value €": float(pnl["value_eur"]),
                "Realised €": float(pnl["realised_eur"]),
                "Unrealised €": float(pnl["unrealised_eur"]),
                "Total Return %": float(total_return_pct),
                "Current Price €": float(price_eur),
            })
            
        except (BitvavoAPIException, InvalidAPIKeyError, RateLimitExceededError) as exc:
            st.warning(f"⚠️ Error processing {asset}: {exc}")
            continue
    
    return pd.DataFrame(data)


@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_available_assets() -> List[str]:
    """Get list of available assets with caching."""
    client = init_bitvavo_client()
    if not client:
        return []
    
    try:
        return get_portfolio_assets(client)
    except BitvavoAPIException:
        return []


def create_pnl_chart(df: pd.DataFrame) -> None:
    """Create a simple P&L visualization."""
    if df.empty:
        return
    
    # Create a summary chart showing realized vs unrealized P&L
    chart_data = pd.DataFrame({
        "Asset": df["Asset"],
        "Realised P&L €": df["Realised €"],
        "Unrealised P&L €": df["Unrealised €"],
    })
    
    st.bar_chart(chart_data.set_index("Asset"))


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Crypto Portfolio Dashboard",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
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

    # Get current prices for all selected assets
    with st.spinner("Fetching current prices..."):
        current_prices = get_current_prices(selected_assets)

    price_overrides = {}
    for asset in selected_assets:
        # Use current price as default, or 0.0 if not available
        current_price = current_prices.get(asset, 0.0)

        # Show current price in the label if available
        if current_price > 0:
            label = f"{asset} Price (€) - Current: €{current_price:.2f}"
            help_text = f"Current live price: €{current_price:.2f}. Modify to run what-if scenarios."
        else:
            label = f"{asset} Price (€) - No EUR pair"
            help_text = f"No EUR trading pair available for {asset}"

        override_value = st.sidebar.number_input(
            label,
            min_value=0.0,
            value=current_price,
            step=0.01,
            format="%.2f",
            help=help_text,
            key=f"price_override_{asset}"  # Unique key to prevent conflicts
        )

        # Only consider it an override if it's different from current price
        if override_value != current_price and override_value > 0:
            price_overrides[asset] = override_value
    
    # Refresh button
    if st.sidebar.button("🔄 Refresh Data", type="primary"):
        st.cache_data.clear()
        st.rerun()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 Portfolio Overview")
        
        # Get portfolio data
        with st.spinner("Fetching portfolio data..."):
            df = get_portfolio_data(selected_assets, price_overrides)
        
        if df.empty:
            st.error("❌ No data available")
            return
        
        # Display the main table
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Amount": st.column_config.NumberColumn(format="%.8f"),
                "Cost €": st.column_config.NumberColumn(format="€%.2f"),
                "Value €": st.column_config.NumberColumn(format="€%.2f"),
                "Realised €": st.column_config.NumberColumn(format="€%.2f"),
                "Unrealised €": st.column_config.NumberColumn(format="€%.2f"),
                "Total Return %": st.column_config.NumberColumn(format="%.2f%%"),
                "Current Price €": st.column_config.NumberColumn(format="€%.2f"),
            }
        )
        
        # Calculate and display totals
        totals = {
            "Total Cost": df["Cost €"].sum(),
            "Total Value": df["Value €"].sum(),
            "Total Realised": df["Realised €"].sum(),
            "Total Unrealised": df["Unrealised €"].sum(),
        }
        
        total_invested = df["Cost €"].sum() + abs(df["Realised €"].sum())
        total_return = ((totals["Total Value"] + totals["Total Realised"]) - total_invested) / total_invested * 100 if total_invested > 0 else 0
        
        st.subheader("💼 Portfolio Summary")
        
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            st.metric("Total Value", f"€{totals['Total Value']:.2f}")
        with col_b:
            st.metric("Total Cost", f"€{totals['Total Cost']:.2f}")
        with col_c:
            st.metric("Realised P&L", f"€{totals['Total Realised']:.2f}")
        with col_d:
            st.metric("Unrealised P&L", f"€{totals['Total Unrealised']:.2f}")
        
        st.metric("📈 Total Return", f"{total_return:.2f}%")
    
    with col2:
        st.subheader("📈 P&L Visualization")
        
        if not df.empty:
            create_pnl_chart(df)
            
            # Additional metrics
            st.subheader("🎯 Key Metrics")
            
            best_performer = df.loc[df["Total Return %"].idxmax()]
            worst_performer = df.loc[df["Total Return %"].idxmin()]
            
            st.success(f"🏆 Best: {best_performer['Asset']} ({best_performer['Total Return %']:.2f}%)")
            st.error(f"📉 Worst: {worst_performer['Asset']} ({worst_performer['Total Return %']:.2f}%)")
            
            # Show price overrides if any
            if price_overrides:
                st.subheader("⚙️ Active Overrides")
                for asset, price in price_overrides.items():
                    st.info(f"{asset}: €{price:.2f}")
    
    # Footer
    st.markdown("---")
    st.markdown("*Data refreshed every 5 minutes. Price overrides update immediately.*")
    st.markdown(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")


if __name__ == "__main__":
    main()
