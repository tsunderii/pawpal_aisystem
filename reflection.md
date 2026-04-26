# PawPal+ Project Reflection

## 1. System Design

(Core actions)
Pet care tasks, generating today's plans, viewing today's tasks, and checking off today's tasks

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

My initial UML design is arranged in a linear hierarchy from Owner to Pet objects, each Pet holding a list of Task objects, and a seperate Scheduler class. My classes include:

Task - Represents a single care activity. Holds information for what task is being done, how long, and how important the task is.
Pet - The animal being cared for -- Owns the list of tasks and knows what tasks are still pending. Sort of the natural container for tasks belonging to the specific animal
Owner - The user -- Holding the time constraints and the list of pets
Scheduler - (Seperate class) Planning logic, taking in Owner as input. The only class that makes deicisons, reading owner's constraints and selecting the tasks that fit, producing an ordered plan with explanation

**b. Design changes**

Yes, two changes were made after an AI review of the class skeleton:

1. Added `pet_name: Optional[str]` to `Task`. The original design had no back-reference from a task to its pet. Once `Scheduler.build_plan()` flattens all tasks into a single list via `get_all_tasks()`, it loses track of which animal each task belongs to. Without this field, the daily plan couldn't say "Walk Max" vs "Feed Luna". The field is set automatically when `Pet.add_task()` is called.

2. Added `skipped: list[Task]` to `Scheduler`. The original skeleton only stored the tasks that made it into the plan. Without a place to record skipped tasks, `get_explanation()` couldn't explain *why* certain tasks were left out (e.g., didn't fit in available time). This attribute gives the explainability feature something to work with.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

