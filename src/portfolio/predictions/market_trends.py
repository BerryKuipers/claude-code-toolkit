"""Market trend analysis for crypto assets.

This module provides comprehensive market trend analysis capabilities including
macro trends, sector rotation, market cycle analysis, and correlation patterns.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class MarketTrendAnalyzer:
    """Comprehensive market trend analysis for crypto portfolios."""

    def __init__(self):
        """Initialize market trend analyzer."""
        self.major_assets = ["BTC", "ETH", "ADA", "DOT", "LINK", "MATIC", "AVAX", "SOL"]
        self.sector_mapping = {
            "BTC": "store_of_value",
            "ETH": "smart_contracts",
            "ADA": "smart_contracts",
            "DOT": "interoperability",
            "LINK": "oracle",
            "MATIC": "layer2",
            "AVAX": "layer1",
            "SOL": "layer1",
            "UNI": "defi",
            "AAVE": "defi",
            "COMP": "defi",
            "MKR": "defi",
            "SUSHI": "defi",
        }

    def analyze_market_trends(self, portfolio_data: pd.DataFrame) -> Dict[str, Any]:
        """Comprehensive market trend analysis.

        Args:
            portfolio_data: Portfolio data for trend analysis

        Returns:
            Dictionary containing comprehensive market trend analysis
        """
        try:
            logger.info("🔍 Analyzing comprehensive market trends")

            # Filter to positioned assets only
            positioned_assets = portfolio_data[portfolio_data["Actual Amount"] > 0]

            if positioned_assets.empty:
                return {
                    "market_trend": "UNKNOWN",
                    "trend_strength": 0.0,
                    "message": "No positioned assets to analyze market trends",
                    "analysis_timestamp": datetime.now().isoformat(),
                }

            # Perform comprehensive analysis
            overall_trend = self._analyze_overall_trend(positioned_assets)
            sector_analysis = self._analyze_sector_trends(positioned_assets)
            market_cycle = self._analyze_market_cycle(positioned_assets)
            correlation_analysis = self._analyze_correlations(positioned_assets)
            momentum_analysis = self._analyze_momentum(positioned_assets)

            return {
                "market_trend": overall_trend["direction"],
                "trend_strength": overall_trend["strength"],
                "trend_confidence": overall_trend["confidence"],
                "market_cycle_phase": market_cycle["phase"],
                "cycle_confidence": market_cycle["confidence"],
                "sector_rotation": sector_analysis,
                "momentum_indicators": momentum_analysis,
                "correlation_insights": correlation_analysis,
                "key_insights": self._generate_key_insights(
                    overall_trend, sector_analysis, market_cycle
                ),
                "recommendations": self._generate_trend_recommendations(
                    overall_trend, sector_analysis
                ),
                "analysis_timestamp": datetime.now().isoformat(),
                "assets_analyzed": len(positioned_assets),
            }

        except Exception as e:
            logger.error(f"Error in market trend analysis: {e}")
            return {
                "market_trend": "ERROR",
                "trend_strength": 0.0,
                "error": str(e),
                "analysis_timestamp": datetime.now().isoformat(),
            }

    def _analyze_overall_trend(self, positioned_assets: pd.DataFrame) -> Dict[str, Any]:
        """Analyze overall market trend based on portfolio performance."""
        returns = positioned_assets["Total Return %"].dropna()

        if returns.empty:
            return {"direction": "UNKNOWN", "strength": 0.0, "confidence": 0.0}

        avg_return = returns.mean()
        positive_ratio = (returns > 0).sum() / len(returns)
        return_std = returns.std()

        # Determine trend direction
        if avg_return > 15 and positive_ratio > 0.7:
            direction = "STRONG_BULLISH"
            strength = min(avg_return / 50, 1.0)  # Normalize to 0-1
        elif avg_return > 5 and positive_ratio > 0.6:
            direction = "BULLISH"
            strength = min(avg_return / 30, 1.0)
        elif avg_return > -5 and positive_ratio > 0.4:
            direction = "NEUTRAL"
            strength = 0.5
        elif avg_return > -15 and positive_ratio > 0.3:
            direction = "BEARISH"
            strength = min(abs(avg_return) / 30, 1.0)
        else:
            direction = "STRONG_BEARISH"
            strength = min(abs(avg_return) / 50, 1.0)

        # Calculate confidence based on consistency
        confidence = max(0.1, 1.0 - (return_std / 100))  # Lower std = higher confidence

        return {
            "direction": direction,
            "strength": round(strength, 3),
            "confidence": round(confidence, 3),
            "avg_return_pct": round(avg_return, 2),
            "positive_ratio": round(positive_ratio, 3),
            "volatility": round(return_std, 2),
        }

    def _analyze_sector_trends(self, positioned_assets: pd.DataFrame) -> Dict[str, Any]:
        """Analyze sector rotation and trends."""
        sector_performance = {}

        for _, asset in positioned_assets.iterrows():
            asset_symbol = asset.get("Asset", "").upper()
            sector = self.sector_mapping.get(asset_symbol, "other")
            return_pct = asset.get("Total Return %", 0)

            if sector not in sector_performance:
                sector_performance[sector] = []
            sector_performance[sector].append(return_pct)

        # Calculate sector averages
        sector_analysis = {}
        for sector, returns in sector_performance.items():
            avg_return = np.mean(returns)
            sector_analysis[sector] = {
                "avg_return_pct": round(avg_return, 2),
                "asset_count": len(returns),
                "trend": (
                    "bullish"
                    if avg_return > 5
                    else "bearish" if avg_return < -5 else "neutral"
                ),
            }

        # Identify leading and lagging sectors
        sorted_sectors = sorted(
            sector_analysis.items(), key=lambda x: x[1]["avg_return_pct"], reverse=True
        )

        return {
            "sector_performance": sector_analysis,
            "leading_sectors": [s[0] for s in sorted_sectors[:2]],
            "lagging_sectors": [s[0] for s in sorted_sectors[-2:]],
            "rotation_signal": (
                "active"
                if len(set([s[1]["trend"] for s in sorted_sectors])) > 1
                else "stable"
            ),
        }

    def _analyze_market_cycle(self, positioned_assets: pd.DataFrame) -> Dict[str, Any]:
        """Analyze current market cycle phase."""
        returns = positioned_assets["Total Return %"].dropna()

        if returns.empty:
            return {"phase": "UNKNOWN", "confidence": 0.0}

        avg_return = returns.mean()
        volatility = returns.std()
        extreme_performers = ((returns > 50) | (returns < -50)).sum() / len(returns)

        # Market cycle classification
        if avg_return > 30 and extreme_performers > 0.3:
            phase = "EUPHORIA"
            confidence = 0.8
        elif avg_return > 15 and volatility < 30:
            phase = "BULL_MARKET"
            confidence = 0.7
        elif avg_return > 0 and volatility > 40:
            phase = "EARLY_BULL"
            confidence = 0.6
        elif avg_return > -10 and volatility < 25:
            phase = "ACCUMULATION"
            confidence = 0.6
        elif avg_return < -20 and extreme_performers > 0.4:
            phase = "CAPITULATION"
            confidence = 0.8
        elif avg_return < -10:
            phase = "BEAR_MARKET"
            confidence = 0.7
        else:
            phase = "CONSOLIDATION"
            confidence = 0.5

        return {
            "phase": phase,
            "confidence": round(confidence, 3),
            "avg_return": round(avg_return, 2),
            "volatility": round(volatility, 2),
            "extreme_performers_ratio": round(extreme_performers, 3),
        }

    def _analyze_correlations(self, positioned_assets: pd.DataFrame) -> Dict[str, Any]:
        """Analyze correlation patterns in the portfolio."""
        returns = positioned_assets["Total Return %"].dropna()

        if len(returns) < 3:
            return {
                "correlation_strength": "insufficient_data",
                "diversification_score": 0.0,
            }

        # Simple correlation analysis based on return patterns
        return_variance = returns.var()
        return_range = returns.max() - returns.min()

        # High variance and range suggest low correlation (good diversification)
        diversification_score = min(return_variance / 1000 + return_range / 200, 1.0)

        if diversification_score > 0.7:
            correlation_strength = "low_correlation"
            diversification_quality = "excellent"
        elif diversification_score > 0.5:
            correlation_strength = "moderate_correlation"
            diversification_quality = "good"
        else:
            correlation_strength = "high_correlation"
            diversification_quality = "poor"

        return {
            "correlation_strength": correlation_strength,
            "diversification_score": round(diversification_score, 3),
            "diversification_quality": diversification_quality,
            "return_variance": round(return_variance, 2),
            "return_range_pct": round(return_range, 2),
        }

    def _analyze_momentum(self, positioned_assets: pd.DataFrame) -> Dict[str, Any]:
        """Analyze momentum indicators across the portfolio."""
        returns = positioned_assets["Total Return %"].dropna()
        values = positioned_assets["Actual Value €"].dropna()

        if returns.empty:
            return {"momentum": "UNKNOWN", "strength": 0.0}

        # Momentum based on return distribution
        positive_momentum = (returns > 10).sum()
        negative_momentum = (returns < -10).sum()
        neutral_momentum = len(returns) - positive_momentum - negative_momentum

        # Weight by portfolio value
        total_value = values.sum()
        if total_value > 0:
            value_weighted_return = (
                positioned_assets["Total Return %"]
                * positioned_assets["Actual Value €"]
            ).sum() / total_value
        else:
            value_weighted_return = returns.mean()

        # Momentum classification
        if positive_momentum > negative_momentum * 2:
            momentum = "STRONG_POSITIVE"
            strength = min(positive_momentum / len(returns), 1.0)
        elif positive_momentum > negative_momentum:
            momentum = "POSITIVE"
            strength = 0.6
        elif negative_momentum > positive_momentum * 2:
            momentum = "STRONG_NEGATIVE"
            strength = min(negative_momentum / len(returns), 1.0)
        elif negative_momentum > positive_momentum:
            momentum = "NEGATIVE"
            strength = 0.6
        else:
            momentum = "NEUTRAL"
            strength = 0.5

        return {
            "momentum": momentum,
            "strength": round(strength, 3),
            "positive_assets": positive_momentum,
            "negative_assets": negative_momentum,
            "neutral_assets": neutral_momentum,
            "value_weighted_return_pct": round(value_weighted_return, 2),
        }

    def _generate_key_insights(
        self, overall_trend: Dict, sector_analysis: Dict, market_cycle: Dict
    ) -> List[str]:
        """Generate key insights from the analysis."""
        insights = []

        # Overall trend insights
        trend_dir = overall_trend["direction"]
        if trend_dir in ["STRONG_BULLISH", "BULLISH"]:
            insights.append(
                f"Market showing {trend_dir.lower().replace('_', ' ')} momentum with {overall_trend['positive_ratio']:.1%} of assets positive"
            )
        elif trend_dir in ["STRONG_BEARISH", "BEARISH"]:
            insights.append(
                f"Market in {trend_dir.lower().replace('_', ' ')} phase with average return of {overall_trend['avg_return_pct']:.1f}%"
            )
        else:
            insights.append(f"Market in neutral phase with mixed signals")

        # Market cycle insights
        cycle_phase = market_cycle["phase"]
        if cycle_phase == "EUPHORIA":
            insights.append("Market may be in euphoria phase - consider taking profits")
        elif cycle_phase == "CAPITULATION":
            insights.append(
                "Potential accumulation opportunity during market capitulation"
            )
        elif cycle_phase == "BULL_MARKET":
            insights.append(
                "Confirmed bull market conditions - momentum strategies may work"
            )

        # Sector rotation insights
        if sector_analysis["rotation_signal"] == "active":
            leading = ", ".join(sector_analysis["leading_sectors"])
            insights.append(
                f"Active sector rotation detected - {leading} sectors leading"
            )

        return insights

    def _generate_trend_recommendations(
        self, overall_trend: Dict, sector_analysis: Dict
    ) -> List[str]:
        """Generate actionable recommendations based on trend analysis."""
        recommendations = []

        trend_dir = overall_trend["direction"]
        confidence = overall_trend["confidence"]

        if trend_dir in ["STRONG_BULLISH", "BULLISH"] and confidence > 0.6:
            recommendations.append("Consider increasing exposure to momentum assets")
            recommendations.append("Look for breakout opportunities in leading sectors")
        elif trend_dir in ["STRONG_BEARISH", "BEARISH"] and confidence > 0.6:
            recommendations.append("Consider defensive positioning and risk management")
            recommendations.append(
                "Look for accumulation opportunities in quality assets"
            )
        else:
            recommendations.append(
                "Maintain balanced approach in uncertain market conditions"
            )
            recommendations.append(
                "Focus on fundamental analysis over momentum strategies"
            )

        # Sector-specific recommendations
        if sector_analysis["rotation_signal"] == "active":
            leading_sectors = sector_analysis["leading_sectors"]
            if leading_sectors:
                recommendations.append(
                    f"Consider increasing allocation to {', '.join(leading_sectors)} sectors"
                )

        return recommendations
