"""
Chat service implementation.

Provides business logic for AI chat operations with function calling support
and integration with existing chat functionality.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional

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
        
        logger.info("Chat service initialized")
    
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
            logger.info(f"Processing chat request: {request.message[:100]}...")
            
            # Validate request
            if not request.message.strip():
                raise InvalidRequestException("Message cannot be empty")
            
            # Generate conversation ID if not provided
            conversation_id = request.conversation_id or str(uuid.uuid4())
            
            # TODO: Integrate with existing AI chat logic
            # For now, return a mock response
            
            # Simulate function calling based on message content
            function_calls = []
            if "portfolio" in request.message.lower() or "summary" in request.message.lower():
                function_calls.append(FunctionCallResponse(
                    function_name="get_portfolio_summary",
                    result={"total_value": "10000.00", "total_return": "17.65%"},
                    success=True,
                    execution_time_ms=150.0
                ))
            
            if "holdings" in request.message.lower() or "assets" in request.message.lower():
                function_calls.append(FunctionCallResponse(
                    function_name="get_current_holdings",
                    result=[{"asset": "BTC", "value": "11250.00"}, {"asset": "ETH", "value": "7500.00"}],
                    success=True,
                    execution_time_ms=200.0
                ))
            
            # Generate AI response
            ai_response = self._generate_ai_response(request.message, function_calls)
            
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
                model_used=request.model_preference or self.settings.default_ai_model,
                function_calls=function_calls,
                token_usage={"input_tokens": 50, "output_tokens": 100},
                response_time_ms=500.0,
                cost_estimate=0.002
            )
            
        except InvalidRequestException:
            raise
        except Exception as e:
            logger.error(f"Error processing chat request: {e}")
            raise ChatServiceException(f"Failed to process chat request: {str(e)}")
    
    def _generate_ai_response(self, message: str, function_calls: List[FunctionCallResponse]) -> str:
        """Generate AI response based on message and function call results."""
        if function_calls:
            # Generate response incorporating function call results
            if any(fc.function_name == "get_portfolio_summary" for fc in function_calls):
                return "Based on your portfolio data, you have a total value of €10,000 with a 17.65% return. Your portfolio is performing well!"
            elif any(fc.function_name == "get_current_holdings" for fc in function_calls):
                return "Your current holdings include BTC (€11,250) and ETH (€7,500). Both assets are showing positive performance."
        
        # Default response
        return f"I understand you're asking about: '{message}'. I'm here to help with your crypto portfolio analysis!"
    
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
            
            categories = {
                "Portfolio": ["get_portfolio_summary", "get_current_holdings", "get_asset_performance"],
                "Market": ["get_market_opportunities"],
            }
            
            return AvailableFunctionsResponse(
                functions=self._function_definitions,
                total_functions=len(self._function_definitions),
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
