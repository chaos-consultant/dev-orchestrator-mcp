"""SQLAlchemy ORM models for dev-orchestrator."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class Command(Base):
    """Command history table."""

    __tablename__ = "commands"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    command: Mapped[str] = mapped_column(Text, nullable=False)
    cwd: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    exit_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    stdout: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stderr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    project_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("projects.id"), nullable=True
    )

    # Relationships
    project: Mapped[Optional["Project"]] = relationship(back_populates="commands")


class SavedCommand(Base):
    """Saved/favorite commands table."""

    __tablename__ = "saved_commands"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    command: Mapped[str] = mapped_column(Text, nullable=False)
    cwd: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    tags: Mapped[list["Tag"]] = relationship(
        secondary="command_tags", back_populates="commands"
    )
    workflow_steps: Mapped[list["WorkflowStep"]] = relationship(
        back_populates="command"
    )


class Tag(Base):
    """Tags for categorizing saved commands."""

    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    color: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relationships
    commands: Mapped[list["SavedCommand"]] = relationship(
        secondary="command_tags", back_populates="tags"
    )


class CommandTag(Base):
    """Many-to-many relationship between saved commands and tags."""

    __tablename__ = "command_tags"
    __table_args__ = (
        UniqueConstraint("command_id", "tag_id", name="uq_command_tag"),
    )

    command_id: Mapped[str] = mapped_column(
        String, ForeignKey("saved_commands.id"), primary_key=True
    )
    tag_id: Mapped[str] = mapped_column(
        String, ForeignKey("tags.id"), primary_key=True
    )


class Project(Base):
    """Projects/repositories table."""

    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    path: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    project_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_accessed: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    total_time_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    commands: Mapped[list["Command"]] = relationship(back_populates="project")
    sessions: Mapped[list["ProjectSession"]] = relationship(back_populates="project")


class ProjectSession(Base):
    """Track time spent on each project."""

    __tablename__ = "project_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String, ForeignKey("projects.id"), nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="sessions")


class Workflow(Base):
    """Command workflows table."""

    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relationships
    steps: Mapped[list["WorkflowStep"]] = relationship(
        back_populates="workflow", order_by="WorkflowStep.step_order"
    )


class WorkflowStep(Base):
    """Individual steps within a workflow."""

    __tablename__ = "workflow_steps"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    workflow_id: Mapped[str] = mapped_column(
        String, ForeignKey("workflows.id"), nullable=False, index=True
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    command_id: Mapped[str] = mapped_column(
        String, ForeignKey("saved_commands.id"), nullable=False
    )

    # Relationships
    workflow: Mapped["Workflow"] = relationship(back_populates="steps")
    command: Mapped["SavedCommand"] = relationship(back_populates="workflow_steps")


class Service(Base):
    """Running services table."""

    __tablename__ = "services"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    command: Mapped[str] = mapped_column(Text, nullable=False)
    port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pid: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    stopped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class Log(Base):
    """System logs table."""

    __tablename__ = "logs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    level: Mapped[str] = mapped_column(String, nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
