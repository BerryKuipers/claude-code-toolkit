"""Sticky navigation bar for the crypto portfolio dashboard.

This module provides a sticky navigation bar that allows users to quickly
jump between different sections of the dashboard.
"""

from typing import Dict, List, Optional

import streamlit as st


def render_sticky_nav():
    """Render simplified navigation bar at the top of the page."""

    # Sticky navigation CSS
    st.markdown(
        """
    <style>
    .sticky-nav {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 999;
        background: linear-gradient(90deg, #1f2937 0%, #374151 100%);
        padding: 12px 20px;
        color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .nav-content {
        max-width: 1200px;
        margin: 0 auto;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .main-content {
        margin-top: 80px;
    }

    /* Override Streamlit's default styles */
    .stApp > header {
        background-color: transparent;
    }

    .stApp {
        margin-top: 0;
    }

    .nav-brand {
        font-size: 20px;
        font-weight: bold;
        color: #f9fafb;
    }

    .nav-status {
        font-size: 12px;
        color: #d1d5db;
        display: flex;
        gap: 15px;
        align-items: center;
    }

    .nav-status span {
        white-space: nowrap;
    }

    .status-item {
        display: flex;
        align-items: center;
        gap: 5px;
    }

    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #10b981;
    }

    .status-dot.warning {
        background: #f59e0b;
    }

    .status-dot.error {
        background: #ef4444;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Get status indicators
    portfolio_status = _get_portfolio_status()
    ai_status = _get_ai_status()
    cost_status = _get_cost_status()

    # Use Streamlit container for better compatibility
    try:
        with st.container():
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown("### 🚀 Crypto Insight Dashboard")

            with col2:
                # Status indicators with error handling
                subcol1, subcol2, subcol3 = st.columns(3)

                with subcol1:
                    try:
                        status_color = (
                            "🟢"
                            if portfolio_status["class"] == ""
                            else (
                                "🟡" if portfolio_status["class"] == "warning" else "🔴"
                            )
                        )
                        st.caption(
                            f"{status_color} Portfolio: {portfolio_status['text']}"
                        )
                    except:
                        st.caption("🟡 Portfolio: Loading...")

                with subcol2:
                    try:
                        ai_color = (
                            "🟢"
                            if ai_status["class"] == ""
                            else "🟡" if ai_status["class"] == "warning" else "🔴"
                        )
                        st.caption(f"{ai_color} AI: {ai_status['text']}")
                    except:
                        st.caption("🟡 AI: Loading...")

                with subcol3:
                    try:
                        st.caption(f"💰 Cost: {cost_status['text']}")
                    except:
                        st.caption("💰 Cost: $0.00")

        st.markdown("---")
    except Exception as e:
        # Fallback simple header
        st.markdown("### 🚀 Crypto Insight Dashboard")
        st.markdown("---")


def add_section_anchor(section_id: str, title: str):
    """Add a simple section header.

    Args:
        section_id: ID for the section (for future navigation)
        title: Display title for the section
    """
    st.markdown(f"## {title}")


def _get_portfolio_status() -> Dict[str, str]:
    """Get portfolio status indicator."""
    try:
        # Check if we have portfolio data
        if (
            hasattr(st.session_state, "portfolio_data")
            and not st.session_state.portfolio_data.empty
        ):
            return {"class": "", "text": "Live"}
        else:
            return {"class": "warning", "text": "Loading"}
    except:
        return {"class": "error", "text": "Error"}


def _get_ai_status() -> Dict[str, str]:
    """Get AI status indicator."""
    try:
        # Check the selected model from session state
        selected_model = st.session_state.get(
            "selected_model", "claude-3-5-sonnet-20241022"
        )

        # Determine provider from model name
        if "gpt" in selected_model.lower() or "openai" in selected_model.lower():
            display_name = "OpenAI"
        elif (
            "claude" in selected_model.lower() or "anthropic" in selected_model.lower()
        ):
            display_name = "Claude"
        else:
            display_name = "AI"

        return {"class": "", "text": display_name}
    except:
        return {"class": "error", "text": "Error"}


def _get_cost_status() -> Dict[str, str]:
    """Get cost status indicator."""
    try:
        # Get cost from the cost tracker
        if "cost_tracker" in st.session_state:
            session_stats = st.session_state.cost_tracker.get_session_stats()
            total_cost = session_stats.get("total_cost_usd", 0.0)
            return {"text": f"${total_cost:.3f}"}
        else:
            return {"text": "$0.000"}
    except Exception as e:
        return {"text": "N/A"}


def render_quick_actions():
    """Render simple navigation links using HTML anchors."""
    # Use HTML links that scroll to sections instead of buttons
    st.markdown(
        """
    <div style="display: flex; gap: 20px; margin: 10px 0; justify-content: center;">
        <a href="#portfolio-overview" style="
            text-decoration: none;
            background: linear-gradient(90deg, #1f2937 0%, #374151 100%);
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
            border: 1px solid #4b5563;
            font-weight: 500;
            transition: all 0.2s;
        " onmouseover="this.style.background='linear-gradient(90deg, #374151 0%, #4b5563 100%)'"
           onmouseout="this.style.background='linear-gradient(90deg, #1f2937 0%, #374151 100%)'">
            📊 Portfolio
        </a>
        <a href="#ltc-analysis" style="
            text-decoration: none;
            background: linear-gradient(90deg, #1f2937 0%, #374151 100%);
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
            border: 1px solid #4b5563;
            font-weight: 500;
            transition: all 0.2s;
        " onmouseover="this.style.background='linear-gradient(90deg, #374151 0%, #4b5563 100%)'"
           onmouseout="this.style.background='linear-gradient(90deg, #1f2937 0%, #374151 100%)'">
            📈 Analysis
        </a>
        <a href="#ai-chat" style="
            text-decoration: none;
            background: linear-gradient(90deg, #1f2937 0%, #374151 100%);
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
            border: 1px solid #4b5563;
            font-weight: 500;
            transition: all 0.2s;
        " onmouseover="this.style.background='linear-gradient(90deg, #374151 0%, #4b5563 100%)'"
           onmouseout="this.style.background='linear-gradient(90deg, #1f2937 0%, #374151 100%)'">
            🤖 AI Chat
        </a>
        <a href="#" onclick="document.querySelector('.stSidebar').style.display = document.querySelector('.stSidebar').style.display === 'none' ? 'block' : 'none'; return false;" style="
            text-decoration: none;
            background: linear-gradient(90deg, #1f2937 0%, #374151 100%);
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
            border: 1px solid #4b5563;
            font-weight: 500;
            transition: all 0.2s;
        " onmouseover="this.style.background='linear-gradient(90deg, #374151 0%, #4b5563 100%)'"
           onmouseout="this.style.background='linear-gradient(90deg, #1f2937 0%, #374151 100%)'">
            ⚙️ Settings
        </a>
    </div>
    """,
        unsafe_allow_html=True,
    )
