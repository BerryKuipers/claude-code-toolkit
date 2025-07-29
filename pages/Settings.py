"""
Settings Page for Crypto Portfolio Dashboard.

Provides comprehensive settings management including:
- AI system prompt editor
- Model configuration
- API key management
- Cache management
- Advanced settings
"""

import streamlit as st
import logging
import os
from datetime import datetime
from typing import Dict, Any

# Set up logging
logger = logging.getLogger(__name__)

# Import API client
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from frontend.api_client import SyncCryptoPortfolioAPIClient


def get_api_client() -> SyncCryptoPortfolioAPIClient:
    """Get API client with backend URL from environment or default."""
    backend_url = os.getenv("BACKEND_API_URL", "http://localhost:8000")
    return SyncCryptoPortfolioAPIClient(base_url=backend_url)


def display_data_management():
    """Display data management section with UI buttons."""
    st.markdown("## 📊 Data Management")
    st.markdown("Manage portfolio data fetching and updates.")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Force Get Bitvavo Assets", help="Force refresh asset list from Bitvavo"):
            try:
                client = get_api_client()
                with st.spinner("Fetching fresh asset list from Bitvavo..."):
                    # Force refresh portfolio data which includes asset discovery
                    success = client.refresh_portfolio_data()

                if success:
                    st.success("✅ Asset list refreshed from Bitvavo!")
                    st.info("💡 New assets will appear in the dashboard on next load.")
                else:
                    st.error("❌ Failed to refresh asset list")

            except Exception as e:
                st.error(f"❌ Failed to fetch assets: {e}")

    with col2:
        if st.button("💰 Update All Prices", help="Force update current market prices"):
            try:
                client = get_api_client()
                with st.spinner("Updating market prices..."):
                    # Clear price cache to force fresh price fetch
                    response = client._run_async(
                        client._get_or_create_client()._request("POST", "/api/v1/cache/force-refresh")
                    )

                if response.get("success", False):
                    st.success("✅ Price cache cleared! Fresh prices will be fetched on next load.")
                    st.info("💡 Consider using CoinGecko API for better rate limits in the future.")
                else:
                    st.warning("⚠️ Price update failed or cache not enabled")

            except Exception as e:
                st.error(f"❌ Failed to update prices: {e}")

    with col3:
        if st.button("⏰ Schedule Price Updates", help="Configure automatic price updates"):
            st.info("🚧 Scheduled updates coming soon!")
            st.markdown("""
            **Planned Features:**
            - Automatic price updates every X minutes
            - Configurable update intervals
            - Rate limiting protection
            - CoinGecko API integration option
            """)

    # Data refresh settings
    st.markdown("### ⚙️ Data Refresh Settings")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Current Refresh Intervals:**")
        st.info("""
        - Portfolio Holdings: Manual + 1h cache
        - Market Prices: Manual + 5min cache
        - Trade History: Manual + 24h cache
        - Asset Discovery: Manual refresh only
        """)

    with col_b:
        st.markdown("**Rate Limiting:**")
        st.warning("""
        ⚠️ **Bitvavo API Limits:**
        - Be careful with frequent updates
        - Consider CoinGecko for price data
        - Current delay: 0.2s between calls
        """)


