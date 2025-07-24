"""
Chat service interface definition.

Defines the contract for AI chat operations with function calling support
and full type safety.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ...models.chat import (
    AvailableFunctionsResponse,
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
    FunctionDefinition,
)


class IChatService(ABC):
    """
    Chat service interface providing C#-like contract definition.
    
    This interface defines all AI chat-related operations with strong typing
    and clear separation of concerns.
    """
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def get_available_functions(self) -> AvailableFunctionsResponse:
        """
        Get list of all available functions for AI function calling.
        
        Returns:
            AvailableFunctionsResponse: Available functions with definitions
            
        Raises:
            ChatServiceException: If function definitions cannot be retrieved
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def create_conversation(self) -> str:
        """
        Create a new chat conversation.
        
        Returns:
            str: New conversation ID
            
        Raises:
            ChatServiceException: If conversation cannot be created
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
