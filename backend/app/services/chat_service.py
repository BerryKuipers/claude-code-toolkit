"""
Chat service implementation.

Provides business logic for AI chat operations with function calling support
and integration with existing chat functionality.
"""

import logging
import os
import sys
import time
import uuid
from datetime import datetime, UTC
from typing import Dict, List, Optional

# Set environment variables from backend config at module level
# This ensures they're available before any LLM client imports
try:
    from ..core.config import get_settings
    _settings = get_settings()
    if _settings.openai_api_key:
        os.environ["OPENAI_API_KEY"] = _settings.openai_api_key
    if _settings.anthropic_api_key:
        os.environ["ANTHROPIC_API_KEY"] = _settings.anthropic_api_key
except Exception:
    # If config loading fails, continue without setting env vars
    pass

# Add src to path to import existing chat logic
# Find the project root and add src to path
current_file = os.path.abspath(__file__)
# Go up: file -> services -> app -> backend -> project_root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))
src_path = os.path.join(project_root, "src")

# Verify src directory exists and add to path
if os.path.exists(src_path):
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
else:
    # Try alternative locations
    alternative_paths = [
        os.path.join(os.getcwd(), "src"),  # From current working directory
        os.path.join(os.path.dirname(os.getcwd()), "src"),  # One level up
        os.path.abspath("../src"),  # Relative to current directory
    ]

    src_found = False
    for alt_path in alternative_paths:
        if os.path.exists(alt_path):
            src_path = alt_path
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
            src_found = True
            break

    if not src_found:
        # Create a more informative error message
        current_dir = os.getcwd()
        file_dir = os.path.dirname(os.path.abspath(__file__))
        raise ImportError(
            f"Could not find 'src' directory.\n"
            f"Current working directory: {current_dir}\n"
            f"Current file directory: {file_dir}\n"
            f"Project root (calculated): {project_root}\n"
            f"Expected src path: {src_path}\n"
            f"Tried alternative paths: {alternative_paths}\n"
            f"Please ensure you're running from the project root directory."
        )

# Import existing chat functionality
# Import will be done lazily in _get_llm_client method to avoid import issues
# Import will be done lazily to avoid import issues

from ..core.config import Settings
from ..core.exceptions import (
    ChatServiceException,
    ConversationNotFoundException,
    FunctionNotFoundException,
    InvalidRequestException,
)
from ..models.chat import (
    AvailableFunctionsResponse,
    ChatHistoryResponse,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    FunctionCallResponse,
    FunctionDefinition,
    FunctionParameter,
    FunctionParameterType,
    MessageRole,
)
from .interfaces.chat_service import IChatService
from .interfaces.portfolio_service import IPortfolioService

logger = logging.getLogger(__name__)


