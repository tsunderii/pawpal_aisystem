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
