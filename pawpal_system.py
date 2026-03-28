"""
PawPal+ logic layer.
All backend classes live here. Connect these to app.py once implemented.
"""

from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
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
    pet_name: Optional[str] = None      # set automatically when added to a Pet
    recurring: bool = False             # legacy flag kept for compatibility
    frequency: str = "once"            # "once" | "daily" | "weekly"
    due_date: Optional[date] = None    # date this task is next due

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.is_complete = True

    def next_occurrence(self) -> Optional[Task]:
        """Return a fresh Task for the next occurrence, or None if frequency is 'once'.

        Uses timedelta to compute the new due_date:
          - daily  → today + 1 day
          - weekly → today + 7 days
        """
        if self.frequency == "once":
            return None
        delta = timedelta(days=1) if self.frequency == "daily" else timedelta(weeks=1)
        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            preferred_time=self.preferred_time,
            pet_name=self.pet_name,
            frequency=self.frequency,
            due_date=date.today() + delta,
        )

    def to_dict(self) -> dict:
        """Return a dictionary representation of this task."""
        return {
            "title": self.title,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "preferred_time": self.preferred_time,
            "is_complete": self.is_complete,
            "pet_name": self.pet_name,
            "frequency": self.frequency,
            "due_date": str(self.due_date) if self.due_date else None,
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

    def mark_task_complete(self, title: str) -> Optional[Task]:
        """Mark a task complete by title and, for daily/weekly tasks, add the next occurrence.

        Returns the newly created Task if one was spawned, otherwise None.
        """
        for task in self.tasks:
            if task.title.lower() == title.lower() and not task.is_complete:
                task.mark_complete()
                next_task = task.next_occurrence()
                if next_task is not None:
                    self.add_task(next_task)
                return next_task
        return None


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

    def sort_by_time(self, tasks: list[Task] | None = None) -> list[Task]:
        """Return tasks sorted by preferred_time (morning → afternoon → evening → unset).

        Uses a lambda with TIME_ORDER as the key so slot names sort correctly
        without relying on alphabetical string comparison.

        Args:
            tasks: Optional list to sort. Defaults to self.schedule when omitted.

        Returns:
            A new sorted list of Task objects; the original list is not modified.
        """
        source = tasks if tasks is not None else self.schedule
        return sorted(source, key=lambda t: TIME_ORDER.get(t.preferred_time or "", 99))

    def filter_tasks(
        self,
        pet_name: str | None = None,
        completed: bool | None = None,
    ) -> list[Task]:
        """Filter all tasks (across every pet) by pet name and/or completion status.

        Args:
            pet_name:  If given, only return tasks belonging to this pet (case-insensitive).
            completed: If True return only done tasks; if False return only pending ones;
                       if None return all regardless of status.

        Returns:
            A filtered list of Task objects matching all supplied criteria.
        """
        all_tasks: list[Task] = []
        for pet in self.owner.pets:
            all_tasks.extend(pet.tasks)

        if pet_name is not None:
            all_tasks = [t for t in all_tasks if (t.pet_name or "").lower() == pet_name.lower()]
        if completed is not None:
            all_tasks = [t for t in all_tasks if t.is_complete == completed]
        return all_tasks

    def detect_conflicts(self) -> list[str]:
        """Return warning messages for scheduling conflicts — never raises.

        Three lightweight checks (returns warnings instead of raising exceptions):
        1. Same-pet, same-slot: owner can only attend to one task per pet at a time.
        2. Cross-pet, same-slot: multiple high-priority tasks across different pets
           compete for the owner's attention simultaneously.
        3. Slot overload: total duration in a slot exceeds 60 minutes.

        Returns:
            A list of human-readable warning strings. Empty list means no conflicts.
        """
        conflicts: list[str] = []
        by_slot: dict[str, list[Task]] = defaultdict(list)
        by_pet_slot: dict[tuple[str, str], list[Task]] = defaultdict(list)

        for task in self.owner.get_all_tasks():
            if not task.preferred_time:
                continue
            by_slot[task.preferred_time].append(task)
            if task.pet_name:
                by_pet_slot[(task.pet_name, task.preferred_time)].append(task)

        # Check 1 — same pet, same slot
        for (pet_name, slot), tasks in by_pet_slot.items():
            if len(tasks) > 1:
                names = ", ".join(f"'{t.title}'" for t in tasks)
                conflicts.append(
                    f"Conflict [{pet_name}] {slot}: tasks overlap ({names})"
                )

        # Checks 2 & 3 — across all pets per slot
        for slot, tasks in by_slot.items():
            high = [t for t in tasks if t.priority == "high"]
            pets_with_high = {t.pet_name for t in high}
            if len(pets_with_high) > 1:
                names = ", ".join(f"'{t.title}' [{t.pet_name}]" for t in high)
                conflicts.append(
                    f"Warning: {slot} has high-priority tasks across multiple pets ({names})"
                )
            total = sum(t.duration_minutes for t in tasks)
            if total > 60:
                conflicts.append(
                    f"Warning: {slot} slot is overloaded ({total} min across {len(tasks)} tasks)"
                )

        return conflicts

    def mark_task_complete(self, task: Task) -> Optional[Task]:
        """Mark a task complete and auto-spawn the next occurrence for daily/weekly tasks.

        Finds the pet that owns the task by pet_name and delegates to
        Pet.mark_task_complete(). For tasks with frequency "daily" or "weekly",
        a new Task is automatically added to the pet with a due_date calculated
        using timedelta (today + 1 day for daily, today + 7 days for weekly).

        Args:
            task: The Task instance to mark as complete.

        Returns:
            The newly created next-occurrence Task, or None if frequency is "once".
        """
        if not task.pet_name:
            task.mark_complete()
            return task.next_occurrence()
        for pet in self.owner.pets:
            if pet.name == task.pet_name:
                return pet.mark_task_complete(task.title)
        return None

    def build_plan(self) -> list[Task]:
        """Select and order tasks by priority to fit within owner.available_minutes; extras go to self.skipped.

        Recurring tasks that are marked complete are still included — they reset each day.
        """
        self.schedule = []
        self.skipped = []

        # Recurring tasks are always treated as pending even if previously marked complete.
        candidates: list[Task] = []
        for pet in self.owner.pets:
            for t in pet.tasks:
                if not t.is_complete or t.recurring:
                    candidates.append(t)

        # Sort: priority first, then preferred_time, then title for stability
        pending = sorted(
            candidates,
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
