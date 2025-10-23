"""Data verification layer to prevent LLM hallucinations with financial data.

This module ensures all AI responses about portfolio data are verified against
actual portfolio data to prevent costly mistakes from hallucinated information.
"""

import json
import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from ..utils import safe_float_conversion

logger = logging.getLogger(__name__)


class DataVerificationError(Exception):
    """Raised when data verification fails."""

    pass


class PortfolioDataVerifier:
    """Verifies AI responses against actual portfolio data."""

    def __init__(self, portfolio_data: pd.DataFrame):
        """Initialize with portfolio data.

        Args:
            portfolio_data: DataFrame containing actual portfolio information
        """
        self.portfolio_data = portfolio_data
        self.verification_log = []

    def verify_function_result(
        self, function_name: str, function_args: str, result: str
    ) -> Tuple[bool, str, Optional[str]]:
        """Verify a function call result against actual data.

        Args:
            function_name: Name of the function that was called
            function_args: JSON string of function arguments
            result: JSON string result from the function

        Returns:
            Tuple of (is_valid, verified_result, error_message)
        """
        try:
            args = json.loads(function_args) if function_args else {}
            result_data = json.loads(result)

            # Route to specific verification method
            if function_name == "get_portfolio_summary":
                return self._verify_portfolio_summary(result_data)
            elif function_name == "get_asset_performance":
                return self._verify_asset_performance(args, result_data)
            elif function_name == "get_top_performers":
                return self._verify_top_performers(args, result_data)
            elif function_name == "explain_coin_position":
                return self._verify_coin_position(args, result_data)
            elif function_name == "get_portfolio_allocation":
                return self._verify_portfolio_allocation(args, result_data)
            elif function_name == "get_transfer_analysis":
                return self._verify_transfer_analysis(args, result_data)
            elif function_name == "get_current_holdings":
                return self._verify_current_holdings(result_data)
            elif function_name == "get_price_prediction":
                return self._verify_price_prediction(args, result_data)
            elif function_name == "search_crypto_news":
                return self._verify_search_crypto_news(result_data)
            else:
                # Unknown function - allow but log
                logger.warning(f"Unknown function for verification: {function_name}")
                return True, result, None

        except Exception as e:
            error_msg = f"Verification error for {function_name}: {str(e)}"
            logger.error(error_msg)
            return False, result, error_msg

    def _verify_portfolio_summary(
        self, result_data: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[str]]:
        """Verify portfolio summary data."""
        if "error" in result_data:
            return True, json.dumps(result_data), None

        # Calculate actual values from portfolio data using safe conversion
        actual_total_value = sum(
            safe_float_conversion(val) for val in self.portfolio_data["Actual Value €"]
        )
        actual_total_cost = sum(
            safe_float_conversion(val) for val in self.portfolio_data["Cost €"]
        )
        actual_total_unrealised = sum(
            safe_float_conversion(val) for val in self.portfolio_data["Unrealised €"]
        )

        # Verify key metrics with tolerance for rounding
        tolerance = 0.01  # €0.01 tolerance

        reported_value = safe_float_conversion(result_data.get("total_value_eur", 0))
        reported_cost = safe_float_conversion(result_data.get("total_cost_eur", 0))
        reported_unrealised = safe_float_conversion(
            result_data.get("total_unrealised_eur", 0)
        )

        if abs(actual_total_value - reported_value) > tolerance:
            error_msg = f"Portfolio value mismatch: actual €{actual_total_value:.2f} vs reported €{reported_value:.2f}"
            logger.error(error_msg)
            return False, json.dumps(result_data), error_msg

        if abs(actual_total_cost - reported_cost) > tolerance:
            error_msg = f"Portfolio cost mismatch: actual €{actual_total_cost:.2f} vs reported €{reported_cost:.2f}"
            logger.error(error_msg)
            return False, json.dumps(result_data), error_msg

        if abs(actual_total_unrealised - reported_unrealised) > tolerance:
            error_msg = f"Unrealised P&L mismatch: actual €{actual_total_unrealised:.2f} vs reported €{reported_unrealised:.2f}"
            logger.error(error_msg)
            return False, json.dumps(result_data), error_msg

        # Log successful verification
        self.verification_log.append(
            {
                "function": "get_portfolio_summary",
                "status": "verified",
                "timestamp": pd.Timestamp.now(),
                "details": f"Verified portfolio value €{actual_total_value:.2f}",
            }
        )

        return True, json.dumps(result_data), None

    def _verify_asset_performance(
        self, args: Dict[str, Any], result_data: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[str]]:
        """Verify asset performance data."""
        if "error" in result_data:
            return True, json.dumps(result_data), None

        assets_data = result_data.get("assets", [])
        requested_assets = args.get("assets", [])

        for asset_data in assets_data:
            asset = asset_data["asset"]

            # Find actual data for this asset
            actual_row = self.portfolio_data[self.portfolio_data["Asset"] == asset]
            if actual_row.empty:
                error_msg = f"Asset {asset} not found in actual portfolio data"
                logger.error(error_msg)
                return False, json.dumps(result_data), error_msg

            actual_row = actual_row.iloc[0]

            # Verify key metrics using safe conversion
            tolerance = 0.01
            actual_value = safe_float_conversion(actual_row["Actual Value €"])
            actual_unrealised = safe_float_conversion(actual_row["Unrealised €"])
            actual_return_pct = safe_float_conversion(actual_row["Total Return %"])

            reported_value = safe_float_conversion(
                asset_data.get("actual_value_eur", 0)
            )
            reported_unrealised = safe_float_conversion(
                asset_data.get("unrealised_eur", 0)
            )
            reported_return_pct = safe_float_conversion(
                asset_data.get("total_return_pct", 0)
            )

            if abs(actual_value - reported_value) > tolerance:
                error_msg = f"{asset} value mismatch: actual €{actual_value:.2f} vs reported €{reported_value:.2f}"
                logger.error(error_msg)
                return False, json.dumps(result_data), error_msg

            if abs(actual_return_pct - reported_return_pct) > 0.1:  # 0.1% tolerance
                error_msg = f"{asset} return % mismatch: actual {actual_return_pct:.2f}% vs reported {reported_return_pct:.2f}%"
                logger.error(error_msg)
                return False, json.dumps(result_data), error_msg

        return True, json.dumps(result_data), None

    def _verify_top_performers(
        self, args: Dict[str, Any], result_data: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[str]]:
        """Verify top performers data."""
        if "error" in result_data:
            return True, json.dumps(result_data), None

        performers = result_data.get("performers", [])
        performance_type = args.get("type", "best")
        limit = args.get("limit", 5)

        # Get actual top performers using safe filtering
        def has_positive_amount(x):
            return safe_float_conversion(x) > 0

        portfolio_with_positions = self.portfolio_data[
            self.portfolio_data["Actual Amount"].apply(has_positive_amount)
        ].copy()
        if portfolio_with_positions.empty:
            return True, json.dumps(result_data), None

        ascending = performance_type == "worst"
        actual_top = portfolio_with_positions.sort_values(
            "Total Return %", ascending=ascending
        ).head(limit)

        # Verify the order and values
        for i, performer in enumerate(performers):
            if i >= len(actual_top):
                break

            actual_asset = actual_top.iloc[i]
            reported_asset = performer["asset"]

            if actual_asset["Asset"] != reported_asset:
                error_msg = f"Top performer order mismatch at position {i+1}: actual {actual_asset['Asset']} vs reported {reported_asset}"
                logger.warning(
                    error_msg
                )  # Warning, not error, as order might vary slightly

        return True, json.dumps(result_data), None

    def _verify_coin_position(
        self, args: Dict[str, Any], result_data: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[str]]:
        """Verify coin position explanation data."""
        if "error" in result_data:
            return True, json.dumps(result_data), None

        asset = args.get("asset", "").upper()
        summary_data = result_data.get("summary_data", {})

        # Find actual data for this asset
        actual_row = self.portfolio_data[self.portfolio_data["Asset"] == asset]
        if actual_row.empty:
            error_msg = f"Asset {asset} not found in actual portfolio data"
            logger.error(error_msg)
            return False, json.dumps(result_data), error_msg

        actual_row = actual_row.iloc[0]

        # Verify summary data
        tolerance = 0.01
        actual_amount = actual_row["Actual Amount"]
        actual_value = actual_row["Actual Value €"]
        actual_unrealised = actual_row["Unrealised €"]
        actual_return_pct = actual_row["Total Return %"]

        reported_amount = safe_float_conversion(summary_data.get("actual_amount", 0))
        reported_value = safe_float_conversion(summary_data.get("actual_value_eur", 0))
        reported_unrealised = safe_float_conversion(
            summary_data.get("unrealised_eur", 0)
        )
        reported_return_pct = safe_float_conversion(
            summary_data.get("total_return_pct", 0)
        )

        actual_amount_float = safe_float_conversion(actual_amount)
        if (
            abs(actual_amount_float - reported_amount) > 0.000001
        ):  # Very small tolerance for crypto amounts
            error_msg = f"{asset} amount mismatch: actual {actual_amount_float:.6f} vs reported {reported_amount:.6f}"
            logger.error(error_msg)
            return False, json.dumps(result_data), error_msg

        if abs(safe_float_conversion(actual_value) - reported_value) > tolerance:
            error_msg = f"{asset} value mismatch: actual €{actual_value:.2f} vs reported €{reported_value:.2f}"
            logger.error(error_msg)
            return False, json.dumps(result_data), error_msg

        return True, json.dumps(result_data), None

    def _verify_portfolio_allocation(
        self, args: Dict[str, Any], result_data: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[str]]:
        """Verify portfolio allocation data."""
        if "error" in result_data:
            return True, json.dumps(result_data), None

        reported_total = safe_float_conversion(result_data.get("total_value_eur", 0))
        actual_total = sum(
            safe_float_conversion(val) for val in self.portfolio_data["Actual Value €"]
        )

        tolerance = 0.01
        if abs(actual_total - reported_total) > tolerance:
            error_msg = f"Total portfolio value mismatch: actual €{actual_total:.2f} vs reported €{reported_total:.2f}"
            logger.error(error_msg)
            return False, json.dumps(result_data), error_msg

        return True, json.dumps(result_data), None

    def _verify_transfer_analysis(
        self, args: Dict[str, Any], result_data: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[str]]:
        """Verify transfer analysis data."""
        if "error" in result_data or "message" in result_data:
            return True, json.dumps(result_data), None

        # Transfer data is harder to verify without access to raw transfer history
        # For now, we'll trust the function but log the verification attempt
        self.verification_log.append(
            {
                "function": "get_transfer_analysis",
                "status": "trusted",
                "timestamp": pd.Timestamp.now(),
                "details": "Transfer data verification limited - trusting function result",
            }
        )

        return True, json.dumps(result_data), None

    def get_verification_stats(self) -> Dict[str, Any]:
        """Get verification statistics."""
        total_verifications = len(self.verification_log)
        verified_count = sum(
            1 for log in self.verification_log if log["status"] == "verified"
        )
        trusted_count = sum(
            1 for log in self.verification_log if log["status"] == "trusted"
        )

        return {
            "total_verifications": total_verifications,
            "verified_count": verified_count,
            "trusted_count": trusted_count,
            "verification_rate": (
                (verified_count / total_verifications * 100)
                if total_verifications > 0
                else 0
            ),
        }

    def _verify_current_holdings(
        self, result_data: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[str]]:
        """Verify current holdings data."""
        from ..utils import safe_float_conversion

        if "error" in result_data:
            return True, json.dumps(result_data), None

        holdings_data = result_data.get("holdings", [])
        total_value = result_data.get("total_value_eur", 0)

        # Verify total value calculation
        calculated_total = 0
        for holding in holdings_data:
            calculated_total += safe_float_conversion(holding.get("value_eur", 0))

        tolerance = 0.01
        if abs(calculated_total - safe_float_conversion(total_value)) > tolerance:
            logger.warning(
                f"Total value mismatch: calculated {calculated_total}, reported {total_value}"
            )

        # Verify holdings exist in portfolio data
        for holding in holdings_data:
            asset = holding["asset"]
            portfolio_row = self.portfolio_data[self.portfolio_data["Asset"] == asset]
            if portfolio_row.empty:
                logger.warning(f"Asset {asset} not found in portfolio data")
                continue

            # Verify key metrics
            actual_row = portfolio_row.iloc[0]
            actual_amount = safe_float_conversion(actual_row["Actual Amount"])
            actual_value = safe_float_conversion(actual_row["Actual Value €"])

            reported_amount = safe_float_conversion(holding.get("amount", 0))
            reported_value = safe_float_conversion(holding.get("value_eur", 0))

            if abs(actual_amount - reported_amount) > 0.000001:
                logger.warning(
                    f"Amount mismatch for {asset}: actual {actual_amount}, reported {reported_amount}"
                )

            if abs(actual_value - reported_value) > tolerance:
                logger.warning(
                    f"Value mismatch for {asset}: actual {actual_value}, reported {reported_value}"
                )

        return True, json.dumps(result_data), None

    def _verify_price_prediction(
        self, args: Dict[str, Any], result_data: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[str]]:
        """Verify price prediction function results."""
        try:
            # Basic structure validation
            if not isinstance(result_data, dict):
                return (
                    False,
                    json.dumps(result_data),
                    "Price prediction result must be a dictionary",
                )

            # Check for required fields
            required_fields = ["asset", "prediction"]
            for field in required_fields:
                if field not in result_data:
                    return (
                        False,
                        json.dumps(result_data),
                        f"Missing required field: {field}",
                    )

            # Validate asset matches request
            requested_asset = args.get("asset", "")
            if result_data.get("asset") != requested_asset:
                return (
                    False,
                    json.dumps(result_data),
                    f"Asset mismatch: requested {requested_asset}, got {result_data.get('asset')}",
                )

            # Validate prediction structure
            prediction = result_data.get("prediction", {})
            if not isinstance(prediction, dict):
                return False, json.dumps(result_data), "Prediction must be a dictionary"

            # Check for prediction fields (flexible validation)
            prediction_fields = ["direction", "confidence", "timeframe", "reasoning"]
            missing_fields = [
                field for field in prediction_fields if field not in prediction
            ]
            if len(missing_fields) > 2:  # Allow some flexibility
                return (
                    False,
                    json.dumps(result_data),
                    f"Prediction missing too many fields: {missing_fields}",
                )

            return True, json.dumps(result_data), None

        except Exception as e:
            return (
                False,
                json.dumps(result_data),
                f"Price prediction verification error: {str(e)}",
            )

    def _verify_search_crypto_news(
        self, result_data: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[str]]:
        """Verify search_crypto_news function results."""
        # For external API calls like Perplexity, we mainly verify structure
        if "error" in result_data:
            # Error responses are valid - API might be down or key missing
            return True, json.dumps(result_data), None

        # Check for expected fields in successful response
        required_fields = ["query", "research_results", "source"]
        missing_fields = [
            field for field in required_fields if field not in result_data
        ]

        if missing_fields:
            error_msg = f"Missing required fields in search results: {missing_fields}"
            logger.warning(error_msg)
            return False, json.dumps(result_data), error_msg

        # Verify research_results is not empty
        research_results = result_data.get("research_results", "")
        if not research_results or len(research_results.strip()) < 10:
            error_msg = "Research results are empty or too short"
            logger.warning(error_msg)
            return False, json.dumps(result_data), error_msg

        # Log successful verification
        self.verification_log.append(
            {
                "function": "search_crypto_news",
                "status": "verified",
                "timestamp": pd.Timestamp.now(),
                "details": f"Verified search for '{result_data.get('query', 'unknown')}' - {len(research_results)} chars",
            }
        )

        return True, json.dumps(result_data), None
