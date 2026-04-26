import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from ai_planner import run_planner_agent
from pawpal_system import Owner, Pet, Scheduler, Task

load_dotenv()  # reads GEMINI_API_KEY from .env if present

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SPECIES_EMOJI = {"dog": "🐶", "cat": "🐱", "other": "🐾"}
TIME_EMOJI    = {"morning": "🌅", "afternoon": "☀️", "evening": "🌙"}
FREQ_EMOJI    = {"once": "1️⃣", "daily": "🔁", "weekly": "📅"}

PRIORITY_BADGE = {
    "high":   "🔴 High",
    "medium": "🟡 Medium",
    "low":    "🟢 Low",
}

# Soft pastel row colours — readable in both light and dark themes
PRIORITY_ROW_COLOR = {
    "high":   "background-color: #ffd5d5; color: #7f0000",
    "medium": "background-color: #fff0cc; color: #7a4000",
    "low":    "background-color: #d5f0d5; color: #005000",
}


def fmt_priority(p: str) -> str:
    return PRIORITY_BADGE.get(p, p)


def fmt_time(t) -> str:
    return f"{TIME_EMOJI.get(t, '')} {t}" if t else "🕐 any"


def fmt_freq(f: str) -> str:
    return f"{FREQ_EMOJI.get(f, '')} {f}"


def styled_task_table(
    tasks: list,
    include_freq: bool = True,
    scheduler=None,
    show_score: bool = False,
):
    """Build a colour-coded styled DataFrame from a list of Task objects."""
    if not tasks:
        return pd.DataFrame()

    priorities, rows = [], []
    for t in tasks:
        priorities.append(t.priority)
        row = {
            "Pet":       t.pet_name or "—",
            "Task":      t.title,
            "⏱ Min":     t.duration_minutes,
            "Priority":  fmt_priority(t.priority),
            "Time slot": fmt_time(t.preferred_time),
        }
        if include_freq:
            row["Frequency"] = fmt_freq(t.frequency)
        if show_score and scheduler is not None:
            row["Score"] = round(scheduler.weighted_score(t), 1)
        rows.append(row)

    df = pd.DataFrame(rows)

    def _row_style(row: pd.Series) -> list[str]:
        style = PRIORITY_ROW_COLOR.get(priorities[row.name], "")
        return [style] * len(row)

    return df.style.apply(_row_style, axis=1).hide(axis="index")


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None
if "scheduler_result" not in st.session_state:
    st.session_state.scheduler_result = None   # (Scheduler, mode) tuple
if "ai_response" not in st.session_state:
    st.session_state.ai_response = None

# ---------------------------------------------------------------------------
# Sidebar — Owner setup + Pet management
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🐾 PawPal+")
    st.caption("Smart daily pet-care scheduling")
    st.divider()

    # ── Owner form ──────────────────────────────────────────────────────────
    st.subheader("👤 Owner Info")
    with st.form("owner_form"):
        owner_name        = st.text_input("Your name", value="Jordan")
        available_minutes = st.number_input(
            "Available time today (min)", min_value=10, max_value=480, value=90
        )
        start_time = st.text_input("Preferred start time", value="08:00")
        if st.form_submit_button("Save", use_container_width=True):
            existing = st.session_state.owner
            if existing is None:
                st.session_state.owner = Owner(
                    name=owner_name,
                    available_minutes=int(available_minutes),
                    preferred_start_time=start_time,
                )
                st.toast(f"Welcome, {owner_name}! 🎉")
            else:
                existing.name = owner_name
                existing.available_minutes = int(available_minutes)
                existing.preferred_start_time = start_time
                st.toast("Owner info updated.")

    if st.session_state.owner is None:
        st.info("Fill in your info above to get started.")
        st.stop()

    owner: Owner = st.session_state.owner
    st.divider()

    # ── Pet list ────────────────────────────────────────────────────────────
    st.subheader("🐾 My Pets")
    if owner.pets:
        for pet in list(owner.pets):
            col_name, col_btn = st.columns([4, 1])
            col_name.markdown(
                f"{SPECIES_EMOJI.get(pet.species, '🐾')} **{pet.name}** "
                f"<span style='color:gray;font-size:0.85em'>({pet.species}, {pet.age}y)</span>",
                unsafe_allow_html=True,
            )
            if col_btn.button("✕", key=f"rm_pet_{pet.name}", help=f"Remove {pet.name}"):
                owner.pets = [p for p in owner.pets if p.name != pet.name]
                st.session_state.scheduler_result = None
                st.session_state.ai_response = None
                st.rerun()
    else:
        st.caption("No pets yet — add one below.")

    with st.expander("➕ Add a pet"):
        with st.form("pet_form"):
            pet_name = st.text_input("Name", value="Max")
            species  = st.selectbox("Species", ["dog", "cat", "other"])
            age      = st.number_input("Age", min_value=0, max_value=30, value=3)
            if st.form_submit_button("Add Pet", use_container_width=True):
                if pet_name.lower() in [p.name.lower() for p in owner.pets]:
                    st.warning(f"'{pet_name}' already exists.")
                else:
                    owner.add_pet(Pet(name=pet_name, species=species, age=int(age)))
                    st.toast(f"{SPECIES_EMOJI.get(species, '🐾')} {pet_name} added!")
                    st.rerun()

    # ── Quick stats ─────────────────────────────────────────────────────────
    if owner.pets:
        st.divider()
        total_tasks   = sum(len(p.tasks) for p in owner.pets)
        pending_count = sum(len(p.get_pending_tasks()) for p in owner.pets)
        done_count    = total_tasks - pending_count
        st.metric("Pending tasks", pending_count)
        if total_tasks > 0:
            st.progress(
                done_count / total_tasks,
                text=f"{done_count} of {total_tasks} tasks done",
            )

# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------
owner = st.session_state.owner

st.title(f"🐾 {owner.name}'s PawPal+ Dashboard")
st.caption(
    f"Available today: **{owner.available_minutes} min** · "
    f"Start time: **{owner.preferred_start_time}**"
)

if not owner.pets:
    st.info("👈 Add a pet in the sidebar to get started.")
    st.stop()

tab_tasks, tab_schedule, tab_ai, tab_insights = st.tabs(
    ["📋 Tasks", "🗓️ Schedule", "🤖 AI Planner", "📊 Insights"]
)

# ===========================================================================
# Tab 1 — Tasks
# ===========================================================================
with tab_tasks:
    with st.expander("➕ Add a New Task", expanded=True):
        with st.form("task_form"):
            col_l, col_r = st.columns(2)
            with col_l:
                selected_pet_name = st.selectbox(
                    "For which pet?", [p.name for p in owner.pets]
                )
                task_title = st.text_input("Task title", value="Morning walk")
                duration   = st.number_input(
                    "Duration (min)", min_value=1, max_value=240, value=20
                )
            with col_r:
                priority       = st.selectbox("Priority", ["high", "medium", "low"])
                preferred_time = st.selectbox(
                    "Preferred time", ["morning", "afternoon", "evening", "any"]
                )
                frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])

            if st.form_submit_button(
                "➕ Add Task", type="primary", use_container_width=True
            ):
                pet = next(p for p in owner.pets if p.name == selected_pet_name)
                pet.add_task(
                    Task(
                        title=task_title,
                        duration_minutes=int(duration),
                        priority=priority,
                        preferred_time=(
                            None if preferred_time == "any" else preferred_time
                        ),
                        frequency=frequency,
                    )
                )
                st.session_state.scheduler_result = None
                st.session_state.ai_response = None
                st.toast(f"Added '{task_title}' for {selected_pet_name}!")
                st.rerun()

    st.divider()

    all_pending = owner.get_all_tasks()

    if not all_pending:
        st.info("No pending tasks yet. Add some above!")
    else:
        st.subheader("Pending Tasks")

        filter_opts     = ["All pets"] + [p.name for p in owner.pets]
        selected_filter = st.selectbox("Filter by pet", filter_opts, key="filter_pet")

        sched_preview = Scheduler(owner)
        display_tasks = (
            all_pending
            if selected_filter == "All pets"
            else sched_preview.filter_tasks(pet_name=selected_filter, completed=False)
        )
        sorted_tasks = sched_preview.sort_by_time(display_tasks)

        if not sorted_tasks:
            st.info("No pending tasks for this pet.")
        else:
            for i, task in enumerate(sorted_tasks):
                pet_obj  = next((p for p in owner.pets if p.name == task.pet_name), None)
                pet_icon = SPECIES_EMOJI.get(
                    pet_obj.species if pet_obj else "other", "🐾"
                )
                key = f"{task.pet_name}_{task.title}_{i}"

                c_info, c_pri, c_dur, c_done, c_del = st.columns([4, 2, 1, 1, 1])
                with c_info:
                    st.markdown(
                        f"**{task.title}** &nbsp; {pet_icon} *{task.pet_name or '—'}*",
                        unsafe_allow_html=True,
                    )
                    st.caption(
                        f"{fmt_time(task.preferred_time)} · {fmt_freq(task.frequency)}"
                    )
                with c_pri:
                    st.markdown(fmt_priority(task.priority))
                with c_dur:
                    st.markdown(f"⏱ **{task.duration_minutes}m**")
                with c_done:
                    if st.button("✅", key=f"done_{key}", help="Mark complete"):
                        if pet_obj:
                            next_t = pet_obj.mark_task_complete(task.title)
                            msg = f"'{task.title}' marked complete!"
                            if next_t:
                                msg += f" Next due: {next_t.due_date}"
                            st.toast(msg)
                            st.session_state.scheduler_result = None
                            st.session_state.ai_response = None
                            st.rerun()
                with c_del:
                    if st.button("🗑️", key=f"del_{key}", help="Delete task"):
                        if pet_obj:
                            pet_obj.remove_task(task.title)
                            st.toast(f"Deleted '{task.title}'")
                            st.session_state.scheduler_result = None
                            st.session_state.ai_response = None
                            st.rerun()
                st.divider()

