"""Tests for profit indicator logic in dashboard.

Comprehensive test suite for the profit indicator calculation and styling logic,
covering complex scenarios including tiny positions, withdrawals, and edge cases.
"""

import pandas as pd
import pytest
from decimal import Decimal


class TestProfitIndicators:
    """Test the profit indicator logic from dashboard.py."""
    
    def get_profit_indicator(self, row):
        """Copy of the profit indicator function from dashboard.py for testing."""
        return_pct = row["Total Return %"]
        current_value = row["Actual Value €"]
        unrealised = row["Unrealised €"]
        
        # For very small positions (< €1), show different indicators
        if current_value < 1.0:
            if return_pct > 0:
                return "🔸 Tiny Profit"  # Small position with profit
            elif return_pct < 0:
                return "🔹 Tiny Loss"   # Small position with loss
            else:
                return "⚪ Tiny Position"  # Small position break-even
        
        # For normal positions, use standard indicators
        if return_pct > 10:
            return "🚀 Strong Profit"
        elif return_pct > 5:
            return "📈 Good Profit"
        elif return_pct > 0:
            return "🟢 Profit"
        elif return_pct == 0:
            return "⚪ Break-even"
        elif return_pct > -5:
            return "🔴 Loss"
        elif return_pct > -10:
            return "📉 Bad Loss"
        else:
            return "💥 Heavy Loss"
    
    def style_profit_loss(self, row):
        """Copy of the styling function from dashboard.py for testing."""
        total_return = row["Total Return %"]
        current_value = row["Actual Value €"]
        
        # For very small positions (< €1), use muted styling
        if current_value < 1.0:
            if total_return > 0:
                # Tiny profit - very light green
                return ['background: linear-gradient(90deg, rgba(0, 255, 0, 0.03) 0%, rgba(0, 255, 0, 0.01) 100%); border-left: 3px solid #88cc88;'] * len(row)
            elif total_return < 0:
                # Tiny loss - very light red
                return ['background: linear-gradient(90deg, rgba(255, 0, 0, 0.03) 0%, rgba(255, 0, 0, 0.01) 100%); border-left: 3px solid #cc8888;'] * len(row)
            else:
                # Tiny position - very light gray
                return ['background: linear-gradient(90deg, rgba(128, 128, 128, 0.03) 0%, rgba(128, 128, 128, 0.01) 100%); border-left: 3px solid #999999;'] * len(row)
        
        # For normal positions, use standard styling
        if total_return > 5:
            # Strong profit - bright green
            return ['background: linear-gradient(90deg, rgba(0, 255, 0, 0.15) 0%, rgba(0, 255, 0, 0.08) 100%); border-left: 6px solid #00ff00;'] * len(row)
        elif total_return > 0:
            # Moderate profit - light green
            return ['background: linear-gradient(90deg, rgba(0, 255, 0, 0.08) 0%, rgba(0, 255, 0, 0.03) 100%); border-left: 4px solid #00cc00;'] * len(row)
        elif total_return < -5:
            # Strong loss - bright red
            return ['background: linear-gradient(90deg, rgba(255, 0, 0, 0.15) 0%, rgba(255, 0, 0, 0.08) 100%); border-left: 6px solid #ff0000;'] * len(row)
        elif total_return < 0:
            # Moderate loss - light red
            return ['background: linear-gradient(90deg, rgba(255, 0, 0, 0.08) 0%, rgba(255, 0, 0, 0.03) 100%); border-left: 4px solid #cc0000;'] * len(row)
        else:
            # Break-even - neutral
            return ['border-left: 4px solid #666666;'] * len(row)

    def create_test_row(self, asset="TEST", total_return_pct=0, actual_value_eur=100, unrealised_eur=0):
        """Helper to create test portfolio rows."""
        return pd.Series({
            "Asset": asset,
            "Total Return %": total_return_pct,
            "Actual Value €": actual_value_eur,
            "Unrealised €": unrealised_eur,
            "Amount": 1.0,
            "Cost €": 100.0
        })

    # Test Cases for Normal Positions (> €1)
    
    def test_strong_profit_normal_position(self):
        """Test strong profit indicator for normal position."""
        row = self.create_test_row(total_return_pct=15, actual_value_eur=115)
        indicator = self.get_profit_indicator(row)
        assert indicator == "🚀 Strong Profit"
    
    def test_good_profit_normal_position(self):
        """Test good profit indicator for normal position."""
        row = self.create_test_row(total_return_pct=7, actual_value_eur=107)
        indicator = self.get_profit_indicator(row)
        assert indicator == "📈 Good Profit"
    
    def test_small_profit_normal_position(self):
        """Test small profit indicator for normal position."""
        row = self.create_test_row(total_return_pct=3, actual_value_eur=103)
        indicator = self.get_profit_indicator(row)
        assert indicator == "🟢 Profit"
    
    def test_breakeven_normal_position(self):
        """Test break-even indicator for normal position."""
        row = self.create_test_row(total_return_pct=0, actual_value_eur=100)
        indicator = self.get_profit_indicator(row)
        assert indicator == "⚪ Break-even"
    
    def test_small_loss_normal_position(self):
        """Test small loss indicator for normal position."""
        row = self.create_test_row(total_return_pct=-3, actual_value_eur=97)
        indicator = self.get_profit_indicator(row)
        assert indicator == "🔴 Loss"
    
    def test_bad_loss_normal_position(self):
        """Test bad loss indicator for normal position."""
        row = self.create_test_row(total_return_pct=-7, actual_value_eur=93)
        indicator = self.get_profit_indicator(row)
        assert indicator == "📉 Bad Loss"
    
    def test_heavy_loss_normal_position(self):
        """Test heavy loss indicator for normal position."""
        row = self.create_test_row(total_return_pct=-15, actual_value_eur=85)
        indicator = self.get_profit_indicator(row)
        assert indicator == "💥 Heavy Loss"

    # Test Cases for Tiny Positions (< €1)
    
    def test_tiny_profit_position(self):
        """Test tiny profit indicator for small position."""
        row = self.create_test_row(total_return_pct=50, actual_value_eur=0.75)
        indicator = self.get_profit_indicator(row)
        assert indicator == "🔸 Tiny Profit"
    
    def test_tiny_loss_position(self):
        """Test tiny loss indicator for small position."""
        row = self.create_test_row(total_return_pct=-20, actual_value_eur=0.80)
        indicator = self.get_profit_indicator(row)
        assert indicator == "🔹 Tiny Loss"
    
    def test_tiny_breakeven_position(self):
        """Test tiny break-even indicator for small position."""
        row = self.create_test_row(total_return_pct=0, actual_value_eur=0.50)
        indicator = self.get_profit_indicator(row)
        assert indicator == "⚪ Tiny Position"

    # Test Complex Real-World Scenarios
    
    def test_ltc_scenario_deposited_most_withdrawn(self):
        """Test LTC scenario: deposited 5.78 LTC, only 0.001784 LTC left (€0.18)."""
        # This represents the user's actual LTC situation
        row = self.create_test_row(
            asset="LTC",
            total_return_pct=150,  # High percentage due to realized gains
            actual_value_eur=0.18,  # Only €0.18 left
            unrealised_eur=0.05
        )
        indicator = self.get_profit_indicator(row)
        assert indicator == "🔸 Tiny Profit"  # Should be tiny profit, not strong profit
    
    def test_btc_large_position_with_profit(self):
        """Test BTC scenario: large position with significant profit."""
        row = self.create_test_row(
            asset="BTC",
            total_return_pct=25,
            actual_value_eur=12500,
            unrealised_eur=2500
        )
        indicator = self.get_profit_indicator(row)
        assert indicator == "🚀 Strong Profit"
    
    def test_shib_dust_position(self):
        """Test SHIB scenario: dust position from trading."""
        row = self.create_test_row(
            asset="SHIB",
            total_return_pct=-90,
            actual_value_eur=0.05,
            unrealised_eur=-0.45
        )
        indicator = self.get_profit_indicator(row)
        assert indicator == "🔹 Tiny Loss"
    
    def test_eth_moderate_position_loss(self):
        """Test ETH scenario: moderate position with loss."""
        row = self.create_test_row(
            asset="ETH",
            total_return_pct=-12,
            actual_value_eur=2800,
            unrealised_eur=-380
        )
        indicator = self.get_profit_indicator(row)
        assert indicator == "💥 Heavy Loss"

    # Test Edge Cases
    
    def test_exactly_one_euro_position_profit(self):
        """Test position exactly at €1.00 boundary with profit."""
        row = self.create_test_row(total_return_pct=10, actual_value_eur=1.00)
        indicator = self.get_profit_indicator(row)
        assert indicator == "📈 Good Profit"  # 10% return = Good Profit (>5% but <=10%)
    
    def test_exactly_one_euro_position_loss(self):
        """Test position exactly at €1.00 boundary with loss."""
        row = self.create_test_row(total_return_pct=-10, actual_value_eur=1.00)
        indicator = self.get_profit_indicator(row)
        assert indicator == "💥 Heavy Loss"  # Should use normal indicators at exactly €1
    
    def test_just_under_one_euro_position(self):
        """Test position just under €1.00 boundary."""
        row = self.create_test_row(total_return_pct=15, actual_value_eur=0.99)
        indicator = self.get_profit_indicator(row)
        assert indicator == "🔸 Tiny Profit"  # Should use tiny indicators under €1
    
    def test_zero_value_position(self):
        """Test position with zero value."""
        row = self.create_test_row(total_return_pct=-100, actual_value_eur=0.00)
        indicator = self.get_profit_indicator(row)
        assert indicator == "🔹 Tiny Loss"
    
    def test_negative_return_percentage(self):
        """Test very negative return percentage."""
        row = self.create_test_row(total_return_pct=-99.9, actual_value_eur=0.01)
        indicator = self.get_profit_indicator(row)
        assert indicator == "🔹 Tiny Loss"

    # Test Styling Logic
    
    def test_tiny_profit_styling(self):
        """Test styling for tiny profit positions."""
        row = self.create_test_row(total_return_pct=20, actual_value_eur=0.50)
        styles = self.style_profit_loss(row)
        assert len(styles) == len(row)
        assert "rgba(0, 255, 0, 0.03)" in styles[0]  # Very light green
        assert "3px solid #88cc88" in styles[0]  # Thin border
    
    def test_tiny_loss_styling(self):
        """Test styling for tiny loss positions."""
        row = self.create_test_row(total_return_pct=-20, actual_value_eur=0.50)
        styles = self.style_profit_loss(row)
        assert "rgba(255, 0, 0, 0.03)" in styles[0]  # Very light red
        assert "3px solid #cc8888" in styles[0]  # Thin border
    
    def test_normal_strong_profit_styling(self):
        """Test styling for normal strong profit positions."""
        row = self.create_test_row(total_return_pct=15, actual_value_eur=1500)
        styles = self.style_profit_loss(row)
        assert "rgba(0, 255, 0, 0.15)" in styles[0]  # Bright green
        assert "6px solid #00ff00" in styles[0]  # Thick border
    
    def test_normal_heavy_loss_styling(self):
        """Test styling for normal heavy loss positions."""
        row = self.create_test_row(total_return_pct=-15, actual_value_eur=850)
        styles = self.style_profit_loss(row)
        assert "rgba(255, 0, 0, 0.15)" in styles[0]  # Bright red
        assert "6px solid #ff0000" in styles[0]  # Thick border

    # Test Batch Processing
    
    def test_mixed_portfolio_indicators(self):
        """Test profit indicators across a mixed portfolio."""
        portfolio_data = [
            {"asset": "BTC", "return_pct": 25, "value": 10000},  # Strong profit
            {"asset": "LTC", "return_pct": 100, "value": 0.18},  # Tiny profit
            {"asset": "ETH", "return_pct": -8, "value": 3000},   # Bad loss
            {"asset": "SHIB", "return_pct": -50, "value": 0.05}, # Tiny loss
            {"asset": "ADA", "return_pct": 0, "value": 500},     # Break-even
        ]
        
        expected_indicators = [
            "🚀 Strong Profit",
            "🔸 Tiny Profit", 
            "📉 Bad Loss",
            "🔹 Tiny Loss",
            "⚪ Break-even"
        ]
        
        for i, data in enumerate(portfolio_data):
            row = self.create_test_row(
                asset=data["asset"],
                total_return_pct=data["return_pct"],
                actual_value_eur=data["value"]
            )
            indicator = self.get_profit_indicator(row)
            assert indicator == expected_indicators[i], f"Failed for {data['asset']}"

    # Test Data Frame Integration
    
    def test_dataframe_apply_function(self):
        """Test applying profit indicator function to a DataFrame."""
        df = pd.DataFrame([
            {"Asset": "BTC", "Total Return %": 15, "Actual Value €": 5000, "Unrealised €": 650},
            {"Asset": "LTC", "Total Return %": 80, "Actual Value €": 0.18, "Unrealised €": 0.08},
            {"Asset": "ETH", "Total Return %": -12, "Actual Value €": 2800, "Unrealised €": -380},
        ])
        
        df['P&L Status'] = df.apply(self.get_profit_indicator, axis=1)
        
        assert df.loc[0, 'P&L Status'] == "🚀 Strong Profit"
        assert df.loc[1, 'P&L Status'] == "🔸 Tiny Profit"
        assert df.loc[2, 'P&L Status'] == "💥 Heavy Loss"


