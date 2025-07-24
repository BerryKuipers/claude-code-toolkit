"""Function handlers for OpenAI function calling with portfolio data."""

import json
import logging
from typing import Any, Dict, List, Optional

import pandas as pd

from ..ai_explanations import generate_coin_explanation
from ..data.dataframe_utils import SafeDataFrameOperations
from ..predictions import PredictionEngine
from ..research.web_search import CryptoWebSearcher
from ..utils import safe_float_conversion
from .data_verification import PortfolioDataVerifier

logger = logging.getLogger(__name__)


class PortfolioFunctionHandler:
    """Handles function calls for portfolio analysis queries."""

    def __init__(self, portfolio_data: pd.DataFrame):
        """Initialize with portfolio data.

        Args:
            portfolio_data: DataFrame containing portfolio information
        """
        self.portfolio_data = portfolio_data
        self.functions = self._define_functions()
        self.verifier = PortfolioDataVerifier(portfolio_data)
        self.prediction_engine = PredictionEngine()
        self.web_searcher = CryptoWebSearcher()

    def _define_functions(self) -> List[Dict[str, Any]]:
        """Define available functions for OpenAI function calling."""
        return [
            {
                "name": "get_portfolio_summary",
                "description": "Get overall portfolio summary with total value, P&L, and key metrics",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
            {
                "name": "get_current_holdings",
                "description": "Get list of all currently held assets with amounts and values - CRITICAL for investment recommendations",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
            {
                "name": "get_asset_performance",
                "description": "Get performance data for specific assets",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "assets": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of asset symbols (e.g., ['BTC', 'ETH'])",
                        },
                        "sort_by": {
                            "type": "string",
                            "enum": ["return_pct", "value", "unrealised"],
                            "description": "How to sort the results",
                            "default": "return_pct",
                        },
                    },
                    "required": [],
                },
            },
            {
                "name": "search_crypto_news",
                "description": "Search for latest cryptocurrency news and market analysis using Perplexity AI",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for crypto news (e.g., 'Solana price prediction 2024', 'DeFi trends')",
                        },
                        "focus": {
                            "type": "string",
                            "enum": [
                                "news",
                                "analysis",
                                "price",
                                "technology",
                                "adoption",
                            ],
                            "description": "Focus area for the search",
                            "default": "news",
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "analyze_market_opportunities",
                "description": "Analyze current market opportunities and trends using web research",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sector": {
                            "type": "string",
                            "enum": [
                                "defi",
                                "layer1",
                                "layer2",
                                "gaming",
                                "ai",
                                "meme",
                                "all",
                            ],
                            "description": "Crypto sector to analyze",
                            "default": "all",
                        },
                        "timeframe": {
                            "type": "string",
                            "enum": ["short", "medium", "long"],
                            "description": "Investment timeframe",
                            "default": "medium",
                        },
                    },
                    "required": [],
                },
            },
            {
                "name": "get_top_performers",
                "description": "Get best or worst performing assets",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["best", "worst"],
                            "description": "Whether to get best or worst performers",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of assets to return",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 20,
                        },
                    },
                    "required": ["type"],
                },
            },
            {
                "name": "explain_coin_position",
                "description": "Get detailed natural language explanation of a specific coin position",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "asset": {
                            "type": "string",
                            "description": "Asset symbol (e.g., 'BTC', 'ETH')",
                        }
                    },
                    "required": ["asset"],
                },
            },
            {
                "name": "get_portfolio_allocation",
                "description": "Get portfolio allocation by value or percentage",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "min_percentage": {
                            "type": "number",
                            "description": "Minimum percentage to include in results",
                            "default": 1.0,
                        }
                    },
                    "required": [],
                },
            },
            {
                "name": "get_transfer_analysis",
                "description": "Get deposit/withdrawal and transfer analysis",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "asset": {
                            "type": "string",
                            "description": "Specific asset symbol or 'all' for all assets",
                        }
                    },
                    "required": [],
                },
            },
            {
                "name": "get_technical_analysis",
                "description": "Get technical analysis including signals, support/resistance, and momentum indicators",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "asset": {
                            "type": "string",
                            "description": "Asset symbol for analysis (e.g., 'BTC', 'ETH')",
                        }
                    },
                    "required": ["asset"],
                },
            },
            {
                "name": "get_risk_assessment",
                "description": "Get comprehensive risk assessment for portfolio or specific asset",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "asset": {
                            "type": "string",
                            "description": "Optional asset symbol for single asset risk assessment",
                        }
                    },
                    "required": [],
                },
            },
            {
                "name": "get_price_prediction",
                "description": "Get price predictions and forecasts for assets",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "asset": {
                            "type": "string",
                            "description": "Asset symbol for price prediction (e.g., 'BTC', 'ETH')",
                        }
                    },
                    "required": ["asset"],
                },
            },
            {
                "name": "get_portfolio_optimization",
                "description": "Get portfolio optimization recommendations and rebalancing suggestions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target_risk": {
                            "type": "string",
                            "description": "Target risk level: 'low', 'medium', 'high'",
                            "default": "medium",
                        }
                    },
                    "required": [],
                },
            },
            {
                "name": "search_crypto_news",
                "description": "Search for latest cryptocurrency news and market analysis using Perplexity AI",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for crypto news (e.g., 'Solana price prediction 2024', 'DeFi trends')",
                        },
                        "focus": {
                            "type": "string",
                            "enum": [
                                "news",
                                "analysis",
                                "price",
                                "technology",
                                "adoption",
                            ],
                            "description": "Focus area for the search",
                            "default": "news",
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "analyze_market_opportunities",
                "description": "Analyze current market opportunities and trends using web research",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sector": {
                            "type": "string",
                            "enum": [
                                "defi",
                                "layer1",
                                "layer2",
                                "gaming",
                                "ai",
                                "meme",
                                "all",
                            ],
                            "description": "Crypto sector to analyze",
                            "default": "all",
                        },
                        "timeframe": {
                            "type": "string",
                            "enum": ["short", "medium", "long"],
                            "description": "Investment timeframe",
                            "default": "medium",
                        },
                    },
                    "required": [],
                },
            },
            {
                "name": "get_current_holdings",
                "description": "Get list of all currently held assets with amounts and values - CRITICAL for investment recommendations",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
            {
                "name": "compare_with_market",
                "description": "Compare portfolio performance with market benchmarks and similar assets",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "benchmark": {
                            "type": "string",
                            "enum": ["btc", "eth", "total_market", "defi_index"],
                            "description": "Benchmark to compare against",
                            "default": "total_market",
                        },
                        "timeframe": {
                            "type": "string",
                            "enum": ["1d", "7d", "30d", "90d", "1y"],
                            "description": "Comparison timeframe",
                            "default": "30d",
                        },
                    },
                    "required": [],
                },
            },
            {
                "name": "get_trading_signals",
                "description": "Get AI-powered trading signals and entry/exit recommendations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "assets": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Assets to analyze for trading signals",
                        },
                        "strategy": {
                            "type": "string",
                            "enum": ["conservative", "moderate", "aggressive"],
                            "description": "Trading strategy risk level",
                            "default": "moderate",
                        },
                    },
                    "required": [],
                },
            },
            {
                "name": "find_similar_assets",
                "description": "Find assets similar to current holdings that might be good additions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reference_asset": {
                            "type": "string",
                            "description": "Asset to find similar alternatives to (e.g., 'ETH')",
                        },
                        "criteria": {
                            "type": "string",
                            "enum": [
                                "technology",
                                "market_cap",
                                "use_case",
                                "performance",
                            ],
                            "description": "Similarity criteria",
                            "default": "technology",
                        },
                    },
                    "required": ["reference_asset"],
                },
            },
        ]

    def handle_function_call(self, function_name: str, arguments: str) -> str:
        """Handle a function call and return the result with data verification.

        Args:
            function_name: Name of the function to call
            arguments: JSON string of function arguments

        Returns:
            JSON string containing the verified function result
        """
        try:
            # Parse arguments
            args = json.loads(arguments) if arguments else {}

            # Route to appropriate handler
            if function_name == "get_portfolio_summary":
                result = self._get_portfolio_summary()
            elif function_name == "get_asset_performance":
                result = self._get_asset_performance(**args)
            elif function_name == "get_top_performers":
                result = self._get_top_performers(**args)
            elif function_name == "explain_coin_position":
                result = self._explain_coin_position(**args)
            elif function_name == "get_portfolio_allocation":
                result = self._get_portfolio_allocation(**args)
            elif function_name == "get_transfer_analysis":
                result = self._get_transfer_analysis(**args)
            elif function_name == "get_technical_analysis":
                result = self._get_technical_analysis(**args)
            elif function_name == "get_risk_assessment":
                result = self._get_risk_assessment(**args)
            elif function_name == "get_price_prediction":
                result = self._get_price_prediction(**args)
            elif function_name == "get_portfolio_optimization":
                result = self._get_portfolio_optimization(**args)
            elif function_name == "get_current_holdings":
                result = self._get_current_holdings()
            elif function_name == "search_crypto_news":
                result = self._search_crypto_news(**args)
            elif function_name == "analyze_market_opportunities":
                result = self._analyze_market_opportunities(**args)
            elif function_name == "compare_with_market":
                result = self._compare_with_market(**args)
            elif function_name == "get_trading_signals":
                result = self._get_trading_signals(**args)
            elif function_name == "find_similar_assets":
                result = self._find_similar_assets(**args)
            else:
                result = {"error": f"Unknown function: {function_name}"}

            result_json = json.dumps(result, default=str)

            # Verify the result against actual portfolio data
            is_valid, verified_result, error_msg = self.verifier.verify_function_result(
                function_name, arguments, result_json
            )

            if not is_valid:
                logger.error(
                    f"Data verification failed for {function_name}: {error_msg}"
                )
                # Return error instead of potentially hallucinated data
                return json.dumps(
                    {
                        "error": f"Data verification failed: {error_msg}",
                        "verification_status": "failed",
                        "original_result": result,
                    }
                )

            # Add verification status to successful results
            if isinstance(result, dict) and "error" not in result:
                result["verification_status"] = "verified"
                return json.dumps(result, default=str)

            return verified_result

        except Exception as e:
            logger.error(f"Error handling function call {function_name}: {e}")
            return json.dumps({"error": f"Function call failed: {str(e)}"})

    def _get_portfolio_summary(self) -> Dict[str, Any]:
        """Get overall portfolio summary."""
        if self.portfolio_data.empty:
            return {"error": "No portfolio data available"}

        # Use clean utility for safe calculations
        totals = SafeDataFrameOperations.calculate_portfolio_totals(self.portfolio_data)

        total_cost = totals["total_cost"]
        total_actual_value = totals["total_actual_value"]
        total_realised = totals["total_realised"]
        total_unrealised = totals["total_unrealised"]
        total_invested = totals["total_invested"]

        total_return_pct = (
            ((total_actual_value + total_realised) - total_invested)
            / total_invested
            * 100
            if total_invested > 0
            else 0
        )

        # Count positions using clean utility
        profitable_positions, total_positions = (
            SafeDataFrameOperations.count_profitable_positions(self.portfolio_data)
        )

        return {
            "total_value_eur": round(total_actual_value, 2),
            "total_cost_eur": round(total_cost, 2),
            "total_invested_eur": round(total_invested, 2),
            "total_realised_eur": round(total_realised, 2),
            "total_unrealised_eur": round(total_unrealised, 2),
            "total_return_pct": round(total_return_pct, 2),
            "profitable_positions": profitable_positions,
            "total_positions": total_positions,
            "profitability_rate": (
                round(profitable_positions / total_positions * 100, 1)
                if total_positions > 0
                else 0
            ),
        }

    def _get_asset_performance(
        self, assets: Optional[List[str]] = None, sort_by: str = "return_pct"
    ) -> Dict[str, Any]:
        """Get performance data for specific assets."""
        df = self.portfolio_data.copy()

        # Filter by assets if specified
        if assets:
            df = df[df["Asset"].isin(assets)]

        # Filter out zero positions using safe conversion
        def has_positive_amount(x):
            return safe_float_conversion(x) > 0

        df = df[df["Actual Amount"].apply(has_positive_amount)]

        if df.empty:
            return {"error": "No matching assets found"}

        # Sort by specified criteria
        if sort_by == "return_pct":
            df = df.sort_values("Total Return %", ascending=False)
        elif sort_by == "value":
            df = df.sort_values("Actual Value €", ascending=False)
        elif sort_by == "unrealised":
            df = df.sort_values("Unrealised €", ascending=False)

        # Format results
        results = []
        for _, row in df.iterrows():
            results.append(
                {
                    "asset": row["Asset"],
                    "actual_amount": round(
                        safe_float_conversion(row["Actual Amount"]), 6
                    ),
                    "actual_value_eur": round(
                        safe_float_conversion(row["Actual Value €"]), 2
                    ),
                    "cost_eur": round(safe_float_conversion(row["Cost €"]), 2),
                    "unrealised_eur": round(
                        safe_float_conversion(row["Unrealised €"]), 2
                    ),
                    "total_return_pct": round(
                        safe_float_conversion(row["Total Return %"]), 2
                    ),
                    "current_price_eur": round(
                        safe_float_conversion(row["Current Price €"]), 2
                    ),
                }
            )

        return {"assets": results}

    def _get_top_performers(self, type: str, limit: int = 5) -> Dict[str, Any]:
        """Get top or worst performing assets."""

        def has_positive_amount(x):
            return safe_float_conversion(x) > 0

        df = self.portfolio_data[
            self.portfolio_data["Actual Amount"].apply(has_positive_amount)
        ].copy()

        if df.empty:
            return {"error": "No positions found"}

        # Sort by return percentage
        ascending = type == "worst"
        df = df.sort_values("Total Return %", ascending=ascending).head(limit)

        results = []
        for _, row in df.iterrows():
            results.append(
                {
                    "asset": row["Asset"],
                    "return_pct": round(
                        safe_float_conversion(row["Total Return %"]), 2
                    ),
                    "unrealised_eur": round(
                        safe_float_conversion(row["Unrealised €"]), 2
                    ),
                    "actual_value_eur": round(
                        safe_float_conversion(row["Actual Value €"]), 2
                    ),
                }
            )

        return {"type": type, "performers": results}

    def _explain_coin_position(self, asset: str) -> Dict[str, Any]:
        """Get detailed explanation of a coin position."""
        asset_row = self.portfolio_data[self.portfolio_data["Asset"] == asset.upper()]

        if asset_row.empty:
            return {"error": f"Asset {asset} not found in portfolio"}

        asset_data = asset_row.iloc[0].to_dict()
        explanation = generate_coin_explanation(asset_data)

        return {
            "asset": asset.upper(),
            "explanation": explanation,
            "summary_data": {
                "actual_amount": round(asset_data["Actual Amount"], 6),
                "actual_value_eur": round(asset_data["Actual Value €"], 2),
                "unrealised_eur": round(asset_data["Unrealised €"], 2),
                "total_return_pct": round(asset_data["Total Return %"], 2),
            },
        }

    def _get_portfolio_allocation(self, min_percentage: float = 1.0) -> Dict[str, Any]:
        """Get portfolio allocation by value."""
        df = self.portfolio_data[
            self.portfolio_data["Actual Value €"].apply(
                lambda x: safe_float_conversion(x) > 0
            )
        ].copy()

        if df.empty:
            return {"error": "No positions found"}

        # Use safe float conversion for calculations
        total_value = sum(safe_float_conversion(val) for val in df["Actual Value €"])

        # Calculate allocation percentages safely
        allocations = []
        for _, row in df.iterrows():
            value_eur = safe_float_conversion(row["Actual Value €"])
            allocation_pct = (value_eur / total_value * 100) if total_value > 0 else 0

            # Filter by minimum percentage
            if allocation_pct >= min_percentage:
                allocations.append(
                    {
                        "asset": row["Asset"],
                        "value_eur": round(value_eur, 2),
                        "allocation_pct": round(allocation_pct, 2),
                    }
                )

        # Sort by allocation percentage descending
        allocations.sort(key=lambda x: x["allocation_pct"], reverse=True)

        return {"total_value_eur": round(total_value, 2), "allocations": allocations}

    def _get_transfer_analysis(self, asset: Optional[str] = None) -> Dict[str, Any]:
        """Get transfer analysis for assets."""
        df = self.portfolio_data.copy()

        if asset and asset.upper() != "ALL":
            df = df[df["Asset"] == asset.upper()]

        if df.empty:
            return {"error": "No matching assets found"}

        # Filter assets with transfer activity
        transfer_df = df[(df["Total Deposits"] != 0) | (df["Total Withdrawals"] != 0)]

        if transfer_df.empty:
            return {"message": "No transfer activity found"}

        transfers = []
        for _, row in transfer_df.iterrows():
            transfers.append(
                {
                    "asset": row["Asset"],
                    "net_transfers": round(row["Net Transfers"], 6),
                    "total_deposits": round(row["Total Deposits"], 6),
                    "total_withdrawals": round(row["Total Withdrawals"], 6),
                    "deposit_count": int(row["Deposit Count"]),
                    "withdrawal_count": int(row["Withdrawal Count"]),
                }
            )

        return {"transfers": transfers}

    def get_available_functions(self) -> List[Dict[str, Any]]:
        """Get list of available functions for OpenAI."""
        return self.functions

    def update_portfolio_data(self, portfolio_data: pd.DataFrame):
        """Update portfolio data and refresh verifier.

        Args:
            portfolio_data: Updated DataFrame containing portfolio information
        """
        self.portfolio_data = portfolio_data
        self.verifier = PortfolioDataVerifier(portfolio_data)

    def get_verification_stats(self) -> Dict[str, Any]:
        """Get data verification statistics."""
        return self.verifier.get_verification_stats()

    def _get_technical_analysis(self, asset: str) -> Dict[str, Any]:
        """Get technical analysis for a specific asset."""
        try:
            asset = asset.upper().strip()

            # Check if asset exists in portfolio
            asset_data = self.portfolio_data[self.portfolio_data["Asset"] == asset]
            if asset_data.empty:
                return {"error": f"Asset {asset} not found in portfolio"}

            # Get comprehensive analysis from prediction engine
            analysis = self.prediction_engine.get_comprehensive_analysis(
                self.portfolio_data, asset
            )

            if "error" in analysis:
                return analysis

            # Extract technical analysis portion
            technical_analysis = analysis.get("technical_analysis", {})
            predictions = analysis.get("predictions", {})

            return {
                "asset": asset,
                "technical_signals": technical_analysis.get("technical_signals", {}),
                "support_resistance": technical_analysis.get("support_resistance", {}),
                "momentum_indicators": technical_analysis.get(
                    "momentum_indicators", {}
                ),
                "volatility_analysis": technical_analysis.get(
                    "volatility_analysis", {}
                ),
                "trend_analysis": technical_analysis.get("trend_analysis", {}),
                "price_predictions": predictions.get("price_targets", {}),
                "short_term_outlook": predictions.get("short_term_outlook", {}),
                "confidence_level": predictions.get("confidence_level", {}),
                "analysis_timestamp": analysis.get("timestamp"),
                "verification_status": "verified",
            }

        except Exception as e:
            logger.error(f"Error getting technical analysis for {asset}: {e}")
            return {"error": f"Technical analysis failed: {str(e)}"}

    def _get_risk_assessment(self, asset: Optional[str] = None) -> Dict[str, Any]:
        """Get risk assessment for portfolio or specific asset."""
        try:
            if asset:
                # Single asset risk assessment
                asset = asset.upper().strip()
                analysis = self.prediction_engine.get_comprehensive_analysis(
                    self.portfolio_data, asset
                )

                if "error" in analysis:
                    return analysis

                return {
                    "analysis_type": "single_asset",
                    "asset": asset,
                    "risk_analysis": analysis.get("risk_analysis", {}),
                    "recommendations": analysis.get("action_recommendations", []),
                    "analysis_timestamp": analysis.get("timestamp"),
                    "verification_status": "verified",
                }
            else:
                # Portfolio-wide risk assessment
                analysis = self.prediction_engine.get_comprehensive_analysis(
                    self.portfolio_data
                )

                if "error" in analysis:
                    return analysis

                portfolio_risk = analysis.get("portfolio_risk", {})

                return {
                    "analysis_type": "portfolio",
                    "overall_risk_score": portfolio_risk.get("overall_risk_score", {}),
                    "concentration_risk": portfolio_risk.get("concentration_risk", {}),
                    "volatility_risk": portfolio_risk.get("volatility_risk", {}),
                    "loss_risk": portfolio_risk.get("loss_risk", {}),
                    "liquidity_risk": portfolio_risk.get("liquidity_risk", {}),
                    "position_sizing_risk": portfolio_risk.get(
                        "position_sizing_risk", {}
                    ),
                    "risk_recommendations": portfolio_risk.get(
                        "risk_recommendations", []
                    ),
                    "portfolio_metrics": portfolio_risk.get("portfolio_metrics", {}),
                    "analysis_timestamp": analysis.get("timestamp"),
                    "verification_status": "verified",
                }

        except Exception as e:
            logger.error(f"Error getting risk assessment: {e}")
            return {"error": f"Risk assessment failed: {str(e)}"}

    def _get_price_prediction(self, asset: str) -> Dict[str, Any]:
        """Get price predictions for a specific asset."""
        try:
            asset = asset.upper().strip()

            # Check if asset exists in portfolio
            asset_data = self.portfolio_data[self.portfolio_data["Asset"] == asset]
            if asset_data.empty:
                return {"error": f"Asset {asset} not found in portfolio"}

            # Get comprehensive analysis from prediction engine
            analysis = self.prediction_engine.get_comprehensive_analysis(
                self.portfolio_data, asset
            )

            if "error" in analysis:
                return analysis

            predictions = analysis.get("predictions", {})
            technical_analysis = analysis.get("technical_analysis", {})

            return {
                "asset": asset,
                "current_price_eur": technical_analysis.get("current_price_eur", 0),
                "price_targets": predictions.get("price_targets", {}),
                "support_resistance": predictions.get("support_resistance", {}),
                "short_term_outlook": predictions.get("short_term_outlook", {}),
                "risk_reward_ratio": predictions.get("risk_reward_ratio", {}),
                "confidence_level": predictions.get("confidence_level", {}),
                "technical_signals": technical_analysis.get("technical_signals", {}),
                "momentum_indicators": technical_analysis.get(
                    "momentum_indicators", {}
                ),
                "analysis_timestamp": analysis.get("timestamp"),
                "disclaimer": "Predictions are based on technical analysis and historical data. Crypto markets are highly volatile and unpredictable.",
                "verification_status": "verified",
            }

        except Exception as e:
            logger.error(f"Error getting price prediction for {asset}: {e}")
            return {"error": f"Price prediction failed: {str(e)}"}

    def _get_portfolio_optimization(
        self, target_risk: str = "medium"
    ) -> Dict[str, Any]:
        """Get portfolio optimization recommendations."""
        try:
            # Get comprehensive portfolio analysis
            analysis = self.prediction_engine.get_comprehensive_analysis(
                self.portfolio_data
            )

            if "error" in analysis:
                return analysis

            portfolio_risk = analysis.get("portfolio_risk", {})
            portfolio_technical = analysis.get("portfolio_technical", {})
            top_assets = analysis.get("top_assets_analysis", {})

            # Generate optimization recommendations based on target risk
            optimization_recs = self._generate_optimization_recommendations(
                portfolio_risk, portfolio_technical, top_assets, target_risk
            )

            return {
                "target_risk_level": target_risk,
                "current_risk_level": portfolio_risk.get("overall_risk_score", {}).get(
                    "risk_level", "UNKNOWN"
                ),
                "optimization_needed": self._assess_optimization_need(
                    portfolio_risk, target_risk
                ),
                "rebalancing_recommendations": optimization_recs.get("rebalancing", []),
                "position_adjustments": optimization_recs.get(
                    "position_adjustments", []
                ),
                "diversification_suggestions": optimization_recs.get(
                    "diversification", []
                ),
                "risk_management_actions": optimization_recs.get("risk_management", []),
                "portfolio_metrics": portfolio_risk.get("portfolio_metrics", {}),
                "concentration_analysis": portfolio_risk.get("concentration_risk", {}),
                "analysis_timestamp": analysis.get("timestamp"),
                "verification_status": "verified",
            }

        except Exception as e:
            logger.error(f"Error getting portfolio optimization: {e}")
            return {"error": f"Portfolio optimization failed: {str(e)}"}

    def _generate_optimization_recommendations(
        self,
        portfolio_risk: Dict,
        portfolio_technical: Dict,
        top_assets: Dict,
        target_risk: str,
    ) -> Dict[str, List[str]]:
        """Generate specific optimization recommendations."""
        recommendations = {
            "rebalancing": [],
            "position_adjustments": [],
            "diversification": [],
            "risk_management": [],
        }

        # Risk-based recommendations
        current_risk = portfolio_risk.get("overall_risk_score", {}).get(
            "risk_level", "MEDIUM"
        )
        concentration_risk = portfolio_risk.get("concentration_risk", {})

        # Concentration recommendations
        if concentration_risk.get("risk_level") in ["HIGH", "VERY_HIGH"]:
            max_position = concentration_risk.get("max_single_position_pct", 0)
            recommendations["rebalancing"].append(
                f"Reduce largest position from {max_position:.1f}% to under 20%"
            )

        # Position adjustment recommendations
        largest_positions = top_assets.get("largest_positions", [])[:3]
        for position in largest_positions:
            if position.get("allocation_pct", 0) > 25:
                recommendations["position_adjustments"].append(
                    f"Consider reducing {position['asset']} position (currently {position['allocation_pct']:.1f}%)"
                )

        # Performance-based recommendations
        top_performers = top_assets.get("top_performers", [])[:2]
        worst_performers = top_assets.get("worst_performers", [])[:2]

        for performer in top_performers:
            if performer.get("return_pct", 0) > 100:
                recommendations["risk_management"].append(
                    f"Consider taking profits on {performer['asset']} (+{performer['return_pct']:.1f}%)"
                )

        for performer in worst_performers:
            if performer.get("return_pct", 0) < -30:
                recommendations["risk_management"].append(
                    f"Review {performer['asset']} position ({performer['return_pct']:.1f}%) - consider stop-loss"
                )

        # Target risk adjustments
        if target_risk == "low" and current_risk in ["HIGH", "VERY_HIGH"]:
            recommendations["risk_management"].extend(
                [
                    "Reduce position sizes to lower overall portfolio risk",
                    "Focus on major liquid assets (BTC, ETH) for stability",
                    "Implement strict stop-loss levels",
                ]
            )
        elif target_risk == "high" and current_risk in ["LOW", "VERY_LOW"]:
            recommendations["diversification"].extend(
                [
                    "Consider adding exposure to higher-growth altcoins",
                    "Increase position sizes in conviction plays",
                    "Explore emerging sector opportunities",
                ]
            )

        # Diversification recommendations
        total_positions = portfolio_technical.get("total_positions", 0)
        if total_positions < 5:
            recommendations["diversification"].append(
                "Consider adding more positions for better diversification"
            )
        elif total_positions > 15:
            recommendations["diversification"].append(
                "Consider consolidating smaller positions"
            )

        return recommendations

    def _assess_optimization_need(self, portfolio_risk: Dict, target_risk: str) -> bool:
        """Assess if portfolio optimization is needed."""
        current_risk = portfolio_risk.get("overall_risk_score", {}).get(
            "risk_level", "MEDIUM"
        )
        concentration_risk = portfolio_risk.get("concentration_risk", {}).get(
            "risk_level", "LOW"
        )

        # Map target risk to acceptable current risk levels
        risk_mapping = {
            "low": ["LOW", "VERY_LOW"],
            "medium": ["LOW", "MEDIUM", "HIGH"],
            "high": ["MEDIUM", "HIGH", "VERY_HIGH"],
        }

        acceptable_risks = risk_mapping.get(target_risk, ["MEDIUM"])

        # Optimization needed if current risk doesn't match target or concentration is too high
        return current_risk not in acceptable_risks or concentration_risk in [
            "HIGH",
            "VERY_HIGH",
        ]

    def _get_current_holdings(self) -> Dict[str, Any]:
        """Get list of all currently held assets with amounts and values."""
        df = SafeDataFrameOperations.filter_positive_amounts(
            self.portfolio_data, "Actual Amount"
        )

        if df.empty:
            return {"error": "No current holdings found"}

        # Sort by value descending
        df = df.sort_values("Actual Value €", ascending=False)

        holdings = []
        # Use safe float conversion for total value calculation
        from ..utils import safe_float_conversion

        total_value = sum(safe_float_conversion(val) for val in df["Actual Value €"])

        for _, row in df.iterrows():
            # Use safe float conversion to handle formatted currency strings
            from ..utils import safe_float_conversion

            actual_value = safe_float_conversion(row["Actual Value €"])
            allocation_pct = (
                (actual_value / total_value) * 100 if total_value > 0 else 0
            )

            holdings.append(
                {
                    "asset": row["Asset"],
                    "amount": safe_float_conversion(row["Actual Amount"]),
                    "value_eur": actual_value,
                    "allocation_pct": round(allocation_pct, 2),
                    "return_pct": safe_float_conversion(row["Total Return %"]),
                    "unrealised_eur": safe_float_conversion(row["Unrealised €"]),
                    "current_price_eur": safe_float_conversion(row["Current Price €"]),
                }
            )

        return {
            "total_holdings": len(holdings),
            "total_value_eur": safe_float_conversion(total_value),
            "holdings": holdings,
            "note": "These are your current holdings - consider this when making new investment recommendations",
        }

    def _search_crypto_news(self, query: str, focus: str = "news") -> Dict[str, Any]:
        """Search for cryptocurrency news using Perplexity AI."""
        try:
            import os

            import requests

            api_key = os.getenv("PERPLEXITY_API_KEY")
            if not api_key:
                return {"error": "Perplexity API key not configured"}

            # Enhance query based on focus
            focus_prompts = {
                "news": f"Latest news and developments about {query}",
                "analysis": f"Technical and fundamental analysis of {query}",
                "price": f"Price analysis and predictions for {query}",
                "technology": f"Technology and development updates for {query}",
                "adoption": f"Adoption and partnership news for {query}",
            }

            enhanced_query = focus_prompts.get(focus, query)

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            data = {
                "model": os.getenv("PERPLEXITY_MODEL", "sonar-pro"),
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a cryptocurrency research assistant. Provide accurate, up-to-date information with sources.",
                    },
                    {"role": "user", "content": enhanced_query},
                ],
                "max_tokens": int(os.getenv("MAX_TOKENS", "4000")),
                "temperature": float(os.getenv("TEMPERATURE", "0.2")),
            }

            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=data,
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]

                return {
                    "query": query,
                    "focus": focus,
                    "research_results": content,
                    "source": "Perplexity AI",
                    "timestamp": "now",
                }
            else:
                return {"error": f"Perplexity API error: {response.status_code}"}

        except Exception as e:
            return {"error": f"Failed to search crypto news: {str(e)}"}

    def _analyze_market_opportunities(
        self, sector: str = "all", timeframe: str = "medium"
    ) -> Dict[str, Any]:
        """Analyze current market opportunities using web research."""
        try:
            # Create sector-specific search query
            sector_queries = {
                "defi": "DeFi cryptocurrency opportunities 2024 yield farming lending protocols",
                "layer1": "Layer 1 blockchain opportunities Ethereum competitors Solana Avalanche",
                "layer2": "Layer 2 scaling solutions Polygon Arbitrum Optimism opportunities",
                "gaming": "GameFi blockchain gaming tokens metaverse opportunities",
                "ai": "AI cryptocurrency tokens artificial intelligence blockchain opportunities",
                "meme": "Meme coin opportunities viral tokens community driven projects",
                "all": "cryptocurrency market opportunities 2024 trending sectors",
            }

            query = sector_queries.get(sector, sector_queries["all"])

            # Use Perplexity to research opportunities
            research_result = self._search_crypto_news(query, "analysis")

            if "error" in research_result:
                return research_result

            return {
                "sector": sector,
                "timeframe": timeframe,
                "market_analysis": research_result["research_results"],
                "opportunities_identified": True,
                "recommendation": f"Based on current market research for {sector} sector with {timeframe} timeframe",
                "source": "Perplexity AI Market Research",
            }

        except Exception as e:
            return {"error": f"Failed to analyze market opportunities: {str(e)}"}

    def _compare_with_market(
        self, benchmark: str = "total_market", timeframe: str = "30d"
    ) -> Dict[str, Any]:
        """Compare portfolio performance with market benchmarks."""
        try:
            # Get portfolio summary for comparison
            portfolio_summary = self._get_portfolio_summary()

            if "error" in portfolio_summary:
                return portfolio_summary

            # Research benchmark performance
            benchmark_queries = {
                "btc": f"Bitcoin BTC price performance last {timeframe}",
                "eth": f"Ethereum ETH price performance last {timeframe}",
                "total_market": f"Total cryptocurrency market performance last {timeframe}",
                "defi_index": f"DeFi index performance last {timeframe}",
            }

            query = benchmark_queries.get(benchmark, benchmark_queries["total_market"])
            benchmark_research = self._search_crypto_news(query, "analysis")

            portfolio_return = portfolio_summary.get("total_return_percentage", 0)

            return {
                "portfolio_return_pct": portfolio_return,
                "benchmark": benchmark,
                "timeframe": timeframe,
                "benchmark_analysis": benchmark_research.get(
                    "research_results", "No data available"
                ),
                "comparison_summary": f"Your portfolio return: {portfolio_return:.2f}%",
                "relative_performance": (
                    "outperforming" if portfolio_return > 0 else "underperforming"
                ),
                "analysis_timestamp": "now",
            }

        except Exception as e:
            return {"error": f"Failed to compare with market: {str(e)}"}

    def _get_trading_signals(
        self, assets: list = None, strategy: str = "moderate"
    ) -> Dict[str, Any]:
        """Get AI-powered trading signals and recommendations."""
        try:
            if not assets:
                # Get top holdings if no assets specified
                holdings = self._get_current_holdings()
                if "error" in holdings:
                    return holdings
                assets = [h["asset"] for h in holdings["holdings"][:5]]

            signals = []

            for asset in assets:
                # Research current technical analysis for each asset
                query = (
                    f"{asset} technical analysis trading signals {strategy} strategy"
                )
                analysis = self._search_crypto_news(query, "analysis")

                if "error" not in analysis:
                    signals.append(
                        {
                            "asset": asset,
                            "strategy": strategy,
                            "analysis": analysis["research_results"],
                            "signal_strength": "moderate",  # Would be calculated from actual TA
                            "recommendation": "HOLD",  # Would be determined from analysis
                        }
                    )

            return {
                "strategy": strategy,
                "signals_generated": len(signals),
                "trading_signals": signals,
                "disclaimer": "Trading signals are for informational purposes only. Always do your own research.",
                "timestamp": "now",
            }

        except Exception as e:
            return {"error": f"Failed to get trading signals: {str(e)}"}

    def _find_similar_assets(
        self, reference_asset: str, criteria: str = "technology"
    ) -> Dict[str, Any]:
        """Find assets similar to current holdings."""
        try:
            # Check if reference asset is in current holdings
            holdings = self._get_current_holdings()
            current_assets = (
                [h["asset"] for h in holdings.get("holdings", [])]
                if "error" not in holdings
                else []
            )

            # Create search query based on criteria
            criteria_queries = {
                "technology": f"cryptocurrencies similar to {reference_asset} same technology blockchain",
                "market_cap": f"cryptocurrencies similar market cap to {reference_asset}",
                "use_case": f"cryptocurrencies similar use case to {reference_asset}",
                "performance": f"cryptocurrencies similar performance to {reference_asset}",
            }

            query = criteria_queries.get(criteria, criteria_queries["technology"])
            research = self._search_crypto_news(query, "analysis")

            if "error" in research:
                return research

            return {
                "reference_asset": reference_asset,
                "criteria": criteria,
                "currently_held": reference_asset in current_assets,
                "similar_assets_analysis": research["research_results"],
                "recommendation": f"Based on {criteria} similarity to {reference_asset}",
                "note": f"You {'already hold' if reference_asset in current_assets else 'do not currently hold'} {reference_asset}",
                "current_holdings": current_assets,
            }

        except Exception as e:
            return {"error": f"Failed to find similar assets: {str(e)}"}
