"""
main.py — temporary testing ground for PawPal+ logic.
Run with: python main.py
"""

from pawpal_system import Task, Pet, Owner, Scheduler


# --- Setup ---
owner = Owner(name="Jordan", available_minutes=90, preferred_start_time="08:00")

max = Pet(name="Max", species="dog", age=3)
luna = Pet(name="Luna", species="cat", age=5)

# --- Tasks for Max ---
max.add_task(Task(title="Morning walk", duration_minutes=30, priority="high", preferred_time="morning"))
max.add_task(Task(title="Feeding", duration_minutes=10, priority="high", preferred_time="morning"))
max.add_task(Task(title="Enrichment toy", duration_minutes=20, priority="low", preferred_time="afternoon"))

# --- Tasks for Luna ---
luna.add_task(Task(title="Brush fur", duration_minutes=15, priority="medium", preferred_time="evening"))
luna.add_task(Task(title="Medication", duration_minutes=5, priority="high", preferred_time="morning"))

# --- Register pets ---
owner.add_pet(max)
owner.add_pet(luna)

# --- Build plan ---
scheduler = Scheduler(owner)
scheduler.build_plan()

# --- Print Today's Schedule ---
print("=" * 45)
print(f"  TODAY'S SCHEDULE FOR {owner.name.upper()}")
print(f"  Available time: {owner.available_minutes} min")
print("=" * 45)

if scheduler.schedule:
    total = 0
    for i, task in enumerate(scheduler.schedule, start=1):
        pet_label = f"[{task.pet_name}]" if task.pet_name else ""
        time_label = f"({task.preferred_time})" if task.preferred_time else ""
        print(f"  {i}. {task.title} {pet_label}")
        print(f"     {task.duration_minutes} min | {task.priority} priority {time_label}")
    total = sum(t.duration_minutes for t in scheduler.schedule)
    print("-" * 45)
    print(f"  Total: {total} min")
else:
    print("  No tasks scheduled.")

if scheduler.skipped:
    print("\n  Skipped (didn't fit):")
    for task in scheduler.skipped:
        pet_label = f"[{task.pet_name}]" if task.pet_name else ""
        print(f"  - {task.title} {pet_label} ({task.duration_minutes} min)")

print("=" * 45)
