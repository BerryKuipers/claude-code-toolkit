"""
Tests for development cache functionality.

Tests the local SQLite cache system for portfolio data, prices, and trades.
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path

from app.core.database import DevCacheDatabase


class TestDevCacheDatabase:
    """Test development cache database functionality."""
    
    @pytest.fixture
    def temp_cache_db(self):
        """Create temporary cache database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        # Create cache instance
        cache = DevCacheDatabase(db_path)
        
        yield cache
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_cache_portfolio_holdings(self, temp_cache_db):
        """Test caching and retrieving portfolio holdings."""
        cache = temp_cache_db
        
        # Test data
        holdings_data = [
            {'asset': 'BTC', 'available': '1.5', 'inOrder': '0.0'},
            {'asset': 'ETH', 'available': '10.0', 'inOrder': '0.5'},
            {'asset': 'ADA', 'available': '1000.0', 'inOrder': '0.0'},
        ]
        
        # Cache the data
        cache.cache_portfolio_holdings(holdings_data, ttl_hours=1)
        
        # Retrieve cached data
        cached_holdings = cache.get_cached_portfolio_holdings()
        
        assert cached_holdings is not None
        assert len(cached_holdings) == 3
        assert cached_holdings[0]['asset'] == 'ADA'  # Should be sorted by asset_symbol
        assert cached_holdings[1]['asset'] == 'BTC'
        assert cached_holdings[2]['asset'] == 'ETH'
    
    def test_cache_market_prices(self, temp_cache_db):
        """Test caching and retrieving market prices."""
        cache = temp_cache_db
        
        # Cache some prices
        cache.cache_market_price('BTC', '45000.50', 'BTC-EUR', ttl_minutes=5)
        cache.cache_market_price('ETH', '3200.75', 'ETH-EUR', ttl_minutes=5)
        
        # Retrieve cached prices
        btc_price = cache.get_cached_market_price('BTC')
        eth_price = cache.get_cached_market_price('ETH')
        ada_price = cache.get_cached_market_price('ADA')  # Not cached
        
        assert btc_price == '45000.50'
        assert eth_price == '3200.75'
        assert ada_price is None
    
    def test_cache_trade_history(self, temp_cache_db):
        """Test caching and retrieving trade history."""
        cache = temp_cache_db
        
        # Test trade data
        trades_data = [
            {
                'id': '123',
                'side': 'buy',
                'amount': '1.0',
                'price': '40000.0',
                'fee': '40.0',
                'timestamp': '1640995200000'
            },
            {
                'id': '124',
                'side': 'sell',
                'amount': '0.5',
                'price': '45000.0',
                'fee': '22.5',
                'timestamp': '1641081600000'
            }
        ]
        
        # Cache the trades
        cache.cache_trade_history('BTC', trades_data, ttl_hours=24)
        
        # Retrieve cached trades
        cached_trades = cache.get_cached_trade_history('BTC')
        
        assert cached_trades is not None
        assert len(cached_trades) == 2
        assert cached_trades[0]['id'] == '123'
        assert cached_trades[1]['side'] == 'sell'
    
    def test_cache_expiration(self, temp_cache_db):
        """Test that expired cache entries are not returned."""
        cache = temp_cache_db
        
        # Cache data with very short TTL
        cache.cache_market_price('BTC', '45000.0', 'BTC-EUR', ttl_minutes=-1)  # Already expired
        
        # Should not return expired data
        cached_price = cache.get_cached_market_price('BTC')
        assert cached_price is None
    
    def test_clear_expired_cache(self, temp_cache_db):
        """Test clearing expired cache entries."""
        cache = temp_cache_db
        
        # Cache some data with different expiration times
        cache.cache_market_price('BTC', '45000.0', 'BTC-EUR', ttl_minutes=5)  # Valid
        cache.cache_market_price('ETH', '3200.0', 'ETH-EUR', ttl_minutes=-1)  # Expired
        
        # Clear expired entries
        cache.clear_expired_cache()
        
        # Valid entry should still exist
        btc_price = cache.get_cached_market_price('BTC')
        assert btc_price == '45000.0'
        
        # Expired entry should be gone
        eth_price = cache.get_cached_market_price('ETH')
        assert eth_price is None
    
    def test_cache_stats(self, temp_cache_db):
        """Test cache statistics functionality."""
        cache = temp_cache_db
        
        # Add some test data
        cache.cache_market_price('BTC', '45000.0', 'BTC-EUR', ttl_minutes=5)
        cache.cache_market_price('ETH', '3200.0', 'ETH-EUR', ttl_minutes=-1)  # Expired
        
        holdings_data = [{'asset': 'BTC', 'available': '1.0', 'inOrder': '0.0'}]
        cache.cache_portfolio_holdings(holdings_data, ttl_hours=1)
        
        # Get stats
        stats = cache.get_cache_stats()
        
        assert 'market_prices_total' in stats
        assert 'portfolio_holdings_total' in stats
        assert stats['market_prices_total'] == 2
        assert stats['portfolio_holdings_total'] == 1
        assert stats['market_prices_valid'] == 1  # Only BTC is valid
        assert stats['portfolio_holdings_valid'] == 1
    
    def test_cache_replacement(self, temp_cache_db):
        """Test that caching the same asset replaces the old entry."""
        cache = temp_cache_db
        
        # Cache initial price
        cache.cache_market_price('BTC', '45000.0', 'BTC-EUR', ttl_minutes=5)
        
        # Cache updated price
        cache.cache_market_price('BTC', '46000.0', 'BTC-EUR', ttl_minutes=5)
        
        # Should return the updated price
        cached_price = cache.get_cached_market_price('BTC')
        assert cached_price == '46000.0'
        
        # Should only have one entry
        stats = cache.get_cache_stats()
        assert stats['market_prices_total'] == 1


class TestCacheIntegration:
    """Test cache integration with the application."""
    
    def test_cache_database_creation(self):
        """Test that cache database is created properly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, 'test_cache.db')
            
            # Create cache instance
            cache = DevCacheDatabase(db_path)
            
            # Database file should exist
            assert os.path.exists(db_path)
            
            # Should be able to perform operations
            cache.cache_market_price('BTC', '45000.0', 'BTC-EUR', ttl_minutes=5)
            price = cache.get_cached_market_price('BTC')
            assert price == '45000.0'
    
    def test_cache_directory_creation(self):
        """Test that cache directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Use nested directory that doesn't exist
            db_path = os.path.join(temp_dir, 'nested', 'cache.db')
            
            # Create cache instance
            cache = DevCacheDatabase(db_path)
            
            # Directory and file should be created
            assert os.path.exists(os.path.dirname(db_path))
            assert os.path.exists(db_path)
