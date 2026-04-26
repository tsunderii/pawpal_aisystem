"""
generate_diagram.py
Run once:  python3 generate_diagram.py
Outputs:   system_diagram.png  (in this folder — ready to screenshot or embed)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

# ── Colour palette ────────────────────────────────────────────────────────────
C_INPUT   = "#4A90D9"   # blue    — human input
C_UI      = "#7B5EA7"   # purple  — Streamlit UI
C_CORE    = "#2E86AB"   # teal    — PawPal+ core logic
C_AI      = "#E07B39"   # orange  — AI agent
C_EXT     = "#D64045"   # red     — external Gemini API
C_OUTPUT  = "#3BB273"   # green   — outputs
C_TEST    = "#555B6E"   # slate   — testing / human review
C_LOG     = "#9B8EA8"   # muted   — log file
BG        = "#F5F6FA"   # page background
LANE_BG   = "#EAECF4"   # column background

# ── Figure setup ──────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(20, 11))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 20)
ax.set_ylim(0, 11)
ax.axis("off")

# ── Helpers ───────────────────────────────────────────────────────────────────

def lane(x, w, label, color):
    """Vertical swim-lane background + header."""
    rect = FancyBboxPatch(
        (x, 1.2), w, 8.4,
        boxstyle="round,pad=0.12",
        linewidth=0,
        facecolor=LANE_BG,
        zorder=0,
    )
    ax.add_patch(rect)
    ax.text(
        x + w / 2, 9.75, label,
        ha="center", va="center",
        fontsize=8.5, fontweight="bold", color=color,
        zorder=1,
    )


def box(cx, cy, w, h, color, line1, line2="", line3=""):
    """Rounded box with 1-3 lines of text."""
    rect = FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle="round,pad=0.15",
        linewidth=1.4,
        edgecolor="white",
        facecolor=color,
        zorder=3,
    )
    ax.add_patch(rect)
    if line2 and line3:
        ax.text(cx, cy + 0.28, line1, ha="center", va="center",
                fontsize=8.5, fontweight="bold", color="white", zorder=4)
        ax.text(cx, cy,       line2, ha="center", va="center",
                fontsize=7.2, color="white", alpha=0.92, zorder=4)
        ax.text(cx, cy - 0.28, line3, ha="center", va="center",
                fontsize=7.2, color="white", alpha=0.85, zorder=4, style="italic")
    elif line2:
        ax.text(cx, cy + 0.16, line1, ha="center", va="center",
                fontsize=8.5, fontweight="bold", color="white", zorder=4)
        ax.text(cx, cy - 0.18, line2, ha="center", va="center",
                fontsize=7.2, color="white", alpha=0.92, zorder=4)
    else:
        ax.text(cx, cy, line1, ha="center", va="center",
                fontsize=8.5, fontweight="bold", color="white", zorder=4,
                multialignment="center")


def arrow(x1, y1, x2, y2, color="#888888", rad=0.0, lw=1.6, style="->"):
    ax.annotate(
        "",
        xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle=style,
            color=color,
            lw=lw,
            connectionstyle=f"arc3,rad={rad}",
        ),
        zorder=2,
    )


def label_arrow(x, y, text, color="#666666"):
    ax.text(x, y, text, ha="center", va="center",
            fontsize=6.5, color=color, style="italic",
            bbox=dict(boxstyle="round,pad=0.1", fc=BG, ec="none"), zorder=5)


# ── Swim lanes ────────────────────────────────────────────────────────────────
lane(0.15,  3.3, "INPUT",        C_INPUT)
lane(3.65,  2.8, "UI LAYER",     C_UI)
lane(6.65,  3.3, "CORE LOGIC",   C_CORE)
lane(10.15, 4.2, "AI LAYER",     C_AI)
lane(14.55, 5.3, "OUTPUT",       C_OUTPUT)

# ── Title ─────────────────────────────────────────────────────────────────────
ax.text(10, 10.55, "PawPal+  —  System Architecture",
        ha="center", va="center",
        fontsize=15, fontweight="bold", color="#2C3E50", zorder=6)
ax.text(10, 10.1, "Agentic Workflow: User Input → Scheduling Engine → AI Planner → Output",
        ha="center", va="center",
        fontsize=9, color="#555555", zorder=6)

# ── INPUT column (x-center ≈ 1.8) ────────────────────────────────────────────
box(1.8, 8.3,  2.9, 0.85, C_INPUT, "Owner Info",      "name · available minutes · start time")
box(1.8, 6.8,  2.9, 0.85, C_INPUT, "Pet & Task Data", "species · priority · duration · frequency")
box(1.8, 5.3,  2.9, 0.85, C_INPUT, "AI Prompt",        "natural language question or request")

# ── UI LAYER column (x-center ≈ 5.1) ─────────────────────────────────────────
box(5.1, 7.2,  2.6, 1.5,  C_UI,    "Streamlit UI",   "app.py",   "Tasks · Schedule · AI Planner · Insights")

# ── CORE LOGIC column (x-center ≈ 8.35) ──────────────────────────────────────
box(8.35, 7.6, 3.1, 0.85, C_CORE,  "PawPal+ Core",      "pawpal_system.py",  "Task · Pet · Owner · session_state")
box(8.35, 5.6, 3.1, 1.45, C_CORE,  "Scheduler",         "build_plan()  ·  build_weighted_plan()",
    "detect_conflicts()  ·  sort_by_time()")

# ── AI LAYER column (x-center ≈ 12.35) ───────────────────────────────────────
box(12.35, 7.65, 3.8, 0.85, C_AI,  "AI Planner Agent",  "ai_planner.py",  "agentic loop · max 5 iterations")
box(12.35, 5.9,  3.8, 1.2,  C_EXT, "Gemini API",        "gemini-2.0-flash",
    "AuthError · RateLimit · ConnectionError caught")
box(12.35, 4.1,  3.8, 0.95, C_AI,  "Tool Calls  ×4",
    "get_schedule_context · build_priority_plan",
    "build_weighted_plan  ·  detect_and_explain")

# ── OUTPUT column (x-center ≈ 17.1) ──────────────────────────────────────────
box(17.1, 8.45, 4.5, 0.75, C_OUTPUT, "Daily Schedule",      "sorted · colour-coded priority table")
box(17.1, 7.25, 4.5, 0.75, C_OUTPUT, "Conflict Warnings",   "same-pet · cross-pet · slot overload")
box(17.1, 6.05, 4.5, 0.75, C_OUTPUT, "AI Response",          "plain-English plan + recommendation")
box(17.1, 4.85, 4.5, 0.75, C_LOG,    "planner.log",          "every tool call + result + errors")

# ── TESTING strip (bottom) ────────────────────────────────────────────────────
test_bg = FancyBboxPatch(
    (0.15, 0.1), 19.7, 0.95,
    boxstyle="round,pad=0.1",
    linewidth=0, facecolor="#DDE3F0", zorder=0,
)
ax.add_patch(test_bg)
ax.text(10, 0.62, "TESTING & HUMAN REVIEW", ha="center", va="center",
        fontsize=8, fontweight="bold", color=C_TEST, zorder=5)

box(4.0,  0.25, 4.5, 0.32, C_TEST, "pytest  —  20 tests  (core logic · scheduler · weighted score · conflicts)")
box(10.5, 0.25, 5.5, 0.32, C_TEST, "Human reviews schedule · conflict warnings · AI response before acting")
box(17.5, 0.25, 4.5, 0.32, C_TEST, "Guardrails: API-key check · 5-step cap · error messages")

# ── Arrows ────────────────────────────────────────────────────────────────────
# Input → Streamlit UI
arrow(3.25, 8.3,  3.8, 7.7,  C_INPUT, rad=0.0)
arrow(3.25, 6.8,  3.8, 7.2,  C_INPUT, rad=0.0)
arrow(3.25, 5.3,  3.8, 6.7,  C_INPUT, rad=0.2)

# Streamlit UI → Core
arrow(6.4,  7.5,  6.8, 7.6,  C_UI)

# Core → Scheduler
arrow(8.35, 7.15, 8.35, 6.35, C_CORE)

# Core → AI Planner (diagonal)
arrow(9.9,  7.65, 10.45, 7.65, C_CORE)

# Scheduler → AI Planner (via tool call path — goes right then up)
arrow(9.9, 5.9, 10.45, 5.9, C_CORE, rad=0.0)
label_arrow(10.2, 5.7, "tool calls read\nscheduler directly")

# AI Planner → Gemini API
arrow(12.35, 7.22, 12.35, 6.55, C_AI)

# Claude API → Tool Calls
arrow(12.35, 5.3,  12.35, 4.6,  C_EXT)

# Tool Calls → back to AI Planner (loop)
arrow(14.25, 4.1,  14.6, 4.5,   C_AI, rad=-0.3, lw=1.3)
arrow(14.6,  4.5,  14.6, 7.65,  C_AI, rad=0.0,  lw=1.3)
arrow(14.6,  7.65, 14.25, 7.65, C_AI, rad=0.0,  lw=1.3)
label_arrow(15.1, 6.1, "loop until\nend_turn")

# Scheduler → Daily Schedule output
arrow(9.9,  6.2,  14.85, 8.45,  C_OUTPUT, rad=-0.15)

# Scheduler → Conflict Warnings
arrow(9.9,  5.6,  14.85, 7.25,  C_OUTPUT, rad=-0.1)

# AI Planner → AI Response
arrow(14.25, 7.3, 14.85, 6.05,  C_OUTPUT, rad=0.15)

# AI Planner → planner.log
arrow(14.25, 7.1, 14.85, 4.85,  C_LOG,    rad=0.2, lw=1.2)

# pytest → Core (testing arrow — short upward from strip to core column)
arrow(6.5, 1.2, 7.5, 4.85,  C_TEST, rad=0.3, lw=1.3, style="->")

# ── Legend ────────────────────────────────────────────────────────────────────
legend_items = [
    mpatches.Patch(color=C_INPUT,  label="Human Input"),
    mpatches.Patch(color=C_UI,     label="UI Layer"),
    mpatches.Patch(color=C_CORE,   label="Core Logic"),
    mpatches.Patch(color=C_AI,     label="AI / Agent"),
    mpatches.Patch(color=C_EXT,    label="External API"),
    mpatches.Patch(color=C_OUTPUT, label="Output"),
    mpatches.Patch(color=C_TEST,   label="Testing & Review"),
]
ax.legend(
    handles=legend_items,
    loc="lower right",
    fontsize=7.5,
    framealpha=0.85,
    edgecolor="#cccccc",
    ncol=4,
    bbox_to_anchor=(0.995, 0.07),
)

# ── Save ──────────────────────────────────────────────────────────────────────
plt.tight_layout(pad=0.3)
plt.savefig("system_diagram.png", dpi=180, bbox_inches="tight",
            facecolor=BG, edgecolor="none")
plt.close()
print("Saved: system_diagram.png")
