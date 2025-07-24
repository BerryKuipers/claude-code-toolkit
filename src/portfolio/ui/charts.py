#!/usr/bin/env python3
"""
Chart utilities for the crypto portfolio dashboard.
Provides visualization functions to avoid circular imports.
"""

import pandas as pd
import streamlit as st


def create_pnl_chart(df: pd.DataFrame) -> None:
    """Create enhanced P&L visualizations."""
    if df.empty:
        return

    # Create tabs for different visualizations
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "📊 P&L Overview",
            "🥧 Portfolio Allocation",
            "📈 Top Performers",
            "🔄 Transfer Analysis",
        ]
    )

    with tab1:
        st.markdown("**💰 Profit & Loss by Asset**")
        st.markdown("*Green = Profit if sold now | Red = Loss if sold now*")

        # Filter out assets with zero unrealized P&L for cleaner chart
        chart_df = df[df["Unrealised €"] != 0].copy()
        if not chart_df.empty:
            # Sort by unrealized P&L for better visualization
            chart_df = chart_df.sort_values("Unrealised €", ascending=True)

            # Create the chart data
            chart_data = pd.DataFrame(
                {
                    "Asset": chart_df["Asset"],
                    "Unrealised P&L €": chart_df["Unrealised €"],
                    "Realised P&L €": chart_df["Realised €"],
                }
            )

            st.bar_chart(chart_data.set_index("Asset"), height=400)
        else:
            st.info("No unrealized P&L to display")

    with tab2:
        st.markdown("**🥧 Portfolio Allocation by Value**")

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
                    height=500,
                )
                fig.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig, use_container_width=True)
            except ImportError:
                # Fallback to simple bar chart if plotly not available
                st.bar_chart(
                    portfolio_df.set_index("Asset")["Actual Value €"], height=400
                )
        else:
            st.info("No portfolio data to display")

    with tab3:
        st.markdown("**📈 Top Performers by Return %**")

        # Show top and bottom performers
        performers_df = df[df["Total Return %"] != 0].copy()
        if not performers_df.empty:
            # Sort by return percentage
            performers_df = performers_df.sort_values("Total Return %", ascending=False)

            # Show top 5 and bottom 5
            top_performers = performers_df.head(5)
            bottom_performers = performers_df.tail(5)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**🏆 Top Performers**")
                for _, row in top_performers.iterrows():
                    return_pct = row["Total Return %"]
                    color = "🟢" if return_pct > 0 else "🔴"
                    st.markdown(
                        f"{color} **{row['Asset']}**: {return_pct:.2f}% "
                        f"(€{row['Unrealised €']:.2f})"
                    )

            with col2:
                st.markdown("**📉 Bottom Performers**")
                for _, row in bottom_performers.iterrows():
                    return_pct = row["Total Return %"]
                    color = "🟢" if return_pct > 0 else "🔴"
                    st.markdown(
                        f"{color} **{row['Asset']}**: {return_pct:.2f}% "
                        f"(€{row['Unrealised €']:.2f})"
                    )

            # Performance distribution chart
            st.markdown("**📊 Return Distribution**")
            performance_chart = pd.DataFrame(
                {
                    "Asset": performers_df["Asset"],
                    "Return %": performers_df["Total Return %"],
                }
            )
            st.bar_chart(performance_chart.set_index("Asset"), height=300)
        else:
            st.info("No performance data to display")

    with tab4:
        st.markdown("**🔄 Transfer Activity Analysis**")

        # Transfer summary metrics
        total_deposits = df["Total Deposits"].sum()
        total_withdrawals = df["Total Withdrawals"].sum()
        net_transfers = df["Net Transfers"].sum()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Deposits", f"€{total_deposits:.2f}")
        with col2:
            st.metric("Total Withdrawals", f"€{total_withdrawals:.2f}")
        with col3:
            st.metric("Net Transfers", f"€{net_transfers:.2f}")

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
                    color_discrete_map={
                        "Total Deposits": "green",
                        "Total Withdrawals": "red",
                    },
                    height=400,
                )
                fig_transfers.update_layout(
                    xaxis_title="Asset",
                    yaxis_title="Amount",
                )
                st.plotly_chart(fig_transfers, use_container_width=True)
            except ImportError:
                # Fallback without plotly
                st.bar_chart(
                    transfer_data.set_index("Asset")[
                        ["Total Deposits", "Total Withdrawals"]
                    ]
                )
        else:
            st.info("No transfer activity detected for visualization.")

        # Discrepancy explanation chart
        st.markdown("**🔍 Discrepancy Explanation Breakdown**")
        # Safely handle Amount Diff column that might contain strings
        discrepancy_data = df[
            abs(pd.to_numeric(df["Amount Diff"], errors="coerce").fillna(0)) > 0.000001
        ].copy()
        if not discrepancy_data.empty:
            try:
                import plotly.express as px

                # Prepare data for stacked bar chart
                explanation_cols = [
                    "Transfer Explained",
                    "Rewards Explained",
                    "Unexplained Diff",
                ]
                fig_discrepancy = px.bar(
                    discrepancy_data,
                    x="Asset",
                    y=explanation_cols,
                    title="How Discrepancies Are Explained",
                    barmode="stack",
                    color_discrete_map={
                        "Transfer Explained": "lightblue",
                        "Rewards Explained": "lightgreen",
                        "Unexplained Diff": "orange",
                    },
                    height=400,
                )
                fig_discrepancy.update_layout(
                    xaxis_title="Asset",
                    yaxis_title="Amount Difference",
                    legend_title="Explanation Type",
                )
                st.plotly_chart(fig_discrepancy, use_container_width=True)
            except ImportError:
                # Fallback without plotly
                st.bar_chart(
                    discrepancy_data.set_index("Asset")[explanation_cols], height=300
                )
        else:
            st.info("No significant discrepancies to explain.")


def create_simple_pnl_chart(df: pd.DataFrame) -> None:
    """Create a simple P&L visualization for basic use cases."""
    if df.empty:
        return

    # Create a summary chart showing realized vs unrealized P&L
    chart_data = pd.DataFrame(
        {
            "Asset": df["Asset"],
            "Realised P&L €": df["Realised €"],
            "Unrealised P&L €": df["Unrealised €"],
        }
    )

    st.bar_chart(chart_data.set_index("Asset"))
