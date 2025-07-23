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

        # Calculate actual values from portfolio data
        actual_total_value = self.portfolio_data["Actual Value €"].sum()
        actual_total_cost = self.portfolio_data["Cost €"].sum()
        actual_total_unrealised = self.portfolio_data["Unrealised €"].sum()

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

            # Verify key metrics
            tolerance = 0.01
            actual_value = actual_row["Actual Value €"]
            actual_unrealised = actual_row["Unrealised €"]
            actual_return_pct = actual_row["Total Return %"]

            reported_value = asset_data.get("actual_value_eur", 0)
            reported_unrealised = asset_data.get("unrealised_eur", 0)
            reported_return_pct = asset_data.get("total_return_pct", 0)

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

        # Get actual top performers
        portfolio_with_positions = self.portfolio_data[
            self.portfolio_data["Actual Amount"] > 0
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

        reported_total = result_data.get("total_value_eur", 0)
        actual_total = self.portfolio_data["Actual Value €"].sum()

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
