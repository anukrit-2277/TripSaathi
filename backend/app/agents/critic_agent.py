"""
TripSaathi Critic Agent
=========================
Reviews the generated itinerary for quality, feasibility, and user preference alignment.

WHY A CRITIC AGENT?
--------------------
Self-evaluation is a key pattern in modern AI systems. Without a critic:
  - The first LLM draft goes straight to the user
  - No checks for budget overruns, scheduling conflicts, or missing preferences
  - Quality depends entirely on one LLM call (unreliable)

With a critic:
  - An independent LLM call reviews the output
  - Deterministic validation catches math errors the LLM wouldn't notice
  - Specific feedback enables targeted revisions
  - The system self-improves through the feedback loop

This mirrors real-world editorial processes:
  Writer → Editor → Writer (revision) → Final Draft

HYBRID VALIDATION APPROACH:
----------------------------
Like the Budget Agent, we use BOTH LLM and Python:

  PYTHON (deterministic checks):
  - Total cost ≤ budget?
  - Activities per day ≤ 5?
  - All days covered?
  - Schedule has no time conflicts?

  LLM (reasoning checks):
  - Do activities match user preferences?
  - Is the itinerary logical and enjoyable?
  - Are travel times between activities realistic?
  - Is there good variety across days?

INTERVIEW QUESTIONS:
- Q: "What is the self-evaluation pattern in AI systems?"
  A: Having a separate LLM call review the output of another LLM call.
     This catches errors, improves quality, and enables iterative refinement.

- Q: "Why is the critic a separate agent and not part of the itinerary agent?"
  A: Separation of concerns. The itinerary agent is optimized for CREATION
     (higher temperature, creative prompting). The critic is optimized for
     EVALUATION (lower temperature, analytical prompting). Combining them
     would compromise both.

- Q: "How do you prevent infinite revision loops?"
  A: A revision_count guard in the conditional edge. After 3 attempts,
     the workflow returns the best effort rather than looping forever.
"""

import json
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.core.llm import get_llm, structured_invoke
from app.core.logger import get_logger
from app.graph.state import TravelState

logger = get_logger(__name__)

# Maximum revision attempts before accepting the itinerary as-is.
# We keep this low (1) because each revision fires two more LLM calls
# (itinerary + critic) and easily pushes total request time past the
# Railway edge / browser fetch timeout. If the first draft fails critique
# we still return it — better a slightly-imperfect trip than a failed request.
MAX_REVISIONS = 1


# ============================================================
# Pydantic Models for Structured Critique Output
# ============================================================

class Issue(BaseModel):
    """A specific issue found in the itinerary."""
    severity: str = Field(description="high, medium, or low")
    issue: str = Field(description="Description of the problem")


class CritiqueLLM(BaseModel):
    """LLM's qualitative evaluation of the itinerary."""
    overall_score: int = Field(description="Quality score from 1-10", ge=1, le=10)
    preference_issues: list[str] = Field(
        description="Issues related to user preference coverage"
    )
    scheduling_issues: list[str] = Field(
        description="Issues with timing, pacing, or logistics"
    )
    improvement_suggestions: list[str] = Field(
        description="Specific actionable suggestions to improve the itinerary"
    )
    preference_coverage: dict[str, bool] = Field(
        description="Whether each user preference is adequately covered"
    )
    overall_assessment: str = Field(
        description="1-2 sentence overall assessment"
    )


CRITIQUE_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a travel itinerary quality reviewer. Evaluate the provided 
itinerary thoroughly and critically.

Scoring Guide:
- 9-10: Excellent, ready to use as-is
- 7-8: Good, minor improvements possible but acceptable
- 5-6: Acceptable but needs improvements
- 3-4: Poor, significant issues
- 1-2: Unacceptable, major rework needed

Be HONEST and CRITICAL. Don't give high scores to mediocre itineraries.
For each issue found, explain WHAT is wrong and HOW to fix it."""
    ),
    (
        "human",
        """Review this travel itinerary:

TRIP DETAILS:
- Destination: {destination}
- Days: {days}
- Travelers: {travelers}
- Budget: ₹{budget}
- Preferences: {preferences}

ITINERARY:
{itinerary}

BUDGET BREAKDOWN:
{budget_breakdown}

AVAILABLE CONTEXT:
{context}

Evaluate the itinerary for:
1. Preference coverage: Does it address each user preference ({preferences})?
2. Scheduling: Are timings realistic? Too packed or too sparse?
3. Budget adherence: Does it respect the budget breakdown?
4. Variety: Good mix of activities across days?
5. Logistics: Are nearby attractions grouped together?
6. Overall quality: Would this be an enjoyable trip?

