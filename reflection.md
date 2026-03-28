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

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