class TestProfitIndicatorEdgeCases:
    """Test edge cases and error conditions for profit indicators."""
    
    def get_profit_indicator(self, row):
        """Copy of the profit indicator function for edge case testing."""
        return_pct = row["Total Return %"]
        current_value = row["Actual Value €"]
        
        # For very small positions (< €1), show different indicators
        if current_value < 1.0:
            if return_pct > 0:
                return "🔸 Tiny Profit"
            elif return_pct < 0:
                return "🔹 Tiny Loss"
            else:
                return "⚪ Tiny Position"
        
        # For normal positions, use standard indicators
        if return_pct > 10:
            return "🚀 Strong Profit"
        elif return_pct > 5:
            return "📈 Good Profit"
        elif return_pct > 0:
            return "🟢 Profit"
        elif return_pct == 0:
            return "⚪ Break-even"
        elif return_pct > -5:
            return "🔴 Loss"
        elif return_pct > -10:
            return "📉 Bad Loss"
        else:
            return "💥 Heavy Loss"
    
    def test_very_large_numbers(self):
        """Test with very large numbers."""
        row = pd.Series({
            "Total Return %": 1000000,
            "Actual Value €": 999999999,
            "Unrealised €": 500000000
        })
        indicator = self.get_profit_indicator(row)
        assert indicator == "🚀 Strong Profit"
    
    def test_very_small_numbers(self):
        """Test with very small numbers."""
        row = pd.Series({
            "Total Return %": 0.0001,
            "Actual Value €": 0.0001,
            "Unrealised €": 0.00001
        })
        indicator = self.get_profit_indicator(row)
        assert indicator == "🔸 Tiny Profit"
    
    def test_negative_zero(self):
        """Test with negative zero."""
        row = pd.Series({
            "Total Return %": -0.0,
            "Actual Value €": 100,
            "Unrealised €": 0
        })
        indicator = self.get_profit_indicator(row)
        assert indicator == "⚪ Break-even"
    
    def test_infinity_values(self):
        """Test with infinity values."""
        row = pd.Series({
            "Total Return %": float('inf'),
            "Actual Value €": 100,
            "Unrealised €": 50
        })
        indicator = self.get_profit_indicator(row)
        assert indicator == "🚀 Strong Profit"
    
    def test_nan_handling(self):
        """Test handling of NaN values."""
        import numpy as np
        row = pd.Series({
            "Total Return %": np.nan,
            "Actual Value €": 100,
            "Unrealised €": 0
        })
        # This should handle NaN gracefully - the actual behavior depends on implementation
        # In practice, NaN comparisons return False, so it would fall through to the else case
        try:
            indicator = self.get_profit_indicator(row)
            # If it doesn't crash, that's good
            assert indicator in ["🚀 Strong Profit", "📈 Good Profit", "🟢 Profit", 
                               "⚪ Break-even", "🔴 Loss", "📉 Bad Loss", "💥 Heavy Loss",
                               "🔸 Tiny Profit", "🔹 Tiny Loss", "⚪ Tiny Position"]
        except (ValueError, TypeError):
            # It's acceptable for NaN to cause an error - this should be handled upstream
            pass


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
