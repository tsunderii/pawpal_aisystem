# Model Card — PawPal+

## Base Project

PawPal+ was originally built in Module 2 as a Python + Streamlit pet-care scheduling app. The base project established the core classes (`Task`, `Pet`, `Owner`, `Scheduler`) and a basic Streamlit UI. Modules 3 and 4 extended it with a weighted urgency scoring algorithm, an agentic AI planner powered by Gemini, an automated evaluation harness, and a system architecture diagram.

---

## AI Collaboration

### How AI was used

AI tools were used during this project to help understand how to create algorithms and write test cases. Specifically, AI was used to help refactor and debug the priority column display in the task table, and to draft README documentation. Goal-oriented prompts were most effective — for example: *"write tests for sorting, recurrence, and conflict detection, with at least one edge case each"* gave directly usable output that was then reviewed before being accepted.

### One moment where AI output was not accepted as-is

When AI generated the weighted scoring formula, it initially suggested using `date.today()` directly inside `Task.next_occurrence()` to calculate the overdue bonus — but that meant the score would silently return `0` for tasks with no `due_date` without making it obvious why. This was caught by manually tracing through the logic with a task that had `due_date=None` and confirmed it would produce an incorrect result. A specific test was written to confirm the guard worked correctly before the code was accepted.

### One helpful and one flawed AI moment

**Helpful:** When designing the weighted scoring algorithm, describing the goal (urgency based on priority, overdue days, and task size) produced a clean three-component formula. The AI also proactively flagged the division-by-zero edge case on `available_minutes` and explained why the `min(..., 50)` cap on the overdue bonus mattered — without being asked. That kind of proactive edge-case thinking saved a debugging cycle.

**Flawed:** When wiring up the Streamlit `filter_tasks` section, AI suggested storing the filtered result in a session state variable and reading from it in the schedule builder. This introduced a silent stale-data bug: if a new task was added after filtering, the cached list wouldn't update and the schedule would be built on outdated data. The AI had no way of knowing this would be a problem because it didn't reason through how Streamlit reruns interact with session state mutations. The fix was to re-derive the filtered list on each rerun instead of caching it.

---

## Biases and Limitations

- The scheduler has no knowledge of what actually matters for a specific animal. It treats a 30-minute walk for a senior dog the same as for a puppy, and has no awareness that cats generally don't need walks. All priority and urgency logic is owner-set — the system doesn't push back if something medically important is marked low priority.
- Conflict detection has a bias toward false positives. It flags any two tasks in the same named time slot (morning, afternoon, evening) as a conflict, even if both are short enough to fit back-to-back.
- The AI planner layer is non-deterministic — the same task list can produce slightly different suggestions on different runs, which limits reliability for real care decisions.

---

## Testing Results

The automated evaluation harness (`eval.py`) runs 20 pass/fail scenarios covering:

- Priority ordering (high before medium before low)
- Time budget enforcement (total scheduled time never exceeds available minutes)
- Overflow handling (tasks that don't fit go to the skipped list)
- Empty schedule edge cases (all tasks too long)
- Time-slot ordering (morning → afternoon → evening)
- Weighted scoring (overdue tasks outrank on-time tasks of higher priority, efficiency bonus applied correctly, overdue bonus capped at 50)
- Recurring task generation (daily → tomorrow, weekly → 7 days)
- Edge cases (identical scores, no-due-date tasks, zero available time)

**Confidence: 4.5 / 5** — AI was used to triple-check logic and write tests, but edge cases like consistent tiebreaking between identical scores and owner-with-no-pets detection were not fully covered and would be the next area to test.

---

## Responsible AI Reflection

### Could this AI be misused?

The subject matter — pet care scheduling — is low-stakes, but a few real risks exist:

1. **Over-trust:** The AI response sounds confident and structured, which could lead an owner to follow its schedule without questioning whether it's right for their specific pet's needs. A simple disclaimer ("always confirm medical tasks with your vet") is included in the UI.
2. **Data exposure:** `planner.log` records every task the owner adds. The log is local and gitignored, but a public deployment without log sanitization would expose personal data.
3. **API key exposure:** The `.env` file is gitignored and `.env.example` uses a placeholder, but there is no hard enforcement preventing accidental commits.

### What surprised me about AI reliability

The biggest surprise was how inconsistently the agent followed its own instructions. The system prompt explicitly says to always call `get_schedule_context` first — but with shorter or vaguer prompts, it would sometimes skip that step and build a plan without reading the current task data. The output still looked reasonable, making the issue easy to miss without reading the log. This reinforced that agent behavior needs to be verified through logging and tracing, not just by reading the final response.
