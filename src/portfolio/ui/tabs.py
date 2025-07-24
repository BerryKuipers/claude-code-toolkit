#!/usr/bin/env python3
"""
Tab management for the crypto portfolio dashboard.
Clean, SOLID implementation of tab navigation and content rendering.
"""

from typing import Dict, List

import pandas as pd
import streamlit as st

from ..ai_explanations import format_currency
from ..chat.model_selector import render_model_selector
from ..chat.prompt_editor import PromptEditor
from ..ui.performance import PerformanceOptimizer


class TabManager:
    """
    Manages tab navigation and content rendering for the dashboard.
    Follows Single Responsibility Principle - only handles tab management.
    """

    def __init__(self):
        """Initialize the tab manager."""
        self.tab_names = ["💼 Portfolio", "📈 Analysis", "⚙️ Settings"]

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
        tab1, tab2, tab3 = st.tabs(self.tab_names)

        # Portfolio Tab (default with sticky chat at bottom)
        with tab1:
            PortfolioTab().render(df, price_overrides)

        # Analysis Tab
        with tab2:
            AnalysisTab().render(df)

        # Settings Tab
        with tab3:
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

        # Add explanation section
        self._render_explanation_section()

        # Portfolio visualizations
        self._render_portfolio_charts(df)

        # Active price overrides
        if price_overrides:
            self._render_active_overrides(price_overrides)

        # Sticky chat at bottom of Portfolio tab
        self._render_sticky_chat(df)

    def _render_portfolio_metrics(self, df: pd.DataFrame):
        """Render key portfolio metrics in a clean card layout."""
        if df.empty:
            return

        # Calculate key metrics
        total_value = df["Actual Value €"].sum()
        total_cost = df["Cost €"].sum()
        total_unrealized = df["Unrealised €"].sum()
        total_realized = df["Realised €"].sum()

        # Calculate return percentage - comprehensive formula including realized gains
        # total_invested = cost + absolute value of realized (to account for both gains and losses)
        total_invested = total_cost + abs(total_realized)
        total_return = (
            ((total_value + total_realized) - total_invested) / total_invested * 100
            if total_invested > 0
            else 0
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
        """Render the main portfolio table with profit/loss indicators."""
        with st.expander("📈 Detailed Portfolio", expanded=True):
            # Add profit/loss status column for visual indicators
            df_display = df.copy()

            # Create P&L Status column with sophisticated logic (restored from original)
            def get_profit_indicator(row):
                return_pct = row.get("Total Return %", 0)
                current_value = row.get("Actual Value €", 0)

                # For very small positions (< €1), show different indicators
                if current_value < 1.0:
                    if return_pct > 0:
                        return "🔸 Tiny Profit"  # Small position with profit
                    elif return_pct < 0:
                        return "🔹 Tiny Loss"  # Small position with loss
                    else:
                        return "⚪ Tiny Position"  # Small position break-even

                # For normal positions, use standard indicators
                if return_pct > 10:
                    return "🚀 Strong Profit"
                elif return_pct > 5:
                    return "📈 Good Profit"
                elif return_pct > 0:
                    return "🟢 Profit"
                elif return_pct == 0:
                    return "⚪ Break-even"
                elif return_pct > -5:
                    return "🔴 Loss"
                elif return_pct > -10:
                    return "📉 Bad Loss"
                else:
                    return "💥 Heavy Loss"

            if "Total Return %" in df_display.columns:
                df_display.insert(
                    1, "P&L Status", df_display.apply(get_profit_indicator, axis=1)
                )

            # Display the table with proper formatting and row selection
            selected_rows = st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                column_config={
                    "Asset": st.column_config.TextColumn("Asset", width="small"),
                    "P&L Status": st.column_config.TextColumn(
                        "P&L Status",
                        width="medium",
                        help="Visual profit/loss indicator",
                    ),
                    "FIFO Amount": st.column_config.NumberColumn(
                        "FIFO Amt",
                        format="%.6f",
                        width="small",
                        help="Amount calculated from trade history",
                    ),
                    "Actual Amount": st.column_config.NumberColumn(
                        "Actual Amt",
                        format="%.6f",
                        width="small",
                        help="Your real current balance on Bitvavo",
                    ),
                    "Cost €": st.column_config.NumberColumn(
                        "Cost €",
                        format="€%.0f",
                        width="small",
                        help="Total amount invested (FIFO cost basis)",
                    ),
                    "FIFO Value €": st.column_config.NumberColumn(
                        "FIFO €",
                        format="€%.0f",
                        width="small",
                        help="Value based on FIFO calculation",
                    ),
                    "Actual Value €": st.column_config.NumberColumn(
                        "Actual €",
                        format="€%.0f",
                        width="small",
                        help="Value based on your real holdings",
                    ),
                    "Amount Diff": st.column_config.NumberColumn(
                        "Diff",
                        format="%.6f",
                        width="small",
                        help="Difference between FIFO and actual amounts",
                    ),
                    "Realised €": st.column_config.NumberColumn(
                        "Realised €",
                        format="€%.0f",
                        width="small",
                        help="Profit/loss from coins you've already sold",
                    ),
                    "Unrealised €": st.column_config.NumberColumn(
                        "Unrealised €",
                        format="€%.0f",
                        width="small",
                        help="Profit/loss if you sell NOW - Positive=Profit, Negative=Loss",
                    ),
                    "Total Return %": st.column_config.NumberColumn(
                        "Return % 📊",
                        format="%.1f%%",
                        width="small",
                        help="Overall performance percentage - 🟢 Green = Profit, 🔴 Red = Loss, 🟡 Yellow = Break-even",
                    ),
                    "Current Price €": st.column_config.TextColumn(
                        "Price €",
                        width="small",
                        help="Current market price per coin",
                    ),
                },
            )

            # Handle row selection for AI analysis
            self._handle_row_selection(selected_rows, df)

    def _render_explanation_section(self):
        """Render explanation of portfolio data columns."""
        with st.expander("ℹ️ Understanding Your Portfolio Data", expanded=False):
            st.markdown(
                """
            **Column Explanations:**

            - **P&L Status**: Visual indicator of your profit/loss status
                - 🟢 **Profit**: Significant gains (>€50)
                - 🔴 **Loss**: Significant losses (<-€50)
                - 🟡 **Small Profit**: Minor gains (€0-€50)
                - 🟠 **Small Loss**: Minor losses (€0--€50)
                - ⚪ **Break-even**: No significant gain/loss

            - **Cost €**: Total amount you invested (FIFO cost basis)
            - **Value €**: Current market value of your holdings
            - **Realised €**: Profit/loss from coins you've already sold
            - **Unrealised €**: Current profit/loss on holdings (if you sold now)
            - **Total Return %**: Overall performance including both realised and unrealised gains
            - **Price €**: Current market price per coin

            **Color Coding:**
            - 🟢 **Green numbers** = Profit/Gains
            - 🔴 **Red numbers** = Loss/Negative
            - ⚫ **Black numbers** = Neutral/Cost basis
            """
            )

    def _handle_row_selection(self, selected_rows, df: pd.DataFrame):
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
                # Import here to avoid circular imports
                from src.portfolio.ai_explanations import generate_coin_explanation

                explanation = generate_coin_explanation(selected_asset.to_dict())

                # Display the explanation in an info box
                st.info(f"💡 **{selected_asset['Asset']} Analysis**\n\n{explanation}")

            except Exception as e:
                st.error(f"Error generating AI explanation: {str(e)}")
        else:
            # Show instruction when no row is selected
            st.info(
                "💡 **Click on any row above to see a detailed AI analysis of that coin position**"
            )

    def _render_portfolio_charts(self, df: pd.DataFrame):
        """Render portfolio charts and visualizations."""
        from .charts import create_pnl_chart

        if not df.empty:
            st.markdown("### 📊 Portfolio Visualizations")
            create_pnl_chart(df)

    def _render_active_overrides(self, price_overrides: Dict[str, float]):
        """Render active price overrides."""
        st.subheader("⚙️ Active Price Overrides")
        for asset, price in price_overrides.items():
            st.info(f"{asset}: {format_currency(price)}")

    def _render_sticky_chat(self, df: pd.DataFrame):
        """Render sticky chat interface at bottom of portfolio page."""

        # Initialize chat state - CLOSED by default
        if "sticky_chat_open" not in st.session_state:
            st.session_state.sticky_chat_open = False

        # Render the sticky chat interface
        self._render_sticky_chat_interface(df)

    def _render_sticky_chat_interface(self, df: pd.DataFrame):
        """Render a simple working chat interface."""

        if st.session_state.sticky_chat_open:
            # Show chat interface at bottom of page
            st.markdown("---")

            # Chat header with close button
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown("### 💬 AI Portfolio Assistant")
            with col2:
                if st.button("✕", key="close_sticky_chat", help="Close Chat"):
                    st.session_state.sticky_chat_open = False
                    st.rerun()

            # Chat input
            user_input = st.text_input(
                "Ask about your portfolio",
                placeholder="Ask about your portfolio performance, holdings, or get analysis...",
                key="portfolio_chat_input",
            )

            # Ask button
            ask_button = st.button("Ask AI", key="portfolio_chat_ask", type="primary")

            # Process the question
            if ask_button and user_input:
                with st.spinner("🤖 Analyzing your portfolio..."):
                    try:
                        # Import here to avoid circular imports
                        from src.portfolio.chat.base_llm_client import LLMClientFactory
                        from src.portfolio.chat.function_handlers import (
                            PortfolioFunctionHandler,
                        )

                        # Initialize function handler with portfolio data
                        function_handler = PortfolioFunctionHandler(df)

                        # Get selected model from session state (configured in Settings tab)
                        if "selected_model" not in st.session_state:
                            selected_model = LLMClientFactory.get_default_model()
                        else:
                            selected_model = st.session_state.selected_model

                        # Get LLM client
                        llm_client = LLMClientFactory.create_client(selected_model)

                        # Generate response using function calling
                        from src.portfolio.chat.chat_interface import _get_ai_response

                        response = _get_ai_response(
                            user_input, llm_client, function_handler
                        )

                        # Display response
                        st.success("🤖 **AI Response:**")
                        st.markdown(response)

                        # Track cost if available
                        if hasattr(st.session_state, "cost_tracker"):
                            # Get model info for cost calculation
                            from src.portfolio.chat.base_llm_client import (
                                AVAILABLE_MODELS,
                            )

                            if selected_model in AVAILABLE_MODELS:
                                model_info = AVAILABLE_MODELS[selected_model]
                                prompt_tokens = int(
                                    len(user_input.split()) * 1.3
                                )  # Rough estimate
                                completion_tokens = int(
                                    len(response.split()) * 1.3
                                )  # Rough estimate
                                cost = (
                                    prompt_tokens / 1000
                                ) * model_info.cost_per_1k_input + (
                                    completion_tokens / 1000
                                ) * model_info.cost_per_1k_output

                                st.session_state.cost_tracker.track_usage(
                                    model_info.provider,
                                    model_info.model_id,
                                    prompt_tokens,
                                    completion_tokens,
                                    cost,
                                    "chat",
                                )

                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        st.info(
                            "💡 Make sure your API keys are configured in the Settings tab"
                        )

        else:
            # Show simple button to open chat
            st.markdown("---")
            st.markdown("### 💬 Need help with your portfolio?")
            if st.button(
                "Open AI Portfolio Assistant", key="open_sticky_chat", type="primary"
            ):
                st.session_state.sticky_chat_open = True
                st.rerun()


