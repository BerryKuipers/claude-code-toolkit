"""Risk assessment tools for crypto portfolio analysis.

This module provides comprehensive risk analysis capabilities that LLMs can use
to evaluate portfolio risk, concentration risk, and provide risk management recommendations.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


class RiskAssessment:
    """Comprehensive risk assessment for crypto portfolios."""
    
    def __init__(self):
        """Initialize risk assessment engine."""
        self.risk_thresholds = {
            "concentration_risk": 0.3,  # 30% in single asset
            "high_volatility": 50,      # 50% return variance
            "loss_threshold": -20,      # 20% loss threshold
            "profit_risk": 100          # 100% profit risk threshold
        }
    
    def assess_portfolio_risk(self, portfolio_data: pd.DataFrame) -> Dict[str, Any]:
        """Comprehensive portfolio risk assessment.
        
        Args:
            portfolio_data: DataFrame containing portfolio information
            
        Returns:
            Dictionary containing detailed risk analysis
        """
        try:
            # Filter assets with positions
            positioned_assets = portfolio_data[portfolio_data["Actual Amount"] > 0].copy()
            
            if positioned_assets.empty:
                return {"message": "No positions to assess risk for"}
            
            # Calculate portfolio metrics
            total_value = positioned_assets["Actual Value €"].sum()
            total_cost = positioned_assets["Cost €"].sum()
            total_unrealized = positioned_assets["Unrealised €"].sum()
            
            # Add allocation percentages
            positioned_assets["Allocation %"] = (positioned_assets["Actual Value €"] / total_value * 100)
            
            risk_analysis = {
                "overall_risk_score": self._calculate_overall_risk_score(positioned_assets),
                "concentration_risk": self._assess_concentration_risk(positioned_assets),
                "volatility_risk": self._assess_volatility_risk(positioned_assets),
                "loss_risk": self._assess_loss_risk(positioned_assets),
                "liquidity_risk": self._assess_liquidity_risk(positioned_assets),
                "correlation_risk": self._assess_correlation_risk(positioned_assets),
                "position_sizing_risk": self._assess_position_sizing_risk(positioned_assets),
                "risk_recommendations": self._generate_risk_recommendations(positioned_assets),
                "portfolio_metrics": {
                    "total_value_eur": round(total_value, 2),
                    "total_cost_eur": round(total_cost, 2),
                    "total_unrealized_eur": round(total_unrealized, 2),
                    "portfolio_return_pct": round((total_unrealized / total_cost * 100) if total_cost > 0 else 0, 2),
                    "number_of_positions": len(positioned_assets)
                }
            }
            
            return risk_analysis
            
        except Exception as e:
            logger.error(f"Error assessing portfolio risk: {e}")
            return {"error": f"Risk assessment failed: {str(e)}"}
    
    def _calculate_overall_risk_score(self, positioned_assets: pd.DataFrame) -> Dict[str, Any]:
        """Calculate overall portfolio risk score (0-100)."""
        risk_factors = []
        
        # Concentration risk factor
        max_allocation = positioned_assets["Allocation %"].max()
        concentration_risk = min(max_allocation / 30 * 25, 25)  # Max 25 points
        risk_factors.append(("concentration", concentration_risk))
        
        # Volatility risk factor (based on return variance)
        return_variance = positioned_assets["Total Return %"].std()
        volatility_risk = min(return_variance / 50 * 25, 25)  # Max 25 points
        risk_factors.append(("volatility", volatility_risk))
        
        # Loss exposure risk factor
        loss_positions = len(positioned_assets[positioned_assets["Total Return %"] < -10])
        loss_risk = (loss_positions / len(positioned_assets)) * 25  # Max 25 points
        risk_factors.append(("loss_exposure", loss_risk))
        
        # Extreme position risk factor
        extreme_positions = len(positioned_assets[positioned_assets["Total Return %"].abs() > 50])
        extreme_risk = (extreme_positions / len(positioned_assets)) * 25  # Max 25 points
        risk_factors.append(("extreme_positions", extreme_risk))
        
        total_risk_score = sum(factor[1] for factor in risk_factors)
        
        # Risk level classification
        if total_risk_score >= 70:
            risk_level = "VERY_HIGH"
        elif total_risk_score >= 50:
            risk_level = "HIGH"
        elif total_risk_score >= 30:
            risk_level = "MEDIUM"
        elif total_risk_score >= 15:
            risk_level = "LOW"
        else:
            risk_level = "VERY_LOW"
        
        return {
            "risk_score": round(total_risk_score, 1),
            "risk_level": risk_level,
            "risk_factors": {factor[0]: round(factor[1], 1) for factor in risk_factors},
            "interpretation": self._interpret_risk_score(total_risk_score)
        }
    
    def _interpret_risk_score(self, score: float) -> str:
        """Interpret the overall risk score."""
        if score >= 70:
            return "Very high risk portfolio - immediate risk management required"
        elif score >= 50:
            return "High risk portfolio - consider reducing exposure and diversifying"
        elif score >= 30:
            return "Medium risk portfolio - monitor positions and maintain discipline"
        elif score >= 15:
            return "Low risk portfolio - well-balanced with manageable risk"
        else:
            return "Very low risk portfolio - conservative approach with minimal risk"
    
    def _assess_concentration_risk(self, positioned_assets: pd.DataFrame) -> Dict[str, Any]:
        """Assess concentration risk in the portfolio."""
        # Calculate allocation percentages
        allocations = positioned_assets["Allocation %"].sort_values(ascending=False)
        
        top_5_concentration = allocations.head(5).sum()
        max_single_position = allocations.max()
        
        # Identify concentrated positions
        concentrated_positions = positioned_assets[positioned_assets["Allocation %"] > 20]
        
        risk_level = "LOW"
        if max_single_position > 50:
            risk_level = "VERY_HIGH"
        elif max_single_position > 30:
            risk_level = "HIGH"
        elif max_single_position > 20:
            risk_level = "MEDIUM"
        
        return {
            "risk_level": risk_level,
            "max_single_position_pct": round(max_single_position, 2),
            "top_5_concentration_pct": round(top_5_concentration, 2),
            "concentrated_positions": len(concentrated_positions),
            "concentrated_assets": concentrated_positions["Asset"].tolist() if not concentrated_positions.empty else [],
            "recommendation": self._get_concentration_recommendation(max_single_position, top_5_concentration)
        }
    
    def _get_concentration_recommendation(self, max_position: float, top_5: float) -> str:
        """Get recommendation for concentration risk."""
        if max_position > 50:
            return "Extremely concentrated - immediately reduce largest position"
        elif max_position > 30:
            return "Highly concentrated - consider rebalancing to reduce single-asset risk"
        elif max_position > 20:
            return "Moderately concentrated - monitor position sizes and consider diversification"
        elif top_5 > 80:
            return "Top-heavy portfolio - consider adding smaller positions for diversification"
        else:
            return "Well-diversified portfolio - maintain current allocation discipline"
    
    def _assess_volatility_risk(self, positioned_assets: pd.DataFrame) -> Dict[str, Any]:
        """Assess volatility risk based on return patterns."""
        returns = positioned_assets["Total Return %"]
        
        volatility_metrics = {
            "return_std": returns.std(),
            "return_range": returns.max() - returns.min(),
            "extreme_positions": len(positioned_assets[positioned_assets["Total Return %"].abs() > 50]),
            "volatile_positions": len(positioned_assets[positioned_assets["Total Return %"].abs() > 30])
        }
        
        # Volatility risk classification
        if volatility_metrics["return_std"] > 50:
            risk_level = "VERY_HIGH"
        elif volatility_metrics["return_std"] > 30:
            risk_level = "HIGH"
        elif volatility_metrics["return_std"] > 20:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            "risk_level": risk_level,
            "return_standard_deviation": round(volatility_metrics["return_std"], 2),
            "return_range_pct": round(volatility_metrics["return_range"], 2),
            "extreme_positions": volatility_metrics["extreme_positions"],
            "volatile_positions": volatility_metrics["volatile_positions"],
            "volatility_score": min(volatility_metrics["return_std"] / 10, 10),
            "recommendation": self._get_volatility_recommendation(risk_level, volatility_metrics)
        }
    
    def _get_volatility_recommendation(self, risk_level: str, metrics: Dict) -> str:
        """Get recommendation for volatility risk."""
        if risk_level == "VERY_HIGH":
            return "Extremely volatile portfolio - implement strict position sizing and stop losses"
        elif risk_level == "HIGH":
            return "High volatility - consider reducing position sizes and taking profits on extreme gainers"
        elif risk_level == "MEDIUM":
            return "Moderate volatility - normal for crypto, maintain risk management discipline"
        else:
            return "Low volatility - stable portfolio, suitable for larger position sizes"
    
    def _assess_loss_risk(self, positioned_assets: pd.DataFrame) -> Dict[str, Any]:
        """Assess risk from losing positions."""
        losing_positions = positioned_assets[positioned_assets["Total Return %"] < 0]
        significant_losses = positioned_assets[positioned_assets["Total Return %"] < -20]
        
        if len(positioned_assets) == 0:
            return {"risk_level": "NONE", "losing_positions": 0}
        
        loss_ratio = len(losing_positions) / len(positioned_assets)
        significant_loss_ratio = len(significant_losses) / len(positioned_assets)
        
        total_loss_value = losing_positions["Unrealised €"].sum() if not losing_positions.empty else 0
        
        # Risk classification
        if significant_loss_ratio > 0.3:
            risk_level = "VERY_HIGH"
        elif loss_ratio > 0.5:
            risk_level = "HIGH"
        elif loss_ratio > 0.3:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            "risk_level": risk_level,
            "losing_positions": len(losing_positions),
            "significant_losses": len(significant_losses),
            "loss_ratio_pct": round(loss_ratio * 100, 1),
            "total_loss_value_eur": round(total_loss_value, 2),
            "worst_performer": {
                "asset": positioned_assets.loc[positioned_assets["Total Return %"].idxmin(), "Asset"],
                "return_pct": round(positioned_assets["Total Return %"].min(), 2)
            } if not positioned_assets.empty else None,
            "recommendation": self._get_loss_risk_recommendation(risk_level, loss_ratio)
        }
    
    def _get_loss_risk_recommendation(self, risk_level: str, loss_ratio: float) -> str:
        """Get recommendation for loss risk management."""
        if risk_level == "VERY_HIGH":
            return "High loss exposure - consider cutting worst performers and reassessing strategy"
        elif risk_level == "HIGH":
            return "Significant losses - implement stop-loss strategy and review position sizing"
        elif risk_level == "MEDIUM":
            return "Moderate losses - normal market behavior, maintain discipline"
        else:
            return "Low loss exposure - portfolio performing well overall"
    
    def _assess_liquidity_risk(self, positioned_assets: pd.DataFrame) -> Dict[str, Any]:
        """Assess liquidity risk based on asset characteristics."""
        # Simple liquidity assessment based on position sizes and known liquid assets
        liquid_assets = ["BTC", "ETH", "ADA", "DOT", "LINK", "AVAX", "SOL", "XRP", "LTC", "DOGE"]
        
        liquid_positions = positioned_assets[positioned_assets["Asset"].isin(liquid_assets)]
        illiquid_positions = positioned_assets[~positioned_assets["Asset"].isin(liquid_assets)]
        
        liquid_value_pct = (liquid_positions["Actual Value €"].sum() / 
                           positioned_assets["Actual Value €"].sum() * 100) if not positioned_assets.empty else 0
        
        # Risk assessment
        if liquid_value_pct > 80:
            risk_level = "LOW"
        elif liquid_value_pct > 60:
            risk_level = "MEDIUM"
        elif liquid_value_pct > 40:
            risk_level = "HIGH"
        else:
            risk_level = "VERY_HIGH"
        
        return {
            "risk_level": risk_level,
            "liquid_positions": len(liquid_positions),
            "illiquid_positions": len(illiquid_positions),
            "liquid_value_pct": round(liquid_value_pct, 1),
            "major_liquid_assets": liquid_positions["Asset"].tolist() if not liquid_positions.empty else [],
            "potentially_illiquid": illiquid_positions["Asset"].tolist() if not illiquid_positions.empty else [],
            "recommendation": self._get_liquidity_recommendation(risk_level, liquid_value_pct)
        }
    
    def _get_liquidity_recommendation(self, risk_level: str, liquid_pct: float) -> str:
        """Get recommendation for liquidity risk."""
        if risk_level == "VERY_HIGH":
            return "Low liquidity exposure - consider increasing allocation to major liquid assets"
        elif risk_level == "HIGH":
            return "Moderate liquidity risk - ensure adequate liquid positions for flexibility"
        else:
            return "Good liquidity profile - sufficient exposure to liquid major assets"
    
    def _assess_correlation_risk(self, positioned_assets: pd.DataFrame) -> Dict[str, Any]:
        """Assess correlation risk (simplified analysis)."""
        # Simplified correlation assessment based on asset categories
        major_coins = ["BTC", "ETH"]
        altcoins = ["ADA", "DOT", "LINK", "AVAX", "SOL", "XRP", "LTC"]
        meme_coins = ["DOGE", "SHIB", "PEPE", "FLOKI"]
        
        major_value = positioned_assets[positioned_assets["Asset"].isin(major_coins)]["Actual Value €"].sum()
        alt_value = positioned_assets[positioned_assets["Asset"].isin(altcoins)]["Actual Value €"].sum()
        meme_value = positioned_assets[positioned_assets["Asset"].isin(meme_coins)]["Actual Value €"].sum()
        other_value = positioned_assets["Actual Value €"].sum() - major_value - alt_value - meme_value
        
        total_value = positioned_assets["Actual Value €"].sum()
        
        if total_value == 0:
            return {"risk_level": "NONE"}
        
        distribution = {
            "major_coins_pct": round(major_value / total_value * 100, 1),
            "altcoins_pct": round(alt_value / total_value * 100, 1),
            "meme_coins_pct": round(meme_value / total_value * 100, 1),
            "other_pct": round(other_value / total_value * 100, 1)
        }
        
        # Risk assessment based on diversification
        max_category = max(distribution.values())
        if max_category > 70:
            risk_level = "HIGH"
        elif max_category > 50:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            "risk_level": risk_level,
            "category_distribution": distribution,
            "diversification_score": round(100 - max_category, 1),
            "recommendation": self._get_correlation_recommendation(risk_level, distribution)
        }
    
    def _get_correlation_recommendation(self, risk_level: str, distribution: Dict) -> str:
        """Get recommendation for correlation risk."""
        if risk_level == "HIGH":
            return "High correlation risk - portfolio concentrated in one asset category"
        elif risk_level == "MEDIUM":
            return "Moderate correlation risk - consider diversifying across asset categories"
        else:
            return "Good diversification across asset categories - low correlation risk"
    
    def _assess_position_sizing_risk(self, positioned_assets: pd.DataFrame) -> Dict[str, Any]:
        """Assess risk from position sizing."""
        # Analyze position size distribution
        allocations = positioned_assets["Allocation %"]
        
        oversized_positions = len(positioned_assets[positioned_assets["Allocation %"] > 25])
        undersized_positions = len(positioned_assets[positioned_assets["Allocation %"] < 2])
        
        size_variance = allocations.std()
        
        # Risk classification
        if oversized_positions > 2 or size_variance > 20:
            risk_level = "HIGH"
        elif oversized_positions > 0 or size_variance > 15:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            "risk_level": risk_level,
            "oversized_positions": oversized_positions,
            "undersized_positions": undersized_positions,
            "size_variance": round(size_variance, 2),
            "largest_position_pct": round(allocations.max(), 2),
            "smallest_position_pct": round(allocations.min(), 2),
            "recommendation": self._get_position_sizing_recommendation(risk_level, oversized_positions)
        }
    
    def _get_position_sizing_recommendation(self, risk_level: str, oversized: int) -> str:
        """Get recommendation for position sizing."""
        if risk_level == "HIGH":
            return f"Poor position sizing - {oversized} oversized positions need rebalancing"
        elif risk_level == "MEDIUM":
            return "Moderate position sizing issues - consider rebalancing largest positions"
        else:
            return "Good position sizing discipline - maintain current approach"
    
    def _generate_risk_recommendations(self, positioned_assets: pd.DataFrame) -> List[str]:
        """Generate comprehensive risk management recommendations."""
        recommendations = []
        
        # Check for immediate risks
        max_allocation = positioned_assets["Allocation %"].max()
        if max_allocation > 40:
            recommendations.append(f"URGENT: Reduce largest position ({max_allocation:.1f}%) to under 25%")
        
        # Check for significant losses
        major_losses = positioned_assets[positioned_assets["Total Return %"] < -30]
        if not major_losses.empty:
            recommendations.append(f"Review {len(major_losses)} positions with >30% losses - consider stop-loss strategy")
        
        # Check for extreme gains
        major_gains = positioned_assets[positioned_assets["Total Return %"] > 100]
        if not major_gains.empty:
            recommendations.append(f"Consider taking profits on {len(major_gains)} positions with >100% gains")
        
        # Diversification recommendations
        if len(positioned_assets) < 5:
            recommendations.append("Consider increasing diversification - portfolio has fewer than 5 positions")
        elif len(positioned_assets) > 20:
            recommendations.append("Consider consolidating positions - portfolio may be over-diversified")
        
        # Risk management basics
        recommendations.extend([
            "Implement position sizing rules (max 20% per asset)",
            "Set stop-loss levels for positions with >20% unrealized losses",
            "Consider taking partial profits on positions with >50% gains",
            "Maintain emergency cash reserves outside of crypto positions",
            "Review and rebalance portfolio monthly"
        ])
        
        return recommendations[:10]  # Limit to top 10 recommendations
