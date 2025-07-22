"""Anthropic Claude client implementation."""

import os
import json
import logging
from typing import Dict, List, Any, Optional
import anthropic
from anthropic.types import Message, ToolUseBlock, TextBlock
from .base_llm_client import BaseLLMClient, ModelInfo

logger = logging.getLogger(__name__)


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude client implementation."""
    
    def __init__(self, model_info: ModelInfo):
        """Initialize Anthropic client with configuration from environment."""
        super().__init__(model_info)
        
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.max_tokens = int(os.getenv("ANTHROPIC_MAX_TOKENS", "4000"))
        self.temperature = float(os.getenv("ANTHROPIC_TEMPERATURE", "0.1"))
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict[str, Any]]] = None,
        function_call: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Message:
        """Create a chat completion with Claude.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            functions: Optional list of function definitions for tool use
            function_call: Optional function call preference (ignored for Claude)
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            
        Returns:
            Claude Message response
        """
        try:
            # Get custom system prompt if available
            custom_system_prompt = None
            try:
                import streamlit as st
                if "prompt_editor" in st.session_state:
                    custom_system_prompt = st.session_state.prompt_editor.get_active_system_prompt()
            except Exception as e:
                logger.warning(f"Failed to load custom system prompt: {e}")
                pass  # Continue with default prompts if custom prompts fail

            # Separate system message from conversation messages
            system_message = ""
            conversation_messages = []

            for msg in messages:
                if msg["role"] == "system":
                    system_message = custom_system_prompt or msg["content"]
                else:
                    conversation_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # Prepare the request parameters
            params = {
                "model": self.model_id,
                "messages": conversation_messages,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature if temperature is not None else self.temperature,
            }
            
            # Add system message if provided
            if system_message:
                params["system"] = system_message
            
            # Add tools (functions) if provided
            if functions and self.supports_function_calling():
                tools = []
                for func in functions:
                    tools.append({
                        "name": func["name"],
                        "description": func["description"],
                        "input_schema": func["parameters"]
                    })
                params["tools"] = tools
            
            # Make the API call
            response = self.client.messages.create(**params)
            
            # Log token usage and track costs
            if hasattr(response, 'usage') and response.usage:
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens

                logger.info(f"Claude API usage - Input: {input_tokens}, "
                           f"Output: {output_tokens}")

                # Track usage for cost monitoring
                query_type = "function_call" if functions else "chat"
                self.track_usage(input_tokens, output_tokens, query_type)

            return response
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in Claude chat completion: {e}")

            # Handle specific error types
            if "529" in error_msg or "overloaded" in error_msg.lower():
                raise Exception("🚨 Anthropic servers are currently overloaded. Please try again in a few minutes or switch to OpenAI GPT-4 in the model selector.")
            elif "401" in error_msg or "authentication" in error_msg.lower():
                raise Exception("❌ Authentication failed. Please check your Anthropic API key in the .env file.")
            elif "rate_limit" in error_msg.lower() or "429" in error_msg:
                raise Exception("⏱️ Rate limit exceeded. Please wait a moment before trying again.")
            else:
                raise Exception(f"❌ Claude API error: {error_msg}")
    
    def get_response_content(self, response: Message) -> str:
        """Extract text content from Claude response."""
        try:
            if response.content:
                # Claude returns a list of content blocks
                text_parts = []
                for block in response.content:
                    if isinstance(block, TextBlock):
                        text_parts.append(block.text)
                    elif hasattr(block, 'text'):
                        text_parts.append(block.text)
                
                return "\n".join(text_parts) if text_parts else "No content in response"
            else:
                return "No content in response"
        except Exception as e:
            logger.error(f"Error extracting Claude response content: {e}")
            return f"Error processing response: {str(e)}"
    
    def get_function_calls(self, response: Message) -> List[Dict[str, Any]]:
        """Extract function calls from Claude response.
        
        Returns:
            List of function call dictionaries with 'id', 'name' and 'arguments'
        """
        function_calls = []
        try:
            if response.content:
                for block in response.content:
                    if isinstance(block, ToolUseBlock):
                        function_calls.append({
                            "id": block.id,
                            "name": block.name,
                            "arguments": json.dumps(block.input) if block.input else "{}"
                        })
                    elif hasattr(block, 'type') and block.type == 'tool_use':
                        function_calls.append({
                            "id": getattr(block, 'id', 'unknown'),
                            "name": getattr(block, 'name', 'unknown'),
                            "arguments": json.dumps(getattr(block, 'input', {}))
                        })
        except Exception as e:
            logger.error(f"Error extracting Claude function calls: {e}")
        
        return function_calls
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string.
        
        Note: Claude doesn't provide a direct tokenization API,
        so we use a rough estimate based on character count.
        """
        try:
            # Rough estimate: ~4 characters per token for Claude
            # This is an approximation and may not be perfectly accurate
            return len(text) // 4
        except Exception as e:
            logger.warning(f"Error counting tokens: {e}")
            return len(text) // 4
    
    def create_tool_result_message(self, tool_call_id: str, result: str) -> Dict[str, Any]:
        """Create a tool result message for Claude.
        
        Args:
            tool_call_id: ID of the tool call
            result: Result content from the function
            
        Returns:
            Message dictionary for tool result
        """
        return {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_call_id,
                    "content": result
                }
            ]
        }
    
    def handle_function_calling_conversation(
        self,
        messages: List[Dict[str, str]],
        functions: List[Dict[str, Any]],
        function_handler
    ) -> str:
        """Handle a complete function calling conversation with Claude.
        
        Args:
            messages: Initial conversation messages
            functions: Available function definitions
            function_handler: Handler object with handle_function_call method
            
        Returns:
            Final response content
        """
        try:
            # Make initial request
            response = self.chat_completion(messages, functions)
            
            # Check for function calls
            function_calls = self.get_function_calls(response)
            
            if function_calls:
                # Add assistant's response with tool calls
                messages.append({
                    "role": "assistant",
                    "content": self.get_response_content(response)
                })
                
                # Execute function calls and add results
                for func_call in function_calls:
                    function_name = func_call["name"]
                    function_args = func_call["arguments"]
                    
                    # Execute function
                    function_result = function_handler.handle_function_call(
                        function_name, 
                        function_args
                    )
                    
                    # Add tool result message
                    tool_result_msg = self.create_tool_result_message(
                        func_call["id"], 
                        function_result
                    )
                    messages.append(tool_result_msg)
                
                # Get final response with function results
                final_response = self.chat_completion(messages)
                return self.get_response_content(final_response)
            
            else:
                # No function calls, return direct response
                return self.get_response_content(response)
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in Claude function calling conversation: {e}")

            # Handle specific error types with user-friendly messages
            if "529" in error_msg or "overloaded" in error_msg.lower():
                return "🚨 **Anthropic servers are currently overloaded.** Please try again in a few minutes or switch to OpenAI GPT-4 using the model selector above."
            elif "401" in error_msg or "authentication" in error_msg.lower():
                return "❌ **Authentication failed.** Please check your Anthropic API key in the .env file."
            elif "rate_limit" in error_msg.lower() or "429" in error_msg:
                return "⏱️ **Rate limit exceeded.** Please wait a moment before trying again."
            else:
                return f"❌ **Claude API error:** {error_msg}\n\n💡 **Tip:** Try switching to OpenAI GPT-4 using the model selector if this persists."
