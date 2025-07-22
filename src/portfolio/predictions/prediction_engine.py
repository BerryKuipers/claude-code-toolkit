"""Main prediction engine that coordinates all analysis modules.

This module provides a unified interface for LLMs to access various prediction
and analysis capabilities including technical analysis, risk assessment, and
market trend analysis.
"""

import logging
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime

from .technical_analysis import TechnicalAnalyzer
from .risk_assessment import RiskAssessment

logger = logging.getLogger(__name__)


class PredictionEngine:
    """Main engine that coordinates all prediction and analysis modules."""
    
    def __init__(self):
        """Initialize prediction engine with all analysis modules."""
        self.technical_analyzer = TechnicalAnalyzer()
        self.risk_assessor = RiskAssessment()
        self.analysis_cache = {}
        self.last_analysis_time = None
    
    def get_comprehensive_analysis(self, portfolio_data: pd.DataFrame, asset: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive analysis combining all prediction modules.
        
        Args:
            portfolio_data: Portfolio data DataFrame
            asset: Optional specific asset to analyze (if None, analyzes entire portfolio)
            
        Returns:
            Dictionary containing comprehensive analysis results
        """
        try:
            analysis_key = f"comprehensive_{asset or 'portfolio'}_{datetime.now().strftime('%Y%m%d_%H')}"
            
            # Check cache (hourly cache)
            if analysis_key in self.analysis_cache:
                logger.info(f"Returning cached analysis for {asset or 'portfolio'}")
                return self.analysis_cache[analysis_key]
            
            if asset:
                # Single asset analysis
                analysis = self._analyze_single_asset(portfolio_data, asset)
            else:
                # Portfolio-wide analysis
                analysis = self._analyze_portfolio(portfolio_data)
            
            # Cache the results
            self.analysis_cache[analysis_key] = analysis
            self.last_analysis_time = datetime.now()
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            return {"error": f"Analysis failed: {str(e)}"}
    
    def _analyze_single_asset(self, portfolio_data: pd.DataFrame, asset: str) -> Dict[str, Any]:
        """Analyze a single asset comprehensively."""
        try:
            # Technical analysis
            technical_analysis = self.technical_analyzer.analyze_asset_technicals(asset, portfolio_data)
            
            # Get asset data for additional analysis
            asset_data = portfolio_data[portfolio_data["Asset"] == asset]
            if asset_data.empty:
                return {"error": f"Asset {asset} not found in portfolio"}
            
            asset_row = asset_data.iloc[0]
            
            # Risk analysis for this specific asset
            asset_risk = self._assess_single_asset_risk(asset_row)
            
            # Generate predictions and recommendations
            predictions = self._generate_asset_predictions(asset_row, technical_analysis)
            
            # Combine all analysis
            comprehensive_analysis = {
                "asset": asset,
                "timestamp": datetime.now().isoformat(),
                "analysis_type": "single_asset",
                "technical_analysis": technical_analysis,
                "risk_analysis": asset_risk,
                "predictions": predictions,
                "summary": self._generate_asset_summary(asset, technical_analysis, asset_risk, predictions),
                "action_recommendations": self._generate_asset_recommendations(asset_row, technical_analysis, asset_risk)
            }
            
            return comprehensive_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing asset {asset}: {e}")
            return {"error": f"Asset analysis failed: {str(e)}"}
    
    def _analyze_portfolio(self, portfolio_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze entire portfolio comprehensively."""
        try:
            # Portfolio-wide technical analysis
            portfolio_technical = self.technical_analyzer.get_portfolio_technical_summary(portfolio_data)
            
            # Comprehensive risk assessment
            portfolio_risk = self.risk_assessor.assess_portfolio_risk(portfolio_data)
            
            # Portfolio predictions
            portfolio_predictions = self._generate_portfolio_predictions(portfolio_data, portfolio_technical, portfolio_risk)
            
            # Top assets analysis
            positioned_assets = portfolio_data[portfolio_data["Actual Amount"] > 0]
            top_assets_analysis = self._analyze_top_assets(positioned_assets)
            
            comprehensive_analysis = {
                "analysis_type": "portfolio",
                "timestamp": datetime.now().isoformat(),
                "portfolio_technical": portfolio_technical,
                "portfolio_risk": portfolio_risk,
                "portfolio_predictions": portfolio_predictions,
                "top_assets_analysis": top_assets_analysis,
                "portfolio_summary": self._generate_portfolio_summary(portfolio_technical, portfolio_risk),
                "strategic_recommendations": self._generate_portfolio_recommendations(portfolio_data, portfolio_risk)
            }
            
            return comprehensive_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing portfolio: {e}")
            return {"error": f"Portfolio analysis failed: {str(e)}"}
    
    def _assess_single_asset_risk(self, asset_row: pd.Series) -> Dict[str, Any]:
        """Assess risk for a single asset."""
        return_pct = float(asset_row.get("Total Return %", 0))
        allocation_pct = float(asset_row.get("Allocation %", 0)) if "Allocation %" in asset_row else 0
        unrealized = float(asset_row.get("Unrealised €", 0))
        
        # Risk factors
        risk_factors = []
        risk_score = 0
        
        # Return-based risk
        if abs(return_pct) > 50:
            risk_factors.append("High volatility (>50% return)")
            risk_score += 3
        elif abs(return_pct) > 30:
            risk_factors.append("Moderate volatility (>30% return)")
            risk_score += 2
        
        # Loss risk
        if return_pct < -20:
            risk_factors.append("Significant loss position")
            risk_score += 3
        elif return_pct < -10:
            risk_factors.append("Loss position")
            risk_score += 1
        
        # Concentration risk (if allocation data available)
        if allocation_pct > 30:
            risk_factors.append("High concentration risk")
            risk_score += 3
        elif allocation_pct > 20:
            risk_factors.append("Moderate concentration risk")
            risk_score += 2
        
        # Risk level
        if risk_score >= 6:
            risk_level = "VERY_HIGH"
        elif risk_score >= 4:
            risk_level = "HIGH"
        elif risk_score >= 2:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "return_pct": return_pct,
            "unrealized_eur": unrealized,
            "recommendation": self._get_single_asset_risk_recommendation(risk_level, return_pct)
        }
    
    def _get_single_asset_risk_recommendation(self, risk_level: str, return_pct: float) -> str:
        """Get risk recommendation for single asset."""
        if risk_level == "VERY_HIGH":
            if return_pct > 0:
                return "Very high risk with gains - strongly consider taking profits"
            else:
                return "Very high risk with losses - implement immediate risk management"
        elif risk_level == "HIGH":
            return "High risk position - monitor closely and consider position sizing"
        elif risk_level == "MEDIUM":
            return "Moderate risk - maintain current monitoring and discipline"
        else:
            return "Low risk position - suitable for current allocation"
    
    def _generate_asset_predictions(self, asset_row: pd.Series, technical_analysis: Dict) -> Dict[str, Any]:
        """Generate predictions for a single asset."""
        current_price = float(asset_row.get("Current Price €", 0))
        return_pct = float(asset_row.get("Total Return %", 0))
        
        # Extract technical signals
        technical_signals = technical_analysis.get("technical_signals", {})
        signal = technical_signals.get("signal", "HOLD")
        momentum = technical_analysis.get("momentum_indicators", {}).get("momentum", "NEUTRAL")
        
        # Price predictions (simple heuristic-based)
        predictions = {
            "short_term_outlook": self._predict_short_term_outlook(signal, momentum, return_pct),
            "support_resistance": technical_analysis.get("support_resistance", {}),
            "price_targets": self._calculate_price_targets(current_price, return_pct, signal),
            "risk_reward_ratio": self._calculate_risk_reward_ratio(current_price, technical_analysis),
            "confidence_level": self._assess_prediction_confidence(technical_analysis)
        }
        
        return predictions
    
    def _predict_short_term_outlook(self, signal: str, momentum: str, return_pct: float) -> Dict[str, Any]:
        """Predict short-term outlook based on signals."""
        outlook_map = {
            "STRONG_BUY": "VERY_BULLISH",
            "BUY": "BULLISH", 
            "HOLD": "NEUTRAL",
            "SELL": "BEARISH",
            "STRONG_SELL": "VERY_BEARISH"
        }
        
        outlook = outlook_map.get(signal, "NEUTRAL")
        
        # Adjust based on momentum
        if momentum in ["VERY_STRONG", "STRONG"] and outlook in ["NEUTRAL", "BULLISH"]:
            outlook = "BULLISH" if outlook == "NEUTRAL" else "VERY_BULLISH"
        elif momentum in ["VERY_WEAK", "NEGATIVE"] and outlook in ["NEUTRAL", "BEARISH"]:
            outlook = "BEARISH" if outlook == "NEUTRAL" else "VERY_BEARISH"
        
        return {
            "outlook": outlook,
            "signal": signal,
            "momentum": momentum,
            "reasoning": self._explain_outlook_reasoning(outlook, signal, momentum, return_pct)
        }
    
    def _explain_outlook_reasoning(self, outlook: str, signal: str, momentum: str, return_pct: float) -> str:
        """Explain the reasoning behind the outlook."""
        base_reason = f"Technical signal: {signal}, Momentum: {momentum}, Current return: {return_pct:.1f}%"
        
        if outlook == "VERY_BULLISH":
            return f"{base_reason}. Strong positive indicators suggest continued upward movement."
        elif outlook == "BULLISH":
            return f"{base_reason}. Positive indicators suggest potential for gains."
        elif outlook == "BEARISH":
            return f"{base_reason}. Negative indicators suggest potential for losses."
        elif outlook == "VERY_BEARISH":
            return f"{base_reason}. Strong negative indicators suggest significant downside risk."
        else:
            return f"{base_reason}. Mixed signals suggest sideways movement or uncertainty."
    
    def _calculate_price_targets(self, current_price: float, return_pct: float, signal: str) -> Dict[str, float]:
        """Calculate potential price targets."""
        if current_price <= 0:
            return {"upside_target": 0, "downside_target": 0}
        
        # Simple target calculation based on signal and current performance
        if signal in ["STRONG_BUY", "BUY"]:
            upside_target = current_price * 1.2  # 20% upside
            downside_target = current_price * 0.9  # 10% downside
        elif signal in ["STRONG_SELL", "SELL"]:
            upside_target = current_price * 1.05  # 5% upside
            downside_target = current_price * 0.8   # 20% downside
        else:
            upside_target = current_price * 1.1   # 10% upside
            downside_target = current_price * 0.9  # 10% downside
        
        return {
            "upside_target": round(upside_target, 4),
            "downside_target": round(downside_target, 4),
            "upside_potential_pct": round((upside_target / current_price - 1) * 100, 1),
            "downside_risk_pct": round((downside_target / current_price - 1) * 100, 1)
        }
    
    def _calculate_risk_reward_ratio(self, current_price: float, technical_analysis: Dict) -> Dict[str, Any]:
        """Calculate risk-reward ratio."""
        support_resistance = technical_analysis.get("support_resistance", {})
        nearest_support = support_resistance.get("nearest_support", current_price * 0.9)
        nearest_resistance = support_resistance.get("nearest_resistance", current_price * 1.1)
        
        if current_price <= 0:
            return {"ratio": 0, "assessment": "Cannot calculate"}
        
        potential_gain = nearest_resistance - current_price
        potential_loss = current_price - nearest_support
        
        if potential_loss <= 0:
            ratio = float('inf')
            assessment = "Excellent"
        else:
            ratio = potential_gain / potential_loss
            if ratio >= 3:
                assessment = "Excellent"
            elif ratio >= 2:
                assessment = "Good"
            elif ratio >= 1:
                assessment = "Fair"
            else:
                assessment = "Poor"
        
        return {
            "ratio": round(ratio, 2) if ratio != float('inf') else "Infinite",
            "assessment": assessment,
            "potential_gain_eur": round(potential_gain, 4),
            "potential_loss_eur": round(potential_loss, 4)
        }
    
    def _assess_prediction_confidence(self, technical_analysis: Dict) -> Dict[str, Any]:
        """Assess confidence level in predictions."""
        # Simple confidence assessment based on signal strength and consistency
        technical_signals = technical_analysis.get("technical_signals", {})
        signal_strength = technical_signals.get("strength", 0)
        
        momentum = technical_analysis.get("momentum_indicators", {})
        momentum_score = momentum.get("momentum_score", 2)
        
        # Calculate confidence score
        confidence_score = (signal_strength + momentum_score) / 2
        
        if confidence_score >= 4:
            confidence_level = "HIGH"
        elif confidence_score >= 3:
            confidence_level = "MEDIUM"
        else:
            confidence_level = "LOW"
        
        return {
            "confidence_level": confidence_level,
            "confidence_score": round(confidence_score, 1),
            "factors": {
                "signal_strength": signal_strength,
                "momentum_score": momentum_score
            }
        }
    
    def _generate_portfolio_predictions(self, portfolio_data: pd.DataFrame, technical: Dict, risk: Dict) -> Dict[str, Any]:
        """Generate portfolio-level predictions."""
        positioned_assets = portfolio_data[portfolio_data["Actual Amount"] > 0]
        
        if positioned_assets.empty:
            return {"message": "No positions to predict"}
        
        avg_return = positioned_assets["Total Return %"].mean()
        total_value = positioned_assets["Actual Value €"].sum()
        
        # Portfolio outlook
        if avg_return > 20:
            outlook = "VERY_POSITIVE"
        elif avg_return > 10:
            outlook = "POSITIVE"
        elif avg_return > -5:
            outlook = "NEUTRAL"
        elif avg_return > -15:
            outlook = "NEGATIVE"
        else:
            outlook = "VERY_NEGATIVE"
        
        return {
            "portfolio_outlook": outlook,
            "expected_volatility": risk.get("overall_risk_score", {}).get("risk_level", "UNKNOWN"),
            "diversification_benefit": technical.get("diversification_score", 0),
            "rebalancing_needed": risk.get("concentration_risk", {}).get("risk_level") in ["HIGH", "VERY_HIGH"],
            "key_risks": risk.get("risk_recommendations", [])[:3],
            "growth_potential": "HIGH" if avg_return > 15 else "MEDIUM" if avg_return > 5 else "LOW"
        }
    
    def _analyze_top_assets(self, positioned_assets: pd.DataFrame) -> Dict[str, Any]:
        """Analyze top performing and worst performing assets."""
        if positioned_assets.empty:
            return {"message": "No positioned assets to analyze"}
        
        # Sort by value and return
        by_value = positioned_assets.sort_values("Actual Value €", ascending=False).head(5)
        by_return = positioned_assets.sort_values("Total Return %", ascending=False)
        
        top_performers = by_return.head(3)
        worst_performers = by_return.tail(3)
        
        return {
            "largest_positions": [
                {
                    "asset": row["Asset"],
                    "value_eur": round(row["Actual Value €"], 2),
                    "return_pct": round(row["Total Return %"], 2),
                    "allocation_pct": round(row["Actual Value €"] / positioned_assets["Actual Value €"].sum() * 100, 1)
                }
                for _, row in by_value.iterrows()
            ],
            "top_performers": [
                {
                    "asset": row["Asset"],
                    "return_pct": round(row["Total Return %"], 2),
                    "value_eur": round(row["Actual Value €"], 2)
                }
                for _, row in top_performers.iterrows()
            ],
            "worst_performers": [
                {
                    "asset": row["Asset"],
                    "return_pct": round(row["Total Return %"], 2),
                    "value_eur": round(row["Actual Value €"], 2)
                }
                for _, row in worst_performers.iterrows()
            ]
        }
    
    def _generate_asset_summary(self, asset: str, technical: Dict, risk: Dict, predictions: Dict) -> str:
        """Generate a summary for single asset analysis."""
        signal = technical.get("technical_signals", {}).get("signal", "HOLD")
        risk_level = risk.get("risk_level", "UNKNOWN")
        outlook = predictions.get("short_term_outlook", {}).get("outlook", "NEUTRAL")
        
        return f"{asset} shows {signal} signal with {risk_level} risk level. Short-term outlook is {outlook}."
    
    def _generate_portfolio_summary(self, technical: Dict, risk: Dict) -> str:
        """Generate portfolio summary."""
        risk_level = risk.get("overall_risk_score", {}).get("risk_level", "UNKNOWN")
        total_positions = technical.get("total_positions", 0)
        avg_return = technical.get("average_return_pct", 0)
        
        return f"Portfolio has {total_positions} positions with {avg_return:.1f}% average return and {risk_level} overall risk."
    
    def _generate_asset_recommendations(self, asset_row: pd.Series, technical: Dict, risk: Dict) -> List[str]:
        """Generate recommendations for single asset."""
        recommendations = []
        
        signal = technical.get("technical_signals", {}).get("signal", "HOLD")
        return_pct = float(asset_row.get("Total Return %", 0))
        risk_level = risk.get("risk_level", "LOW")
        
        if signal in ["STRONG_SELL", "SELL"] and return_pct > 50:
            recommendations.append("Consider taking profits - strong sell signal with high gains")
        elif signal in ["STRONG_BUY", "BUY"] and return_pct < -20:
            recommendations.append("Potential buying opportunity - buy signal with significant discount")
        
        if risk_level in ["VERY_HIGH", "HIGH"]:
            recommendations.append("Implement strict risk management - high risk position")
        
        if return_pct > 100:
            recommendations.append("Exceptional gains - consider partial profit taking")
        elif return_pct < -30:
            recommendations.append("Significant losses - reassess position and consider stop-loss")
        
        return recommendations[:5]
    
    def _generate_portfolio_recommendations(self, portfolio_data: pd.DataFrame, risk: Dict) -> List[str]:
        """Generate strategic recommendations for portfolio."""
        recommendations = []
        
        # Get risk recommendations
        risk_recs = risk.get("risk_recommendations", [])
        recommendations.extend(risk_recs[:3])
        
        # Add strategic recommendations
        positioned_assets = portfolio_data[portfolio_data["Actual Amount"] > 0]
        if not positioned_assets.empty:
            avg_return = positioned_assets["Total Return %"].mean()
            
            if avg_return > 30:
                recommendations.append("Strong portfolio performance - consider systematic profit taking")
            elif avg_return < -15:
                recommendations.append("Portfolio underperforming - review strategy and risk management")
        
        return recommendations[:8]