# ===========================================================================
# Tab 2 — Schedule
# ===========================================================================
with tab_schedule:
    st.subheader("Generate Today's Schedule")

    all_pending = owner.get_all_tasks()

    col_mode, col_btn = st.columns([3, 1])
    with col_mode:
        schedule_mode = st.radio(
            "Scheduling mode",
            [
                "Priority (high → medium → low)",
                "Weighted Score (urgency + overdue + efficiency)",
            ],
            horizontal=True,
        )
    with col_btn:
        build_clicked = st.button(
            "🗓️ Build Schedule",
            type="primary",
            use_container_width=True,
            disabled=not all_pending,
        )

    if not all_pending:
        st.info("Add tasks in the **Tasks** tab, then build a schedule here.")

    if build_clicked and all_pending:
        scheduler = Scheduler(owner)
        if "Weighted" in schedule_mode:
            scheduler.build_weighted_plan()
        else:
            scheduler.build_plan()
        st.session_state.scheduler_result = (scheduler, schedule_mode)

    if st.session_state.scheduler_result:
        scheduler, mode = st.session_state.scheduler_result

        conflicts = scheduler.detect_conflicts()
        if conflicts:
            with st.expander(
                f"⚠️ {len(conflicts)} scheduling conflict(s) — click to expand",
                expanded=True,
            ):
                for msg in conflicts:
                    st.warning(msg)
        else:
            st.success("✅ No scheduling conflicts detected.")

        total_scheduled = sum(t.duration_minutes for t in scheduler.schedule)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Tasks scheduled", len(scheduler.schedule))
        m2.metric("Tasks skipped",   len(scheduler.skipped))
        m3.metric("Minutes used",    total_scheduled)
        m4.metric("Minutes left",    owner.available_minutes - total_scheduled)

        st.subheader("Today's Schedule")
        if "Weighted" in mode:
            st.caption(
                "Ranked by urgency score "
                "(priority base + overdue bonus + efficiency bonus)"
            )
        else:
            st.caption("Sorted by priority 🔴→🟡→🟢, then time slot 🌅→☀️→🌙")

        if scheduler.schedule:
            st.dataframe(
                styled_task_table(
                    scheduler.sort_by_time(),
                    scheduler=scheduler if "Weighted" in mode else None,
                    show_score="Weighted" in mode,
                ),
                use_container_width=True,
            )
        else:
            st.warning(
                "No tasks fit in the available time. "
                "Try increasing available minutes in the sidebar."
            )

        if scheduler.skipped:
            st.subheader("⏭️ Skipped (didn't fit in available time)")
            st.dataframe(
                styled_task_table(scheduler.skipped, include_freq=False),
                use_container_width=True,
            )

        with st.expander("📝 Full scheduling explanation"):
            st.text(scheduler.get_explanation())

