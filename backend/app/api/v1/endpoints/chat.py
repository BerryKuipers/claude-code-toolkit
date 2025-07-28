"""
Chat API endpoints.

Provides strongly typed REST endpoints for AI chat operations with function calling
support and comprehensive error handling.
"""

from fastapi import APIRouter, HTTPException

from ....core.dependencies import ChatServiceDep
from ....core.exceptions import (
    ChatServiceException,
    ConversationNotFoundException,
    FunctionNotFoundException,
    InvalidRequestException,
)
from ....models.chat import (
    AvailableFunctionsResponse,
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
    CreateConversationResponse,
    DeleteConversationResponse,
    FunctionDefinition,
    RefreshDataResponse,
)

router = APIRouter()


@router.post(
    "/query",
    response_model=ChatResponse,
    summary="Process Chat Query",
    description="Process a chat request with optional function calling support",
)
async def process_chat_query(request: ChatRequest, chat_service: ChatServiceDep) -> ChatResponse:
    """
    Process a chat request with AI function calling.

    This endpoint handles natural language queries about the portfolio
    and can execute functions to retrieve real-time data.

    Features:
    - Multi-model AI support (OpenAI, Anthropic)
    - Function calling for portfolio data
    - Cost tracking and token usage
    - Conversation context management

    Args:
        request: Chat request with message and configuration
        chat_service: Injected chat service

    Returns:
        ChatResponse: AI response with function call results

    Raises:
        HTTPException: If chat processing fails or request is invalid
    """
    try:
        return await chat_service.process_chat_request(request)
    except InvalidRequestException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ChatServiceException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/functions",
    response_model=AvailableFunctionsResponse,
    summary="Get Available Functions",
    description="Get list of all available functions for AI function calling",
)
async def get_available_functions(chat_service: ChatServiceDep) -> AvailableFunctionsResponse:
    """
    Get all available functions for AI function calling.

    Returns comprehensive list of functions that the AI can call
    to retrieve portfolio data, market analysis, and other information.

    Args:
        chat_service: Injected chat service

    Returns:
        AvailableFunctionsResponse: Available functions with definitions

    Raises:
        HTTPException: If function definitions cannot be retrieved
    """
    try:
        return await chat_service.get_available_functions()
    except ChatServiceException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/functions/{function_name}",
    response_model=FunctionDefinition,
    summary="Get Function Definition",
    description="Get definition for a specific function",
)
async def get_function_definition(
    function_name: str, chat_service: ChatServiceDep
) -> FunctionDefinition:
    """
    Get definition for a specific function.

    Args:
        function_name: Name of the function
        chat_service: Injected chat service

    Returns:
        FunctionDefinition: Function definition with parameters

    Raises:
        HTTPException: If function is not found or definition cannot be retrieved
    """
    try:
        return await chat_service.get_function_definition(function_name)
    except FunctionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ChatServiceException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/conversations",
    response_model=CreateConversationResponse,
    summary="Create Conversation",
    description="Create a new chat conversation",
)
async def create_conversation(chat_service: ChatServiceDep) -> CreateConversationResponse:
    """
    Create a new chat conversation.

    Args:
        chat_service: Injected chat service

    Returns:
        dict: New conversation information

    Raises:
        HTTPException: If conversation cannot be created
    """
    try:
        conversation_id = await chat_service.create_conversation()
        return CreateConversationResponse(
            conversation_id=conversation_id,
            message="Conversation created successfully"
        )
    except ChatServiceException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/conversations/{conversation_id}",
    response_model=ChatHistoryResponse,
    summary="Get Chat History",
    description="Get chat conversation history",
)
async def get_chat_history(
    conversation_id: str, chat_service: ChatServiceDep
) -> ChatHistoryResponse:
    """
    Get chat conversation history.

    Args:
        conversation_id: Conversation identifier
        chat_service: Injected chat service

    Returns:
        ChatHistoryResponse: Conversation history

    Raises:
        HTTPException: If conversation is not found or history cannot be retrieved
    """
    try:
        return await chat_service.get_chat_history(conversation_id)
    except ConversationNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ChatServiceException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/conversations/{conversation_id}",
    response_model=dict,
    summary="Delete Conversation",
    description="Delete a chat conversation and its history",
)
async def delete_conversation(conversation_id: str, chat_service: ChatServiceDep) -> dict:
    """
    Delete a chat conversation and its history.

    Args:
        conversation_id: Conversation identifier
        chat_service: Injected chat service

    Returns:
        dict: Deletion status

    Raises:
        HTTPException: If conversation is not found or deletion fails
    """
    try:
        success = await chat_service.delete_conversation(conversation_id)
        return {
            "success": success,
            "message": (
                "Conversation deleted successfully" if success else "Failed to delete conversation"
            ),
        }
    except ConversationNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ChatServiceException as e:
        raise HTTPException(status_code=500, detail=str(e))
