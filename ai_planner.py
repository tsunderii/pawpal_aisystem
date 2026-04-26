"""
ai_planner.py — Agentic scheduling assistant for PawPal+.

Uses the Google Gemini API (google-genai SDK) with function calling so the
model can inspect live task data, build a plan, and check for conflicts before
replying in plain English. All tool calls and errors are written to planner.log.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types

from pawpal_system import Owner, Scheduler

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_PATH = Path(__file__).parent / "planner.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[logging.FileHandler(LOG_PATH, encoding="utf-8")],
)
log = logging.getLogger("pawpal.planner")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MODEL          = "gemini-2.0-flash"
MAX_TOKENS     = 1024
MAX_ITERATIONS = 5

SYSTEM_PROMPT = """\
You are PawPal+, a friendly and concise pet-care scheduling assistant.
You have four tools. Use them in this order every time:

1. get_schedule_context  — always call this first to see all pets and tasks.
2. build_weighted_plan OR build_priority_plan — pick weighted if any tasks
   have a due_date or might be overdue; otherwise pick priority.
3. detect_and_explain — always call this after building the plan to check
   for conflicts and get the full explanation text.

Then give a final reply in plain, friendly language. Keep it under 150 words:
summarise the plan, mention any conflicts, and give one concrete suggestion.
"""

# ---------------------------------------------------------------------------
# Tool declarations (no input parameters — all context comes from owner state)
# ---------------------------------------------------------------------------
TOOLS = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="get_schedule_context",
            description=(
                "Return all pets, their pending tasks, and the owner's available "
                "time. Call this first before building any plan."
            ),
        ),
        types.FunctionDeclaration(
            name="build_priority_plan",
            description=(
                "Build a schedule sorted by priority (high → medium → low). "
                "Use when tasks have no due dates and urgency is not the main concern."
            ),
        ),
        types.FunctionDeclaration(
            name="build_weighted_plan",
            description=(
                "Build a schedule using weighted urgency scoring "
                "(priority base + overdue bonus + efficiency bonus). "
                "Use when any tasks have a due_date set or may be overdue."
            ),
        ),
        types.FunctionDeclaration(
            name="detect_and_explain",
            description=(
                "Check for scheduling conflicts and return a plain-English "
                "explanation of the current plan. Always call after building a plan."
            ),
        ),
    ]
)

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def _get_schedule_context(owner: Owner) -> dict[str, Any]:
    pets_data = []
    for pet in owner.pets:
        pending = pet.get_pending_tasks()
        pets_data.append({
            "name": pet.name,
            "species": pet.species,
            "age": pet.age,
            "pending_tasks": [t.to_dict() for t in pending],
            "pending_count": len(pending),
            "pending_minutes": sum(t.duration_minutes for t in pending),
        })
    all_pending = owner.get_all_tasks()
    return {
        "owner": owner.name,
        "available_minutes": owner.available_minutes,
        "preferred_start_time": owner.preferred_start_time,
        "pets": pets_data,
        "total_pending_tasks": len(all_pending),
        "total_pending_minutes": sum(t.duration_minutes for t in all_pending),
        "has_tasks_with_due_date": any(t.due_date is not None for t in all_pending),
    }


def _format_plan(scheduler: Scheduler) -> dict[str, Any]:
    total = sum(t.duration_minutes for t in scheduler.schedule)
    return {
        "scheduled": [t.to_dict() for t in scheduler.schedule],
        "skipped": [t.to_dict() for t in scheduler.skipped],
        "tasks_scheduled": len(scheduler.schedule),
        "tasks_skipped": len(scheduler.skipped),
        "total_scheduled_minutes": total,
        "minutes_remaining": scheduler.owner.available_minutes - total,
    }


def _detect_and_explain(owner: Owner, scheduler: Scheduler | None) -> dict[str, Any]:
    if scheduler is None:
        scheduler = Scheduler(owner)
        scheduler.build_plan()
    conflicts = scheduler.detect_conflicts()
    return {
        "conflicts": conflicts,
        "has_conflicts": bool(conflicts),
        "conflict_count": len(conflicts),
        "explanation": scheduler.get_explanation(),
    }


def _dispatch(tool_name: str, owner: Owner, ctx: dict[str, Any]) -> dict[str, Any]:
    if tool_name == "get_schedule_context":
        return _get_schedule_context(owner)
    if tool_name == "build_priority_plan":
        s = Scheduler(owner)
        s.build_plan()
        ctx["scheduler"] = s
        return _format_plan(s)
    if tool_name == "build_weighted_plan":
        s = Scheduler(owner)
        s.build_weighted_plan()
        ctx["scheduler"] = s
        return _format_plan(s)
    if tool_name == "detect_and_explain":
        return _detect_and_explain(owner, ctx.get("scheduler"))
    return {"error": f"Unknown tool: {tool_name}"}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_planner_agent(owner: Owner, user_prompt: str) -> str:
    """Run the agentic planning loop and return a natural-language response."""

    # ── Guardrail 1: API key ─────────────────────────────────────────────────
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return (
            "⚠️ **GEMINI_API_KEY not set.**\n\n"
            "Create a `.env` file in the project folder with:\n"
            "```\nGEMINI_API_KEY=AIza...\n```\n"
            "See the README for full setup steps."
        )

    # ── Guardrail 2: must have something to schedule ─────────────────────────
    if not owner.pets or not owner.get_all_tasks():
        return (
            "I don't see any pets or tasks yet. "
            "Add a pet and at least one task first, then ask me to plan your day!"
        )

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    log.info("=== run %s started ===", run_id)
    log.info("prompt: %s", user_prompt)

    client = genai.Client(api_key=api_key)

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[TOOLS],
        max_output_tokens=MAX_TOKENS,
    )

    # Build conversation history as a list of Content objects
    contents: list[types.Content] = [
        types.Content(role="user", parts=[types.Part(text=user_prompt)])
    ]
    ctx: dict[str, Any] = {"scheduler": None}

    try:
        for iteration in range(1, MAX_ITERATIONS + 1):
            log.info("iteration %d/%d", iteration, MAX_ITERATIONS)

            response = client.models.generate_content(
                model=MODEL,
                contents=contents,
                config=config,
            )

            candidate = response.candidates[0]
            contents.append(candidate.content)  # add model turn to history

            # Collect any function calls in this response
            fn_calls = [
                p for p in candidate.content.parts
                if p.function_call and p.function_call.name
            ]

            log.info(
                "finish_reason=%s  fn_calls=%d",
                candidate.finish_reason,
                len(fn_calls),
            )

            # ── No function calls → extract text and return ──────────────────
            if not fn_calls:
                text = response.text.strip() if response.text else ""
                log.info("final response (%d chars)", len(text))
                log.info("=== run %s complete ===", run_id)
                return text

            # ── Dispatch each function call ──────────────────────────────────
            fn_response_parts: list[types.Part] = []
            for part in fn_calls:
                fn_name = part.function_call.name
                log.info("tool_call  name=%s", fn_name)
                result = _dispatch(fn_name, owner, ctx)
                log.info("tool_result  name=%s  keys=%s", fn_name, list(result.keys()))
                fn_response_parts.append(
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=fn_name,
                            response={"output": json.dumps(result)},
                        )
                    )
                )

            # Add tool results as a user turn
            contents.append(
                types.Content(role="user", parts=fn_response_parts)
            )

    except Exception as exc:
        # Catch-all: classify common Gemini errors into friendly messages
        err = str(exc)
        log.error("error during run %s: %s", run_id, err)

        if "API_KEY_INVALID" in err or "API key not valid" in err:
            return "⚠️ Invalid API key. Double-check `GEMINI_API_KEY` in your `.env` file."
        if "quota" in err.lower() or "rate" in err.lower() or "429" in err:
            return "⚠️ Rate limit reached. Wait a moment and try again."
        if "connect" in err.lower() or "network" in err.lower():
            return "⚠️ Could not reach the Gemini API. Check your internet connection."
        return f"⚠️ API error: {exc}"

    # ── Guardrail 3: iteration cap ───────────────────────────────────────────
    log.warning("hit MAX_ITERATIONS (%d) without finishing", MAX_ITERATIONS)
    return (
        "The planner hit its step limit before finishing. "
        "Try a simpler or more specific question. "
        "Check `planner.log` for the full trace."
    )
