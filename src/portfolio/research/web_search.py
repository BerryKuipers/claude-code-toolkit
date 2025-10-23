"""Web search utilities for cryptocurrency research using Perplexity AI."""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class CryptoWebSearcher:
    """Utility class for performing web searches related to cryptocurrency research."""

    def __init__(self):
        """Initialize the web searcher with API configuration."""
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        self.model = os.getenv("PERPLEXITY_MODEL", "sonar-pro")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "4000"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.2"))
        self.base_url = "https://api.perplexity.ai/chat/completions"

        if not self.api_key:
            logger.warning(
                "PERPLEXITY_API_KEY not found - web search functionality will be limited"
            )

    def search_crypto_news(self, query: str, focus: str = "general") -> Dict[str, Any]:
        """Search for cryptocurrency news and analysis.

        Args:
            query: Search query
            focus: Focus area (general, technical, fundamental, market, news)

        Returns:
            Dictionary with search results in structured format
        """
        if not self.api_key:
            return {
                "error": "Perplexity API key not configured",
                "suggestion": "Add PERPLEXITY_API_KEY to your .env file to enable web search",
            }

        try:
            enhanced_query = self._enhance_query_by_focus(query, focus)

            response_data = self._make_api_request(enhanced_query)

            if "error" in response_data:
                return response_data

            return {
                "query": query,
                "focus": focus,
                "enhanced_query": enhanced_query,
                "results": response_data["content"],
                "source": "Perplexity AI",
                "timestamp": datetime.now().isoformat(),
                "tokens_used": response_data.get("usage", {}).get("total_tokens", 0),
            }

        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return {"error": f"Web search failed: {str(e)}"}

    def search_investment_opportunities(
        self, current_holdings: list, risk_level: str = "medium"
    ) -> Dict[str, Any]:
        """Search for investment opportunities based on current holdings.

        Args:
            current_holdings: List of currently held assets
            risk_level: Risk tolerance (low, medium, high)

        Returns:
            Dictionary with investment opportunity analysis
        """
        holdings_str = (
            ", ".join(current_holdings) if current_holdings else "no current holdings"
        )

        query = f"""
        Investment opportunities in cryptocurrency for someone who currently holds: {holdings_str}.
        Risk tolerance: {risk_level}.
        Focus on:
        1. Diversification opportunities
        2. Emerging projects with strong fundamentals
        3. Market trends and sectors showing growth
        4. Risk-adjusted recommendations
        """

        return self.search_crypto_news(query, "investment")

    def search_market_analysis(
        self, assets: list, timeframe: str = "30d"
    ) -> Dict[str, Any]:
        """Search for market analysis of specific assets.

        Args:
            assets: List of asset symbols to analyze
            timeframe: Analysis timeframe

        Returns:
            Dictionary with market analysis results
        """
        assets_str = ", ".join(assets) if assets else "cryptocurrency market"

        query = f"""
        Market analysis for {assets_str} over the last {timeframe}.
        Include:
        1. Price performance and trends
        2. Technical indicators and signals
        3. Fundamental developments
        4. Market sentiment and news impact
        5. Future outlook and predictions
        """

        return self.search_crypto_news(query, "technical")

    def _enhance_query_by_focus(self, query: str, focus: str) -> str:
        """Enhance the search query based on focus area.

        Args:
            query: Original query
            focus: Focus area

        Returns:
            Enhanced query string
        """
        focus_prompts = {
            "general": f"Latest cryptocurrency news and information about: {query}",
            "technical": f"Technical analysis, price charts, and trading signals for: {query}",
            "fundamental": f"Fundamental analysis, project developments, and long-term outlook for: {query}",
            "market": f"Market trends, sentiment, and broader market impact related to: {query}",
            "news": f"Recent news, announcements, and developments about: {query}",
            "investment": f"Investment analysis, opportunities, and recommendations for: {query}",
            "risk": f"Risk analysis, volatility assessment, and risk management for: {query}",
        }

        return focus_prompts.get(focus, query)

    def _make_api_request(self, query: str) -> Dict[str, Any]:
        """Make API request to Perplexity.

        Args:
            query: Search query

        Returns:
            API response data
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a cryptocurrency research assistant. Provide accurate, up-to-date information with sources. Format your response as structured analysis with clear sections.",
                },
                {"role": "user", "content": query},
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        try:
            response = requests.post(
                self.base_url, headers=headers, json=data, timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "content": result["choices"][0]["message"]["content"],
                    "usage": result.get("usage", {}),
                }
            else:
                return {
                    "error": f"Perplexity API error: {response.status_code} - {response.text}"
                }

        except requests.exceptions.Timeout:
            return {
                "error": "Request timeout - Perplexity API took too long to respond"
            }
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}

    def is_available(self) -> bool:
        """Check if web search functionality is available.

        Returns:
            True if API key is configured
        """
        return bool(self.api_key)
