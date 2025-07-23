"""Streamlit chat interface for portfolio AI assistant."""

import logging
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from .api_status import get_error_suggestion, render_error_help
from .base_llm_client import LLMClientFactory, LLMProvider
from .cost_tracker import (CostTracker, render_cost_footer,
                           render_detailed_cost_analysis)
from .function_handlers import PortfolioFunctionHandler
from .model_selector import (render_model_selector,
                             render_model_status_indicator,
                             show_model_switch_success)
from .prompt_editor import PromptEditor

logger = logging.getLogger(__name__)


def render_chat_interface(portfolio_data: pd.DataFrame):
    """Render the AI chat interface for portfolio queries.

    Args:
        portfolio_data: DataFrame containing portfolio information
    """
    # Model selection UI
    selected_model = render_model_selector()

    # Check if model changed
    if "current_model" not in st.session_state:
        st.session_state.current_model = selected_model
    elif st.session_state.current_model != selected_model:
        old_model = st.session_state.current_model
        st.session_state.current_model = selected_model
        # Clear the client to force recreation with new model
        if "llm_client" in st.session_state:
            del st.session_state.llm_client
        show_model_switch_success(old_model, selected_model)

    st.markdown("---")
    st.subheader("💬 Portfolio Chat")

    # Show current model status
    render_model_status_indicator(selected_model)

    # Initialize session state for chat
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {
                "role": "assistant",
                "content": "Hi! I'm your portfolio AI assistant. Ask me anything about your crypto portfolio - performance, allocations, specific coins, or get detailed explanations of your positions!",
            }
        ]

    # Initialize cost tracker
    if "cost_tracker" not in st.session_state:
        st.session_state.cost_tracker = CostTracker()

    # Initialize prompt editor
    if "prompt_editor" not in st.session_state:
        st.session_state.prompt_editor = PromptEditor()

    # Initialize LLM client
    if "llm_client" not in st.session_state:
        try:
            st.session_state.llm_client = LLMClientFactory.create_client(selected_model)
        except ValueError as e:
            st.error(f"❌ AI model configuration error: {e}")
            st.info(
                "Please check your API keys in the .env file to use the AI chat feature."
            )
            return

    if "function_handler" not in st.session_state:
        st.session_state.function_handler = PortfolioFunctionHandler(portfolio_data)

    # Update function handler with latest portfolio data
    st.session_state.function_handler.update_portfolio_data(portfolio_data)

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
                        st.session_state.llm_client,
                        st.session_state.function_handler,
                    )
                    st.markdown(response_content)

                    # Add assistant response to chat
                    st.session_state.chat_messages.append(
                        {"role": "assistant", "content": response_content}
                    )

                except Exception as e:
                    error_message = str(e)

                    # Create user-friendly error message with suggestions
                    if (
                        "🚨" in error_message
                        or "❌" in error_message
                        or "⏱️" in error_message
                    ):
                        # Error message already formatted
                        formatted_error = error_message
                    else:
                        # Add formatting
                        formatted_error = f"❌ **Error:** {error_message}"

                    # Add helpful suggestion
                    suggestion = get_error_suggestion(error_message)
                    full_error_message = f"{formatted_error}\n\n{suggestion}"

                    st.error(full_error_message)
                    st.session_state.chat_messages.append(
                        {"role": "assistant", "content": full_error_message}
                    )

                    # Show specific help for overload errors
                    if "529" in error_message or "overloaded" in error_message.lower():
                        st.info(
                            "💡 **Quick Fix:** Use the model selector above to switch to OpenAI GPT-4 while Anthropic recovers."
                        )

    # Add some example queries
    with st.expander("💡 Example Questions"):
        st.markdown(
            """
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
        """
        )

    # Add detailed cost analysis
    render_detailed_cost_analysis()

    # Add prompt editor section
    st.markdown("---")
    with st.expander("🎭 Customize AI Behavior & Prompts"):
        st.session_state.prompt_editor.render_prompt_editor()

    # Add API status and error help
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        with st.expander("🔍 API Status Monitor"):
            try:
                if (
                    hasattr(st.session_state, "api_status_checker")
                    and st.session_state.api_status_checker
                ):
                    st.session_state.api_status_checker.render_status_widget()
                else:
                    st.warning(
                        "API status checker not initialized. Please refresh the page."
                    )
            except Exception as e:
                st.error(f"Error loading API status: {str(e)}")
                st.info("Try refreshing the page to fix this issue.")

    with col2:
        render_error_help()


