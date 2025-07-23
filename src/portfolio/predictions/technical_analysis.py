"""Technical analysis tools for crypto portfolio predictions.

This module provides technical analysis indicators and patterns that can be
used by LLMs to analyze price movements and generate trading insights.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


def _safe_float_conversion(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float, handling strings and other types.

    Args:
        value: Value to convert to float
        default: Default value if conversion fails

    Returns:
        Float value or default if conversion fails
    """
    if value is None:
        return default

    try:
        # Handle string values that might have currency symbols or formatting
        if isinstance(value, str):
            # Remove common currency symbols, percentage signs, and whitespace
            cleaned_value = (value.replace('€', '')
                           .replace('$', '')
                           .replace('%', '')
                           .replace(',', '')
                           .strip())
            if cleaned_value == '' or cleaned_value == '-':
                return default
            return float(cleaned_value)

        # Handle numeric types
        return float(value)
    except (ValueError, TypeError):
        return default


class TechnicalAnalyzer:
    """Provides technical analysis indicators for crypto assets."""

    def __init__(self):
        """Initialize technical analyzer."""
        self.indicators = {}

    def analyze_asset_technicals(
        self, asset: str, portfolio_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Analyze technical indicators for a specific asset.

        Args:
            asset: Asset symbol to analyze
            portfolio_data: Portfolio data containing price and volume info

        Returns:
            Dictionary containing technical analysis results
        """
        try:
            # Find asset data
            asset_data = portfolio_data[portfolio_data["Asset"] == asset]
            if asset_data.empty:
                return {"error": f"No data found for asset {asset}"}

            asset_row = asset_data.iloc[0]

            # Basic technical indicators based on available data
            analysis = {
                "asset": asset,
                "current_price_eur": _safe_float_conversion(asset_row.get("Current Price €", 0)),
                "position_size": _safe_float_conversion(asset_row.get("Actual Amount", 0)),
                "cost_basis": _safe_float_conversion(asset_row.get("Cost €", 0)),
                "unrealized_pnl": _safe_float_conversion(asset_row.get("Unrealised €", 0)),
                "return_percentage": _safe_float_conversion(asset_row.get("Total Return %", 0)),
                "technical_signals": self._generate_technical_signals(asset_row),
                "support_resistance": self._calculate_support_resistance(asset_row),
                "momentum_indicators": self._calculate_momentum_indicators(asset_row),
                "volatility_analysis": self._analyze_volatility(asset_row),
                "trend_analysis": self._analyze_trend(asset_row),
            }

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing technicals for {asset}: {e}")
            return {"error": f"Technical analysis failed: {str(e)}"}

    def _generate_technical_signals(self, asset_row: pd.Series) -> Dict[str, Any]:
        """Generate technical trading signals based on available data."""
        current_price = _safe_float_conversion(asset_row.get("Current Price €", 0))
        cost_basis = _safe_float_conversion(asset_row.get("Cost €", 0))
        actual_amount = _safe_float_conversion(asset_row.get("Actual Amount", 0))
        return_pct = _safe_float_conversion(asset_row.get("Total Return %", 0))

        if actual_amount == 0 or cost_basis == 0:
            return {"signal": "NEUTRAL", "strength": 0, "reason": "No position"}

        avg_cost_per_unit = cost_basis / actual_amount

        signals = []
        strength = 0

        # Price vs cost basis analysis
        if current_price > avg_cost_per_unit * 1.2:  # 20% above cost
            signals.append("Strong profit position - consider taking profits")
            strength += 2
        elif current_price > avg_cost_per_unit * 1.1:  # 10% above cost
            signals.append("Profitable position - monitor for exit opportunities")
            strength += 1
        elif current_price < avg_cost_per_unit * 0.8:  # 20% below cost
            signals.append("Significant loss position - consider risk management")
            strength -= 2
        elif current_price < avg_cost_per_unit * 0.9:  # 10% below cost
            signals.append("Loss position - monitor closely")
            strength -= 1

        # Return percentage analysis
        if return_pct > 50:
            signals.append("Exceptional performance - high profit taking consideration")
            strength += 2
        elif return_pct > 20:
            signals.append("Strong performance - partial profit taking may be wise")
            strength += 1
        elif return_pct < -30:
            signals.append("Poor performance - reassess position size")
            strength -= 2
        elif return_pct < -10:
            signals.append("Underperforming - monitor for improvement")
            strength -= 1

        # Determine overall signal
        if strength >= 2:
            signal = "STRONG_SELL"
        elif strength == 1:
            signal = "SELL"
        elif strength == -1:
            signal = "BUY"
        elif strength <= -2:
            signal = "STRONG_BUY"
        else:
            signal = "HOLD"

        return {
            "signal": signal,
            "strength": abs(strength),
            "signals": signals,
            "price_vs_cost": (
                round((current_price / avg_cost_per_unit - 1) * 100, 2)
                if avg_cost_per_unit > 0
                else 0
            ),
        }

    def _calculate_support_resistance(self, asset_row: pd.Series) -> Dict[str, Any]:
        """Calculate support and resistance levels based on cost basis and current performance."""
        current_price = _safe_float_conversion(asset_row.get("Current Price €", 0))
        cost_basis = _safe_float_conversion(asset_row.get("Cost €", 0))
        actual_amount = _safe_float_conversion(asset_row.get("Actual Amount", 0))

        if actual_amount == 0 or cost_basis == 0:
            return {"support": 0, "resistance": 0, "analysis": "Insufficient data"}

        avg_cost = cost_basis / actual_amount

        # Simple support/resistance based on psychological levels
        support_levels = [
            avg_cost * 0.9,  # 10% below cost
            avg_cost * 0.8,  # 20% below cost
            avg_cost * 0.7,  # 30% below cost
        ]

        resistance_levels = [
            avg_cost * 1.1,  # 10% above cost
            avg_cost * 1.2,  # 20% above cost
            avg_cost * 1.5,  # 50% above cost
        ]

        # Find nearest levels
        nearest_support = max(
            [level for level in support_levels if level < current_price],
            default=support_levels[-1],
        )
        nearest_resistance = min(
            [level for level in resistance_levels if level > current_price],
            default=resistance_levels[-1],
        )

        return {
            "nearest_support": round(nearest_support, 4),
            "nearest_resistance": round(nearest_resistance, 4),
            "support_levels": [round(level, 4) for level in support_levels],
            "resistance_levels": [round(level, 4) for level in resistance_levels],
            "distance_to_support": round(
                (current_price - nearest_support) / current_price * 100, 2
            ),
            "distance_to_resistance": round(
                (nearest_resistance - current_price) / current_price * 100, 2
            ),
        }

    def _calculate_momentum_indicators(self, asset_row: pd.Series) -> Dict[str, Any]:
        """Calculate momentum indicators based on return performance."""
        return_pct = _safe_float_conversion(asset_row.get("Total Return %", 0))
        unrealized = _safe_float_conversion(asset_row.get("Unrealised €", 0))

        # Simple momentum classification
        if return_pct > 30:
            momentum = "VERY_STRONG"
            momentum_score = 5
        elif return_pct > 15:
            momentum = "STRONG"
            momentum_score = 4
        elif return_pct > 5:
            momentum = "POSITIVE"
            momentum_score = 3
        elif return_pct > -5:
            momentum = "NEUTRAL"
            momentum_score = 2
        elif return_pct > -15:
            momentum = "NEGATIVE"
            momentum_score = 1
        else:
            momentum = "VERY_WEAK"
            momentum_score = 0

        return {
            "momentum": momentum,
            "momentum_score": momentum_score,
            "return_percentage": return_pct,
            "unrealized_pnl": unrealized,
            "interpretation": self._interpret_momentum(momentum, return_pct),
        }

    def _interpret_momentum(self, momentum: str, return_pct: float) -> str:
        """Provide interpretation of momentum indicators."""
        interpretations = {
            "VERY_STRONG": f"Exceptional upward momentum ({return_pct:.1f}%) - consider profit-taking strategies",
            "STRONG": f"Strong positive momentum ({return_pct:.1f}%) - trending well",
            "POSITIVE": f"Positive momentum ({return_pct:.1f}%) - healthy growth",
            "NEUTRAL": f"Neutral momentum ({return_pct:.1f}%) - sideways movement",
            "NEGATIVE": f"Negative momentum ({return_pct:.1f}%) - showing weakness",
            "VERY_WEAK": f"Very weak momentum ({return_pct:.1f}%) - significant underperformance",
        }
        return interpretations.get(momentum, "Unknown momentum state")

    def _analyze_volatility(self, asset_row: pd.Series) -> Dict[str, Any]:
        """Analyze volatility based on available data."""
        return_pct = _safe_float_conversion(asset_row.get("Total Return %", 0))
        current_price = _safe_float_conversion(asset_row.get("Current Price €", 0))

        # Estimate volatility based on return magnitude
        volatility_estimate = abs(return_pct) / 10  # Simple heuristic

        if volatility_estimate > 10:
            volatility_level = "VERY_HIGH"
            risk_level = "HIGH"
        elif volatility_estimate > 5:
            volatility_level = "HIGH"
            risk_level = "MEDIUM_HIGH"
        elif volatility_estimate > 2:
            volatility_level = "MEDIUM"
            risk_level = "MEDIUM"
        elif volatility_estimate > 1:
            volatility_level = "LOW"
            risk_level = "LOW"
        else:
            volatility_level = "VERY_LOW"
            risk_level = "VERY_LOW"

        return {
            "volatility_level": volatility_level,
            "volatility_estimate": round(volatility_estimate, 2),
            "risk_level": risk_level,
            "price_stability": "STABLE" if volatility_estimate < 2 else "VOLATILE",
            "recommendation": self._get_volatility_recommendation(
                volatility_level, return_pct
            ),
        }

    def _get_volatility_recommendation(
        self, volatility_level: str, return_pct: float
    ) -> str:
        """Get recommendation based on volatility analysis."""
        if volatility_level in ["VERY_HIGH", "HIGH"]:
            if return_pct > 0:
                return "High volatility with gains - consider taking profits to lock in returns"
            else:
                return "High volatility with losses - implement strict risk management"
        elif volatility_level == "MEDIUM":
            return "Moderate volatility - normal market behavior, monitor position size"
        else:
            return "Low volatility - stable asset, suitable for long-term holding"

    def _analyze_trend(self, asset_row: pd.Series) -> Dict[str, Any]:
        """Analyze trend based on performance data."""
        return_pct = _safe_float_conversion(asset_row.get("Total Return %", 0))
        unrealized = _safe_float_conversion(asset_row.get("Unrealised €", 0))

        # Trend classification based on returns
        if return_pct > 20:
            trend = "STRONG_UPTREND"
            trend_strength = 5
        elif return_pct > 10:
            trend = "UPTREND"
            trend_strength = 4
        elif return_pct > 0:
            trend = "WEAK_UPTREND"
            trend_strength = 3
        elif return_pct > -10:
            trend = "SIDEWAYS"
            trend_strength = 2
        elif return_pct > -20:
            trend = "DOWNTREND"
            trend_strength = 1
        else:
            trend = "STRONG_DOWNTREND"
            trend_strength = 0

        return {
            "trend": trend,
            "trend_strength": trend_strength,
            "trend_direction": (
                "UP" if return_pct > 0 else "DOWN" if return_pct < 0 else "SIDEWAYS"
            ),
            "trend_quality": "STRONG" if abs(return_pct) > 15 else "WEAK",
            "recommendation": self._get_trend_recommendation(trend, return_pct),
        }

    def _get_trend_recommendation(self, trend: str, return_pct: float) -> str:
        """Get recommendation based on trend analysis."""
        recommendations = {
            "STRONG_UPTREND": "Strong upward trend - consider holding but watch for reversal signals",
            "UPTREND": "Positive trend - good momentum, monitor for continuation",
            "WEAK_UPTREND": "Weak upward movement - cautious optimism",
            "SIDEWAYS": "No clear trend - wait for breakout direction",
            "DOWNTREND": "Negative trend - consider risk management strategies",
            "STRONG_DOWNTREND": "Strong downward trend - reassess position or cut losses",
        }
        return recommendations.get(trend, "Trend analysis inconclusive")

    def get_portfolio_technical_summary(
        self, portfolio_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Get technical analysis summary for entire portfolio."""
        try:
            # Filter assets with positions
            positioned_assets = portfolio_data[portfolio_data["Actual Amount"] > 0]

            if positioned_assets.empty:
                return {"message": "No positions to analyze"}

            total_value = positioned_assets["Actual Value €"].sum()
            total_unrealized = positioned_assets["Unrealised €"].sum()
            avg_return = positioned_assets["Total Return %"].mean()

            # Analyze momentum distribution
            strong_performers = len(
                positioned_assets[positioned_assets["Total Return %"] > 20]
            )
            weak_performers = len(
                positioned_assets[positioned_assets["Total Return %"] < -10]
            )

            # Risk assessment
            high_risk_positions = len(
                positioned_assets[positioned_assets["Total Return %"].abs() > 30]
            )

            return {
                "total_positions": len(positioned_assets),
                "total_value_eur": round(total_value, 2),
                "total_unrealized_eur": round(total_unrealized, 2),
                "average_return_pct": round(avg_return, 2),
                "strong_performers": strong_performers,
                "weak_performers": weak_performers,
                "high_risk_positions": high_risk_positions,
                "portfolio_momentum": (
                    "POSITIVE"
                    if avg_return > 5
                    else "NEGATIVE" if avg_return < -5 else "NEUTRAL"
                ),
                "diversification_score": min(
                    len(positioned_assets) / 10 * 100, 100
                ),  # Simple diversification metric
                "risk_level": (
                    "HIGH"
                    if high_risk_positions > len(positioned_assets) * 0.3
                    else "MEDIUM" if high_risk_positions > 0 else "LOW"
                ),
            }

        except Exception as e:
            logger.error(f"Error generating portfolio technical summary: {e}")
            return {"error": f"Portfolio analysis failed: {str(e)}"}
