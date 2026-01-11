"""Migrate data from JSON state file to SQLite database."""

import asyncio
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_config
from .engine import get_session_maker, init_db
from .repositories import (
    CommandRepository,
    SavedCommandRepository,
    ProjectRepository,
)


async def migrate_json_to_sqlite(
    json_path: Optional[Path] = None,
    backup: bool = True
) -> dict:
    """
    Migrate data from JSON state file to SQLite database.

    Args:
        json_path: Path to JSON state file (defaults to ~/.dev-orchestrator/state.json)
        backup: Whether to create backup of JSON file before migration

    Returns:
        Dictionary with migration statistics
    """
    config = get_config()

    # Default JSON path
    if json_path is None:
        json_path = Path("~/.dev-orchestrator/state.json").expanduser()

    # Check if JSON file exists
    if not json_path.exists():
        print(f"✅ No existing JSON state file found at {json_path}")
        print("   Starting with fresh database")
        return {
            "status": "skipped",
            "reason": "no_json_file",
            "commands_migrated": 0,
            "saved_commands_migrated": 0,
        }

    # Load JSON data
    print(f"📖 Reading JSON state from {json_path}")
    with open(json_path, "r") as f:
        state_data = json.load(f)

    # Create backup if requested
    if backup:
        backup_path = json_path.with_suffix(".json.backup")
        print(f"💾 Creating backup at {backup_path}")
        shutil.copy2(json_path, backup_path)

    # Initialize database
    print("🗄️  Initializing SQLite database...")
    await init_db()

    # Create session and repositories
    session_maker = get_session_maker()
    session: AsyncSession = session_maker()

    command_repo = CommandRepository(session)
    saved_command_repo = SavedCommandRepository(session)
    project_repo = ProjectRepository(session)

    stats = {
        "status": "success",
        "commands_migrated": 0,
        "saved_commands_migrated": 0,
        "errors": [],
    }

    try:
        # Migrate command history
        command_history = state_data.get("command_history", [])
        print(f"📝 Migrating {len(command_history)} command history entries...")

        for cmd in command_history:
            try:
                # Parse timestamp
                timestamp_str = cmd.get("timestamp")
                if timestamp_str:
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str)
                    except (ValueError, TypeError):
                        timestamp = datetime.now()
                else:
                    timestamp = datetime.now()

                # Add command
                await command_repo.add_command(
                    command=cmd.get("command", ""),
                    cwd=cmd.get("cwd", "."),
                    status=cmd.get("status", "unknown"),
                    exit_code=cmd.get("exit_code"),
                    stdout=cmd.get("stdout"),
                    stderr=cmd.get("stderr"),
                    project_id=None,  # No project tracking in old JSON
                    timestamp=timestamp,
                )
                stats["commands_migrated"] += 1

            except Exception as e:
                error_msg = f"Failed to migrate command: {str(e)}"
                stats["errors"].append(error_msg)
                print(f"   ⚠️  {error_msg}")

        # Migrate saved commands
        saved_commands = state_data.get("saved_commands", [])
        print(f"⭐ Migrating {len(saved_commands)} saved commands...")

        for saved_cmd in saved_commands:
            try:
                # Parse created_at timestamp
                created_at_str = saved_cmd.get("created_at")
                if created_at_str:
                    try:
                        # Handle both ISO format and other formats
                        created_at = datetime.fromisoformat(created_at_str)
                    except (ValueError, TypeError):
                        created_at = datetime.now()
                else:
                    created_at = datetime.now()

                # Extract tags if present
                tags = saved_cmd.get("tags", [])

                # Add saved command with tags
                await saved_command_repo.add_saved_command(
                    name=saved_cmd.get("name", "Unnamed"),
                    command=saved_cmd.get("command", ""),
                    cwd=saved_cmd.get("cwd"),
                    description=saved_cmd.get("description"),
                    tag_names=tags if isinstance(tags, list) else None,
                    created_at=created_at,
                )
                stats["saved_commands_migrated"] += 1

            except Exception as e:
                error_msg = f"Failed to migrate saved command: {str(e)}"
                stats["errors"].append(error_msg)
                print(f"   ⚠️  {error_msg}")

        # Note: Logs are not migrated as they're typically ephemeral
        # Services are not migrated as they're runtime state only

        await session.commit()
        print(f"\n✅ Migration complete!")
        print(f"   Commands migrated: {stats['commands_migrated']}")
        print(f"   Saved commands migrated: {stats['saved_commands_migrated']}")

        if stats["errors"]:
            print(f"   ⚠️  Errors encountered: {len(stats['errors'])}")

        return stats

    except Exception as e:
        await session.rollback()
        stats["status"] = "failed"
        stats["error"] = str(e)
        print(f"\n❌ Migration failed: {e}")
        raise

    finally:
        await session.close()


async def verify_migration() -> None:
    """Verify that migration was successful by checking database contents."""
    print("\n🔍 Verifying migration...")

    session_maker = get_session_maker()
    session: AsyncSession = session_maker()

    try:
        command_repo = CommandRepository(session)
        saved_command_repo = SavedCommandRepository(session)

        # Count records
        commands = await command_repo.get_recent(limit=10000)
        saved_commands = await saved_command_repo.get_all_with_tags()

        print(f"   📊 Database contains:")
        print(f"      - {len(commands)} command history entries")
        print(f"      - {len(saved_commands)} saved commands")

        # Show sample of recent commands
        if commands:
            print(f"\n   📝 Most recent commands:")
            for cmd in commands[:5]:
                print(f"      - {cmd.command[:60]}... ({cmd.status})")

        # Show saved commands with tags
        if saved_commands:
            print(f"\n   ⭐ Saved commands:")
            for sc in saved_commands[:5]:
                tags_str = ", ".join(tag.name for tag in sc.tags) if sc.tags else "no tags"
                print(f"      - {sc.name}: {sc.command[:40]}... ({tags_str})")

    finally:
        await session.close()


async def main():
    """Main entry point for migration script."""
    print("=" * 60)
    print("Dev Orchestrator: JSON to SQLite Migration")
    print("=" * 60)
    print()

    try:
        # Run migration
        stats = await migrate_json_to_sqlite()

        # Verify if successful
        if stats["status"] == "success":
            await verify_migration()

            print("\n" + "=" * 60)
            print("✅ Migration completed successfully!")
            print("=" * 60)
            print()
            print("The old JSON state file has been backed up.")
            print("You can now start the dev-orchestrator server with:")
            print("  python -m src.server")

        elif stats["status"] == "skipped":
            print("\n" + "=" * 60)
            print("✅ Fresh database initialized")
            print("=" * 60)

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ Migration failed: {e}")
        print("=" * 60)
        print()
        print("Your original JSON state file has been preserved.")
        print("Please report this error if it persists.")
        raise


if __name__ == "__main__":
    asyncio.run(main())
