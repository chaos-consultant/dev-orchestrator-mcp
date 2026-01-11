"""
NLP Manager - orchestrates multiple NLP providers with fallback logic.
"""

import asyncio
from typing import Dict, Any, Optional, List
from .base import NLPProvider, NLPContext, NLPResult
from .command_templates import CommandTemplateProvider
from .ollama_provider import OllamaProvider
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider
from .anthropic_provider import AnthropicProvider


class NLPManager:
    """
    Manages multiple NLP providers with intelligent fallback.

    Provider priority:
    1. Command Templates (instant, always tried first)
    2. Primary provider (Ollama, OpenAI, Gemini, or Anthropic)
    3. Fallback to local if primary is API-based and fails
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize NLP manager with configuration.

        Args:
            config: Configuration dict with provider settings
        """
        self.config = config
        self.providers: Dict[str, NLPProvider] = {}
        self.primary_provider: Optional[str] = None
        self.fallback_enabled = config.get('fallback_to_local', True)

        # Always initialize template provider
        self.providers['template'] = CommandTemplateProvider(
            config.get('template', {})
        )

        # Initialize configured providers
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize NLP providers based on configuration."""
        providers_config = self.config.get('providers', {})

        # Initialize Ollama if configured
        if 'ollama' in providers_config and providers_config['ollama'].get('enabled'):
            try:
                self.providers['ollama'] = OllamaProvider(providers_config['ollama'])
            except Exception as e:
                print(f"Failed to initialize Ollama provider: {e}")

        # Initialize OpenAI if configured
        if 'openai' in providers_config and providers_config['openai'].get('enabled'):
            try:
                self.providers['openai'] = OpenAIProvider(providers_config['openai'])
            except Exception as e:
                print(f"Failed to initialize OpenAI provider: {e}")

        # Initialize Gemini if configured
        if 'gemini' in providers_config and providers_config['gemini'].get('enabled'):
            try:
                self.providers['gemini'] = GeminiProvider(providers_config['gemini'])
            except Exception as e:
                print(f"Failed to initialize Gemini provider: {e}")

        # Initialize Anthropic if configured
        if 'anthropic' in providers_config and providers_config['anthropic'].get('enabled'):
            try:
                self.providers['anthropic'] = AnthropicProvider(providers_config['anthropic'])
            except Exception as e:
                print(f"Failed to initialize Anthropic provider: {e}")

        # Set primary provider
        self.primary_provider = self.config.get('primary_provider', 'ollama')

        # Validate primary provider exists
        if self.primary_provider not in self.providers:
            # Fall back to first available provider
            available = [k for k in self.providers.keys() if k != 'template']
            self.primary_provider = available[0] if available else None

    async def translate(
        self,
        user_input: str,
        context: NLPContext
    ) -> NLPResult:
        """
        Translate natural language to shell command.

        Strategy:
        1. Try template provider first (instant)
        2. Use primary provider
        3. Fall back to local Ollama if primary fails

        Args:
            user_input: Natural language command
            context: Execution context

        Returns:
            NLPResult with translated command

        Raises:
            Exception if all providers fail
        """
        errors = []

        # 1. Try template provider first (instant match)
        template_result = await self.providers['template'].translate(user_input, context)
        if template_result:
            return template_result

        # 2. Try primary provider
        if self.primary_provider and self.primary_provider in self.providers:
            try:
                result = await self.providers[self.primary_provider].translate(
                    user_input,
                    context
                )
                return result
            except Exception as e:
                errors.append(f"{self.primary_provider}: {str(e)}")

        # 3. Fall back to Ollama if enabled and primary was API-based
        if self.fallback_enabled and self.primary_provider != 'ollama':
            if 'ollama' in self.providers:
                try:
                    result = await self.providers['ollama'].translate(
                        user_input,
                        context
                    )
                    result.explanation = f"Fallback: {result.explanation}"
                    return result
                except Exception as e:
                    errors.append(f"ollama (fallback): {str(e)}")

        # All providers failed
        error_msg = "All NLP providers failed:\n" + "\n".join(errors)
        raise Exception(error_msg)

    async def test_providers(self) -> Dict[str, bool]:
        """
        Test all configured providers.

        Returns:
            Dict mapping provider name to connection status
        """
        results = {}

        # Test each provider concurrently
        tasks = []
        provider_names = []

        for name, provider in self.providers.items():
            tasks.append(provider.test_connection())
            provider_names.append(name)

        test_results = await asyncio.gather(*tasks, return_exceptions=True)

        for name, result in zip(provider_names, test_results):
            if isinstance(result, Exception):
                results[name] = False
            else:
                results[name] = result

        return results

    def get_provider(self, name: str) -> Optional[NLPProvider]:
        """Get a specific provider by name."""
        return self.providers.get(name)

    def list_providers(self) -> List[str]:
        """List all initialized providers."""
        return list(self.providers.keys())

    def get_primary_provider(self) -> Optional[str]:
        """Get the name of the primary provider."""
        return self.primary_provider

    def set_primary_provider(self, provider_name: str):
        """
        Set the primary provider.

        Args:
            provider_name: Name of provider to set as primary

        Raises:
            ValueError if provider doesn't exist
        """
        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not available")

        self.primary_provider = provider_name

    async def add_template(self, pattern: str, command: str):
        """Add a custom command template."""
        template_provider = self.providers.get('template')
        if template_provider and isinstance(template_provider, CommandTemplateProvider):
            template_provider.add_template(pattern, command)

    async def learn_from_correction(self, user_input: str, correct_command: str):
        """
        Learn from user corrections by adding new templates.

        Args:
            user_input: The original natural language input
            correct_command: The command the user actually used
        """
        template_provider = self.providers.get('template')
        if template_provider and isinstance(template_provider, CommandTemplateProvider):
            template_provider.learn_from_correction(user_input, correct_command)

    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers."""
        status = {
            'primary_provider': self.primary_provider,
            'fallback_enabled': self.fallback_enabled,
            'providers': {}
        }

        for name, provider in self.providers.items():
            status['providers'][name] = {
                'enabled': provider.is_enabled(),
                'type': type(provider).__name__
            }

        return status
