"""
PawPal+ logic layer.
All backend classes live here. Connect these to app.py once implemented.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
TIME_ORDER = {"morning": 0, "afternoon": 1, "evening": 2}


@dataclass
class Task:
    """A single pet care activity."""

    title: str
    duration_minutes: int
    priority: str  # "low", "medium", "high"
    preferred_time: Optional[str] = None  # "morning", "afternoon", "evening"
    is_complete: bool = False
    pet_name: Optional[str] = None  # set automatically when added to a Pet

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.is_complete = True

    def to_dict(self) -> dict:
        """Return a dictionary representation of this task."""
        return {
            "title": self.title,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "preferred_time": self.preferred_time,
            "is_complete": self.is_complete,
            "pet_name": self.pet_name,
        }


@dataclass
class Pet:
    """An animal being cared for."""

    name: str
    species: str  # "dog", "cat", "other"
    age: int
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet, stamping the pet's name onto the task."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, title: str) -> None:
        """Remove a task by title (case-insensitive match)."""
        self.tasks = [t for t in self.tasks if t.title.lower() != title.lower()]

    def get_pending_tasks(self) -> list[Task]:
        """Return tasks that are not yet complete."""
        return [t for t in self.tasks if not t.is_complete]


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
        self.pets.append(pet)

    def get_all_tasks(self) -> list[Task]:
        """Collect all pending tasks across every pet."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.get_pending_tasks())
        return all_tasks


class Scheduler:
    """Builds a daily plan from the owner's tasks and constraints."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner
        self.schedule: list[Task] = []
        self.skipped: list[Task] = []  # tasks that didn't fit in available time

    def build_plan(self) -> list[Task]:
        """Select and order tasks by priority to fit within owner.available_minutes; extras go to self.skipped."""
        self.schedule = []
        self.skipped = []

        # Sort: priority first, then preferred_time, then title for stability
        pending = sorted(
            self.owner.get_all_tasks(),
            key=lambda t: (
                PRIORITY_ORDER.get(t.priority, 99),
                TIME_ORDER.get(t.preferred_time or "", 99),
                t.title,
            ),
        )

        time_remaining = self.owner.available_minutes
        for task in pending:
            if task.duration_minutes <= time_remaining:
                self.schedule.append(task)
                time_remaining -= task.duration_minutes
            else:
                self.skipped.append(task)

        return self.schedule

    def get_explanation(self) -> str:
        """Return a human-readable summary of scheduled and skipped tasks with reasons."""
        if not self.schedule and not self.skipped:
            return "No plan built yet. Call build_plan() first."

        lines = [f"Daily plan for {self.owner.name} ({self.owner.available_minutes} min available)\n"]

        if self.schedule:
            lines.append("Scheduled:")
            total = 0
            for task in self.schedule:
                pet_label = f" [{task.pet_name}]" if task.pet_name else ""
                lines.append(
                    f"  - {task.title}{pet_label} — {task.duration_minutes} min ({task.priority} priority)"
                )
                total += task.duration_minutes
            lines.append(f"  Total: {total} min\n")

        if self.skipped:
            lines.append("Skipped (didn't fit in remaining time):")
            for task in self.skipped:
                pet_label = f" [{task.pet_name}]" if task.pet_name else ""
                lines.append(
                    f"  - {task.title}{pet_label} — {task.duration_minutes} min ({task.priority} priority)"
                )

        return "\n".join(lines)