Revision attempt: {revision_count} of {max_revisions}
If this is a revision, be especially strict about previously identified issues."""
    ),
])


# ============================================================
# Deterministic Validation Functions (Python, not LLM)
# ============================================================

def _validate_budget(state: TravelState) -> list[Issue]:
    """Check if the itinerary stays within budget. Pure Python."""
    issues = []
    budget_breakdown = state.get("budget_breakdown", {})
    budget_limit = state.get("budget", 0)
    total_estimated = budget_breakdown.get("total_estimated", 0)

    if total_estimated > budget_limit:
        over_by = total_estimated - budget_limit
        issues.append(Issue(
            severity="high",
            issue=f"Budget exceeded by ₹{round(over_by)}. "
                  f"Total: ₹{round(total_estimated)}, Limit: ₹{round(budget_limit)}"
        ))

    return issues


def _validate_schedule(state: TravelState) -> list[Issue]:
    """Check scheduling issues. Pure Python."""
    issues = []
    itinerary = state.get("itinerary", {})
    days_planned = itinerary.get("days", [])
    expected_days = state.get("days", 0)

    # Check if all days are covered
    if len(days_planned) != expected_days:
        issues.append(Issue(
            severity="high",
            issue=f"Expected {expected_days} days but itinerary has {len(days_planned)} days"
        ))

    # Check activities per day
    for day_plan in days_planned:
        day_num = day_plan.get("day", "?")
        activities = day_plan.get("activities", [])

        if len(activities) > 5:
            issues.append(Issue(
                severity="medium",
                issue=f"Day {day_num} has {len(activities)} activities — too packed "
                      f"(recommended: 3-5)"
            ))
        elif len(activities) < 2:
            issues.append(Issue(
                severity="low",
                issue=f"Day {day_num} has only {len(activities)} activity — consider adding more"
            ))

        # Check if meals are included
        meals = day_plan.get("meals", [])
        if len(meals) < 2:
            issues.append(Issue(
                severity="low",
                issue=f"Day {day_num} has only {len(meals)} meal recommendation(s) "
                      f"— add at least breakfast, lunch, and dinner"
            ))

    return issues


# ============================================================
# Agent Node Function
# ============================================================

async def critic_agent_node(state: TravelState) -> dict:
    """
    LangGraph node function for the Critic Agent.
    
    Performs both deterministic (Python) and qualitative (LLM) validation.
    Sets status to "approved" or "rejected" and increments revision_count.
    
    Reads from state:
      - ALL fields (it reviews the complete output)
    
    Writes to state:
      - critique
      - revision_count
      - status
    """
    revision_count = state.get("revision_count", 0)

    logger.info(f"🔍 Critic Agent starting (revision #{revision_count})")

    try:
        # === DETERMINISTIC VALIDATION (Python) ===
        deterministic_issues: list[Issue] = []
        deterministic_issues.extend(_validate_budget(state))
        deterministic_issues.extend(_validate_schedule(state))

        logger.info(f"   Deterministic checks found {len(deterministic_issues)} issue(s)")

        # === QUALITATIVE VALIDATION (LLM) ===
        preferences_text = ", ".join(state.get("preferences", []))
        itinerary_text = json.dumps(state.get("itinerary", {}), indent=2)
        budget_text = json.dumps(state.get("budget_breakdown", {}), indent=2)
        context_text = "\n".join(state.get("retrieved_context", [])[:3])

        # structured_invoke() does tool-calling first; if the model returns
        # partial args (common on gpt-oss-20b) it retries with json_mode.
        llm_critique: CritiqueLLM = await structured_invoke(
            CRITIQUE_PROMPT,
            CritiqueLLM,
            {
                "destination": state["destination"],
                "days": state["days"],
                "travelers": state["travelers"],
                "budget": state["budget"],
                "preferences": preferences_text,
                "itinerary": itinerary_text,
                "budget_breakdown": budget_text,
                "context": context_text,
                "revision_count": revision_count,
                "max_revisions": MAX_REVISIONS,
            },
            temperature=0.2,
        )

        # Combine LLM issues with deterministic issues
        all_issues = [issue.model_dump() for issue in deterministic_issues]

        for issue_text in llm_critique.preference_issues:
            all_issues.append({"severity": "medium", "issue": issue_text})

        for issue_text in llm_critique.scheduling_issues:
            all_issues.append({"severity": "medium", "issue": issue_text})

        # Determine approval
        high_issues = sum(1 for i in all_issues if i["severity"] == "high")
        total_issues = len(all_issues)
        score = llm_critique.overall_score

        # Approval criteria:
        # - Score >= 7 AND no high-severity issues
        # - OR max revisions reached (accept best effort)
        new_revision_count = revision_count + 1
        max_revisions_reached = new_revision_count >= MAX_REVISIONS

        if (score >= 7 and high_issues == 0) or max_revisions_reached:
            status = "approved" if not max_revisions_reached else "max_revisions_reached"
            if max_revisions_reached and score < 7:
                logger.warning(
                    f"⚠️ Max revisions reached. Accepting with score {score}/10"
                )
        else:
            status = "rejected"

        critique = {
            "status": status,
            "score": score,
            "issues": all_issues,
            "suggestions": llm_critique.improvement_suggestions,
            "preference_coverage": llm_critique.preference_coverage,
            "overall_assessment": llm_critique.overall_assessment,
        }

        if status == "approved" or status == "max_revisions_reached":
            logger.info(
                f"✅ Critic Agent: {'APPROVED' if status == 'approved' else 'ACCEPTED (max revisions)'} "
                f"— Score: {score}/10, Issues: {total_issues}"
            )
        else:
            logger.info(
                f"❌ Critic Agent: REJECTED — Score: {score}/10, "
                f"Issues: {total_issues} ({high_issues} high severity). "
                f"Routing back to Itinerary Agent."
            )

        return {
            "critique": critique,
            "revision_count": new_revision_count,
            "status": status,
        }

    except Exception as e:
        logger.error(f"❌ Critic Agent failed: {e}", exc_info=True)
        # On critic failure, approve to avoid blocking the workflow
        return {
            "critique": {
                "status": "approved",
                "score": 5,
                "issues": [{"severity": "low", "issue": f"Critic evaluation failed: {str(e)}"}],
                "suggestions": [],
                "preference_coverage": {},
                "overall_assessment": "Critic evaluation failed. Itinerary accepted without review.",
            },
            "revision_count": revision_count + 1,
            "status": "approved",
            "error": f"Critic Agent error: {str(e)}",
        }
