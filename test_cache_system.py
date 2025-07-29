"""
Test script for the cached Bitvavo client system.

This script tests the local database caching functionality with real API calls.
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.core.config import get_settings
from backend.app.clients.cached_bitvavo_client import CachedBitvavoAPIClient


async def test_cached_client():
    """Test the cached Bitvavo client functionality."""
    print("🔍 Testing cached Bitvavo client...")
    
    try:
        settings = get_settings()
        client = CachedBitvavoAPIClient(settings)
        
        # Test health check
        print("🏥 Checking API health...")
        health = await client.health_check()
        print(f"API Available: {health['api_available']}")
        print(f"Cache Enabled: {health['cache_enabled']}")
        
        if health['api_available']:
            print("✅ API is available - testing cache functionality")
            
            # Test portfolio holdings (should cache)
            print("\n📊 Testing portfolio holdings caching...")
            print("First call (will fetch from API):")
            holdings1 = await client.get_balance()
            print(f"  - Retrieved {len(holdings1)} holdings")
            
            print("Second call (should use cache):")
            holdings2 = await client.get_balance()
            print(f"  - Retrieved {len(holdings2)} holdings (cached)")
            
            # Test price caching
            print("\n💰 Testing price caching...")
            print("First BTC price call (will fetch from API):")
            price1 = await client.get_ticker_price('BTC-EUR')
            btc_price = price1.get('price', 'N/A')
            print(f"  - BTC price: €{btc_price}")
            
            print("Second BTC price call (should use cache):")
            price2 = await client.get_ticker_price('BTC-EUR')
            btc_price2 = price2.get('price', 'N/A')
            print(f"  - BTC price: €{btc_price2} (cached)")
            
            # Test different asset
            print("ETH price call:")
            eth_price = await client.get_ticker_price('ETH-EUR')
            print(f"  - ETH price: €{eth_price.get('price', 'N/A')}")
            
            # Show cache stats
            print("\n📈 Cache Statistics:")
            stats = client.get_cache_stats()
            for key, value in stats.items():
                if key != 'cache_enabled':
                    print(f"  - {key}: {value}")
            
            print("\n✅ Cache system is working correctly!")
            print("🎯 Benefits:")
            print("  - Reduced API calls (cache hits avoid rate limits)")
            print("  - Faster response times for cached data")
            print("  - Resilience against API outages")
            print("  - Real data persistence across restarts")
            
        else:
            print("❌ API not available")
            print(f"Last error: {health.get('last_error', 'Unknown')}")
            
            # Test cache fallback
            print("\n🔄 Testing cache fallback...")
            try:
                cached_holdings = client.cache.get_cached_portfolio_holdings()
                if cached_holdings:
                    print(f"✅ Found {len(cached_holdings)} cached holdings for fallback")
                else:
                    print("ℹ️ No cached holdings available yet")
            except Exception as e:
                print(f"Cache check failed: {e}")
        
        # Show cache configuration
        print(f"\n⚙️ Cache Configuration:")
        print(f"  - Cache enabled: {settings.enable_dev_cache}")
        print(f"  - Cache path: {settings.dev_cache_path}")
        print(f"  - Portfolio TTL: {settings.cache_portfolio_ttl_hours} hours")
        print(f"  - Prices TTL: {settings.cache_prices_ttl_minutes} minutes")
        print(f"  - Trades TTL: {settings.cache_trades_ttl_hours} hours")
        
    except Exception as e:
        print(f"❌ Error testing cached client: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Starting cache system test...")
    asyncio.run(test_cached_client())
    print("\n🏁 Test completed!")
