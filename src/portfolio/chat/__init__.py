"""AI Chat module for crypto portfolio analysis.

This module provides multi-LLM chat functionality for natural language
portfolio queries and analysis, supporting OpenAI, Anthropic Claude, and more.
"""

from .anthropic_client import AnthropicClient
from .base_llm_client import AVAILABLE_MODELS, LLMClientFactory, LLMProvider
from .chat_interface import render_chat_interface
from .function_handlers import PortfolioFunctionHandler
from .model_selector import render_model_selector
from .openai_client import OpenAIClient

__all__ = [
    "LLMClientFactory",
    "AVAILABLE_MODELS",
    "LLMProvider",
    "OpenAIClient",
    "AnthropicClient",
    "PortfolioFunctionHandler",
    "render_chat_interface",
    "render_model_selector",
]
