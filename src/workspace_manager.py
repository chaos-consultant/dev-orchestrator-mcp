"""Workspace manager for multi-repo orchestration."""

import os
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Dict


@dataclass
class RepoInfo:
    """Information about a git repository in the workspace."""
    name: str
    path: str
    branch: Optional[str] = None
    has_uncommitted_changes: bool = False
    ahead_behind: Optional[str] = None  # e.g., "↑2 ↓1" or "up to date"
    last_commit_message: Optional[str] = None
    last_commit_time: Optional[str] = None
    last_commit_author: Optional[str] = None
    is_git_repo: bool = True
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class WorkspaceManager:
    """Manages workspace-level operations across multiple repositories."""

    def __init__(self, workspace_root: Optional[str] = None):
        """
        Initialize workspace manager.

        Args:
            workspace_root: Root directory containing multiple repos.
                          Defaults to parent of current directory.
        """
        root = workspace_root if workspace_root is not None else str(Path.cwd().parent)
        self.workspace_root = Path(root).resolve()

    def discover_repos(self, max_depth: int = 2) -> List[RepoInfo]:
        """
        Discover all git repositories in workspace.

        Args:
            max_depth: Maximum directory depth to search (1 = direct children only)

        Returns:
            List of RepoInfo objects for discovered repos
        """
        repos = []

        if not self.workspace_root.exists():
            return repos

        # Search for .git directories
        for root, dirs, _ in os.walk(self.workspace_root):
            # Calculate current depth
            depth = str(root).count(os.sep) - str(self.workspace_root).count(os.sep)

            if depth >= max_depth:
                # Don't recurse deeper
                dirs.clear()
                continue

            # Check if this directory is a git repo
            if '.git' in dirs:
                repo_path = Path(root)
                repo_info = self._get_repo_info(repo_path)
                repos.append(repo_info)

                # Don't recurse into this repo
                dirs.clear()

        # Sort by name
        repos.sort(key=lambda r: r.name)
        return repos

    def _get_repo_info(self, repo_path: Path) -> RepoInfo:
        """
        Get detailed information about a git repository.

        Args:
            repo_path: Path to git repository

        Returns:
            RepoInfo object with repository details
        """
        name = repo_path.name
        path = str(repo_path)

        try:
            # Get current branch
            branch = self._run_git_command(repo_path, ['branch', '--show-current'])

            # Check for uncommitted changes (both staged and unstaged)
            status_output = self._run_git_command(repo_path, ['status', '--porcelain'])
            has_uncommitted_changes = bool(status_output.strip())

            # Get ahead/behind status
            ahead_behind = self._get_ahead_behind(repo_path, branch)

            # Get last commit info
            commit_info = self._get_last_commit_info(repo_path)

            return RepoInfo(
                name=name,
                path=path,
                branch=branch or 'unknown',
                has_uncommitted_changes=has_uncommitted_changes,
                ahead_behind=ahead_behind,
                last_commit_message=commit_info.get('message'),
                last_commit_time=commit_info.get('time'),
                last_commit_author=commit_info.get('author'),
                is_git_repo=True
            )

        except Exception as e:
            return RepoInfo(
                name=name,
                path=path,
                is_git_repo=True,
                error=str(e)
            )

    def _get_ahead_behind(self, repo_path: Path, branch: str) -> str:
        """Get ahead/behind status compared to upstream."""
        try:
            # Get upstream branch
            upstream = self._run_git_command(
                repo_path,
                ['rev-parse', '--abbrev-ref', f'{branch}@{{upstream}}']
            )

            if not upstream:
                return 'no upstream'

            # Get ahead/behind counts
            output = self._run_git_command(
                repo_path,
                ['rev-list', '--left-right', '--count', f'{branch}...{upstream}']
            )

            if output:
                parts = output.strip().split()
                if len(parts) == 2:
                    ahead, behind = int(parts[0]), int(parts[1])

                    if ahead == 0 and behind == 0:
                        return 'up to date'

                    status_parts = []
                    if ahead > 0:
                        status_parts.append(f'↑{ahead}')
                    if behind > 0:
                        status_parts.append(f'↓{behind}')
                    return ' '.join(status_parts)

            return 'unknown'

        except Exception:
            return 'no upstream'

    def _get_last_commit_info(self, repo_path: Path) -> Dict[str, str]:
        """Get information about the last commit."""
        try:
            # Get commit message (first line only)
            message = self._run_git_command(
                repo_path,
                ['log', '-1', '--pretty=format:%s']
            )

            # Get commit time (relative)
            time = self._run_git_command(
                repo_path,
                ['log', '-1', '--pretty=format:%ar']
            )

            # Get commit author
            author = self._run_git_command(
                repo_path,
                ['log', '-1', '--pretty=format:%an']
            )

            return {
                'message': message or 'No commits',
                'time': time or 'unknown',
                'author': author or 'unknown'
            }

        except Exception:
            return {
                'message': 'No commits',
                'time': 'unknown',
                'author': 'unknown'
            }

    def _run_git_command(self, repo_path: Path, args: List[str]) -> str:
        """
        Run a git command in a repository.

        Args:
            repo_path: Path to git repository
            args: Git command arguments (without 'git' prefix)

        Returns:
            Command output as string
        """
        try:
            result = subprocess.run(
                ['git'] + args,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            raise Exception('Git command timed out')
        except Exception as e:
            raise Exception(f'Git command failed: {e}')

    def get_workspace_summary(self) -> Dict:
        """
        Get summary of entire workspace.

        Returns:
            Dictionary with workspace statistics
        """
        repos = self.discover_repos()

        total = len(repos)
        with_changes = sum(1 for r in repos if r.has_uncommitted_changes)
        with_upstream = sum(1 for r in repos if r.ahead_behind and '↑' in r.ahead_behind)
        need_pull = sum(1 for r in repos if r.ahead_behind and '↓' in r.ahead_behind)

        return {
            'workspace_root': str(self.workspace_root),
            'total_repos': total,
            'repos_with_changes': with_changes,
            'repos_ahead_of_upstream': with_upstream,
            'repos_need_pull': need_pull,
            'repos': [r.to_dict() for r in repos]
        }

    def get_repos_with_changes(self) -> List[RepoInfo]:
        """Get only repositories with uncommitted changes."""
        repos = self.discover_repos()
        return [r for r in repos if r.has_uncommitted_changes]

    def find_repo_by_name(self, name: str) -> Optional[RepoInfo]:
        """
        Find a repository by name.

        Args:
            name: Repository name (case-insensitive)

        Returns:
            RepoInfo if found, None otherwise
        """
        repos = self.discover_repos()
        name_lower = name.lower()

        for repo in repos:
            if repo.name.lower() == name_lower:
                return repo

        return None
