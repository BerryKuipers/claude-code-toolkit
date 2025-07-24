"""Utility functions for safe DataFrame operations with formatted currency data."""

from typing import Any, Dict, List

import pandas as pd

from ..utils import safe_float_conversion


class SafeDataFrameOperations:
    """Utility class for safe DataFrame operations that handle formatted currency strings."""

    @staticmethod
    def filter_positive_amounts(df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Filter DataFrame to only include rows with positive amounts in the specified column.

        Args:
            df: DataFrame to filter
            column: Column name to check for positive values

        Returns:
            Filtered DataFrame
        """

        def has_positive_value(x):
            return safe_float_conversion(x) > 0

        return df[df[column].apply(has_positive_value)].copy()

    @staticmethod
    def safe_sum(df: pd.DataFrame, column: str) -> float:
        """Safely sum a column that may contain formatted currency strings.

        Args:
            df: DataFrame containing the column
            column: Column name to sum

        Returns:
            Sum as float
        """
        return sum(safe_float_conversion(val) for val in df[column])

    @staticmethod
    def count_positive_values(df: pd.DataFrame, column: str) -> int:
        """Count rows with positive values in the specified column.

        Args:
            df: DataFrame to analyze
            column: Column name to check

        Returns:
            Count of positive values
        """
        count = 0
        for _, row in df.iterrows():
            if safe_float_conversion(row[column]) > 0:
                count += 1
        return count

    @staticmethod
    def safe_sort(
        df: pd.DataFrame, column: str, ascending: bool = True
    ) -> pd.DataFrame:
        """Safely sort DataFrame by a column that may contain formatted strings.

        Args:
            df: DataFrame to sort
            column: Column name to sort by
            ascending: Sort order

        Returns:
            Sorted DataFrame
        """
        # Create a temporary column with converted values for sorting
        temp_col = f"_temp_sort_{column}"
        df_copy = df.copy()
        df_copy[temp_col] = df_copy[column].apply(safe_float_conversion)
        sorted_df = df_copy.sort_values(temp_col, ascending=ascending)
        return sorted_df.drop(columns=[temp_col])

    @staticmethod
    def create_safe_holding_dict(row: pd.Series) -> Dict[str, Any]:
        """Create a holding dictionary with safe float conversions.

        Args:
            row: DataFrame row containing holding data

        Returns:
            Dictionary with safely converted values
        """
        return {
            "asset": row["Asset"],
            "amount": safe_float_conversion(row["Actual Amount"]),
            "value_eur": safe_float_conversion(row["Actual Value €"]),
            "cost_eur": safe_float_conversion(row["Cost €"]),
            "unrealised_eur": safe_float_conversion(row["Unrealised €"]),
            "total_return_pct": safe_float_conversion(row["Total Return %"]),
            "current_price_eur": safe_float_conversion(row["Current Price €"]),
        }

    @staticmethod
    def calculate_portfolio_totals(df: pd.DataFrame) -> Dict[str, float]:
        """Calculate portfolio totals with safe conversions.

        Args:
            df: Portfolio DataFrame

        Returns:
            Dictionary with portfolio totals
        """
        return {
            "total_cost": SafeDataFrameOperations.safe_sum(df, "Cost €"),
            "total_actual_value": SafeDataFrameOperations.safe_sum(
                df, "Actual Value €"
            ),
            "total_realised": SafeDataFrameOperations.safe_sum(df, "Realised €"),
            "total_unrealised": SafeDataFrameOperations.safe_sum(df, "Unrealised €"),
            "total_invested": (
                SafeDataFrameOperations.safe_sum(df, "Total Invested €")
                if "Total Invested €" in df.columns
                else SafeDataFrameOperations.safe_sum(df, "Cost €")
            ),
        }

    @staticmethod
    def count_profitable_positions(df: pd.DataFrame) -> tuple[int, int]:
        """Count profitable and total positions.

        Args:
            df: Portfolio DataFrame

        Returns:
            Tuple of (profitable_positions, total_positions)
        """
        profitable_positions = 0
        total_positions = 0

        for _, row in df.iterrows():
            actual_amount = safe_float_conversion(row["Actual Amount"])
            if actual_amount > 0:
                total_positions += 1
                total_return_pct = safe_float_conversion(row["Total Return %"])
                if total_return_pct > 0:
                    profitable_positions += 1

        return profitable_positions, total_positions
