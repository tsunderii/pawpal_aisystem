# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

The `Scheduler` class includes four algorithmic improvements beyond the basic daily plan:

- **`sort_by_time()`** — orders any task list by time slot (morning → afternoon → evening) using a lambda key, so the daily plan reads in chronological order regardless of how tasks were added.
- **`filter_tasks(pet_name, completed)`** — filters across all pets by owner name and/or completion status, making it easy to view only what still needs to be done for a specific pet.
- **`detect_conflicts()`** — scans pending tasks and returns plain-English warning messages for three situations: the same pet having multiple tasks in one slot, high-priority tasks competing across different pets in the same slot, and any slot whose total duration exceeds 60 minutes. It never crashes the app — it always returns a list (empty means no conflicts).
- **Recurring tasks (`frequency` + `mark_task_complete()`)** — tasks can be marked `"daily"` or `"weekly"`. When completed, `Scheduler.mark_task_complete()` automatically adds the next occurrence to the pet's task list with a new `due_date` calculated using Python's `timedelta` (today + 1 day for daily, today + 7 days for weekly).

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
