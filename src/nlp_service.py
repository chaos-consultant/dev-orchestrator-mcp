"""Natural Language Processing service using multiple providers for command translation."""

import os
from typing import Optional, Literal
from dataclasses import dataclass

from .nlp.manager import NLPManager
from .nlp.base import NLPContext


@dataclass
class CommandIntent:
    """Parsed command intent from natural language."""
    type: Literal["shell", "detect_project", "start_service", "stop_service", "git_status", "list_services", "unknown"]
    command: str
    confidence: float
    reasoning: str
    parameters: Optional[dict] = None


class NLPService:
    """
    NLP service that uses multiple providers for natural language command translation.

    Supports:
    - Local Ollama models (CodeLlama, WizardCoder, DeepSeek)
    - OpenAI API (GPT-3.5, GPT-4)
    - Google Gemini API (Gemini Pro, 1.5 Pro)
    - Anthropic Claude API (Claude 3.5 Sonnet/Haiku)
    - Command templates for instant matching
    """

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize NLP service with configuration.

        Args:
            config: NLP configuration dict. If None, uses default config.
        """
        if config is None:
            config = self._load_default_config()

        self.config = config
        self.nlp_manager = NLPManager(config)

    def _load_default_config(self) -> dict:
        """Load default NLP configuration."""
        return {
            'enabled': True,
            'primary_provider': 'ollama',
            'fallback_to_local': True,
            'template': {
                'enabled': True,
            },
            'providers': {
                'ollama': {
                    'enabled': True,
                    'ollama_url': os.getenv('OLLAMA_URL', 'http://localhost:11434'),
                    'model': os.getenv('OLLAMA_MODEL', 'codellama:7b-instruct'),
                    'temperature': 0.1,
                    'max_tokens': 512,
                },
                'openai': {
                    'enabled': False,
                    'api_key': os.getenv('OPENAI_API_KEY', ''),
                    'model': 'gpt-3.5-turbo',
                    'temperature': 0.1,
                    'max_tokens': 150,
                },
                'gemini': {
                    'enabled': False,
                    'api_key': os.getenv('GEMINI_API_KEY', ''),
                    'model': 'gemini-pro',
                    'tier': 'free',
                    'temperature': 0.1,
                    'max_tokens': 150,
                },
                'anthropic': {
                    'enabled': False,
                    'api_key': os.getenv('ANTHROPIC_API_KEY', ''),
                    'model': 'claude-3-5-sonnet-20241022',
                    'temperature': 0.1,
                    'max_tokens': 150,
                },
            }
        }

    async def parse_natural_language(self, natural_language: str, cwd: str = ".") -> CommandIntent:
        """
        Parse natural language input and return command intent.

        Args:
            natural_language: Natural language command
            cwd: Current working directory

        Returns:
            CommandIntent with translated command
        """
        # Quick check if it's already a shell command
        if self._is_shell_command(natural_language):
            return CommandIntent(
                type="shell",
                command=natural_language,
                confidence=1.0,
                reasoning="Direct shell command detected"
            )

        # Build context
        context = NLPContext(
            cwd=cwd,
            os_type=os.uname().sysname if hasattr(os, 'uname') else 'Darwin',
            shell_type=os.getenv('SHELL', '/bin/bash').split('/')[-1],
            project_type=None,  # Could be enhanced to detect project type
            recent_commands=None  # Could be enhanced with command history
        )

        try:
            # Use NLP manager to translate
            result = await self.nlp_manager.translate(natural_language, context)

            # Determine intent type based on command content
            intent_type = self._classify_command(result.command)

            return CommandIntent(
                type=intent_type,
                command=result.command,
                confidence=result.confidence,
                reasoning=result.explanation or f"Translated by {result.source}",
                parameters=None  # Could be enhanced to extract parameters
            )

        except Exception as e:
            # Fallback: treat as shell command if translation fails
            return CommandIntent(
                type="shell",
                command=natural_language,
                confidence=0.1,
                reasoning=f"Translation failed ({str(e)}), treating as shell command"
            )

    def _is_shell_command(self, text: str) -> bool:
        """Quick check if input looks like a shell command."""
        shell_indicators = [
            text.startswith("ls"),
            text.startswith("cd"),
            text.startswith("pwd"),
            text.startswith("echo"),
            text.startswith("cat"),
            text.startswith("grep"),
            text.startswith("find"),
            text.startswith("git "),
            text.startswith("npm"),
            text.startswith("python"),
            text.startswith("docker"),
            text.startswith("kubectl"),
            text.startswith("./"),
            "/" in text and not " " in text.split("/")[0],  # Looks like a path
        ]
        return any(shell_indicators)

    def _classify_command(self, command: str) -> Literal["shell", "detect_project", "start_service", "stop_service", "git_status", "list_services", "unknown"]:
        """
        Classify command type for intent detection.

        This is a simple heuristic - could be enhanced with ML classification.
        """
        # Check for MCP tool patterns
        if any(pattern in command.lower() for pattern in ['detect', 'project', 'analyze']):
            return "detect_project"
        elif any(pattern in command.lower() for pattern in ['start', 'run', 'launch']) and 'service' in command.lower():
            return "start_service"
        elif any(pattern in command.lower() for pattern in ['stop', 'kill']) and 'service' in command.lower():
            return "stop_service"
        elif 'git status' in command.lower() or 'git st' in command.lower():
            return "git_status"
        elif 'list' in command.lower() and 'service' in command.lower():
            return "list_services"

        # Default to shell command
        return "shell"

    async def test_connection(self) -> dict[str, bool]:
        """
        Test connection to all configured providers.

        Returns:
            Dict mapping provider name to connection status
        """
        return await self.nlp_manager.test_providers()

    async def update_config(self, new_config: dict):
        """
        Update NLP configuration and reinitialize manager.

        Args:
            new_config: New configuration dict
        """
        self.config = new_config
        self.nlp_manager = NLPManager(new_config)

    def get_config(self) -> dict:
        """Get current NLP configuration."""
        return self.config

    def get_status(self) -> dict:
        """Get status of all providers."""
        return self.nlp_manager.get_provider_status()

    async def learn_from_correction(self, user_input: str, correct_command: str):
        """
        Learn from user corrections by adding to template database.

        Args:
            user_input: The original natural language input
            correct_command: The command the user actually used
        """
        await self.nlp_manager.learn_from_correction(user_input, correct_command)


# Singleton instance
_nlp_service: Optional[NLPService] = None


def get_nlp_service() -> NLPService:
    """Get or create NLP service singleton."""
    global _nlp_service
    if _nlp_service is None:
        _nlp_service = NLPService()
    return _nlp_service


def reset_nlp_service():
    """Reset NLP service singleton (useful for testing or reloading config)."""
    global _nlp_service
    _nlp_service = None
