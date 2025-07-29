"""
Local database for development caching.

This module provides SQLite-based caching for portfolio data, prices, and trades
to reduce API calls during development and provide resilience against API issues.
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Optional, Dict, List, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DevCacheDatabase:
    """
    SQLite-based development cache for portfolio data.
    
    Provides persistent caching of:
    - Portfolio holdings and balances
    - Current market prices
    - Trade history
    - Asset metadata
    """
    
    def __init__(self, db_path: str = "data/dev_cache.db"):
        """Initialize database connection and create tables."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        logger.info(f"Development cache database initialized: {self.db_path}")
    
    def _init_database(self):
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Portfolio holdings cache
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_holdings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_symbol TEXT NOT NULL,
                    quantity TEXT NOT NULL,
                    available TEXT NOT NULL,
                    in_order TEXT NOT NULL,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    UNIQUE(asset_symbol)
                )
            """)
            
            # Market prices cache
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_symbol TEXT NOT NULL,
                    price_eur TEXT NOT NULL,
                    market TEXT NOT NULL,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    UNIQUE(asset_symbol)
                )
            """)
            
            # Trade history cache
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trade_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_symbol TEXT NOT NULL,
                    trade_data TEXT NOT NULL,  -- JSON blob
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    UNIQUE(asset_symbol)
                )
            """)
            
            # Portfolio summary cache
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    summary_data TEXT NOT NULL,  -- JSON blob
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL
                )
            """)
            
            # Cache metadata
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            logger.debug("Database tables created/verified")
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper cleanup."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        finally:
            conn.close()
    
    def cache_portfolio_holdings(self, holdings_data: List[Dict], ttl_hours: int = 1):
        """Cache portfolio holdings data."""
        expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            for holding in holdings_data:
                cursor.execute("""
                    INSERT OR REPLACE INTO portfolio_holdings 
                    (asset_symbol, quantity, available, in_order, expires_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    holding.get('asset', ''),
                    str(holding.get('available', '0')),
                    str(holding.get('available', '0')),
                    str(holding.get('inOrder', '0')),
                    expires_at
                ))
            
            conn.commit()
            logger.info(f"Cached {len(holdings_data)} portfolio holdings (TTL: {ttl_hours}h)")
    
    def get_cached_portfolio_holdings(self) -> Optional[List[Dict]]:
        """Get cached portfolio holdings if not expired."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT asset_symbol, quantity, available, in_order
                FROM portfolio_holdings 
                WHERE expires_at > CURRENT_TIMESTAMP
                ORDER BY asset_symbol
            """)
            
            rows = cursor.fetchall()
            if not rows:
                return None
            
            holdings = []
            for row in rows:
                holdings.append({
                    'asset': row['asset_symbol'],
                    'available': row['available'],
                    'inOrder': row['in_order']
                })
            
            logger.info(f"Retrieved {len(holdings)} cached portfolio holdings")
            return holdings
    
    def cache_market_price(self, asset_symbol: str, price_eur: str, market: str, ttl_minutes: int = 5):
        """Cache market price for an asset."""
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO market_prices 
                (asset_symbol, price_eur, market, expires_at)
                VALUES (?, ?, ?, ?)
            """, (asset_symbol, price_eur, market, expires_at))
            
            conn.commit()
            logger.debug(f"Cached price for {asset_symbol}: €{price_eur} (TTL: {ttl_minutes}m)")
    
    def get_cached_market_price(self, asset_symbol: str) -> Optional[str]:
        """Get cached market price if not expired."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT price_eur FROM market_prices 
                WHERE asset_symbol = ? AND expires_at > CURRENT_TIMESTAMP
            """, (asset_symbol,))
            
            row = cursor.fetchone()
            if row:
                logger.debug(f"Retrieved cached price for {asset_symbol}: €{row['price_eur']}")
                return row['price_eur']
            
            return None
    
    def cache_trade_history(self, asset_symbol: str, trades_data: List[Dict], ttl_hours: int = 24):
        """Cache trade history for an asset."""
        expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO trade_history 
                (asset_symbol, trade_data, expires_at)
                VALUES (?, ?, ?)
            """, (asset_symbol, json.dumps(trades_data), expires_at))
            
            conn.commit()
            logger.info(f"Cached {len(trades_data)} trades for {asset_symbol} (TTL: {ttl_hours}h)")
    
    def get_cached_trade_history(self, asset_symbol: str) -> Optional[List[Dict]]:
        """Get cached trade history if not expired."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT trade_data FROM trade_history 
                WHERE asset_symbol = ? AND expires_at > CURRENT_TIMESTAMP
            """, (asset_symbol,))
            
            row = cursor.fetchone()
            if row:
                trades = json.loads(row['trade_data'])
                logger.info(f"Retrieved {len(trades)} cached trades for {asset_symbol}")
                return trades
            
            return None
    
    def clear_expired_cache(self):
        """Clear all expired cache entries."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            tables = ['portfolio_holdings', 'market_prices', 'trade_history', 'portfolio_summary']
            total_cleared = 0
            
            for table in tables:
                cursor.execute(f"DELETE FROM {table} WHERE expires_at <= CURRENT_TIMESTAMP")
                cleared = cursor.rowcount
                total_cleared += cleared
                logger.debug(f"Cleared {cleared} expired entries from {table}")
            
            conn.commit()
            logger.info(f"Cleared {total_cleared} total expired cache entries")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            tables = ['portfolio_holdings', 'market_prices', 'trade_history', 'portfolio_summary']
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                stats[f"{table}_total"] = cursor.fetchone()['count']
                
                cursor.execute(f"SELECT COUNT(*) as count FROM {table} WHERE expires_at > CURRENT_TIMESTAMP")
                stats[f"{table}_valid"] = cursor.fetchone()['count']
            
            return stats


# Global cache instance
_dev_cache: Optional[DevCacheDatabase] = None


def get_dev_cache() -> DevCacheDatabase:
    """Get the global development cache instance."""
    global _dev_cache
    
    if _dev_cache is None:
        _dev_cache = DevCacheDatabase()
    
    return _dev_cache
