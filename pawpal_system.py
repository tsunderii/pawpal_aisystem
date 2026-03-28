"""
PawPal+ logic layer.
All backend classes live here. Connect these to app.py once implemented.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Task:
    """A single pet care activity."""

    title: str
    duration_minutes: int
    priority: str  # "low", "medium", "high"
    preferred_time: Optional[str] = None  # "morning", "afternoon", "evening"
    is_complete: bool = False

    def mark_complete(self) -> None:
        """Mark this task as done."""
        pass

    def to_dict(self) -> dict:
        """Return a dictionary representation of this task."""
        pass


@dataclass
class Pet:
    """An animal being cared for."""

    name: str
    species: str  # "dog", "cat", "other"
    age: int
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet."""
        pass

    def remove_task(self, title: str) -> None:
        """Remove a task by title."""
        pass

    def get_pending_tasks(self) -> list[Task]:
        """Return tasks that are not yet complete."""
        pass


class Owner:
    """The person using the app."""

    def __init__(
        self,
        name: str,
        available_minutes: int,
        preferred_start_time: str = "08:00",
    ) -> None:
        self.name = name
        self.available_minutes = available_minutes
        self.preferred_start_time = preferred_start_time
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a pet to this owner."""
        pass

    def get_all_tasks(self) -> list[Task]:
        """Collect all tasks across every pet."""
        pass


class Scheduler:
    """Builds a daily plan from the owner's tasks and constraints."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner
        self.schedule: list[Task] = []

    def build_plan(self) -> list[Task]:
        """
        Select and order tasks to fit within owner.available_minutes.
        Higher-priority tasks come first; preferred_time is used as a
        tiebreaker. Returns the ordered list of scheduled tasks.
        """
        pass

    def get_explanation(self) -> str:
        """
        Return a human-readable summary explaining which tasks were
        scheduled, which were skipped, and why.
        """
        pass