# ===========================================================================
# Tab 3 — AI Planner
# ===========================================================================
with tab_ai:
    st.subheader("🤖 AI Planner")
    st.caption(
        "Ask the AI to plan your day, flag conflicts, or explain trade-offs. "
        "The agent calls your live task data — no copy-pasting required."
    )

    # Show a warning if the API key isn't set, but don't hide the UI
    api_key_present = bool(os.getenv("GEMINI_API_KEY", "").strip())
    if not api_key_present:
        st.warning(
            "**GEMINI_API_KEY not set.** "
            "Create a `.env` file in the project folder and add:\n"
            "```\nGEMINI_API_KEY=AIza...\n```\n"
            "Then restart the app. See the README for details.",
            icon="⚠️",
        )

    # Prompt suggestions the user can copy in
    st.markdown(
        "**Try asking:** &nbsp; "
        "`Plan my day` &nbsp;·&nbsp; "
        "`Which tasks should I prioritize?` &nbsp;·&nbsp; "
        "`Are there any conflicts?`"
    )

    prompt = st.text_input(
        "Your question",
        placeholder="e.g. Plan my day and flag any conflicts",
        label_visibility="collapsed",
    )

    col_run, col_clear = st.columns([1, 5])
    run_clicked = col_run.button(
        "🤖 Ask",
        type="primary",
        disabled=not (prompt and api_key_present),
    )
    if col_clear.button("Clear response"):
        st.session_state.ai_response = None
        st.rerun()

    if run_clicked and prompt:
        with st.spinner("Thinking…"):
            st.session_state.ai_response = run_planner_agent(owner, prompt)

    if st.session_state.ai_response:
        st.divider()
        st.markdown(st.session_state.ai_response)
        st.caption("Powered by Gemini · Full trace saved to `planner.log`")

# ===========================================================================
# Tab 4 — Insights
# ===========================================================================
with tab_insights:
    st.subheader("📊 Pet Care Insights")

    for pet in owner.pets:
        pet_icon  = SPECIES_EMOJI.get(pet.species, "🐾")
        pending_t = pet.get_pending_tasks()
        done_t    = [t for t in pet.tasks if t.is_complete]

        with st.expander(
            f"{pet_icon} {pet.name} — {pet.species}, {pet.age}y  "
            f"({len(pending_t)} pending)",
            expanded=True,
        ):
            c1, c2, c3 = st.columns(3)
            c1.metric("Total tasks", len(pet.tasks))
            c2.metric("Pending",     len(pending_t))
            c3.metric("Completed",   len(done_t))

            if pending_t:
                total_time = sum(t.duration_minutes for t in pending_t)
                high_c = sum(1 for t in pending_t if t.priority == "high")
                med_c  = sum(1 for t in pending_t if t.priority == "medium")
                low_c  = sum(1 for t in pending_t if t.priority == "low")
                st.caption(
                    f"Pending care time: **{total_time} min** · "
                    f"🔴 {high_c} high · 🟡 {med_c} medium · 🟢 {low_c} low"
                )

    st.divider()
    st.subheader("Overall Summary")

    all_tasks_flat  = [t for p in owner.pets for t in p.tasks]
    pending_flat    = [t for t in all_tasks_flat if not t.is_complete]
    total_pend_time = sum(t.duration_minutes for t in pending_flat)

    o1, o2, o3 = st.columns(3)
    o1.metric("Pets registered",     len(owner.pets))
    o2.metric("Total pending tasks", len(pending_flat))
    o3.metric("Total pending time",  f"{total_pend_time} min")

    if total_pend_time > owner.available_minutes:
        overflow = total_pend_time - owner.available_minutes
        st.warning(
            f"⚠️ You have **{overflow} more minutes** of tasks than available today. "
            "Some tasks will be skipped — use the Schedule tab to see which ones."
        )
    elif pending_flat:
        st.success(
            f"✅ All {len(pending_flat)} pending tasks ({total_pend_time} min) "
            f"fit within your available time ({owner.available_minutes} min)."
        )

    recurring = [t for t in pending_flat if t.frequency != "once"]
    if recurring:
        st.subheader("🔁 Recurring Tasks")
        for t in recurring:
            pet_obj = next((p for p in owner.pets if p.name == t.pet_name), None)
            icon    = SPECIES_EMOJI.get(pet_obj.species if pet_obj else "other", "🐾")
            due_str = f" · due **{t.due_date}**" if t.due_date else ""
            st.markdown(
                f"- {icon} **{t.title}** ({t.pet_name}) — "
                f"{fmt_freq(t.frequency)}{due_str}"
            )
