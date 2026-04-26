"""
eval.py — PawPal+ Scheduling Engine Evaluation Harness

Runs 12 predefined scenarios through the core scheduler and prints a
structured pass/fail report with confidence ratings. No API key needed.

Run with:  python3 eval.py
           python3 eval.py --verbose    (show extra detail per scenario)
"""

import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Callable

from pawpal_system import Task, Pet, Owner, Scheduler

# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class ScenarioResult:
    name:       str
    category:   str
    passed:     bool
    detail:     str
    checks:     int   # total sub-checks attempted
    hits:       int   # sub-checks that passed
    confidence: float = field(init=False)

    def __post_init__(self):
        self.confidence = self.hits / self.checks if self.checks else 0.0


# ---------------------------------------------------------------------------
# Scenario runner
# ---------------------------------------------------------------------------

def run(name: str, category: str, fn: Callable) -> ScenarioResult:
    """Execute a scenario function and catch any unexpected exceptions."""
    try:
        passed, detail, checks, hits = fn()
        return ScenarioResult(name, category, passed, detail, checks, hits)
    except Exception as exc:
        return ScenarioResult(name, category, False, f"EXCEPTION: {exc}", 1, 0)


# ---------------------------------------------------------------------------
# Helper: build a fresh owner with one pet
# ---------------------------------------------------------------------------

def _owner(minutes: int = 120) -> tuple[Owner, Pet, Scheduler]:
    o = Owner(name="Eval", available_minutes=minutes)
    p = Pet(name="Max", species="dog", age=3)
    o.add_pet(p)
    return o, p, Scheduler(o)


# ---------------------------------------------------------------------------
# Scenarios — Scheduling correctness
# ---------------------------------------------------------------------------

def s01_priority_ordering():
    """High-priority task is scheduled before low-priority when both fit."""
    o, p, s = _owner(120)
    p.add_task(Task("Low task",  duration_minutes=20, priority="low",  preferred_time="morning"))
    p.add_task(Task("High task", duration_minutes=20, priority="high", preferred_time="morning"))
    s.build_plan()
    first = s.schedule[0].priority if s.schedule else None
    passed = (first == "high")
    detail = f"First scheduled priority: '{first}' (expected 'high')"
    return passed, detail, 1, int(passed)


def s02_time_budget_respected():
    """Total scheduled minutes never exceeds available_minutes."""
    o, p, s = _owner(60)
    p.add_task(Task("Walk",    duration_minutes=30, priority="high"))
    p.add_task(Task("Groom",   duration_minutes=20, priority="medium"))
    p.add_task(Task("Play",    duration_minutes=25, priority="low"))
    s.build_plan()
    total = sum(t.duration_minutes for t in s.schedule)
    passed = (total <= 60)
    detail = f"Scheduled: {total} min  ≤  60 min available"
    return passed, detail, 1, int(passed)


def s03_overflow_goes_to_skipped():
    """Tasks that exceed the time budget land in skipped, not schedule."""
    o, p, s = _owner(30)
    p.add_task(Task("Short", duration_minutes=30, priority="high"))
    p.add_task(Task("Long",  duration_minutes=60, priority="low"))
    s.build_plan()
    sched_titles  = {t.title for t in s.schedule}
    skip_titles   = {t.title for t in s.skipped}
    c1 = "Short" in sched_titles
    c2 = "Long"  in skip_titles
    passed = c1 and c2
    detail = f"schedule={sched_titles}  skipped={skip_titles}"
    return passed, detail, 2, int(c1) + int(c2)


def s04_empty_schedule_when_all_too_long():
    """If every task exceeds available time, schedule is empty."""
    o, p, s = _owner(10)
    p.add_task(Task("Big task", duration_minutes=60, priority="high"))
    s.build_plan()
    c1 = len(s.schedule) == 0
    c2 = len(s.skipped)  == 1
    passed = c1 and c2
    detail = f"schedule has {len(s.schedule)} tasks, skipped has {len(s.skipped)}"
    return passed, detail, 2, int(c1) + int(c2)


def s05_sort_by_time_order():
    """sort_by_time() returns morning → afternoon → evening regardless of insertion order."""
    o, p, s = _owner(200)
    p.add_task(Task("Evening thing",   duration_minutes=10, priority="low",  preferred_time="evening"))
    p.add_task(Task("Morning thing",   duration_minutes=10, priority="high", preferred_time="morning"))
    p.add_task(Task("Afternoon thing", duration_minutes=10, priority="medium", preferred_time="afternoon"))
    s.build_plan()
    ordered = [t.preferred_time for t in s.sort_by_time()]
    expected = ["morning", "afternoon", "evening"]
    passed = (ordered == expected)
    detail = f"order={ordered}  expected={expected}"
    return passed, detail, 1, int(passed)


