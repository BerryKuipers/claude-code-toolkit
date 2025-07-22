"""Streamlit chat interface for portfolio AI assistant."""

import json
import logging
from typing import List, Dict, Any
import streamlit as st
import pandas as pd
from .openai_client import OpenAIClient
from .function_handlers import PortfolioFunctionHandler

logger = logging.getLogger(__name__)


def render_chat_interface(portfolio_data: pd.DataFrame):
    """Render the AI chat interface for portfolio queries.
    
    Args:
        portfolio_data: DataFrame containing portfolio information
    """
    st.subheader("🤖 Portfolio AI Assistant")
    
    # Initialize session state for chat
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {
                "role": "assistant", 
                "content": "Hi! I'm your portfolio AI assistant. Ask me anything about your crypto portfolio - performance, allocations, specific coins, or get detailed explanations of your positions!"
            }
        ]
    
    if "openai_client" not in st.session_state:
        try:
            st.session_state.openai_client = OpenAIClient()
        except ValueError as e:
            st.error(f"❌ OpenAI configuration error: {e}")
            st.info("Please set your OPENAI_API_KEY in the .env file to use the AI chat feature.")
            return
    
    if "function_handler" not in st.session_state:
        st.session_state.function_handler = PortfolioFunctionHandler(portfolio_data)
    
    # Update function handler with latest portfolio data
    st.session_state.function_handler.portfolio_data = portfolio_data
    
    # Display chat messages
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about your portfolio..."):
        # Add user message to chat
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response_content = _get_ai_response(
                        prompt, 
                        st.session_state.openai_client,
                        st.session_state.function_handler
                    )
                    st.markdown(response_content)
                    
                    # Add assistant response to chat
                    st.session_state.chat_messages.append({
                        "role": "assistant", 
                        "content": response_content
                    })
                    
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_messages.append({
                        "role": "assistant", 
                        "content": error_msg
                    })
    
    # Add some example queries
    with st.expander("💡 Example Questions"):
        st.markdown("""
        **Portfolio Overview:**
        - "What's my total portfolio value?"
        - "How many profitable positions do I have?"
        - "Show me my portfolio allocation"
        
        **Performance Analysis:**
        - "What are my best performing assets?"
        - "Which coins are losing money?"
        - "How is Bitcoin performing in my portfolio?"
        
        **Detailed Explanations:**
        - "Explain my Ethereum position"
        - "Tell me about my transfer activity"
        - "What should I know about my ADA holdings?"
        
        **Specific Queries:**
        - "How much profit have I made on BTC?"
        - "Which assets make up more than 5% of my portfolio?"
        - "Show me assets with deposit activity"
        """)


def _get_ai_response(
    user_message: str, 
    openai_client: OpenAIClient, 
    function_handler: PortfolioFunctionHandler
) -> str:
    """Get AI response with function calling support.
    
    Args:
        user_message: User's message/query
        openai_client: OpenAI client instance
        function_handler: Portfolio function handler
        
    Returns:
        AI response content
    """
    try:
        # Prepare messages for OpenAI
        messages = [
            {
                "role": "system",
                "content": _get_system_prompt()
            },
            {
                "role": "user", 
                "content": user_message
            }
        ]
        
        # Get available functions
        functions = function_handler.get_available_functions()
        
        # Make initial API call
        response = openai_client.chat_completion(
            messages=messages,
            functions=functions,
            function_call="auto"
        )
        
        # Check if function calls were made
        function_calls = openai_client.get_function_calls(response)
        
        if function_calls:
            # Handle function calls
            for func_call in function_calls:
                function_name = func_call["name"]
                function_args = func_call["arguments"]
                
                # Execute function
                function_result = function_handler.handle_function_call(
                    function_name, 
                    function_args
                )
                
                # Add function result to messages
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": func_call["id"],
                        "type": "function",
                        "function": {
                            "name": function_name,
                            "arguments": function_args
                        }
                    }]
                })
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": func_call["id"],
                    "content": function_result
                })
            
            # Get final response with function results
            final_response = openai_client.chat_completion(messages=messages)
            return openai_client.get_response_content(final_response)
        
        else:
            # No function calls, return direct response
            return openai_client.get_response_content(response)
            
    except Exception as e:
        logger.error(f"Error getting AI response: {e}")
        return f"I apologize, but I encountered an error processing your request: {str(e)}"


def _get_system_prompt() -> str:
    """Get the system prompt for the portfolio AI assistant."""
    return """You are a helpful AI assistant specialized in cryptocurrency portfolio analysis. 

You have access to the user's complete portfolio data including:
- Asset holdings (FIFO and actual amounts)
- Cost basis and current values
- Realized and unrealized P&L
- Transfer history (deposits/withdrawals)
- Performance metrics

When answering questions:
1. Use the provided functions to access real portfolio data
2. Provide clear, actionable insights
3. Explain financial concepts in simple terms
4. Include specific numbers and percentages when relevant
5. Be conversational and helpful
6. If asked about a specific coin, use the explain_coin_position function for detailed analysis

Always base your responses on the actual portfolio data, not general market information.
Format monetary amounts clearly (e.g., €1,234.56) and percentages with appropriate precision.
"""


def clear_chat_history():
    """Clear the chat message history."""
    if "chat_messages" in st.session_state:
        st.session_state.chat_messages = [
            {
                "role": "assistant", 
                "content": "Chat history cleared! How can I help you with your portfolio?"
            }
        ]
