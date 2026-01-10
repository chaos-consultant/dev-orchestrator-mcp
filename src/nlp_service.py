"""Natural Language Processing service using Ollama for command translation."""

import json
from typing import Optional, Literal
import httpx
from dataclasses import dataclass


@dataclass
class CommandIntent:
    """Parsed command intent from natural language."""
    type: Literal["shell", "detect_project", "start_service", "stop_service", "git_status", "list_services", "unknown"]
    command: str
    confidence: float
    reasoning: str
    parameters: Optional[dict] = None


class OllamaNLPService:
    """NLP service using Ollama for natural language command translation."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "granite3-dense:8b"):
        self.base_url = base_url
        self.model = model
        self.system_prompt = """You are a command translation assistant for a dev orchestrator tool.

Available MCP tools:
- detect_project: Detect project type and configuration (args: path)
- start_service: Start a dev service (args: service=[backend|frontend|test|all], port)
- stop_service: Stop a running service (args: service_id)
- git_status: Get git status for current project
- list_services: List all running services
- run_tests: Run project tests
- check_ports: Check which ports are in use

Convert natural language to either:
1. Shell command (for file operations, directory navigation, etc.)
2. MCP tool call (for project detection, service management, etc.)

Respond in JSON format:
{
  "type": "shell" or "detect_project" or "start_service" etc.,
  "command": "the actual command or tool name",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation",
  "parameters": {"key": "value"} (for MCP tools only)
}

Examples:
Input: "list files in current directory"
Output: {"type": "shell", "command": "ls -la", "confidence": 0.95, "reasoning": "Basic file listing command"}

Input: "detect the webapp-ui project"
Output: {"type": "detect_project", "command": "detect_project", "confidence": 0.9, "reasoning": "User wants to detect a project", "parameters": {"path": "webapp-ui"}}

Input: "start the backend server"
Output: {"type": "start_service", "command": "start_service", "confidence": 0.9, "reasoning": "User wants to start a service", "parameters": {"service": "backend"}}

Input: "what's the git status"
Output: {"type": "git_status", "command": "git_status", "confidence": 0.95, "reasoning": "User wants git repository status"}
"""

    async def parse_natural_language(self, natural_language: str) -> CommandIntent:
        """Parse natural language input and return command intent."""

        # Quick pattern matching for common cases (faster than LLM)
        if self._is_shell_command(natural_language):
            return CommandIntent(
                type="shell",
                command=natural_language,
                confidence=1.0,
                reasoning="Direct shell command detected"
            )

        # Use Ollama for complex natural language
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": f"{self.system_prompt}\n\nInput: {natural_language}\nOutput:",
                        "stream": False,
                        "format": "json"
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "")

                    # Parse JSON response
                    try:
                        intent_data = json.loads(response_text)
                        return CommandIntent(
                            type=intent_data.get("type", "unknown"),
                            command=intent_data.get("command", natural_language),
                            confidence=float(intent_data.get("confidence", 0.5)),
                            reasoning=intent_data.get("reasoning", ""),
                            parameters=intent_data.get("parameters")
                        )
                    except json.JSONDecodeError:
                        # Fallback: treat as shell command
                        return CommandIntent(
                            type="shell",
                            command=natural_language,
                            confidence=0.3,
                            reasoning="Failed to parse LLM response, treating as shell command"
                        )
                else:
                    # Non-200 status code from Ollama
                    return CommandIntent(
                        type="shell",
                        command=natural_language,
                        confidence=0.2,
                        reasoning=f"Ollama returned status {response.status_code}"
                    )

        except Exception as e:
            # Fallback: treat as shell command if Ollama is unavailable
            return CommandIntent(
                type="shell",
                command=natural_language,
                confidence=0.1,
                reasoning=f"Ollama unavailable ({str(e)}), treating as shell command"
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
            text.startswith("./"),
            "/" in text and not " " in text.split("/")[0],  # Looks like a path
        ]
        return any(shell_indicators)

    async def test_connection(self) -> bool:
        """Test if Ollama is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False


# Singleton instance
_nlp_service: Optional[OllamaNLPService] = None

def get_nlp_service() -> OllamaNLPService:
    """Get or create NLP service singleton."""
    global _nlp_service
    if _nlp_service is None:
        _nlp_service = OllamaNLPService()
    return _nlp_service
