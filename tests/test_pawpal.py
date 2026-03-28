"""
Tests for PawPal+ core logic.
Run with: python -m pytest
"""

from pawpal_system import Task, Pet


def test_mark_complete_changes_status():
    """Calling mark_complete() should set is_complete to True."""
    task = Task(title="Morning walk", duration_minutes=30, priority="high")
    assert task.is_complete is False
    task.mark_complete()
    assert task.is_complete is True


def test_add_task_increases_pet_task_count():
    """Adding a task to a Pet should increase its task list by one."""
    pet = Pet(name="Max", species="dog", age=3)
    assert len(pet.tasks) == 0
    pet.add_task(Task(title="Feeding", duration_minutes=10, priority="high"))
    assert len(pet.tasks) == 1