def display_cache_management():
    """Display cache management section with UI buttons."""
    st.markdown("## 🗄️ Cache Management")
    st.markdown("Manage portfolio data caching for better performance.")

    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 View Cache Stats", help="View current cache statistics and health"):
            try:
                client = get_api_client()
                with st.spinner("Fetching cache statistics..."):
                    cache_stats = client.get_cache_stats()
                
                if cache_stats.get("cache_enabled", False):
                    st.success("✅ Cache is enabled and working")
                    
                    # Display cache statistics
                    stats = cache_stats.get("stats", {})
                    if stats:
                        st.markdown("### 📈 Cache Statistics")
                        
                        # Create metrics display
                        col_a, col_b = st.columns(2)
                        
                        with col_a:
                            st.metric("Portfolio Holdings", f"{stats.get('portfolio_holdings_valid', 0)}/{stats.get('portfolio_holdings_total', 0)}")
                            st.metric("Market Prices", f"{stats.get('market_prices_valid', 0)}/{stats.get('market_prices_total', 0)}")
                            st.metric("Trade History", f"{stats.get('trade_history_valid', 0)}/{stats.get('trade_history_total', 0)}")
                        
                        with col_b:
                            st.metric("Deposit History", f"{stats.get('deposit_history_valid', 0)}/{stats.get('deposit_history_total', 0)}")
                            st.metric("Withdrawal History", f"{stats.get('withdrawal_history_valid', 0)}/{stats.get('withdrawal_history_total', 0)}")
                            st.metric("Portfolio Summary", f"{stats.get('portfolio_summary_valid', 0)}/{stats.get('portfolio_summary_total', 0)}")
                        
                        st.info("📝 Format: Valid/Total entries")
                    
                    # Display health information
                    health = cache_stats.get("health", {})
                    if health:
                        st.markdown("### 🏥 API Health")
                        api_status = "🟢 Available" if health.get("api_available", False) else "🔴 Unavailable"
                        st.write(f"**Bitvavo API**: {api_status}")
                        
                        if health.get("last_error"):
                            st.error(f"Last Error: {health['last_error']}")
                else:
                    st.warning("⚠️ Cache is not enabled")
                    
            except Exception as e:
                st.error(f"❌ Failed to fetch cache stats: {e}")
    
    with col2:
        if st.button("🧹 Clear Expired Cache", help="Remove expired cache entries"):
            try:
                client = get_api_client()
                with st.spinner("Clearing expired cache entries..."):
                    # Call the cache clear endpoint
                    response = client._run_async(
                        client._get_or_create_client()._request("POST", "/api/v1/cache/clear-expired")
                    )
                
                if response.get("success", False):
                    st.success("✅ Expired cache entries cleared successfully!")
                else:
                    st.warning("⚠️ No expired entries to clear or cache not enabled")
                    
            except Exception as e:
                st.error(f"❌ Failed to clear expired cache: {e}")
    
    with col3:
        if st.button("🔄 Force Refresh Cache", help="Clear all cache and force fresh data fetch"):
            try:
                client = get_api_client()
                with st.spinner("Forcing cache refresh..."):
                    # Call the force refresh endpoint
                    response = client._run_async(
                        client._get_or_create_client()._request("POST", "/api/v1/cache/force-refresh")
                    )
                
                if response.get("success", False):
                    st.success("✅ Cache cleared! Next API calls will fetch fresh data.")
                    st.info("💡 Refresh the main dashboard to see updated data.")
                else:
                    st.warning("⚠️ Cache not enabled or operation failed")
                    
            except Exception as e:
                st.error(f"❌ Failed to force refresh cache: {e}")
    
    # Cache configuration info
    st.markdown("### ⚙️ Cache Configuration")
    st.info("""
    **Cache TTL Settings:**
    - Portfolio Holdings: 1 hour
    - Market Prices: 5 minutes  
    - Trade History: 24 hours
    - Deposit/Withdrawal History: 24 hours
    
    **Cache Benefits:**
    - Faster loading times
    - Reduced API calls
    - Better rate limit management
    - Offline data availability
    """)


