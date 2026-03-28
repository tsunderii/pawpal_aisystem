"""
main.py — PawPal+ Phase 3 demo.
Run with: python3 main.py

Demonstrates:
  - sort_by_time()          tasks ordered morning → afternoon → evening
  - filter_tasks()          by pet and completion status
  - detect_conflicts()      same-pet/cross-pet/slot-overload warnings
  - frequency + timedelta   daily/weekly tasks auto-spawn next occurrence
"""

from datetime import date
from pawpal_system import Task, Pet, Owner, Scheduler

SEP = "=" * 52

# ── Setup ──────────────────────────────────────────────
owner = Owner(name="Jordan", available_minutes=120, preferred_start_time="08:00")

max  = Pet(name="Max",  species="dog", age=3)
luna = Pet(name="Luna", species="cat", age=5)

# Tasks added OUT OF ORDER to make sort_by_time() meaningful
max.add_task(Task(title="Enrichment toy", duration_minutes=20, priority="low",
                  preferred_time="afternoon"))
max.add_task(Task(title="Morning walk",   duration_minutes=30, priority="high",
                  preferred_time="morning"))
# Daily recurring — should spawn a new task when completed
max.add_task(Task(title="Feeding",        duration_minutes=10, priority="high",
                  preferred_time="morning", frequency="daily",
                  due_date=date.today()))

luna.add_task(Task(title="Brush fur",  duration_minutes=15, priority="medium",
                   preferred_time="evening"))
# Weekly recurring
luna.add_task(Task(title="Medication", duration_minutes=5,  priority="high",
                   preferred_time="morning", frequency="weekly",
                   due_date=date.today()))

# ── Conflict demo: two tasks for Luna in the SAME slot ──
luna.add_task(Task(title="Vet check",      duration_minutes=40, priority="high",
                   preferred_time="morning"))   # <-- same slot as Medication

# Max also has a morning task that clashes cross-pet with Luna's high-priority pile
max.add_task(Task(title="Flea treatment",  duration_minutes=15, priority="high",
                  preferred_time="morning"))

owner.add_pet(max)
owner.add_pet(luna)

scheduler = Scheduler(owner)
scheduler.build_plan()

# ── 1. Priority-ordered schedule ───────────────────────
print(SEP)
print("  SCHEDULE  (priority order)")
print(SEP)
for i, t in enumerate(scheduler.schedule, 1):
    label = f"[{t.pet_name}]" if t.pet_name else ""
    freq  = f" ({t.frequency})" if t.frequency != "once" else ""
    print(f"  {i}. {t.title} {label}{freq}")
    print(f"     {t.duration_minutes} min | {t.priority} | {t.preferred_time or 'any'}")

# ── 2. Sorted by time slot ─────────────────────────────
print()
print(SEP)
print("  SORTED BY TIME  (morning → afternoon → evening)")
print(SEP)
for t in scheduler.sort_by_time():
    label = f"[{t.pet_name}]" if t.pet_name else ""
    print(f"  {t.preferred_time or 'any':12s}  {t.title} {label}  ({t.duration_minutes} min)")

# ── 3. Filter: Max's pending tasks ────────────────────
print()
print(SEP)
print("  FILTER: Max's pending tasks")
print(SEP)
for t in scheduler.filter_tasks(pet_name="Max", completed=False):
    print(f"  - {t.title}  ({t.duration_minutes} min | {t.priority})")

# ── 4. Conflict detection ─────────────────────────────
print()
print(SEP)
print("  CONFLICT DETECTION")
print(SEP)
conflicts = scheduler.detect_conflicts()
if conflicts:
    for msg in conflicts:
        print(f"  ! {msg}")
else:
    print("  No conflicts detected.")

# ── 5. Frequency / auto-spawn demo ────────────────────
print()
print(SEP)
print("  FREQUENCY — auto-spawn next occurrence")
print(SEP)

for title, pet in [("Feeding", max), ("Medication", luna)]:
    task = next(t for t in pet.tasks if t.title == title)
    print(f"  '{task.title}' [{task.pet_name}]  frequency={task.frequency}  due={task.due_date}")
    new_task = scheduler.mark_task_complete(task)
    if new_task:
        print(f"    → marked complete; next occurrence added  due={new_task.due_date}")
    else:
        print(f"    → marked complete; no recurrence (once).")

# Confirm new tasks appear in the next build
print()
print("  Tasks in next build_plan() that came from auto-spawn:")
scheduler.build_plan()
spawned_titles = {"Feeding", "Medication"}
for t in scheduler.schedule:
    if t.title in spawned_titles and not t.is_complete:
        print(f"    ✓ '{t.title}' [{t.pet_name}]  due={t.due_date}  (frequency={t.frequency})")

print(SEP)