# ---------------------------------------------------------------------------
# Scenarios — Weighted scoring
# ---------------------------------------------------------------------------

def s06_weighted_overdue_outranks_ontime():
    """An overdue medium task scores higher than an on-time high task."""
    o, p, s = _owner(40)
    overdue = Task("Overdue groom", duration_minutes=20, priority="medium",
                   due_date=date.today() - timedelta(days=20))
    ontime  = Task("On-time walk",  duration_minutes=20, priority="high")
    p.add_task(overdue)
    p.add_task(ontime)
    s.build_weighted_plan()
    first = s.schedule[0].title if s.schedule else None
    passed = (first == "Overdue groom")
    detail = f"First task: '{first}' (expected 'Overdue groom')"
    return passed, detail, 1, int(passed)


def s07_efficiency_bonus_applied():
    """Quick task (≤25% of available time) earns +15 efficiency bonus."""
    o, p, s = _owner(100)
    quick = Task("Quick feed", duration_minutes=25, priority="low")   # 25% → bonus
    slow  = Task("Slow walk",  duration_minutes=26, priority="low")   # 26% → no bonus
    p.add_task(quick)
    p.add_task(slow)
    score_quick = s.weighted_score(quick)
    score_slow  = s.weighted_score(slow)
    diff = round(score_quick - score_slow, 1)
    passed = (diff == 15.0)
    detail = f"quick={score_quick}  slow={score_slow}  diff={diff}  (expected 15.0)"
    return passed, detail, 1, int(passed)


def s08_overdue_bonus_capped_at_50():
    """Overdue bonus tops out at 50 no matter how many days late."""
    o, p, s = _owner(500)
    very_late = Task("Ancient task", duration_minutes=200, priority="low",
                     due_date=date.today() - timedelta(days=999))
    p.add_task(very_late)
    score = s.weighted_score(very_late)
    # base=10, overdue capped at 50, no efficiency bonus (200/500=40%>25%)
    passed = (score == 60.0)
    detail = f"score={score}  expected=60.0  (base 10 + overdue cap 50)"
    return passed, detail, 1, int(passed)


def s09_no_due_date_zero_overdue():
    """Tasks without a due_date receive zero overdue bonus."""
    o, p, s = _owner(200)
    task = Task("No date task", duration_minutes=60, priority="medium", due_date=None)
    p.add_task(task)
    score = s.weighted_score(task)
    # base=50, no overdue, no efficiency (60/200=30%>25%)
    passed = (score == 50.0)
    detail = f"score={score}  expected=50.0"
    return passed, detail, 1, int(passed)


# ---------------------------------------------------------------------------
# Scenarios — Conflict detection
# ---------------------------------------------------------------------------

def s10_same_pet_same_slot_flagged():
    """Two tasks for the same pet in the same slot produce a conflict warning."""
    o, p, s = _owner(120)
    p.add_task(Task("Walk",  duration_minutes=20, priority="high",   preferred_time="morning"))
    p.add_task(Task("Feed",  duration_minutes=10, priority="medium", preferred_time="morning"))
    conflicts = s.detect_conflicts()
    has_pet_conflict = any("Max" in c and "morning" in c for c in conflicts)
    passed = has_pet_conflict
    detail = f"{len(conflicts)} conflict(s): {conflicts[0][:60] + '...' if conflicts else 'none'}"
    return passed, detail, 1, int(passed)


def s11_slot_overload_flagged():
    """A slot totalling >60 min triggers an overload warning."""
    o, p, s = _owner(300)
    for i in range(4):
        p.add_task(Task(f"Task{i}", duration_minutes=20, priority="low", preferred_time="afternoon"))
    conflicts = s.detect_conflicts()
    overloaded = any("overloaded" in c and "afternoon" in c for c in conflicts)
    passed = overloaded
    detail = f"{len(conflicts)} conflict(s) found"
    return passed, detail, 1, int(passed)


