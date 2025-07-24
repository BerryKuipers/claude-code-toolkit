"""Streamlit chat interface for portfolio AI assistant."""

import logging
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from .api_status import get_error_suggestion, render_error_help
from .base_llm_client import LLMClientFactory, LLMProvider
from .cost_tracker import CostTracker, render_cost_footer, render_detailed_cost_analysis
from .function_handlers import PortfolioFunctionHandler
from .model_selector import (
    render_model_selector,
    render_model_status_indicator,
    show_model_switch_success,
)
from .orchestrator import OrchestratorAgent
from .prompt_editor import PromptEditor

logger = logging.getLogger(__name__)


def render_chat_interface(portfolio_data: pd.DataFrame):
    """Render the AI chat interface for portfolio queries.

    Args:
        portfolio_data: DataFrame containing portfolio information
    """
    # Get selected model from session state (configured in Settings tab)
    if "selected_model" not in st.session_state:
        from .base_llm_client import LLMClientFactory

        st.session_state.selected_model = LLMClientFactory.get_default_model()

    selected_model = st.session_state.selected_model

    # Check if model changed (from Settings tab)
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

    # Header with model status
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("💬 Portfolio Chat")
    with col2:
        # Show current model status (compact)
        render_model_status_indicator(selected_model)
        st.caption("*Configure in Settings tab*")

    # Initialize session state for chat
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {
                "role": "assistant",
                "content": "Hi! I'm your portfolio AI assistant. Ask me anything about your crypto portfolio - performance, allocations, specific coins, or get detailed explanations of your positions!",
            }
        ]

    # Use existing cost tracker from main dashboard (don't create a new one)
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

    # Add detailed cost analysis (keep this for the chat interface)
    render_detailed_cost_analysis()


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
        system_prompt = _get_system_prompt(llm_client.provider)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        # Get available functions
        functions = function_handler.get_available_functions()

        # Debug logging
        logger.info(f"Function calling setup: {len(functions)} functions available")
        logger.info(
            f"System prompt contains function calling instructions: {'MUST use function calls' in system_prompt}"
        )
        logger.info(
            f"Client supports function calling: {llm_client.supports_function_calling()}"
        )

        # Check if client supports function calling
        if not llm_client.supports_function_calling():
            logger.warning(
                "Function calling not supported - falling back to simple chat"
            )
            # Simple chat without function calling
            response = llm_client.chat_completion(messages=messages)
            return llm_client.get_response_content(response)

        # Use provider-specific function calling if available
        if hasattr(llm_client, "handle_function_calling_conversation"):
            # Claude-style function calling
            logger.info("Using Claude-style function calling")
            return llm_client.handle_function_calling_conversation(
                messages, functions, function_handler
            )
        else:
            # OpenAI-style function calling
            logger.info("Using OpenAI-style function calling")
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
    logger.info(f"Making OpenAI API call with {len(functions)} functions")

    # Make initial API call
    response = llm_client.chat_completion(
        messages=messages, functions=functions, function_call="auto"
    )

    # Check if function calls were made
    function_calls = llm_client.get_function_calls(response)
    logger.info(f"Received {len(function_calls)} function calls from API")

    if function_calls:
        logger.info("Processing function calls...")
        # Handle function calls
        for func_call in function_calls:
            function_name = func_call["name"]
            function_args = func_call["arguments"]
            logger.info(
                f"Executing function: {function_name} with args: {function_args}"
            )

            # Execute function
            function_result = function_handler.handle_function_call(
                function_name, function_args
            )
            logger.info(
                f"Function {function_name} returned {len(str(function_result))} characters"
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
        logger.info("Getting final response with function results...")
        final_response = llm_client.chat_completion(messages=messages)
        final_content = llm_client.get_response_content(final_response)
        logger.info(f"Final response: {len(final_content)} characters")
        return final_content

    else:
        # No function calls, return direct response
        logger.warning(
            "No function calls made - returning direct response (this may be generic)"
        )
        direct_content = llm_client.get_response_content(response)
        logger.info(f"Direct response: {len(direct_content)} characters")
        return direct_content


def _get_system_prompt(provider: LLMProvider = None) -> str:
    """Get the system prompt for the portfolio AI assistant.

    Args:
        provider: LLM provider to optimize prompt for

    Returns:
        Optimized system prompt
    """
    base_prompt = """You are an expert cryptocurrency portfolio analyst with access to the user's real portfolio data through function calls.

CRITICAL: You MUST use function calls to analyze the actual portfolio data before providing any recommendations or analysis. Never give generic advice without first examining the real data.

WORKFLOW FOR ALL QUERIES:
1. ALWAYS start by calling get_portfolio_summary() to understand the current portfolio state
2. Use additional specific functions based on the user's question
3. Provide specific, data-driven recommendations based on the actual portfolio analysis
4. Include concrete numbers, percentages, and specific asset recommendations

🚨 MANDATORY WORKFLOW for investment questions ("what coin should I buy", "new coin to add", etc.):
1. 📋 FIRST call get_current_holdings() - REQUIRED to see current assets
2. 📊 Call get_portfolio_summary() - REQUIRED to see allocations and performance
3. 🔍 Call analyze_market_opportunities() - REQUIRED to identify trending sectors and specific coins
4. 📰 Call search_crypto_news() - REQUIRED to research current market opportunities
5. ⚖️ Call get_risk_assessment() - REQUIRED to understand risk profile
6. 🎯 Provide SPECIFIC coin recommendations with exact reasoning, amounts, and percentages
7. ✅ ALWAYS mention if suggested coins are already held and adjust recommendations accordingly

YOU MUST CALL ALL 5 FUNCTIONS ABOVE when user asks about buying new coins. No exceptions.

Available functions:
- get_current_holdings: Get list of all currently held assets (CRITICAL - use first for investment recommendations)
- get_portfolio_summary: Overall portfolio metrics and performance
- get_asset_performance: Detailed performance data for specific assets
- search_crypto_news: Search latest crypto news and analysis using Perplexity AI
- analyze_market_opportunities: Analyze current market opportunities and trends
- get_technical_analysis: Technical indicators and trading signals
- get_risk_assessment: Portfolio risk and diversification analysis
- compare_with_market: Compare portfolio performance with market benchmarks
- get_trading_signals: Get AI-powered trading signals and recommendations
- find_similar_assets: Find assets similar to current holdings
- get_correlation_analysis: Analyze correlations between assets
- get_rebalancing_suggestions: Portfolio rebalancing recommendations
- get_tax_implications: Tax implications of trades
- get_profit_loss_breakdown: Detailed P&L analysis

NEVER provide generic suggestions like "research projects" or "consider market trends" - instead USE THE FUNCTIONS to do that research and provide specific, actionable recommendations based on the actual portfolio data.

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
