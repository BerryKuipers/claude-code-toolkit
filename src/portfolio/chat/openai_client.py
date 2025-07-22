"""OpenAI client wrapper for portfolio chat functionality."""

import os
import logging
from typing import Dict, List, Any, Optional
import tiktoken
from openai import OpenAI
from openai.types.chat import ChatCompletion

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Wrapper for OpenAI API with portfolio-specific functionality."""
    
    def __init__(self):
        """Initialize OpenAI client with configuration from environment."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.1"))
        
        # Initialize tokenizer for token counting
        try:
            self.tokenizer = tiktoken.encoding_for_model(self.model)
        except KeyError:
            # Fallback to cl100k_base for newer models
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string."""
        try:
            return len(self.tokenizer.encode(text))
        except Exception as e:
            logger.warning(f"Error counting tokens: {e}")
            # Rough estimate: ~4 characters per token
            return len(text) // 4
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict[str, Any]]] = None,
        function_call: Optional[str] = None
    ) -> ChatCompletion:
        """Create a chat completion with optional function calling.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            functions: Optional list of function definitions for function calling
            function_call: Optional function call preference ('auto', 'none', or specific function)
            
        Returns:
            ChatCompletion response from OpenAI
        """
        try:
            # Prepare the request parameters
            params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
            }
            
            # Add function calling parameters if provided
            if functions:
                params["tools"] = [{"type": "function", "function": func} for func in functions]
                if function_call:
                    if function_call == "auto":
                        params["tool_choice"] = "auto"
                    elif function_call == "none":
                        params["tool_choice"] = "none"
                    else:
                        # Specific function call
                        params["tool_choice"] = {"type": "function", "function": {"name": function_call}}
            
            # Make the API call
            response = self.client.chat.completions.create(**params)
            
            # Log token usage
            if hasattr(response, 'usage') and response.usage:
                logger.info(f"OpenAI API usage - Prompt: {response.usage.prompt_tokens}, "
                           f"Completion: {response.usage.completion_tokens}, "
                           f"Total: {response.usage.total_tokens}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error in OpenAI chat completion: {e}")
            raise
    
    def get_response_content(self, response: ChatCompletion) -> str:
        """Extract text content from chat completion response."""
        try:
            if response.choices and len(response.choices) > 0:
                message = response.choices[0].message
                if message.content:
                    return message.content
                else:
                    return "No content in response"
            else:
                return "No response choices available"
        except Exception as e:
            logger.error(f"Error extracting response content: {e}")
            return f"Error processing response: {str(e)}"
    
    def get_function_calls(self, response: ChatCompletion) -> List[Dict[str, Any]]:
        """Extract function calls from chat completion response.
        
        Returns:
            List of function call dictionaries with 'name' and 'arguments'
        """
        function_calls = []
        try:
            if response.choices and len(response.choices) > 0:
                message = response.choices[0].message
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    for tool_call in message.tool_calls:
                        if tool_call.type == "function":
                            function_calls.append({
                                "id": tool_call.id,
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            })
        except Exception as e:
            logger.error(f"Error extracting function calls: {e}")
        
        return function_calls
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost of API call based on token usage.
        
        Note: This is a rough estimate based on GPT-4 pricing.
        Actual costs may vary based on model and pricing changes.
        """
        # GPT-4 pricing (as of 2024): $0.03/1K prompt tokens, $0.06/1K completion tokens
        prompt_cost = (prompt_tokens / 1000) * 0.03
        completion_cost = (completion_tokens / 1000) * 0.06
        return prompt_cost + completion_cost
    
    def validate_function_schema(self, functions: List[Dict[str, Any]]) -> bool:
        """Validate function schema format for OpenAI function calling."""
        required_fields = ["name", "description", "parameters"]
        
        for func in functions:
            for field in required_fields:
                if field not in func:
                    logger.error(f"Function missing required field '{field}': {func}")
                    return False
            
            # Validate parameters schema
            params = func.get("parameters", {})
            if not isinstance(params, dict) or "type" not in params:
                logger.error(f"Invalid parameters schema in function: {func['name']}")
                return False
        
        return True