def s12_no_false_conflict_different_slots():
    """Tasks in different slots for the same pet produce no same-pet conflict."""
    o, p, s = _owner(120)
    p.add_task(Task("Walk", duration_minutes=20, priority="high",   preferred_time="morning"))
    p.add_task(Task("Feed", duration_minutes=10, priority="medium", preferred_time="evening"))
    conflicts = s.detect_conflicts()
    false_positive = any("Max" in c and "Conflict" in c for c in conflicts)
    passed = not false_positive
    detail = f"{len(conflicts)} conflict(s) — no same-pet clash expected"
    return passed, detail, 1, int(passed)


# ---------------------------------------------------------------------------
# Report printer
# ---------------------------------------------------------------------------

CATEGORIES = {
    "Scheduling": "📋",
    "Weighted":   "⚖️ ",
    "Conflicts":  "⚠️ ",
}

WIDTH = 65

def _bar(ratio: float, width: int = 20) -> str:
    filled = round(ratio * width)
    return "█" * filled + "░" * (width - filled)


def print_report(results: list[ScenarioResult], verbose: bool) -> None:
    passed_count = sum(1 for r in results if r.passed)
    total        = len(results)
    overall_pct  = passed_count / total * 100

    print()
    print("=" * WIDTH)
    print("  PawPal+  —  Scheduling Engine Evaluation Harness")
    print("=" * WIDTH)
    print(f"  {total} scenarios  |  no API key required")
    print("=" * WIDTH)
    print()

    current_cat = None
    for r in results:
        if r.category != current_cat:
            current_cat = r.category
            icon = CATEGORIES.get(r.category, "  ")
            print(f"  {icon} {r.category.upper()}")
            print()

        status  = "PASS ✓" if r.passed else "FAIL ✗"
        conf    = f"{r.confidence * 100:.0f}%"
        name_w  = 42
        print(f"    {status}  [{conf:>4}]  {r.name[:name_w]:<{name_w}}")
        if verbose or not r.passed:
            print(f"              {r.detail}")
        print()

    # ── Summary ──────────────────────────────────────────────────────────────
    print("=" * WIDTH)
    bar = _bar(passed_count / total)
    print(f"  RESULT:  {passed_count} / {total} passed  ({overall_pct:.1f}%)   {bar}")

    if passed_count == total:
        print("  All systems nominal — core scheduler is working correctly.")
    elif passed_count >= total * 0.8:
        failed = [r.name for r in results if not r.passed]
        print(f"  Minor issues in: {', '.join(failed)}")
    else:
        failed = [r.name for r in results if not r.passed]
        print(f"  Failures: {', '.join(failed)}")

    # ── Per-category breakdown ────────────────────────────────────────────────
    print()
    print("  Category breakdown:")
    cats = {}
    for r in results:
        cats.setdefault(r.category, []).append(r)
    for cat, cat_results in cats.items():
        n_pass = sum(1 for r in cat_results if r.passed)
        n_total = len(cat_results)
        icon = CATEGORIES.get(cat, "  ")
        bar_cat = _bar(n_pass / n_total, width=10)
        print(f"    {icon} {cat:<12}  {n_pass}/{n_total}  {bar_cat}")

    print("=" * WIDTH)
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

SCENARIOS = [
    ("Priority ordering",              "Scheduling", s01_priority_ordering),
    ("Time budget respected",          "Scheduling", s02_time_budget_respected),
    ("Overflow goes to skipped",       "Scheduling", s03_overflow_goes_to_skipped),
    ("Empty schedule when all long",   "Scheduling", s04_empty_schedule_when_all_too_long),
    ("sort_by_time order",             "Scheduling", s05_sort_by_time_order),
    ("Overdue outranks on-time",       "Weighted",   s06_weighted_overdue_outranks_ontime),
    ("Efficiency bonus applied",       "Weighted",   s07_efficiency_bonus_applied),
    ("Overdue bonus capped at 50",     "Weighted",   s08_overdue_bonus_capped_at_50),
    ("No due_date = zero overdue",     "Weighted",   s09_no_due_date_zero_overdue),
    ("Same-pet same-slot flagged",     "Conflicts",  s10_same_pet_same_slot_flagged),
    ("Slot overload flagged",          "Conflicts",  s11_slot_overload_flagged),
    ("No false conflict diff slots",   "Conflicts",  s12_no_false_conflict_different_slots),
]


if __name__ == "__main__":
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    results = [run(name, cat, fn) for name, cat, fn in SCENARIOS]
    print_report(results, verbose)
    sys.exit(0 if all(r.passed for r in results) else 1)
