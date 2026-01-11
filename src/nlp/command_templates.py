"""
Command template database for instant common command translation.
"""

import re
from typing import Optional, Dict, Any, Tuple
from .base import NLPProvider, NLPContext, NLPResult


# Common command templates with regex patterns
COMMAND_TEMPLATES = {
    # File operations
    r"list\s+files?": "ls -lah",
    r"list\s+all\s+files?": "ls -lah",
    r"show\s+files?": "ls -lah",
    r"show\s+hidden\s+files?": "ls -lah",
    r"list\s+directories": "ls -d */",
    r"tree\s+view": "tree -L 2",
    r"find\s+file.*named\s+(\S+)": "find . -name '{0}'",
    r"find\s+files?\s+containing\s+(.+)": "grep -r '{0}' .",
    r"search\s+for\s+(.+)\s+in\s+files?": "grep -r '{0}' .",

    # Process management
    r"show\s+process(?:es)?": "ps aux",
    r"list\s+process(?:es)?": "ps aux",
    r"show\s+running\s+process(?:es)?": "ps aux | grep -v grep",
    r"find\s+process\s+(.+)": "ps aux | grep '{0}'",
    r"kill\s+process\s+(.+)": "pkill -f '{0}'",
    r"kill\s+all\s+(.+)": "pkill -9 -f '{0}'",

    # System info
    r"show\s+disk\s+space": "df -h",
    r"disk\s+usage": "du -sh *",
    r"show\s+memory": "free -h",
    r"memory\s+usage": "free -h",
    r"show\s+cpu": "top -bn1 | head -20",
    r"system\s+info": "uname -a",

    # Git operations
    r"git\s+status": "git status",
    r"show\s+git\s+status": "git status",
    r"show\s+changes": "git diff",
    r"show\s+git\s+diff": "git diff",
    r"git\s+log": "git log --oneline -10",
    r"show\s+git\s+history": "git log --oneline -10",
    r"show\s+branches": "git branch -a",
    r"list\s+branches": "git branch -a",
    r"create\s+branch\s+(.+)": "git checkout -b {0}",
    r"switch\s+to\s+(.+)": "git checkout {0}",
    r"commit\s+(.+)": "git commit -m '{0}'",
    r"push\s+changes": "git push",
    r"pull\s+changes": "git pull",

    # Docker operations
    r"list\s+containers": "docker ps -a",
    r"show\s+containers": "docker ps -a",
    r"running\s+containers": "docker ps",
    r"list\s+images": "docker images",
    r"show\s+images": "docker images",
    r"stop\s+container\s+(.+)": "docker stop {0}",
    r"start\s+container\s+(.+)": "docker start {0}",
    r"remove\s+container\s+(.+)": "docker rm {0}",
    r"docker\s+logs\s+(.+)": "docker logs {0}",

    # Network operations
    r"show\s+ports?": "netstat -tuln",
    r"list\s+ports?": "netstat -tuln",
    r"show\s+connections": "netstat -an",
    r"ping\s+(.+)": "ping -c 4 {0}",
    r"check\s+port\s+(\d+)": "lsof -i :{0}",
    r"what'?s\s+on\s+port\s+(\d+)": "lsof -i :{0}",

    # Python/Node operations
    r"run\s+python\s+(.+)": "python3 {0}",
    r"install\s+(?:python\s+)?package\s+(.+)": "pip install {0}",
    r"install\s+npm\s+(.+)": "npm install {0}",
    r"run\s+tests?": "pytest",
    r"run\s+npm\s+tests?": "npm test",
    r"start\s+dev\s+server": "npm run dev",
    r"build\s+project": "npm run build",

    # File content
    r"show\s+(?:file\s+)?(.+\.[\w]+)": "cat {0}",
    r"view\s+(.+\.[\w]+)": "cat {0}",
    r"read\s+(?:file\s+)?(.+\.[\w]+)": "cat {0}",
    r"tail\s+(.+\.[\w]+)": "tail -f {0}",
    r"follow\s+(.+\.[\w]+)": "tail -f {0}",
    r"head\s+(.+\.[\w]+)": "head -20 {0}",

    # Directory navigation
    r"go\s+to\s+(.+)": "cd {0}",
    r"change\s+(?:to\s+)?directory\s+(.+)": "cd {0}",
    r"go\s+back": "cd ..",
    r"go\s+home": "cd ~",
    r"go\s+up": "cd ..",

    # Archive operations
    r"compress\s+(.+)": "tar -czf {0}.tar.gz {0}",
    r"extract\s+(.+\.tar\.gz)": "tar -xzf {0}",
    r"unzip\s+(.+\.zip)": "unzip {0}",
    r"zip\s+(.+)": "zip -r {0}.zip {0}",

    # Permissions
    r"make\s+(.+)\s+executable": "chmod +x {0}",
    r"change\s+permissions\s+(.+)": "chmod 755 {0}",
    r"change\s+owner\s+(.+)": "chown $USER: {0}",

    # Misc
    r"clear\s+screen": "clear",
    r"show\s+path": "echo $PATH",
    r"show\s+env(?:ironment)?": "env",
    r"what\s+is\s+my\s+ip": "curl -s ifconfig.me",
    r"show\s+date": "date",
    r"show\s+calendar": "cal",
    r"count\s+lines\s+in\s+(.+)": "wc -l {0}",
    r"word\s+count\s+(.+)": "wc -w {0}",
}


class CommandTemplateProvider(NLPProvider):
    """Provider that uses regex templates for instant command translation."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.templates = COMMAND_TEMPLATES
        self.case_sensitive = config.get('case_sensitive', False)

    async def translate(
        self,
        user_input: str,
        context: NLPContext
    ) -> Optional[NLPResult]:
        """
        Try to match input against command templates.

        Returns None if no template matches.
        """
        # Normalize input
        normalized = user_input.strip().lower()

        # Try to match against each template
        for pattern, template in self.templates.items():
            flags = 0 if self.case_sensitive else re.IGNORECASE
            match = re.match(pattern, normalized, flags)

            if match:
                # Extract captured groups
                groups = match.groups()

                # Format command with captured groups
                try:
                    command = template.format(*groups)
                except (IndexError, KeyError):
                    command = template

                return NLPResult(
                    command=command,
                    confidence=1.0,
                    source='template',
                    explanation=f"Matched template: {pattern}"
                )

        return None

    async def test_connection(self) -> bool:
        """Template provider is always available."""
        return True

    def add_template(self, pattern: str, command: str):
        """Add a custom template at runtime."""
        self.templates[pattern] = command

    def learn_from_correction(self, user_input: str, correct_command: str):
        """
        Learn from user corrections by adding new templates.

        Args:
            user_input: The original natural language input
            correct_command: The command the user actually used
        """
        # Create a simple pattern from the input
        pattern = re.escape(user_input.lower()).replace(r"\ ", r"\s+")
        self.add_template(pattern, correct_command)
