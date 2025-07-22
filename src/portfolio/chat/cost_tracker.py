"""LLM cost tracking and monitoring system.

This module tracks token usage and costs across different LLM providers
to help users understand their AI usage expenses.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import streamlit as st

from .base_llm_client import AVAILABLE_MODELS, LLMProvider

logger = logging.getLogger(__name__)


class CostTracker:
    """Tracks LLM usage costs and token consumption."""

    def __init__(self):
        """Initialize cost tracker."""
        self.session_costs = []
        self.total_session_cost = 0.0
        self.total_session_tokens = 0
        self.query_count = 0

    def track_usage(
        self,
        provider: LLMProvider,
        model_id: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float,
        query_type: str = "chat",
    ):
        """Track a single LLM usage event.

        Args:
            provider: LLM provider used
            model_id: Model identifier
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            cost: Cost in USD for this query
            query_type: Type of query (chat, function_call, etc.)
        """
        usage_event = {
            "timestamp": datetime.now(),
            "provider": provider.value,
            "model_id": model_id,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "cost_usd": cost,
            "query_type": query_type,
        }

        self.session_costs.append(usage_event)
        self.total_session_cost += cost
        self.total_session_tokens += prompt_tokens + completion_tokens
        self.query_count += 1

        # Store in session state for persistence
        if "llm_cost_history" not in st.session_state:
            st.session_state.llm_cost_history = []

        st.session_state.llm_cost_history.append(usage_event)

        # Update session totals
        st.session_state.total_llm_cost = (
            getattr(st.session_state, "total_llm_cost", 0.0) + cost
        )
        st.session_state.total_llm_tokens = (
            getattr(st.session_state, "total_llm_tokens", 0)
            + prompt_tokens
            + completion_tokens
        )
        st.session_state.total_llm_queries = (
            getattr(st.session_state, "total_llm_queries", 0) + 1
        )

        logger.info(
            f"LLM usage tracked: {provider.value} {model_id} - {prompt_tokens}+{completion_tokens} tokens, ${cost:.4f}"
        )

    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics."""
        if not self.session_costs:
            return {
                "total_cost_usd": 0.0,
                "total_tokens": 0,
                "query_count": 0,
                "avg_cost_per_query": 0.0,
                "avg_tokens_per_query": 0.0,
                "providers_used": [],
                "models_used": [],
            }

        providers_used = list(set(event["provider"] for event in self.session_costs))
        models_used = list(set(event["model_id"] for event in self.session_costs))

        return {
            "total_cost_usd": self.total_session_cost,
            "total_tokens": self.total_session_tokens,
            "query_count": self.query_count,
            "avg_cost_per_query": (
                self.total_session_cost / self.query_count
                if self.query_count > 0
                else 0.0
            ),
            "avg_tokens_per_query": (
                self.total_session_tokens / self.query_count
                if self.query_count > 0
                else 0.0
            ),
            "providers_used": providers_used,
            "models_used": models_used,
        }

    def get_total_stats(self) -> Dict[str, Any]:
        """Get total statistics from session state."""
        return {
            "total_cost_usd": getattr(st.session_state, "total_llm_cost", 0.0),
            "total_tokens": getattr(st.session_state, "total_llm_tokens", 0),
            "total_queries": getattr(st.session_state, "total_llm_queries", 0),
            "avg_cost_per_query": (
                getattr(st.session_state, "total_llm_cost", 0.0)
                / getattr(st.session_state, "total_llm_queries", 1)
            ),
            "avg_tokens_per_query": (
                getattr(st.session_state, "total_llm_tokens", 0)
                / getattr(st.session_state, "total_llm_queries", 1)
            ),
        }

    def get_cost_breakdown_by_provider(self) -> Dict[str, Dict[str, Any]]:
        """Get cost breakdown by provider."""
        breakdown = {}

        history = getattr(st.session_state, "llm_cost_history", [])

        for event in history:
            provider = event["provider"]
            if provider not in breakdown:
                breakdown[provider] = {
                    "total_cost": 0.0,
                    "total_tokens": 0,
                    "query_count": 0,
                    "models_used": set(),
                }

            breakdown[provider]["total_cost"] += event["cost_usd"]
            breakdown[provider]["total_tokens"] += event["total_tokens"]
            breakdown[provider]["query_count"] += 1
            breakdown[provider]["models_used"].add(event["model_id"])

        # Convert sets to lists for JSON serialization
        for provider_data in breakdown.values():
            provider_data["models_used"] = list(provider_data["models_used"])

        return breakdown

    def get_recent_usage(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent usage within specified hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        history = getattr(st.session_state, "llm_cost_history", [])

        recent_usage = [event for event in history if event["timestamp"] > cutoff_time]

        return recent_usage

    def estimate_monthly_cost(self) -> float:
        """Estimate monthly cost based on recent usage patterns."""
        recent_24h = self.get_recent_usage(24)

        if not recent_24h:
            return 0.0

        daily_cost = sum(event["cost_usd"] for event in recent_24h)
        estimated_monthly = daily_cost * 30

        return estimated_monthly

    def reset_session_stats(self):
        """Reset current session statistics."""
        self.session_costs = []
        self.total_session_cost = 0.0
        self.total_session_tokens = 0
        self.query_count = 0

    def clear_all_history(self):
        """Clear all cost tracking history."""
        self.reset_session_stats()

        # Clear session state
        if "llm_cost_history" in st.session_state:
            del st.session_state.llm_cost_history
        if "total_llm_cost" in st.session_state:
            del st.session_state.total_llm_cost
        if "total_llm_tokens" in st.session_state:
            del st.session_state.total_llm_tokens
        if "total_llm_queries" in st.session_state:
            del st.session_state.total_llm_queries


def render_cost_footer():
    """Render sticky footer with cost information."""
    if "cost_tracker" not in st.session_state:
        st.session_state.cost_tracker = CostTracker()

    tracker = st.session_state.cost_tracker
    session_stats = tracker.get_session_stats()
    total_stats = tracker.get_total_stats()

    # Create sticky footer using custom CSS
    st.markdown(
        """
    <style>
    .cost-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: rgba(240, 242, 246, 0.95);
        border-top: 1px solid #e0e0e0;
        padding: 8px 16px;
        font-size: 12px;
        z-index: 999;
        backdrop-filter: blur(10px);
    }
    .cost-metric {
        display: inline-block;
        margin-right: 20px;
        color: #666;
    }
    .cost-value {
        font-weight: bold;
        color: #333;
    }
    .cost-warning {
        color: #ff6b6b;
    }
    .cost-good {
        color: #51cf66;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Determine cost status
    session_cost = session_stats["total_cost_usd"]
    total_cost = total_stats["total_cost_usd"]

    cost_status_class = "cost-good"
    if total_cost > 5.0:  # Warning if total cost > $5
        cost_status_class = "cost-warning"
    elif total_cost > 1.0:  # Caution if total cost > $1
        cost_status_class = "cost-value"

    # Format the footer content
    footer_html = f"""
    <div class="cost-footer">
        <span class="cost-metric">Session: <span class="cost-value">${session_cost:.4f}</span> ({session_stats["query_count"]} queries)</span>
        <span class="cost-metric">Total: <span class="{cost_status_class}">${total_cost:.4f}</span> ({total_stats["total_queries"]} queries)</span>
        <span class="cost-metric">Tokens: <span class="cost-value">{total_stats["total_tokens"]:,}</span></span>
        <span class="cost-metric">Avg/Query: <span class="cost-value">${total_stats["avg_cost_per_query"]:.4f}</span></span>
        <span class="cost-metric">Est. Monthly: <span class="cost-value">${tracker.estimate_monthly_cost():.2f}</span></span>
    </div>
    """

    st.markdown(footer_html, unsafe_allow_html=True)


def render_detailed_cost_analysis():
    """Render detailed cost analysis in an expander."""
    if "cost_tracker" not in st.session_state:
        st.session_state.cost_tracker = CostTracker()

    tracker = st.session_state.cost_tracker

    with st.expander("💰 Detailed Cost Analysis"):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("Session Stats")
            session_stats = tracker.get_session_stats()
            st.metric("Session Cost", f"${session_stats['total_cost_usd']:.4f}")
            st.metric("Session Queries", session_stats["query_count"])
            st.metric("Session Tokens", f"{session_stats['total_tokens']:,}")

        with col2:
            st.subheader("Total Stats")
            total_stats = tracker.get_total_stats()
            st.metric("Total Cost", f"${total_stats['total_cost_usd']:.4f}")
            st.metric("Total Queries", total_stats["total_queries"])
            st.metric("Total Tokens", f"{total_stats['total_tokens']:,}")

        with col3:
            st.subheader("Projections")
            monthly_est = tracker.estimate_monthly_cost()
            st.metric("Est. Monthly", f"${monthly_est:.2f}")
            st.metric("Avg/Query", f"${total_stats['avg_cost_per_query']:.4f}")
            st.metric("Tokens/Query", f"{total_stats['avg_tokens_per_query']:.0f}")

        # Provider breakdown
        st.subheader("Cost by Provider")
        breakdown = tracker.get_cost_breakdown_by_provider()

        if breakdown:
            breakdown_data = []
            for provider, data in breakdown.items():
                breakdown_data.append(
                    {
                        "Provider": provider.title(),
                        "Cost": f"${data['total_cost']:.4f}",
                        "Queries": data["query_count"],
                        "Tokens": f"{data['total_tokens']:,}",
                        "Models": ", ".join(data["models_used"]),
                    }
                )

            st.table(breakdown_data)
        else:
            st.info("No usage data available yet.")

        # Reset buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Reset Session Stats"):
                tracker.reset_session_stats()
                st.success("Session stats reset!")
                st.rerun()

        with col2:
            if st.button("Clear All History", type="secondary"):
                if st.button("Confirm Clear All", type="secondary"):
                    tracker.clear_all_history()
                    st.success("All cost history cleared!")
                    st.rerun()
