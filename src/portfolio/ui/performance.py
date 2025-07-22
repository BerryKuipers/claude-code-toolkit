"""Performance optimization utilities for the crypto portfolio dashboard.

This module provides caching, lazy loading, and other performance optimizations
to improve the user experience with large portfolios and complex AI features.
"""

import streamlit as st
import pandas as pd
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import hashlib
import pickle
import functools

logger = logging.getLogger(__name__)


class PerformanceOptimizer:
    """Handles performance optimizations for the dashboard."""
    
    def __init__(self):
        """Initialize performance optimizer."""
        self.cache_duration = timedelta(minutes=5)
        self.max_cache_size = 50
    
    @staticmethod
    def cache_dataframe(cache_key: str, duration_minutes: int = 5):
        """Decorator to cache DataFrame results in session state.
        
        Args:
            cache_key: Unique key for caching
            duration_minutes: Cache duration in minutes
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key with function arguments
                args_hash = hashlib.md5(str(args + tuple(kwargs.items())).encode()).hexdigest()[:8]
                full_cache_key = f"{cache_key}_{args_hash}"
                
                # Check if cached result exists and is still valid
                if full_cache_key in st.session_state:
                    cached_data = st.session_state[full_cache_key]
                    cache_time = cached_data.get("timestamp")
                    
                    if cache_time and datetime.now() - cache_time < timedelta(minutes=duration_minutes):
                        logger.debug(f"Using cached result for {cache_key}")
                        return cached_data["data"]
                
                # Execute function and cache result
                logger.debug(f"Computing and caching result for {cache_key}")
                result = func(*args, **kwargs)
                
                st.session_state[full_cache_key] = {
                    "data": result,
                    "timestamp": datetime.now()
                }
                
                return result
            
            return wrapper
        return decorator
    
    @staticmethod
    def optimize_dataframe_display(df: pd.DataFrame, max_rows: int = 1000) -> pd.DataFrame:
        """Optimize DataFrame for display performance.
        
        Args:
            df: DataFrame to optimize
            max_rows: Maximum rows to display
            
        Returns:
            Optimized DataFrame
        """
        if len(df) > max_rows:
            logger.warning(f"DataFrame has {len(df)} rows, truncating to {max_rows} for performance")
            df = df.head(max_rows)
        
        # Optimize data types for display
        for col in df.columns:
            if df[col].dtype == 'object':
                # Convert string columns to category if they have few unique values
                unique_ratio = df[col].nunique() / len(df)
                if unique_ratio < 0.5:
                    df[col] = df[col].astype('category')
        
        return df
    
    @staticmethod
    def lazy_load_component(component_key: str, load_func: Callable, *args, **kwargs):
        """Lazy load expensive components only when needed.
        
        Args:
            component_key: Unique key for the component
            load_func: Function to load the component
            *args, **kwargs: Arguments for load_func
        """
        if f"lazy_{component_key}" not in st.session_state:
            with st.spinner(f"Loading {component_key}..."):
                st.session_state[f"lazy_{component_key}"] = load_func(*args, **kwargs)
        
        return st.session_state[f"lazy_{component_key}"]
    
    @staticmethod
    def batch_api_calls(api_calls: list, batch_size: int = 10, delay: float = 0.1):
        """Batch API calls to reduce rate limiting and improve performance.
        
        Args:
            api_calls: List of API call functions
            batch_size: Number of calls per batch
            delay: Delay between batches in seconds
        """
        import time
        
        results = []
        for i in range(0, len(api_calls), batch_size):
            batch = api_calls[i:i + batch_size]
            
            # Execute batch
            batch_results = []
            for call in batch:
                try:
                    result = call()
                    batch_results.append(result)
                except Exception as e:
                    logger.error(f"API call failed: {e}")
                    batch_results.append(None)
            
            results.extend(batch_results)
            
            # Delay between batches
            if i + batch_size < len(api_calls):
                time.sleep(delay)
        
        return results
    
    @staticmethod
    def optimize_streamlit_config():
        """Apply Streamlit performance optimizations."""
        # Configure Streamlit for better performance
        st.set_page_config(
            page_title="Crypto Portfolio Dashboard",
            page_icon="📈",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        # Add custom CSS for performance
        st.markdown("""
        <style>
        /* Optimize scrolling performance */
        .main > div {
            scroll-behavior: smooth;
        }
        
        /* Reduce animation overhead */
        * {
            transition: none !important;
            animation: none !important;
        }
        
        /* Optimize table rendering */
        .dataframe {
            font-size: 12px;
        }
        
        /* Reduce memory usage for large tables */
        .stDataFrame {
            height: 400px;
            overflow-y: auto;
        }
        
        /* Optimize chat interface */
        .stChatMessage {
            margin-bottom: 0.5rem;
        }
        
        /* Reduce padding for better space usage */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def clear_old_cache(max_age_hours: int = 24):
        """Clear old cached data from session state.
        
        Args:
            max_age_hours: Maximum age of cached data in hours
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        keys_to_remove = []
        
        for key, value in st.session_state.items():
            if isinstance(value, dict) and "timestamp" in value:
                if value["timestamp"] < cutoff_time:
                    keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del st.session_state[key]
            logger.debug(f"Removed old cache entry: {key}")
        
        if keys_to_remove:
            logger.info(f"Cleared {len(keys_to_remove)} old cache entries")
    
    @staticmethod
    def get_memory_usage() -> Dict[str, Any]:
        """Get current memory usage statistics.
        
        Returns:
            Dictionary with memory usage information
        """
        import sys
        
        # Calculate session state size
        session_size = 0
        session_items = 0
        
        for key, value in st.session_state.items():
            try:
                item_size = sys.getsizeof(pickle.dumps(value))
                session_size += item_size
                session_items += 1
            except Exception:
                session_items += 1
        
        return {
            "session_state_size_mb": round(session_size / (1024 * 1024), 2),
            "session_state_items": session_items,
            "cache_entries": len([k for k in st.session_state.keys() if "cache" in k.lower()]),
            "lazy_components": len([k for k in st.session_state.keys() if k.startswith("lazy_")])
        }
    
    @staticmethod
    def render_performance_monitor():
        """Render performance monitoring widget."""
        with st.expander("⚡ Performance Monitor"):
            col1, col2, col3 = st.columns(3)
            
            memory_stats = PerformanceOptimizer.get_memory_usage()
            
            with col1:
                st.metric(
                    "Session Memory", 
                    f"{memory_stats['session_state_size_mb']} MB",
                    help="Memory used by session state"
                )
                st.metric(
                    "Session Items", 
                    memory_stats['session_state_items'],
                    help="Number of items in session state"
                )
            
            with col2:
                st.metric(
                    "Cache Entries", 
                    memory_stats['cache_entries'],
                    help="Number of cached data entries"
                )
                st.metric(
                    "Lazy Components", 
                    memory_stats['lazy_components'],
                    help="Number of lazy-loaded components"
                )
            
            with col3:
                if st.button("🧹 Clear Old Cache"):
                    PerformanceOptimizer.clear_old_cache()
                    st.success("Old cache cleared!")
                    st.rerun()
                
                if st.button("🔄 Reset Session"):
                    for key in list(st.session_state.keys()):
                        if key not in ['selected_model', 'llm_client', 'function_handler']:
                            del st.session_state[key]
                    st.success("Session reset!")
                    st.rerun()


def optimize_portfolio_data_loading():
    """Optimize portfolio data loading with caching."""
    @PerformanceOptimizer.cache_dataframe("portfolio_data", duration_minutes=5)
    def load_portfolio_data():
        # This would be replaced with actual portfolio loading logic
        # For now, return None to indicate it should use existing logic
        return None
    
    return load_portfolio_data()


def optimize_ai_responses():
    """Optimize AI response generation with caching."""
    @PerformanceOptimizer.cache_dataframe("ai_response", duration_minutes=10)
    def generate_ai_response(query: str, context: str):
        # This would cache AI responses for identical queries
        # Implementation would go in the actual AI client
        return None
    
    return generate_ai_response


def render_optimized_dataframe(df: pd.DataFrame, key: str, **kwargs):
    """Render DataFrame with performance optimizations."""
    # Optimize DataFrame for display
    optimized_df = PerformanceOptimizer.optimize_dataframe_display(df)
    
    # Use Streamlit's built-in optimization features
    return st.dataframe(
        optimized_df,
        key=key,
        use_container_width=True,
        hide_index=True,
        **kwargs
    )


def optimize_chat_interface():
    """Apply optimizations to chat interface."""
    # Limit chat history to prevent memory bloat
    if "chat_history" in st.session_state:
        max_messages = 50
        if len(st.session_state.chat_history) > max_messages:
            st.session_state.chat_history = st.session_state.chat_history[-max_messages:]
    
    # Clear old AI analysis cache
    PerformanceOptimizer.clear_old_cache(max_age_hours=6)


def apply_global_optimizations():
    """Apply global performance optimizations."""
    # Configure Streamlit
    PerformanceOptimizer.optimize_streamlit_config()
    
    # Clear old cache periodically
    if "last_cache_clear" not in st.session_state:
        st.session_state.last_cache_clear = datetime.now()
    
    # Clear cache every hour
    if datetime.now() - st.session_state.last_cache_clear > timedelta(hours=1):
        PerformanceOptimizer.clear_old_cache()
        st.session_state.last_cache_clear = datetime.now()
    
    # Optimize chat interface
    optimize_chat_interface()
