"""AI Chat module for crypto portfolio analysis.

This module provides multi-LLM chat functionality for natural language
portfolio queries and analysis, supporting OpenAI, Anthropic Claude, and more.
"""

from .base_llm_client import LLMClientFactory, AVAILABLE_MODELS, LLMProvider
from .openai_client import OpenAIClient
from .anthropic_client import AnthropicClient
from .function_handlers import PortfolioFunctionHandler
from .chat_interface import render_chat_interface
from .model_selector import render_model_selector

__all__ = [
    "LLMClientFactory",
    "AVAILABLE_MODELS",
    "LLMProvider",
    "OpenAIClient",
    "AnthropicClient",
    "PortfolioFunctionHandler",
    "render_chat_interface",
    "render_model_selector"
]