def display_ai_settings():
    """Display AI system settings."""
    st.markdown("## 🤖 AI System Settings")
    
    # AI Model Configuration
    st.markdown("### 🧠 Model Configuration")
    
    # Get current settings from session state or defaults
    current_model = st.session_state.get("selected_model", "claude-sonnet-4")
    current_temperature = st.session_state.get("ai_temperature", 0.1)
    current_max_tokens = st.session_state.get("ai_max_tokens", 4000)
    
    col1, col2 = st.columns(2)
    
    with col1:
        model_options = [
            "claude-sonnet-4",
            "claude-haiku-3",
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-3.5-turbo"
        ]
        
        selected_model = st.selectbox(
            "Default AI Model",
            options=model_options,
            index=model_options.index(current_model) if current_model in model_options else 0,
            help="Choose the default AI model for analysis"
        )
        
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=current_temperature,
            step=0.1,
            help="Controls randomness in AI responses (0.0 = deterministic, 2.0 = very creative)"
        )
    
    with col2:
        max_tokens = st.number_input(
            "Max Tokens",
            min_value=100,
            max_value=8000,
            value=current_max_tokens,
            step=100,
            help="Maximum number of tokens in AI responses"
        )
        
        function_calling = st.checkbox(
            "Enable Function Calling",
            value=st.session_state.get("enable_function_calling", True),
            help="Allow AI to call portfolio analysis functions"
        )
    
    # Save settings
    if st.button("💾 Save AI Settings"):
        st.session_state.selected_model = selected_model
        st.session_state.ai_temperature = temperature
        st.session_state.ai_max_tokens = max_tokens
        st.session_state.enable_function_calling = function_calling
        st.success("✅ AI settings saved!")
    
    # System Prompt Editor
    st.markdown("### 📝 System Prompt Editor")
    
    default_prompt = """You are a professional cryptocurrency portfolio analyst. You have access to the user's portfolio data and can provide insights on:

- Portfolio performance and allocation
- Risk assessment and diversification
- Market trends and opportunities
- Technical analysis of holdings
- Investment recommendations

Always provide data-driven insights and explain your reasoning. Be concise but thorough in your analysis."""
    
    current_prompt = st.session_state.get("system_prompt", default_prompt)
    
    system_prompt = st.text_area(
        "System Prompt",
        value=current_prompt,
        height=200,
        help="Define how the AI should behave and what context it should use"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save System Prompt"):
            st.session_state.system_prompt = system_prompt
            st.success("✅ System prompt saved!")
    
    with col2:
        if st.button("🔄 Reset to Default"):
            st.session_state.system_prompt = default_prompt
            st.success("✅ System prompt reset to default!")
            st.rerun()


def display_api_settings():
    """Display API key management."""
    st.markdown("## 🔑 API Key Management")
    st.warning("⚠️ API keys are managed through environment variables for security. Update your .env file to change API keys.")
    
    # Show current API key status (without revealing keys)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏦 Bitvavo API")
        bitvavo_key = os.getenv("BITVAVO_API_KEY", "")
        bitvavo_secret = os.getenv("BITVAVO_API_SECRET", "")
        
        if bitvavo_key and bitvavo_secret:
            st.success("✅ Bitvavo API keys configured")
            st.info(f"Key: {bitvavo_key[:8]}...{bitvavo_key[-4:] if len(bitvavo_key) > 12 else ''}")
        else:
            st.error("❌ Bitvavo API keys not configured")
    
    with col2:
        st.markdown("### 🤖 AI API Keys")
        openai_key = os.getenv("OPENAI_API_KEY", "")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        
        if openai_key:
            st.success("✅ OpenAI API key configured")
        else:
            st.warning("⚠️ OpenAI API key not configured")
            
        if anthropic_key:
            st.success("✅ Anthropic API key configured")
        else:
            st.warning("⚠️ Anthropic API key not configured")
    
    st.markdown("### 📋 Environment Variables")
    st.code("""
# Add these to your .env file:
BITVAVO_API_KEY=your_bitvavo_api_key
BITVAVO_API_SECRET=your_bitvavo_api_secret
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
""", language="bash")


def main():
    """Main settings page."""
    st.set_page_config(
        page_title="Settings - Crypto Portfolio Dashboard",
        page_icon="⚙️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    st.title("⚙️ Settings")
    st.markdown("Configure your crypto portfolio dashboard settings.")
    
    # Create tabs for different settings sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Data Management",
        "🗄️ Cache Management",
        "🤖 AI Settings",
        "🔑 API Keys",
        "⚙️ Advanced"
    ])

    with tab1:
        display_data_management()

    with tab2:
        display_cache_management()

    with tab3:
        display_ai_settings()

    with tab4:
        display_api_settings()

    with tab5:
        st.markdown("## 📊 Advanced Settings")
        st.info("🚧 Advanced settings coming soon!")
        
        # Placeholder for future advanced settings
        st.markdown("### 🔧 Future Features")
        st.markdown("""
        - Custom data refresh intervals
        - Portfolio rebalancing alerts
        - Export/import settings
        - Theme customization
        - Notification preferences
        """)


if __name__ == "__main__":
    main()
