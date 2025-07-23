#!/usr/bin/env python3
"""
Tab management for the crypto portfolio dashboard.
Clean, SOLID implementation of tab navigation and content rendering.
"""

from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st

from ..ai_explanations import format_currency, generate_coin_explanation
from ..chat import render_chat_interface
from ..ui import add_section_anchor
from ..ui.performance import PerformanceOptimizer


class TabManager:
    """
    Manages tab navigation and content rendering for the dashboard.
    Follows Single Responsibility Principle - only handles tab management.
    """

    def __init__(self):
        """Initialize the tab manager."""
        self.tab_names = ["💼 Portfolio", "📈 Analysis", "🤖 Chat", "⚙️ Settings"]

    def render_tabs(
        self,
        df: pd.DataFrame,
        selected_assets: List[str],
        price_overrides: Dict[str, float],
        current_prices: Dict[str, float],
    ):
        """
        Render the main tab navigation structure.

        Args:
            df: Portfolio dataframe
            selected_assets: List of selected asset symbols
            price_overrides: Dictionary of price overrides
            current_prices: Dictionary of current prices
        """
        # Create main tab navigation structure
        tab1, tab2, tab3, tab4 = st.tabs(self.tab_names)

        # Portfolio Tab
        with tab1:
            PortfolioTab().render(df, price_overrides)

        # Analysis Tab
        with tab2:
            AnalysisTab().render(df)

        # Chat Tab
        with tab3:
            ChatTab().render(df)

        # Settings Tab
        with tab4:
            SettingsTab().render(selected_assets, current_prices, price_overrides)


class BaseTab:
    """
    Base class for all tabs. Implements common functionality.
    Follows Open/Closed Principle - open for extension, closed for modification.
    """

    def render(self, *args, **kwargs):
        """Render the tab content. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement render method")

    def _render_section_header(self, title: str, icon: str = ""):
        """Render a consistent section header."""
        if icon:
            st.subheader(f"{icon} {title}")
        else:
            st.subheader(title)


class PortfolioTab(BaseTab):
    """
    Portfolio tab implementation.
    Handles portfolio overview, metrics, and visualizations.
    """

    def render(self, df: pd.DataFrame, price_overrides: Dict[str, float]):
        """Render the Portfolio tab content."""
        self._render_section_header("Portfolio Overview", "📊")

        if df.empty:
            st.warning("No portfolio data available")
            return

        # Portfolio summary metrics
        self._render_portfolio_metrics(df)

        # Portfolio table
        self._render_portfolio_table(df)

        # Portfolio visualizations
        self._render_portfolio_charts(df)

        # Active price overrides
        if price_overrides:
            self._render_active_overrides(price_overrides)

    def _render_portfolio_metrics(self, df: pd.DataFrame):
        """Render key portfolio metrics in a clean card layout."""
        if df.empty:
            return

        # Calculate key metrics
        total_value = df["Actual Value €"].sum()
        total_cost = df["Cost €"].sum()
        total_unrealized = df["Unrealised €"].sum()
        total_realized = df["Realised €"].sum()

        # Calculate return percentage
        total_return = (
            ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0
        )

        # Display metrics in columns
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Total Value", f"€{total_value:.0f}")
        with col2:
            st.metric("Total Cost", f"€{total_cost:.0f}")
        with col3:
            st.metric("Realized P&L", f"€{total_realized:.0f}")
        with col4:
            st.metric("Unrealized P&L", f"€{total_unrealized:.0f}")
        with col5:
            st.metric("Total Return", f"{total_return:.1f}%")

    def _render_portfolio_table(self, df: pd.DataFrame):
        """Render the main portfolio table."""
        # For now, render a simplified table
        # This will be enhanced in the next iteration
        with st.expander("📈 Detailed Portfolio", expanded=True):
            st.dataframe(df, use_container_width=True)

    def _render_portfolio_charts(self, df: pd.DataFrame):
        """Render portfolio charts and visualizations."""
        # Import here to avoid circular imports
        # Note: create_pnl_chart will be imported from dashboard module
        # For now, we'll implement a placeholder
        if not df.empty:
            st.markdown("### 📊 Portfolio Visualizations")
            st.info("Charts will be implemented in the next iteration")

    def _render_active_overrides(self, price_overrides: Dict[str, float]):
        """Render active price overrides."""
        st.subheader("⚙️ Active Price Overrides")
        for asset, price in price_overrides.items():
            st.info(f"{asset}: {format_currency(price)}")


class AnalysisTab(BaseTab):
    """
    Analysis tab implementation.
    Handles detailed portfolio analysis and performance monitoring.
    """

    def render(self, df: pd.DataFrame):
        """Render the Analysis tab content."""
        self._render_section_header("Portfolio Analysis", "📊")

        # Performance Monitor
        self._render_performance_monitor()

        # Analysis explanations
        self._render_analysis_explanations()

    def _render_performance_monitor(self):
        """Render the performance monitoring section."""
        st.markdown("### 🔍 Performance Monitor")
        PerformanceOptimizer.render_performance_monitor()

    def _render_analysis_explanations(self):
        """Render analysis explanations and help text."""
        with st.expander("ℹ️ What do these metrics mean?"):
            st.markdown(
                """
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
            """
            )


class ChatTab(BaseTab):
    """
    Chat tab implementation.
    Handles AI chat interface for portfolio questions.
    """

    def render(self, df: pd.DataFrame):
        """Render the Chat tab content."""
        self._render_section_header("AI Portfolio Assistant", "🤖")

        # AI Chat Interface
        render_chat_interface(df)


class SettingsTab(BaseTab):
    """
    Settings tab implementation.
    Handles configuration and price overrides.
    """

    def render(
        self,
        selected_assets: List[str],
        current_prices: Dict[str, float],
        price_overrides: Dict[str, float],
    ):
        """Render the Settings tab content."""
        self._render_section_header("Configuration & Settings", "⚙️")

        # Price overrides section
        self._render_price_overrides_info(price_overrides)

        # Additional settings can be added here
        self._render_additional_settings()

    def _render_price_overrides_info(self, price_overrides: Dict[str, float]):
        """Render information about price overrides."""
        st.markdown("### 💰 Price Overrides")
        st.markdown(
            "*Price overrides are managed in the sidebar for easy access while viewing data.*"
        )

        if price_overrides:
            st.markdown("**Currently Active Overrides:**")
            for asset, price in price_overrides.items():
                st.info(f"{asset}: {format_currency(price)}")
        else:
            st.info(
                "No price overrides currently active. Use the sidebar to set overrides for what-if scenarios."
            )

    def _render_additional_settings(self):
        """Render additional settings and configuration options."""
        st.markdown("### 🔧 Additional Settings")
        st.info(
            "Additional configuration options will be added here in future updates."
        )
