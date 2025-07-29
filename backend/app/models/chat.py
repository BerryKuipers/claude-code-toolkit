"""
AI Chat Pydantic models.

These models provide strongly typed interfaces for AI chat interactions,
function calling, and response handling with full validation.
"""

from datetime import datetime, UTC
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator

from .common import BaseResponse


class MessageRole(str, Enum):
    """Chat message roles."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


class FunctionParameterType(str, Enum):
    """Function parameter types."""

    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


class ChatMessage(BaseModel):
    """Individual chat message."""

    role: MessageRole = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Message timestamp"
    )
    function_call: Optional[Dict[str, Any]] = Field(
        None, description="Function call data"
    )

    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Message content cannot be empty")
        return v


class FunctionParameter(BaseModel):
    """Function parameter definition."""

    name: str = Field(..., description="Parameter name")
    type: FunctionParameterType = Field(..., description="Parameter type")
    description: str = Field(..., description="Parameter description")
    required: bool = Field(False, description="Whether parameter is required")
    enum_values: Optional[List[str]] = Field(
        None, description="Allowed values for enum parameters"
    )

    @field_validator("name")
    @classmethod
    def validate_parameter_name(cls, v):
        if not v.isidentifier():
            raise ValueError("Parameter name must be a valid identifier")
        return v


class FunctionDefinition(BaseModel):
    """AI function definition for function calling."""

    name: str = Field(..., description="Function name")
    description: str = Field(..., description="Function description")
    parameters: List[FunctionParameter] = Field(..., description="Function parameters")

    @field_validator("name")
    @classmethod
    def validate_function_name(cls, v):
        if not v.isidentifier():
            raise ValueError("Function name must be a valid identifier")
        return v


class FunctionCallRequest(BaseModel):
    """Function call request data."""

    function_name: str = Field(..., description="Name of function to call")
    arguments: Dict[str, Any] = Field(..., description="Function arguments")

    @field_validator("function_name")
    @classmethod
    def validate_function_name(cls, v):
        if not v.isidentifier():
            raise ValueError("Function name must be a valid identifier")
        return v


class FunctionCallResponse(BaseModel):
    """Function call response data."""

    function_name: str = Field(..., description="Name of function called")
    result: Any = Field(..., description="Function execution result")
    success: bool = Field(..., description="Whether function call succeeded")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    execution_time_ms: float = Field(
        ..., description="Function execution time in milliseconds"
    )


class ChatRequest(BaseModel):
    """Chat request with message and optional function calling."""

    message: str = Field(..., description="User message/query")
    conversation_id: Optional[str] = Field(
        None, description="Conversation ID for context"
    )
    use_function_calling: bool = Field(
        True, description="Whether to enable function calling"
    )
    model_preference: Optional[str] = Field(None, description="Preferred AI model")
    temperature: float = Field(0.1, description="Response creativity (0.0-1.0)")
    max_tokens: Optional[int] = Field(None, description="Maximum response tokens")

    @field_validator("message")
    @classmethod
    def validate_message_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v

    @field_validator("temperature")
    @classmethod
    def validate_temperature_range(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Temperature must be between 0.0 and 1.0")
        return v


class ChatResponse(BaseResponse):
    """AI chat response with function call results."""

    message: str = Field(..., description="AI response message")
    conversation_id: str = Field(..., description="Conversation ID")
    model_used: str = Field(..., description="AI model that generated response")
    function_calls: List[FunctionCallResponse] = Field(
        default_factory=list, description="Function calls made"
    )
    token_usage: Dict[str, int] = Field(..., description="Token usage statistics")
    response_time_ms: float = Field(
        ..., description="Total response time in milliseconds"
    )
    cost_estimate: float = Field(..., description="Estimated cost in USD")

    @field_validator("message")
    @classmethod
    def validate_response_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Response message cannot be empty")
        return v


class ChatHistoryResponse(BaseResponse):
    """Chat conversation history."""

    conversation_id: str = Field(..., description="Conversation ID")
    messages: List[ChatMessage] = Field(..., description="Conversation messages")
    total_messages: int = Field(..., description="Total message count")
    total_cost: float = Field(..., description="Total conversation cost in USD")
    created_at: datetime = Field(..., description="Conversation start time")
    last_updated: datetime = Field(..., description="Last message timestamp")


class AvailableFunctionsResponse(BaseResponse):
    """Available AI functions response."""

    functions: List[FunctionDefinition] = Field(..., description="Available functions")
    total_functions: int = Field(..., description="Total function count")
    categories: Dict[str, List[str]] = Field(
        ..., description="Functions grouped by category"
    )


class ChatHistoryResponse(BaseResponse):
    """Response model for chat conversation history."""

    conversation_id: str = Field(..., description="Conversation identifier")
    messages: List[ChatMessage] = Field(
        ..., description="Chat messages in conversation"
    )
    total_messages: int = Field(..., description="Total number of messages")
    total_cost: float = Field(..., description="Total cost of conversation")
    created_at: datetime = Field(..., description="Conversation creation timestamp")
    last_updated: datetime = Field(..., description="Last message timestamp")


class CreateConversationResponse(BaseResponse):
    """Response model for creating a new conversation."""

    conversation_id: str = Field(..., description="New conversation identifier")
    message: str = Field(..., description="Success message")


class DeleteConversationResponse(BaseResponse):
    """Response model for deleting a conversation."""

    success: bool = Field(..., description="Whether deletion was successful")
    message: str = Field(..., description="Status message")


class RefreshDataResponse(BaseResponse):
    """Response model for data refresh operations."""

    success: bool = Field(..., description="Whether refresh was successful")
    message: str = Field(..., description="Status message")
