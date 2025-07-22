"""API status checker and health monitoring for LLM providers.

This module provides utilities to check the health and status of various
LLM API providers and help users understand service availability.
"""

import streamlit as st
import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)


class APIStatusChecker:
    """Monitors API status for various LLM providers."""
    
    def __init__(self):
        """Initialize API status checker."""
        self.status_cache = {}
        self.cache_duration = timedelta(minutes=5)
    
    def check_anthropic_status(self) -> Dict[str, Any]:
        """Check Anthropic API status."""
        cache_key = "anthropic_status"
        
        # Check cache first
        if self._is_cached(cache_key):
            return self.status_cache[cache_key]["data"]
        
        try:
            # Try a simple API call to check status
            import anthropic
            
            # This is a minimal test - we don't actually send a request
            # but check if we can create a client
            client = anthropic.Anthropic(api_key="test")
            
            status = {
                "status": "unknown",
                "message": "Unable to verify status without making API calls",
                "last_checked": datetime.now().isoformat(),
                "recommendation": "Try making a test query to verify"
            }
            
        except ImportError:
            status = {
                "status": "unavailable",
                "message": "Anthropic library not installed",
                "last_checked": datetime.now().isoformat(),
                "recommendation": "Install anthropic library"
            }
        except Exception as e:
            status = {
                "status": "error",
                "message": f"Error checking status: {str(e)}",
                "last_checked": datetime.now().isoformat(),
                "recommendation": "Check API key and network connection"
            }
        
        # Cache the result
        self._cache_result(cache_key, status)
        return status
    
    def check_openai_status(self) -> Dict[str, Any]:
        """Check OpenAI API status."""
        cache_key = "openai_status"
        
        # Check cache first
        if self._is_cached(cache_key):
            return self.status_cache[cache_key]["data"]
        
        try:
            # Try to check OpenAI status page
            response = requests.get("https://status.openai.com/api/v2/status.json", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                status_indicator = data.get("status", {}).get("indicator", "unknown")
                
                status = {
                    "status": "operational" if status_indicator == "none" else status_indicator,
                    "message": data.get("status", {}).get("description", "Status unknown"),
                    "last_checked": datetime.now().isoformat(),
                    "recommendation": "Service appears operational" if status_indicator == "none" else "Check OpenAI status page"
                }
            else:
                status = {
                    "status": "unknown",
                    "message": "Unable to fetch status",
                    "last_checked": datetime.now().isoformat(),
                    "recommendation": "Check network connection"
                }
                
        except Exception as e:
            status = {
                "status": "error",
                "message": f"Error checking status: {str(e)}",
                "last_checked": datetime.now().isoformat(),
                "recommendation": "Check network connection and try again"
            }
        
        # Cache the result
        self._cache_result(cache_key, status)
        return status
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status for all supported providers."""
        return {
            "anthropic": self.check_anthropic_status(),
            "openai": self.check_openai_status()
        }
    
    def _is_cached(self, cache_key: str) -> bool:
        """Check if result is cached and still valid."""
        if cache_key not in self.status_cache:
            return False
        
        cached_time = self.status_cache[cache_key]["timestamp"]
        return datetime.now() - cached_time < self.cache_duration
    
    def _cache_result(self, cache_key: str, data: Dict[str, Any]):
        """Cache a result with timestamp."""
        self.status_cache[cache_key] = {
            "data": data,
            "timestamp": datetime.now()
        }
    
    def render_status_widget(self):
        """Render API status widget in Streamlit."""
        st.subheader("🔍 API Status Monitor")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Anthropic Claude")
            anthropic_status = self.check_anthropic_status()
            
            status_color = {
                "operational": "🟢",
                "degraded": "🟡", 
                "partial_outage": "🟠",
                "major_outage": "🔴",
                "unknown": "⚪",
                "error": "🔴",
                "unavailable": "⚫"
            }.get(anthropic_status["status"], "⚪")
            
            st.markdown(f"{status_color} **Status:** {anthropic_status['status'].title()}")
            st.caption(anthropic_status["message"])
            st.caption(f"💡 {anthropic_status['recommendation']}")
        
        with col2:
            st.markdown("### OpenAI GPT")
            openai_status = self.check_openai_status()
            
            status_color = {
                "operational": "🟢",
                "degraded": "🟡",
                "partial_outage": "🟠", 
                "major_outage": "🔴",
                "unknown": "⚪",
                "error": "🔴",
                "unavailable": "⚫"
            }.get(openai_status["status"], "⚪")
            
            st.markdown(f"{status_color} **Status:** {openai_status['status'].title()}")
            st.caption(openai_status["message"])
            st.caption(f"💡 {openai_status['recommendation']}")
        
        # Refresh button
        if st.button("🔄 Refresh Status", key="refresh_api_status"):
            # Clear cache to force refresh
            self.status_cache.clear()
            st.rerun()
        
        # Last updated info
        st.caption(f"Last checked: {datetime.now().strftime('%H:%M:%S')}")


def render_error_help():
    """Render help section for common API errors."""
    with st.expander("🆘 Common API Error Solutions"):
        st.markdown("""
        ### 🚨 **Anthropic Overloaded (529 Error)**
        - **What it means:** Anthropic's servers are at capacity
        - **Solution:** Switch to OpenAI GPT-4 temporarily
        - **Wait time:** Usually resolves in 5-15 minutes
        
        ### ❌ **Authentication Errors (401)**
        - **Check:** API key is correctly set in `.env` file
        - **Format:** `ANTHROPIC_API_KEY=sk-ant-...` or `OPENAI_API_KEY=sk-...`
        - **Restart:** Restart the dashboard after changing `.env`
        
        ### ⏱️ **Rate Limit Errors (429)**
        - **Wait:** A few seconds between requests
        - **Upgrade:** Consider upgrading your API plan
        - **Switch:** Try the other model temporarily
        
        ### 💳 **Quota/Billing Errors**
        - **Check:** Your API usage and billing status
        - **Add:** Credits to your account
        - **Monitor:** Set up usage alerts
        
        ### 🔧 **Quick Fixes**
        1. **Switch Models:** Use the model selector above
        2. **Wait & Retry:** Most errors are temporary
        3. **Check Status:** Use the API status monitor
        4. **Restart:** Restart the dashboard if needed
        """)


def get_error_suggestion(error_message: str) -> str:
    """Get a helpful suggestion based on the error message."""
    error_lower = error_message.lower()
    
    if "529" in error_message or "overloaded" in error_lower:
        return "💡 **Quick Fix:** Switch to OpenAI GPT-4 using the model selector while Anthropic recovers."
    elif "401" in error_message or "authentication" in error_lower:
        return "💡 **Quick Fix:** Check your API key in the `.env` file and restart the dashboard."
    elif "429" in error_message or "rate_limit" in error_lower:
        return "💡 **Quick Fix:** Wait 30 seconds and try again, or switch to the other model."
    elif "quota" in error_lower or "billing" in error_lower:
        return "💡 **Quick Fix:** Check your OpenAI billing dashboard and add credits if needed."
    else:
        return "💡 **Quick Fix:** Try switching to the other AI model using the selector above."


# Initialize global status checker
if "api_status_checker" not in st.session_state:
    st.session_state.api_status_checker = APIStatusChecker()
