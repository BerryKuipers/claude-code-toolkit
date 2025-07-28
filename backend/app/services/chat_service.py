"""
Chat service implementation.

Provides business logic for AI chat operations with function calling support
and integration with existing chat functionality.
"""

import logging
import sys
import os
import uuid
import time
from datetime import datetime
from typing import Dict, List, Optional

# Add src to path to import existing chat logic
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

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

# Import existing chat functionality
from src.portfolio.chat.base_llm_client import LLMClientFactory, LLMProvider
from src.portfolio.chat.function_handlers import PortfolioFunctionHandler

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

        logger.info("Chat service initialized")

    def _get_llm_client(self):
        """Get or create LLM client instance."""
        if self._llm_client is None:
            # Determine which provider to use based on available API keys
            if self.settings.anthropic_api_key:
                provider = LLMProvider.ANTHROPIC
                api_key = self.settings.anthropic_api_key
                model = "claude-3-5-sonnet-20241022"
            elif self.settings.openai_api_key:
                provider = LLMProvider.OPENAI
                api_key = self.settings.openai_api_key
                model = "gpt-4"
            else:
                raise ChatServiceException("No AI API keys configured")

            self._llm_client = LLMClientFactory.create_client(
                provider=provider,
                api_key=api_key,
                model_id=model,
                temperature=self.settings.ai_temperature,
                max_tokens=self.settings.ai_max_tokens
            )

        return self._llm_client

    async def _get_function_handler(self):
        """Get or create function handler with current portfolio data."""
        if self._function_handler is None:
            # Get current portfolio data for function handler
            holdings = await self.portfolio_service.get_current_holdings()

            # Convert holdings to DataFrame format expected by function handler
            import pandas as pd
            portfolio_data = []

            for holding in holdings:
                portfolio_data.append({
                    "Asset": holding.asset,
                    "Actual Amount": float(holding.quantity),
                    "Actual Value €": float(holding.value_eur),
                    "Total Return %": float(holding.total_return_percentage),
                    "Unrealised €": float(holding.unrealized_pnl),
                    "Current Price €": float(holding.current_price),
                })

            df = pd.DataFrame(portfolio_data)
            self._function_handler = PortfolioFunctionHandler(df)

        return self._function_handler
    
    def _create_function_definitions(self) -> List[FunctionDefinition]:
        """Create function definitions for AI function calling."""
        return [
            FunctionDefinition(
                name="get_portfolio_summary",
                description="Get overall portfolio summary with total value, P&L, and key metrics",
                parameters=[]
            ),
            FunctionDefinition(
                name="get_current_holdings",
                description="Get list of all currently held assets with amounts and values",
                parameters=[]
            ),
            FunctionDefinition(
                name="get_asset_performance",
                description="Get detailed performance data for a specific asset",
                parameters=[
                    FunctionParameter(
                        name="asset",
                        type=FunctionParameterType.STRING,
                        description="Asset symbol (e.g., 'BTC', 'ETH')",
                        required=True
                    )
                ]
            ),
            FunctionDefinition(
                name="get_market_opportunities",
                description="Analyze current market for investment opportunities",
                parameters=[]
            )
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
            llm_client = self._get_llm_client()
            function_handler = await self._get_function_handler() if request.use_function_calling else None

            # Prepare messages
            system_prompt = self._get_system_prompt(llm_client.provider)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message},
            ]

            # Get available functions if function calling is enabled
            functions = function_handler.get_available_functions() if function_handler else []

            # Process with AI client
            if hasattr(llm_client, "handle_function_calling_conversation") and function_handler:
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
                    max_tokens=request.max_tokens
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

                            function_calls.append(FunctionCallResponse(
                                function_name=func_call["name"],
                                result=result,
                                success=True,
                                execution_time_ms=(func_end_time - func_start_time) * 1000
                            ))
                        except Exception as e:
                            function_calls.append(FunctionCallResponse(
                                function_name=func_call["name"],
                                result=None,
                                success=False,
                                error_message=str(e),
                                execution_time_ms=0.0
                            ))

            # Calculate response time
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000

            # Get token usage and cost estimate
            token_usage = {"input_tokens": 0, "output_tokens": 0}
            cost_estimate = 0.0

            if hasattr(llm_client, 'last_usage'):
                token_usage = llm_client.last_usage
                cost_estimate = llm_client.calculate_cost(
                    token_usage.get("input_tokens", 0),
                    token_usage.get("output_tokens", 0)
                )

            # Store conversation
            if conversation_id not in self._conversations:
                self._conversations[conversation_id] = []

            self._conversations[conversation_id].extend([
                ChatMessage(
                    role=MessageRole.USER,
                    content=request.message,
                    timestamp=datetime.utcnow()
                ),
                ChatMessage(
                    role=MessageRole.ASSISTANT,
                    content=ai_response,
                    timestamp=datetime.utcnow()
                )
            ])

            return ChatResponse(
                message=ai_response,
                conversation_id=conversation_id,
                model_used=llm_client.model_id,
                function_calls=function_calls,
                token_usage=token_usage,
                response_time_ms=response_time_ms,
                cost_estimate=cost_estimate
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
            categories = {
                "Portfolio": [],
                "Market": [],
                "Analysis": [],
                "Research": []
            }

            for func in raw_functions:
                func_name = func["name"]

                # Convert parameters
                parameters = []
                if "parameters" in func and "properties" in func["parameters"]:
                    for param_name, param_info in func["parameters"]["properties"].items():
                        param_type = param_info.get("type", "string")
                        # Map JSON schema types to our enum
                        type_mapping = {
                            "string": FunctionParameterType.STRING,
                            "number": FunctionParameterType.NUMBER,
                            "integer": FunctionParameterType.INTEGER,
                            "boolean": FunctionParameterType.BOOLEAN,
                            "array": FunctionParameterType.ARRAY,
                            "object": FunctionParameterType.OBJECT
                        }

                        parameters.append(FunctionParameter(
                            name=param_name,
                            type=type_mapping.get(param_type, FunctionParameterType.STRING),
                            description=param_info.get("description", ""),
                            required=param_name in func["parameters"].get("required", [])
                        ))

                function_def = FunctionDefinition(
                    name=func_name,
                    description=func["description"],
                    parameters=parameters
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
                categories=categories
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
                created_at=messages[0].timestamp if messages else datetime.utcnow(),
                last_updated=messages[-1].timestamp if messages else datetime.utcnow()
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