class AnalysisTab(BaseTab):
    """
    Analysis tab implementation.
    Handles detailed portfolio analysis and performance monitoring.
    """

    def render(self, df: pd.DataFrame):
        """Render the Analysis tab content."""
        # Remove duplicate header - the tab already shows "Analysis"

        if df.empty:
            st.warning("No portfolio data available for analysis")
            return

        # Portfolio Analytics
        self._render_portfolio_analytics(df)

        # Performance Monitor
        self._render_performance_monitor()

        # Analysis explanations
        self._render_analysis_explanations()

    def _render_portfolio_analytics(self, df: pd.DataFrame):
        """Render portfolio analytics and insights."""
        st.markdown("### 📊 Portfolio Analytics")

        # Basic analytics for now - can be enhanced later
        if not df.empty:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Asset Distribution**")
                if "Actual Value €" in df.columns:
                    asset_values = df.set_index("Asset")["Actual Value €"]
                    st.bar_chart(asset_values)

            with col2:
                st.markdown("**Performance Overview**")
                if "Unrealised €" in df.columns:
                    performance = df.set_index("Asset")["Unrealised €"]
                    st.bar_chart(performance)

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

        # Add a prominent welcome message
        st.markdown(
            """
        <div style="background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
                   color: white; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
            <h3 style="margin: 0; color: white;">💬 Welcome to your AI Portfolio Assistant!</h3>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">
                Ask questions about your portfolio, get insights, or request analysis.
                I can help you understand your holdings, performance, and trends.
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Info about sticky chat
        st.info(
            "💡 **The AI chat is now available at the bottom of every page!** "
            "You can ask questions about your portfolio while viewing any tab. "
            "Look for the expandable 'AI Portfolio Assistant' section below."
        )

        # Show some helpful information about the AI assistant
        st.markdown("### 🤖 About Your AI Assistant")
        st.markdown(
            """
            Your AI assistant can help you with:

            **📊 Portfolio Analysis:**
            - Total portfolio value and performance
            - Asset allocation and diversification
            - Profit/loss analysis for individual coins

            **🔍 Detailed Insights:**
            - Explain specific positions and their performance
            - Analyze transfer activity and discrepancies
            - Provide recommendations based on your data

            **💡 Smart Queries:**
            - "What's my best performing asset?"
            - "Explain my Bitcoin position"
            - "Which coins are losing money?"
            - "Show me my portfolio allocation"
            """
        )

        # Show current model info
        st.markdown("### ⚙️ AI Model Information")
        st.markdown(
            """
            The assistant uses advanced AI models to analyze your portfolio:
            - **GPT-4**: For complex analysis and detailed explanations
            - **Claude**: For large context and comprehensive insights
            - **Function Calling**: Direct access to your portfolio data
            """
        )

        st.markdown("---")
        st.markdown(
            "**💬 Start chatting by expanding the AI assistant section at the bottom of any page!**"
        )


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

        # AI Model Selection section
        self._render_ai_model_settings()

        # AI Prompt Configuration section
        self._render_ai_prompt_settings()

        # Price overrides section
        self._render_price_overrides_info(price_overrides)

        # Additional settings can be added here
        self._render_additional_settings()

    def _render_ai_model_settings(self):
        """Render AI model selection and configuration."""
        st.markdown("### 🤖 AI Model Configuration")
        st.markdown(
            "*Configure which AI model to use for portfolio analysis and chat.*"
        )

        # Render the model selector (moved from chat interface)
        render_model_selector()

    def _render_ai_prompt_settings(self):
        """Render AI prompt and behavior configuration."""
        st.markdown("### 🎭 AI Behavior & Prompts")
        st.markdown("*Customize how the AI assistant responds and behaves.*")

        # Initialize prompt editor in session state if not exists
        if "prompt_editor" not in st.session_state:
            st.session_state.prompt_editor = PromptEditor()

        # Render the prompt editor (moved from chat interface)
        st.session_state.prompt_editor.render_prompt_editor()

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
