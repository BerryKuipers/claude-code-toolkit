#!/usr/bin/env python3
"""
Test script to verify function calling works properly and get coin recommendation.
"""

import sys
import os
sys.path.append('src')

# Set up environment
os.environ.setdefault('STREAMLIT_SERVER_HEADLESS', 'true')

import streamlit as st
from portfolio.chat.function_handlers import PortfolioFunctionHandler
from dashboard import get_available_assets, get_current_prices, get_portfolio_data

def test_function_calling():
    """Test the function calling system and get coin recommendation."""
    print("🚀 Testing Function Calling System...")
    
    try:
        # Initialize Streamlit session state
        if not hasattr(st, 'session_state'):
            st.session_state = {}
            
        print("📊 Getting portfolio data...")
        available_assets = get_available_assets()
        if not available_assets:
            print("❌ No assets found - check API connection")
            return
            
        current_prices = get_current_prices(available_assets)
        df = get_portfolio_data(available_assets, {}, current_prices)
        
        if df.empty:
            print("❌ No portfolio data available")
            return
            
        print(f"✅ Portfolio data loaded: {len(df)} assets")
        
        # Create function handler
        print("🔧 Creating function handler...")
        handler = PortfolioFunctionHandler(df)
        
        # Test get_current_holdings
        print("\n📋 Testing get_current_holdings...")
        holdings_result = handler.call_function('get_current_holdings', {})
        
        if 'error' in holdings_result:
            print(f"❌ Error getting holdings: {holdings_result['error']}")
            return
            
        holdings = holdings_result.get('holdings', [])
        print(f"✅ Current holdings: {len(holdings)} assets")
        
        # Show top holdings
        print("\n💰 Top Holdings:")
        for i, holding in enumerate(holdings[:5]):
            asset = holding.get('asset', 'Unknown')
            value = holding.get('value_eur', 0)
            percentage = holding.get('portfolio_percentage', 0)
            print(f"  {i+1}. {asset}: €{value:.0f} ({percentage:.1f}%)")
        
        # Test analyze_market_opportunities
        print("\n🔍 Testing analyze_market_opportunities...")
        market_result = handler.call_function('analyze_market_opportunities', {
            'sector': 'all',
            'timeframe': 'medium'
        })
        
        if 'error' in market_result:
            print(f"❌ Error analyzing market: {market_result['error']}")
        else:
            print("✅ Market analysis completed")
            
            # Show market insights
            insights = market_result.get('insights', [])
            if insights:
                print("\n📈 Market Insights:")
                for insight in insights[:3]:
                    print(f"  • {insight}")
            
            # Show recommendations
            recommendations = market_result.get('recommendations', [])
            if recommendations:
                print("\n🎯 Investment Recommendations:")
                for rec in recommendations[:3]:
                    print(f"  • {rec}")
        
        # Test search_crypto_news for LINK analysis
        print("\n📰 Testing crypto news search for LINK...")
        news_result = handler.call_function('search_crypto_news', {
            'query': 'Chainlink LINK price analysis 2025 investment oracle'
        })
        
        if 'error' not in news_result:
            articles = news_result.get('articles', [])
            print(f"✅ Found {len(articles)} news articles about LINK")
            
            if articles:
                print("\n📰 Recent LINK News:")
                for article in articles[:2]:
                    title = article.get('title', 'No title')
                    summary = article.get('summary', 'No summary')
                    print(f"  • {title}")
                    print(f"    {summary[:100]}...")
        
        print("\n🎉 Function calling test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during function calling test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_function_calling()
    if success:
        print("\n✅ Function calling is working properly!")
        print("🚀 The AI should now be able to provide proper coin recommendations.")
    else:
        print("\n❌ Function calling needs debugging.")
