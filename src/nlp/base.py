"""
Base NLP provider interface.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class NLPContext:
    """Context information for NLP translation."""
    cwd: str
    os_type: str
    shell_type: str
    project_type: Optional[str] = None
    recent_commands: Optional[list[str]] = None


@dataclass
class NLPResult:
    """Result of NLP translation."""
    command: str
    confidence: float
    source: str  # 'template', 'ollama', 'openai', etc.
    explanation: Optional[str] = None


class NLPProvider(ABC):
    """Base class for NLP providers."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the NLP provider.

        Args:
            config: Provider-specific configuration
        """
        self.config = config
        self.enabled = config.get('enabled', True)

    @abstractmethod
    async def translate(
        self,
        user_input: str,
        context: NLPContext
    ) -> NLPResult:
        """
        Translate natural language input to shell command.

        Args:
            user_input: Natural language command request
            context: Execution context

        Returns:
            NLPResult with translated command and metadata
        """
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test if the provider is configured and accessible.

        Returns:
            True if provider is ready, False otherwise
        """
        pass

    def is_enabled(self) -> bool:
        """Check if provider is enabled."""
        return self.enabled