Some examples of constraints that the scheduler considers is available time (owner's total minutes in a day), task priority, preferred time slot, and how long each task takes. I decided which constraints mattered the most depending on priority. A pet owner can use other applications to take care of time-specific scheduling up to the minute but putting priority as a constrait ensures that important tasks are not forgotten.
**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

Looking at filter_tasks(), one tradeoff that the scheduler is that when the scheduler sees two appointment tasks on the same day and assumes that they must overlap without checking what time each one starts. So, the tradeoff would be that the scheduler works in a simple manner, only able to take in one task at a time rather than being more complex and detecting when tasks start/begin, forfetting accuracy. This tradeoff is reasonable considering that this is a pet care app for a single owner managing daily tasks -- the owner doesn't need minute-by-minute precision, keeping the app's purpose centralized.
---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used AI tools during this project to help understand how to create algorithms and test cases. Specifically, I mostly used AI to help me refactor and debug the _priority colum showing up in the table, and effectively drafting up READMEs -- describing what I needed and then reviewed what it produced before making major changes. Goal-oriented prompts and questions were the most helpful for me to understand the reasoning behind AI decisions. One prompt example is "write tests for sorting, recurrence, and conflict detection, with at least one edge case each" gave directly usable output."

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

One moment where I didn't accept AI as-is:
When AI generated the weighted scoring formula, it initially suggested using date.today() directly inside Task.next_occurrence() to calculate the overdue bonus — but that meant the score would silently return 0 for tasks with no due_date without making it obvious why. I caught this by manually tracing through the logic with a task that had due_date=None and confirmed it would produce an incorrect result. 

I verified this by asking the AI to write a specific test mentioning the error and confirming that the guard worked correctly with py.test

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

Some behaviors I test included: Ensuring daily tasks spawn a next occurance due tommorow, weekly tasks become due in 7 days, overdue medium outtanking on-time high, and conflict detection.

These tests are important because it is impossible to manually check the logic for all these small edge cases, so it is eaisier to be able to detect bugs or conflicts by aiming to "break" the system using tests. These tests are able to ensure that the features actually work and not assumed to work.
**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I would give my confidence a 4.5/5 overall. I believe that I used AI to triple check logic and write up tests but there is always a possibility that I have missed something or edge cases that I didn't consider. Some edge cases that I would test next time if I had more time would be testing if two tasks with identical weighted scores have a tiebreaker that's consistent and if an owner with no pets is detected (and vice versa).

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I am most satisfied with the project being able to translate the UML diagram into a working algorithm. In general, I am satisfied with my AI and human collaboration and my increasing skills in understanding how to effectively understand what the AI is writing down instead of blindly accepting changes.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

If I had another iteration, one thing that I would like to improve on is the UI -- making it more interesting and less like the stereotypical Streamlit UI with black backgrounds, etc. Another aspect that I would improve on is a way to mark tasks complete through the UI so the app is eaisier to use and having a button in the app to trigger it

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

One important thing I learned while designing systems is to be strategic in ideation to execution. This means just not implementing features willy-nilly but actually having a format that I inted to stick by. This makes it so that it is eaisier to identify logic holes or bugs in the program, such as edge cases.

---

## 6. Responsible AI Reflection

**a. Limitations and biases in the system**

The biggest limitation is that the scheduler has no knowledge of what actually matters for a specific animal. It treats a 30-minute walk for a senior dog the same as a 30-minute walk for a puppy, and it has no idea that cats generally don't need walks at all. All of the priority and urgency logic is set by the owner — the system doesn't push back or warn you if something seems medically important. If an owner marks a medication as "low priority," the system will happily skip it to make room for a lower-urgency task.

The conflict detection also has a bias toward false positives. It flags any two tasks in the same named time slot (morning, afternoon, evening) as a conflict, even if both tasks are short enough to comfortably fit back-to-back. A 5-minute feeding and a 10-minute grooming both marked "morning" will trigger a conflict warning, which could cause an owner to unnecessarily restructure their day.

The AI planner layer adds another layer of non-determinism — the same task list will produce slightly different suggestions on different runs. This means the app can't be fully trusted to give consistent advice, which matters if someone is making real care decisions based on what it says.

**b. Could your AI be misused, and how would you prevent that?**

The subject matter — pet care scheduling — is low-stakes enough that direct harm from misuse is unlikely. That said, a few real risks exist:

The most practical one is over-trust. The AI response sounds confident and structured, which could lead an owner to follow its schedule without questioning whether it's actually right for their pet's specific needs. A sick or elderly animal, for example, might need a vet's schedule — not an AI's. A simple disclaimer in the UI ("always confirm medical tasks with your vet") would help set the right expectations.

The second risk is data exposure. The `planner.log` file records every task the owner has added, including task names that could reveal personal information if the app were ever deployed publicly. Right now the log is local and gitignored, but if someone pushed a deployment without thinking about it, that data would be exposed. The fix would be to sanitize log output or make logging opt-in.

The third is API key exposure. The `.env` file is gitignored, but a user could accidentally commit it. The `.env.example` pattern and the gitignore entry mitigate this, but there's no hard enforcement.

**c. What surprised me while testing the AI's reliability**

The biggest surprise was how inconsistently the agent followed its own instructions. The system prompt explicitly says to always call `get_schedule_context` first, then build a plan, then call `detect_and_explain`. Most of the time it did. But sometimes — especially with shorter or vaguer prompts like "what should I do today?" — it would skip `get_schedule_context` entirely and jump straight to building a plan, which meant it was making scheduling decisions without actually reading the current task data first. The output still looked reasonable, which made the issue easy to miss without reading the log.

I also didn't expect the AI to sometimes produce useful suggestions that weren't in the scheduling tools at all — it would notice things like "you have three high-priority tasks and only 90 minutes, you might want to delegate one" even though there's no tool for delegation advice. That was genuinely helpful, but it also means the system is doing reasoning I didn't explicitly design, which is a little unsettling from a reliability standpoint.

**d. AI collaboration — one helpful moment and one flawed moment**

*Helpful:* When I was designing the weighted scoring algorithm, I described what I wanted (urgency based on priority, overdue days, and task size) and the AI produced a clean three-component formula with a cap on the overdue bonus. What made it actually useful wasn't just the formula — it was that the AI immediately flagged the `division-by-zero` edge case on `available_minutes` before I even asked, and explained why the `min(..., 50)` cap mattered (without it, a task that's 100 days overdue would completely dominate the schedule in a way that wasn't useful). That kind of proactive edge-case thinking saved a debugging cycle.

*Flawed:* When I asked the AI to help wire up the Streamlit `filter_tasks` section, it suggested storing the filtered result in a new session state variable and then reading from that variable in the schedule builder. On the surface this seemed reasonable, but it introduced a silent stale-data bug: if the owner added a new task after filtering, the cached filtered list wouldn't update, so the schedule would be built on outdated data. The AI had no way of knowing this would cause a problem because it didn't reason through how Streamlit reruns interact with session state mutations. I caught it by manually adding a task mid-session and noticing the schedule didn't change. The fix was simple — just re-derive the filtered list on each rerun instead of caching it — but it reinforced that AI-generated UI code needs to be traced through the actual execution model, not just read as if it were regular Python.