def _get_ai_response(
    user_message: str, llm_client, function_handler: PortfolioFunctionHandler
) -> str:
    """Get AI response with function calling support.

    Args:
        user_message: User's message/query
        llm_client: LLM client instance (OpenAI, Claude, etc.)
        function_handler: Portfolio function handler

    Returns:
        AI response content
    """
    try:
        # Prepare messages with model-specific system prompt
        messages = [
            {"role": "system", "content": _get_system_prompt(llm_client.provider)},
            {"role": "user", "content": user_message},
        ]

        # Get available functions
        functions = function_handler.get_available_functions()

        # Check if client supports function calling
        if not llm_client.supports_function_calling():
            # Simple chat without function calling
            response = llm_client.chat_completion(messages=messages)
            return llm_client.get_response_content(response)

        # Use provider-specific function calling if available
        if hasattr(llm_client, "handle_function_calling_conversation"):
            # Claude-style function calling
            return llm_client.handle_function_calling_conversation(
                messages, functions, function_handler
            )
        else:
            # OpenAI-style function calling
            return _handle_openai_function_calling(
                messages, functions, llm_client, function_handler
            )

    except Exception as e:
        logger.error(f"Error getting AI response: {e}")
        return (
            f"I apologize, but I encountered an error processing your request: {str(e)}"
        )


def _handle_openai_function_calling(
    messages, functions, llm_client, function_handler
) -> str:
    """Handle OpenAI-style function calling."""
    # Make initial API call
    response = llm_client.chat_completion(
        messages=messages, functions=functions, function_call="auto"
    )

    # Check if function calls were made
    function_calls = llm_client.get_function_calls(response)

    if function_calls:
        # Handle function calls
        for func_call in function_calls:
            function_name = func_call["name"]
            function_args = func_call["arguments"]

            # Execute function
            function_result = function_handler.handle_function_call(
                function_name, function_args
            )

            # Add function result to messages
            messages.append(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": func_call["id"],
                            "type": "function",
                            "function": {
                                "name": function_name,
                                "arguments": function_args,
                            },
                        }
                    ],
                }
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": func_call["id"],
                    "content": function_result,
                }
            )

        # Get final response with function results
        final_response = llm_client.chat_completion(messages=messages)
        return llm_client.get_response_content(final_response)

    else:
        # No function calls, return direct response
        return llm_client.get_response_content(response)


def _get_system_prompt(provider: LLMProvider = None) -> str:
    """Get the system prompt for the portfolio AI assistant.

    Args:
        provider: LLM provider to optimize prompt for

    Returns:
        Optimized system prompt
    """
    base_prompt = """You are a helpful AI assistant specialized in cryptocurrency portfolio analysis.

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
Format monetary amounts clearly (e.g., €1,234.56) and percentages with appropriate precision."""

    # Add provider-specific optimizations
    if provider == LLMProvider.ANTHROPIC:
        return (
            base_prompt
            + """

Claude-specific instructions:
- Provide detailed analytical reasoning for your recommendations
- Use structured thinking when analyzing complex portfolio scenarios
- Be thorough in your explanations while remaining concise
- Consider risk factors and market context in your analysis
- Offer actionable insights based on the portfolio data"""
        )

    elif provider == LLMProvider.OPENAI:
        return (
            base_prompt
            + """

OpenAI-specific instructions:
- Focus on clear, direct responses
- Use bullet points for complex information
- Provide step-by-step reasoning when appropriate
- Balance detail with brevity
- Emphasize practical recommendations"""
        )

    else:
        return base_prompt


def clear_chat_history():
    """Clear the chat message history."""
    if "chat_messages" in st.session_state:
        st.session_state.chat_messages = [
            {
                "role": "assistant",
                "content": "Chat history cleared! How can I help you with your portfolio?",
            }
        ]