class ChatService(IChatService):
    """
    Chat service implementation providing C#-like business logic layer.

    This service integrates with existing AI chat functionality
    and provides strongly typed responses for the API.
    """

    def __init__(self, settings: Settings, portfolio_service: IPortfolioService):
        """
        Initialize chat service with configuration and dependencies.

        Args:
            settings: Application settings
            portfolio_service: Portfolio service for function calling
        """
        self.settings = settings
        self.portfolio_service = portfolio_service
        self._conversations: Dict[str, List[ChatMessage]] = {}
        self._function_definitions = self._create_function_definitions()

        # Initialize AI clients
        self._llm_client = None
        self._function_handler = None
        self._cached_portfolio_data = None
        self._cache_timestamp = None

        logger.info("Chat service initialized")

    def _get_llm_client(self, model_preference: Optional[str] = None):
        """Get or create LLM client instance using backend configuration."""

        # If model preference is provided, create a new client for that model
        if model_preference:
            try:
                from src.portfolio.chat.base_llm_client import LLMClientFactory
                return LLMClientFactory.create_client(model_preference)
            except Exception as e:
                logger.warning(f"Failed to create client for preferred model {model_preference}: {e}")
                # Fall back to default behavior

        if self._llm_client is None:
            # Lazy import to avoid module-level import issues
            try:
                from src.portfolio.chat.base_llm_client import LLMClientFactory
            except ImportError as e:
                raise ChatServiceException(f"Failed to import LLM client: {e}")



            # Use the factory's default model selection based on available API keys
            try:
                model_key = LLMClientFactory.get_default_model()
                self._llm_client = LLMClientFactory.create_client(model_key)
            except Exception as e:
                raise ChatServiceException(f"Failed to create LLM client: {e}")

        return self._llm_client

    async def _get_function_handler(self, force_refresh: bool = False):
        """Get or create function handler with current portfolio data."""
        import time

        # Check if we need to refresh the cache (5 minutes cache)
        current_time = time.time()
        cache_expired = (
            self._cache_timestamp is None
            or (current_time - self._cache_timestamp) > 300  # 5 minutes
        )

        if self._function_handler is None or force_refresh or cache_expired:
            logger.info("🔄 Refreshing portfolio data for function handler...")

            # Get current portfolio data for function handler
            holdings = await self.portfolio_service.get_current_holdings()

            # Convert holdings to DataFrame format expected by function handler
            import pandas as pd

            portfolio_data = []

            for holding in holdings:
                portfolio_data.append(
                    {
                        "Asset": holding.asset,
                        "Actual Amount": float(holding.quantity),
                        "Actual Value €": float(holding.value_eur),
                        "Total Return %": float(holding.total_return_percentage),
                        "Unrealised €": float(holding.unrealized_pnl),
                        "Current Price €": float(holding.current_price),
                    }
                )

            df = pd.DataFrame(portfolio_data)

            # Lazy import to avoid module-level import issues
            try:
                from src.portfolio.chat.function_handlers import PortfolioFunctionHandler
            except ImportError as e:
                raise ChatServiceException(f"Failed to import function handler: {e}")

            self._function_handler = PortfolioFunctionHandler(df)
            self._cached_portfolio_data = df
            self._cache_timestamp = current_time

            logger.info(f"✅ Portfolio data cached with {len(df)} holdings")
        else:
            logger.info("📋 Using cached portfolio data for function handler")

        return self._function_handler

    def _get_portfolio_context_summary(self) -> str:
        """Generate a concise portfolio context summary to reduce redundant function calls."""
        if self._cached_portfolio_data is None or self._cached_portfolio_data.empty:
            return "No portfolio data available."

        df = self._cached_portfolio_data
        total_holdings = len(df)
        total_value = df["Actual Value €"].sum()

        # Get top 5 holdings by value
        top_holdings = df.nlargest(5, "Actual Value €")
        holdings_summary = []

        for _, row in top_holdings.iterrows():
            holdings_summary.append(
                f"- {row['Asset']}: {row['Actual Amount']:.4f} (€{row['Actual Value €']:.2f}, {row['Total Return %']:.1f}%)"
            )

        context = f"""You have access to current portfolio data with {total_holdings} holdings worth €{total_value:.2f} total.

Top holdings:
{chr(10).join(holdings_summary)}

For detailed analysis, you can use the available functions, but avoid calling get_current_holdings() unless specifically requested as this data is already available."""

        return context

    def _create_function_definitions(self) -> List[FunctionDefinition]:
        """Create function definitions for AI function calling."""
        return [
            FunctionDefinition(
                name="get_portfolio_summary",
                description="Get overall portfolio summary with total value, P&L, and key metrics",
                parameters=[],
            ),
            FunctionDefinition(
                name="get_current_holdings",
                description="Get list of all currently held assets with amounts and values",
                parameters=[],
            ),
            FunctionDefinition(
                name="get_asset_performance",
                description="Get detailed performance data for a specific asset",
                parameters=[
                    FunctionParameter(
                        name="asset",
                        type=FunctionParameterType.STRING,
                        description="Asset symbol (e.g., 'BTC', 'ETH')",
                        required=True,
                    )
                ],
            ),
            FunctionDefinition(
                name="get_market_opportunities",
                description="Analyze current market for investment opportunities",
                parameters=[],
            ),
        ]

    async def process_chat_request(self, request: ChatRequest) -> ChatResponse:
        """
        Process a chat request with optional function calling.

        Args:
            request: Chat request with message and configuration

        Returns:
            ChatResponse: AI response with function call results

        Raises:
            ChatServiceException: If chat processing fails
            InvalidRequestException: If request is malformed
        """
        try:
            start_time = time.time()
            logger.info(f"Processing chat request: {request.message[:100]}...")

            # Validate request
            if not request.message.strip():
                raise InvalidRequestException("Message cannot be empty")

            # Generate conversation ID if not provided
            conversation_id = request.conversation_id or str(uuid.uuid4())

            # Get AI client and function handler
            llm_client = self._get_llm_client(request.model_preference)
            function_handler = None

            if request.use_function_calling:
                try:
                    function_handler = await self._get_function_handler()
                except Exception as e:
                    logger.warning(f"Failed to initialize function handler: {e}")
                    # Continue without function calling if portfolio data unavailable
                    logger.info("Continuing chat without function calling due to data unavailability")

            # Prepare messages with portfolio context
            system_prompt = self._get_system_prompt(llm_client.provider)

            # Add portfolio context if function calling is enabled
            if request.use_function_calling and self._cached_portfolio_data is not None:
                portfolio_summary = self._get_portfolio_context_summary()
                system_prompt += f"\n\nCURRENT PORTFOLIO CONTEXT:\n{portfolio_summary}"
            elif request.use_function_calling and function_handler is None:
                # Add notice about limited functionality when API is unavailable
                system_prompt += "\n\nNOTE: Portfolio data is currently unavailable due to API limitations. You can still provide general crypto advice and analysis, but cannot access specific portfolio information."

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message},
            ]

            # Get available functions if function calling is enabled
            functions = (
                function_handler.get_available_functions() if function_handler else []
            )

            # Process with AI client
            if (
                hasattr(llm_client, "handle_function_calling_conversation")
                and function_handler
            ):
                # Claude-style function calling
                ai_response = llm_client.handle_function_calling_conversation(
                    messages, functions, function_handler
                )
                function_calls = []  # Function calls are handled internally
            else:
                # OpenAI-style or no function calling
                response = llm_client.chat_completion(
                    messages=messages,
                    functions=functions if function_handler else None,
                    function_call="auto" if function_handler else None,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                )

                ai_response = llm_client.get_response_content(response)

                # Handle function calls if any
                function_calls = []
                if function_handler:
                    raw_function_calls = llm_client.get_function_calls(response)
                    for func_call in raw_function_calls:
                        try:
                            func_start_time = time.time()
                            result = function_handler.handle_function_call(
                                func_call["name"], func_call["arguments"]
                            )
                            func_end_time = time.time()

                            function_calls.append(
                                FunctionCallResponse(
                                    function_name=func_call["name"],
                                    result=result,
                                    success=True,
                                    execution_time_ms=(func_end_time - func_start_time)
                                    * 1000,
                                )
                            )
                        except Exception as e:
                            function_calls.append(
                                FunctionCallResponse(
                                    function_name=func_call["name"],
                                    result=None,
                                    success=False,
                                    error_message=str(e),
                                    execution_time_ms=0.0,
                                )
                            )

            # Calculate response time
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000

            # Get token usage and cost estimate
            token_usage = {"input_tokens": 0, "output_tokens": 0}
            cost_estimate = 0.0

            if hasattr(llm_client, "last_usage"):
                token_usage = llm_client.last_usage
                cost_estimate = llm_client.calculate_cost(
                    token_usage.get("input_tokens", 0),
                    token_usage.get("output_tokens", 0),
                )

            # Store conversation
            if conversation_id not in self._conversations:
                self._conversations[conversation_id] = []

            self._conversations[conversation_id].extend(
                [
                    ChatMessage(
                        role=MessageRole.USER,
                        content=request.message,
                        timestamp=datetime.now(UTC),
                    ),
                    ChatMessage(
                        role=MessageRole.ASSISTANT,
                        content=ai_response,
                        timestamp=datetime.now(UTC),
                    ),
                ]
            )

            return ChatResponse(
                message=ai_response,
                conversation_id=conversation_id,
                model_used=llm_client.model_id,
                function_calls=function_calls,
                token_usage=token_usage,
                response_time_ms=response_time_ms,
                cost_estimate=cost_estimate,
            )

        except InvalidRequestException:
            raise
        except Exception as e:
            logger.error(f"Error processing chat request: {e}")
            raise ChatServiceException(f"Failed to process chat request: {str(e)}")

    def _get_system_prompt(self, provider) -> str:
        """Get system prompt for the AI model."""
        return """You are a crypto portfolio analysis assistant with access to real-time portfolio data and market information.

You have access to powerful functions that can:
- Analyze portfolio performance and holdings
- Provide market insights and predictions
- Explain complex crypto concepts
- Search for current market information
- Generate detailed analysis reports

IMPORTANT: You MUST use function calls when users ask about:
- Portfolio data, holdings, or performance
- Market analysis or predictions
- Specific coin information or explanations
- Current prices or market trends

Always provide detailed, accurate analysis based on the function call results. Be helpful, informative, and professional in your responses."""

    async def get_available_functions(self) -> AvailableFunctionsResponse:
        """
        Get list of all available functions for AI function calling.

        Returns:
            AvailableFunctionsResponse: Available functions with definitions

        Raises:
            ChatServiceException: If function definitions cannot be retrieved
        """
        try:
            logger.info("Getting available functions")

            function_handler = await self._get_function_handler()
            raw_functions = function_handler.get_available_functions()

            # Convert to our function definition format
            functions = []
            categories = {"Portfolio": [], "Market": [], "Analysis": [], "Research": []}

            for func in raw_functions:
                func_name = func["name"]

                # Convert parameters
                parameters = []
                if "parameters" in func and "properties" in func["parameters"]:
                    for param_name, param_info in func["parameters"][
                        "properties"
                    ].items():
                        param_type = param_info.get("type", "string")
                        # Map JSON schema types to our enum
                        type_mapping = {
                            "string": FunctionParameterType.STRING,
                            "number": FunctionParameterType.NUMBER,
                            "integer": FunctionParameterType.INTEGER,
                            "boolean": FunctionParameterType.BOOLEAN,
                            "array": FunctionParameterType.ARRAY,
                            "object": FunctionParameterType.OBJECT,
                        }

                        parameters.append(
                            FunctionParameter(
                                name=param_name,
                                type=type_mapping.get(
                                    param_type, FunctionParameterType.STRING
                                ),
                                description=param_info.get("description", ""),
                                required=param_name
                                in func["parameters"].get("required", []),
                            )
                        )

                function_def = FunctionDefinition(
                    name=func_name,
                    description=func["description"],
                    parameters=parameters,
                )
                functions.append(function_def)

                # Categorize functions
                if "portfolio" in func_name.lower() or "holding" in func_name.lower():
                    categories["Portfolio"].append(func_name)
                elif "market" in func_name.lower() or "price" in func_name.lower():
                    categories["Market"].append(func_name)
                elif "explain" in func_name.lower() or "analyze" in func_name.lower():
                    categories["Analysis"].append(func_name)
                elif "search" in func_name.lower() or "research" in func_name.lower():
                    categories["Research"].append(func_name)
                else:
                    categories["Portfolio"].append(func_name)  # Default category

            return AvailableFunctionsResponse(
                functions=functions,
                total_functions=len(functions),
                categories=categories,
            )

        except Exception as e:
            logger.error(f"Error getting available functions: {e}")
            raise ChatServiceException(f"Failed to get available functions: {str(e)}")

    async def get_chat_history(self, conversation_id: str) -> ChatHistoryResponse:
        """
        Get chat conversation history.

        Args:
            conversation_id: Conversation identifier

        Returns:
            ChatHistoryResponse: Conversation history

        Raises:
            ConversationNotFoundException: If conversation is not found
            ChatServiceException: If history cannot be retrieved
        """
        try:
            logger.info(f"Getting chat history for conversation: {conversation_id}")

            if conversation_id not in self._conversations:
                raise ConversationNotFoundException(conversation_id)

            messages = self._conversations[conversation_id]

            return ChatHistoryResponse(
                conversation_id=conversation_id,
                messages=messages,
                total_messages=len(messages),
                total_cost=len(messages) * 0.001,  # Mock cost calculation
                created_at=messages[0].timestamp if messages else datetime.now(UTC),
                last_updated=messages[-1].timestamp if messages else datetime.now(UTC),
            )

        except ConversationNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            raise ChatServiceException(f"Failed to get chat history: {str(e)}")

    async def create_conversation(self) -> str:
        """
        Create a new chat conversation.

        Returns:
            str: New conversation ID

        Raises:
            ChatServiceException: If conversation cannot be created
        """
        try:
            conversation_id = str(uuid.uuid4())
            self._conversations[conversation_id] = []

            logger.info(f"Created new conversation: {conversation_id}")
            return conversation_id

        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            raise ChatServiceException(f"Failed to create conversation: {str(e)}")

    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a chat conversation and its history.

        Args:
            conversation_id: Conversation identifier

        Returns:
            bool: True if deletion was successful

        Raises:
            ConversationNotFoundException: If conversation is not found
            ChatServiceException: If deletion fails
        """
        try:
            logger.info(f"Deleting conversation: {conversation_id}")

            if conversation_id not in self._conversations:
                raise ConversationNotFoundException(conversation_id)

            del self._conversations[conversation_id]
            return True

        except ConversationNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            raise ChatServiceException(f"Failed to delete conversation: {str(e)}")

    async def get_function_definition(self, function_name: str) -> FunctionDefinition:
        """
        Get definition for a specific function.

        Args:
            function_name: Name of the function

        Returns:
            FunctionDefinition: Function definition with parameters

        Raises:
            FunctionNotFoundException: If function is not found
            ChatServiceException: If definition cannot be retrieved
        """
        try:
            logger.info(f"Getting function definition for: {function_name}")

            for func_def in self._function_definitions:
                if func_def.name == function_name:
                    return func_def

            raise FunctionNotFoundException(function_name)

        except FunctionNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error getting function definition: {e}")
            raise ChatServiceException(f"Failed to get function definition: {str(e)}")
