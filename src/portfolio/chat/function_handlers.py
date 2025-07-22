"""Function handlers for OpenAI function calling with portfolio data."""

import json
import logging
from typing import Dict, List, Any, Optional
import pandas as pd
from ..ai_explanations import generate_coin_explanation

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
    
    def _define_functions(self) -> List[Dict[str, Any]]:
        """Define available functions for OpenAI function calling."""
        return [
            {
                "name": "get_portfolio_summary",
                "description": "Get overall portfolio summary with total value, P&L, and key metrics",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
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
                            "description": "List of asset symbols (e.g., ['BTC', 'ETH'])"
                        },
                        "sort_by": {
                            "type": "string",
                            "enum": ["return_pct", "value", "unrealised"],
                            "description": "How to sort the results",
                            "default": "return_pct"
                        }
                    },
                    "required": []
                }
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
                            "description": "Whether to get best or worst performers"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of assets to return",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 20
                        }
                    },
                    "required": ["type"]
                }
            },
            {
                "name": "explain_coin_position",
                "description": "Get detailed natural language explanation of a specific coin position",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "asset": {
                            "type": "string",
                            "description": "Asset symbol (e.g., 'BTC', 'ETH')"
                        }
                    },
                    "required": ["asset"]
                }
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
                            "default": 1.0
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_transfer_analysis",
                "description": "Get deposit/withdrawal and transfer analysis",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "asset": {
                            "type": "string",
                            "description": "Specific asset symbol or 'all' for all assets"
                        }
                    },
                    "required": []
                }
            }
        ]
    
    def handle_function_call(self, function_name: str, arguments: str) -> str:
        """Handle a function call and return the result.
        
        Args:
            function_name: Name of the function to call
            arguments: JSON string of function arguments
            
        Returns:
            JSON string containing the function result
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
            else:
                result = {"error": f"Unknown function: {function_name}"}
            
            return json.dumps(result, default=str)
            
        except Exception as e:
            logger.error(f"Error handling function call {function_name}: {e}")
            return json.dumps({"error": f"Function call failed: {str(e)}"})
    
    def _get_portfolio_summary(self) -> Dict[str, Any]:
        """Get overall portfolio summary."""
        if self.portfolio_data.empty:
            return {"error": "No portfolio data available"}
        
        total_cost = self.portfolio_data["Cost €"].sum()
        total_actual_value = self.portfolio_data["Actual Value €"].sum()
        total_realised = self.portfolio_data["Realised €"].sum()
        total_unrealised = self.portfolio_data["Unrealised €"].sum()
        
        # Calculate total return
        total_invested = total_cost + abs(total_realised)
        total_return_pct = ((total_actual_value + total_realised) - total_invested) / total_invested * 100 if total_invested > 0 else 0
        
        # Count positions
        profitable_positions = len(self.portfolio_data[self.portfolio_data["Total Return %"] > 0])
        total_positions = len(self.portfolio_data[self.portfolio_data["Actual Amount"] > 0])
        
        return {
            "total_value_eur": round(total_actual_value, 2),
            "total_cost_eur": round(total_cost, 2),
            "total_invested_eur": round(total_invested, 2),
            "total_realised_eur": round(total_realised, 2),
            "total_unrealised_eur": round(total_unrealised, 2),
            "total_return_pct": round(total_return_pct, 2),
            "profitable_positions": profitable_positions,
            "total_positions": total_positions,
            "profitability_rate": round(profitable_positions / total_positions * 100, 1) if total_positions > 0 else 0
        }
    
    def _get_asset_performance(self, assets: Optional[List[str]] = None, sort_by: str = "return_pct") -> Dict[str, Any]:
        """Get performance data for specific assets."""
        df = self.portfolio_data.copy()
        
        # Filter by assets if specified
        if assets:
            df = df[df["Asset"].isin(assets)]
        
        # Filter out zero positions
        df = df[df["Actual Amount"] > 0]
        
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
            results.append({
                "asset": row["Asset"],
                "actual_amount": round(row["Actual Amount"], 6),
                "actual_value_eur": round(row["Actual Value €"], 2),
                "cost_eur": round(row["Cost €"], 2),
                "unrealised_eur": round(row["Unrealised €"], 2),
                "total_return_pct": round(row["Total Return %"], 2),
                "current_price_eur": round(row["Current Price €"], 2)
            })
        
        return {"assets": results}
    
    def _get_top_performers(self, type: str, limit: int = 5) -> Dict[str, Any]:
        """Get top or worst performing assets."""
        df = self.portfolio_data[self.portfolio_data["Actual Amount"] > 0].copy()
        
        if df.empty:
            return {"error": "No positions found"}
        
        # Sort by return percentage
        ascending = (type == "worst")
        df = df.sort_values("Total Return %", ascending=ascending).head(limit)
        
        results = []
        for _, row in df.iterrows():
            results.append({
                "asset": row["Asset"],
                "return_pct": round(row["Total Return %"], 2),
                "unrealised_eur": round(row["Unrealised €"], 2),
                "actual_value_eur": round(row["Actual Value €"], 2)
            })
        
        return {
            "type": type,
            "performers": results
        }
    
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
                "total_return_pct": round(asset_data["Total Return %"], 2)
            }
        }
    
    def _get_portfolio_allocation(self, min_percentage: float = 1.0) -> Dict[str, Any]:
        """Get portfolio allocation by value."""
        df = self.portfolio_data[self.portfolio_data["Actual Value €"] > 0].copy()
        
        if df.empty:
            return {"error": "No positions found"}
        
        total_value = df["Actual Value €"].sum()
        df["allocation_pct"] = (df["Actual Value €"] / total_value * 100)
        
        # Filter by minimum percentage
        df = df[df["allocation_pct"] >= min_percentage]
        df = df.sort_values("allocation_pct", ascending=False)
        
        allocations = []
        for _, row in df.iterrows():
            allocations.append({
                "asset": row["Asset"],
                "value_eur": round(row["Actual Value €"], 2),
                "allocation_pct": round(row["allocation_pct"], 2)
            })
        
        return {
            "total_value_eur": round(total_value, 2),
            "allocations": allocations
        }
    
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
            transfers.append({
                "asset": row["Asset"],
                "net_transfers": round(row["Net Transfers"], 6),
                "total_deposits": round(row["Total Deposits"], 6),
                "total_withdrawals": round(row["Total Withdrawals"], 6),
                "deposit_count": int(row["Deposit Count"]),
                "withdrawal_count": int(row["Withdrawal Count"])
            })
        
        return {"transfers": transfers}

    def get_available_functions(self) -> List[Dict[str, Any]]:
        """Get list of available functions for OpenAI."""
        return self.functions
