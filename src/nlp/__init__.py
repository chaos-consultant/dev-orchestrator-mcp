"""
Natural Language Processing module for command translation.
"""

from .base import NLPProvider
from .ollama_provider import OllamaProvider
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider
from .anthropic_provider import AnthropicProvider
from .command_templates import CommandTemplateProvider

__all__ = [
    'NLPProvider',
    'OllamaProvider',
    'OpenAIProvider',
    'GeminiProvider',
    'AnthropicProvider',
    'CommandTemplateProvider',
]
