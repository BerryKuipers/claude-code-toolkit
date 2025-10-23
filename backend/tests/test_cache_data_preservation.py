"""
Test cache data preservation and asset symbol validation.

This test ensures that the asset symbol validation doesn't incorrectly
filter out valid cryptocurrency symbols, preventing cache data loss.
"""

import pytest
from unittest.mock import patch
import tempfile
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from app.core.database import DevCacheDatabase

# Import Clean Architecture components
try:
    from portfolio_core.domain.value_objects import AssetSymbol
    from portfolio_core.infrastructure.mappers import BitvavoDataMapper
    CLEAN_ARCH_AVAILABLE = True
except ImportError:
    CLEAN_ARCH_AVAILABLE = False


class TestCacheDataPreservation:
    """Test cache data preservation with various asset symbols."""
    
    @pytest.fixture
    def temp_cache_db(self):
        """Create temporary cache database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        cache = DevCacheDatabase(db_path)
        yield cache
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.mark.skipif(not CLEAN_ARCH_AVAILABLE, reason="Clean Architecture components not available")
    def test_single_character_asset_symbols_accepted(self):
        """Test that single character asset symbols are accepted."""
        # Test various single character symbols that exist in crypto
        single_char_symbols = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']

        for symbol in single_char_symbols:
            # Should not raise an exception
            asset_symbol = AssetSymbol(symbol)
            assert str(asset_symbol) == symbol.upper()
    
    @pytest.mark.skipif(not CLEAN_ARCH_AVAILABLE, reason="Clean Architecture components not available")
    def test_common_crypto_symbols_accepted(self):
        """Test that common cryptocurrency symbols are accepted."""
        common_symbols = [
            'BTC', 'ETH', 'ADA', 'DOT', 'LINK', 'UNI', 'MATIC', 'AVAX',
            'SOL', 'ATOM', 'XRP', 'LTC', 'BCH', 'ETC', 'DOGE', 'SHIB',
            'USDC', 'USDT', 'DAI', 'BUSD', 'AAVE', 'COMP', 'MKR', 'SNX'
        ]
        
        for symbol in common_symbols:
            asset_symbol = AssetSymbol(symbol)
            assert str(asset_symbol) == symbol.upper()
    
    def test_balance_data_mapping_preserves_all_valid_symbols(self):
        """Test that balance data mapping preserves all valid symbols."""
        # Simulate Bitvavo balance data with various symbol lengths
        test_balance_data = [
            {'symbol': 'A', 'available': '100.0', 'inOrder': '0.0'},
            {'symbol': 'BTC', 'available': '0.5', 'inOrder': '0.0'},
            {'symbol': 'ETH', 'available': '2.0', 'inOrder': '0.0'},
            {'symbol': 'USDC', 'available': '1000.0', 'inOrder': '0.0'},
            {'symbol': 'DOGE', 'available': '5000.0', 'inOrder': '0.0'},
            {'symbol': 'SHIB', 'available': '1000000.0', 'inOrder': '0.0'},
            {'symbol': 'MATIC', 'available': '500.0', 'inOrder': '0.0'},
            {'symbol': 'EUR', 'available': '1000.0', 'inOrder': '0.0'},  # Should be skipped
            {'symbol': '', 'available': '0', 'inOrder': '0.0'},  # Should be skipped
        ]
        
        mapper = BitvavoDataMapper()
        balances = mapper.map_balance_data_to_holdings(test_balance_data)
        
        # Should preserve all valid symbols except EUR and empty string
        expected_symbols = {'A', 'BTC', 'ETH', 'USDC', 'DOGE', 'SHIB', 'MATIC'}
        actual_symbols = set(str(symbol) for symbol in balances.keys())
        
        assert actual_symbols == expected_symbols
        assert len(balances) == 7  # All except EUR and empty string
    
    def test_cache_preserves_single_character_symbols(self, temp_cache_db):
        """Test that cache preserves single character symbols."""
        # Test data with single character symbols
        holdings_data = [
            {'symbol': 'A', 'available': '100.0', 'inOrder': '0.0'},
            {'symbol': 'B', 'available': '50.0', 'inOrder': '0.0'},
            {'symbol': 'BTC', 'available': '0.5', 'inOrder': '0.0'},
            {'symbol': 'ETH', 'available': '2.0', 'inOrder': '0.0'},
        ]
        
        # Cache the data
        temp_cache_db.cache_portfolio_holdings(holdings_data, ttl_hours=1)
        
        # Retrieve from cache
        cached_holdings = temp_cache_db.get_cached_portfolio_holdings()
        
        assert cached_holdings is not None
        assert len(cached_holdings) == 4
        
        # Verify all symbols are preserved
        cached_symbols = {holding['symbol'] for holding in cached_holdings}
        expected_symbols = {'A', 'B', 'BTC', 'ETH'}
        assert cached_symbols == expected_symbols
    
    def test_no_cache_data_loss_with_mixed_symbol_lengths(self, temp_cache_db):
        """Test that no cache data is lost with mixed symbol lengths."""
        # Simulate a realistic portfolio with various symbol lengths
        realistic_holdings = [
            {'symbol': 'A', 'available': '100.0', 'inOrder': '0.0'},      # 1 char
            {'symbol': 'BTC', 'available': '0.5', 'inOrder': '0.0'},      # 3 chars
            {'symbol': 'ETH', 'available': '2.0', 'inOrder': '0.0'},      # 3 chars
            {'symbol': 'USDC', 'available': '1000.0', 'inOrder': '0.0'},  # 4 chars
            {'symbol': 'MATIC', 'available': '500.0', 'inOrder': '0.0'},  # 5 chars
            {'symbol': 'CHAINLINK', 'available': '50.0', 'inOrder': '0.0'}, # 9 chars (hypothetical)
        ]
        
        # Cache the data
        temp_cache_db.cache_portfolio_holdings(realistic_holdings, ttl_hours=1)
        
        # Retrieve from cache
        cached_holdings = temp_cache_db.get_cached_portfolio_holdings()
        
        # Should preserve all holdings
        assert cached_holdings is not None
        assert len(cached_holdings) == len(realistic_holdings)
        
        # Verify no data loss
        original_symbols = {holding['symbol'] for holding in realistic_holdings}
        cached_symbols = {holding['symbol'] for holding in cached_holdings}
        assert cached_symbols == original_symbols
    
    def test_asset_symbol_validation_edge_cases(self):
        """Test edge cases for asset symbol validation."""
        # Valid edge cases
        valid_symbols = ['A', 'Z', '1', '9', 'BTC', 'VERYLONGSYMBOL']
        
        for symbol in valid_symbols:
            asset_symbol = AssetSymbol(symbol)
            assert str(asset_symbol) == symbol.upper()
        
        # Invalid cases
        invalid_symbols = ['', 'TOOLONGSYMBOLNAME123']  # Empty and too long
        
        for symbol in invalid_symbols:
            with pytest.raises(ValueError):
                AssetSymbol(symbol)
    
    def test_cache_data_loss_prevention_integration(self, temp_cache_db):
        """Integration test to prevent the 48->2 cache data loss issue."""
        # Simulate the original issue: 48 holdings reduced to 2
        # This represents a realistic Bitvavo portfolio response
        large_portfolio = []
        
        # Add various symbol types that should all be preserved
        symbols = [
            # Single character (previously rejected)
            'A', 'B', 'C', 'D', 'E',
            # Common crypto symbols
            'BTC', 'ETH', 'ADA', 'DOT', 'LINK', 'UNI', 'MATIC', 'AVAX',
            'SOL', 'ATOM', 'XRP', 'LTC', 'BCH', 'ETC', 'DOGE', 'SHIB',
            'USDC', 'USDT', 'DAI', 'BUSD', 'AAVE', 'COMP', 'MKR', 'SNX',
            # Longer symbols
            'CHAINLINK', 'POLYGON', 'CARDANO', 'POLKADOT', 'UNISWAP',
            # Mixed case (should be normalized)
            'btc', 'eth', 'ada', 'dot', 'link'
        ]
        
        for i, symbol in enumerate(symbols):
            large_portfolio.append({
                'symbol': symbol,
                'available': f'{i + 1}.0',
                'inOrder': '0.0'
            })
        
        # Cache the large portfolio
        temp_cache_db.cache_portfolio_holdings(large_portfolio, ttl_hours=1)
        
        # Retrieve from cache
        cached_holdings = temp_cache_db.get_cached_portfolio_holdings()
        
        # Should preserve all holdings (no data loss)
        assert cached_holdings is not None
        assert len(cached_holdings) == len(large_portfolio)
        
        # Verify specific symbols that were previously lost
        cached_symbols = {holding['symbol'] for holding in cached_holdings}
        assert 'A' in cached_symbols  # This was previously rejected
        assert 'BTC' in cached_symbols
        assert 'ETH' in cached_symbols
        
        print(f"✅ Cache data preservation test passed: {len(cached_holdings)} holdings preserved")
