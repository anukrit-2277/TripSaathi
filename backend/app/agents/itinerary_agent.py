"""
TripSaathi Itinerary Agent
============================
Creates a detailed day-by-day travel itinerary.

This is the most "creative" agent — it needs to:
1. Consider user preferences (history, food, photography, etc.)
2. Balance the schedule (not too packed, not too empty)
3. Respect opening hours and visit durations
4. Consider distances between attractions
5. Stay within budget
6. If a revision: incorporate critique feedback

WHY THIS USES LLM HEAVILY:
---------------------------
Unlike the Budget Agent (which uses Python for math), the Itinerary Agent
needs genuine REASONING:
  - "Amber Fort is far from the city → schedule it for a full morning"
  - "User likes photography → include sunset at Nahargarh Fort"
  - "Day 2 is too packed → move one activity to Day 3"

This is exactly what LLMs excel at — contextual planning and reasoning.

REVISION HANDLING:
------------------
When the Critic Agent rejects an itinerary, LangGraph routes back here.
The state now contains a `critique` field with specific issues:
  - "Day 2 has too many activities"
  - "Budget exceeded"
  - "Missing photography-related spots"

The prompt includes the critique, so the LLM can address specific issues
instead of regenerating blindly.

INTERVIEW QUESTIONS:
- Q: "How does the revision loop work?"
  A: Critic writes issues to state.critique. LangGraph routes back here.
     We detect revision_count > 0 and include the critique in our prompt.
     The LLM sees the feedback and adjusts the itinerary accordingly.

- Q: "Why not just regenerate from scratch on rejection?"
  A: That wastes the LLM's previous work. By including the critique,
     the LLM makes targeted fixes rather than random regeneration.
"""

import json
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.core.llm import get_llm
from app.core.logger import get_logger
from app.graph.state import TravelState

logger = get_logger(__name__)


# ============================================================
# Pydantic Models for Structured Itinerary Output
# ============================================================

class Activity(BaseModel):
    """A single activity in the itinerary."""
    time: str = Field(description="Start time, e.g., '09:00 AM'")
    activity: str = Field(description="Name of the activity")
    duration: str = Field(description="Duration, e.g., '2 hours'")
    cost_per_person: float = Field(description="Cost per person in INR")
    notes: str = Field(description="Practical tips or notes for this activity")


class Meal(BaseModel):
    """A meal recommendation."""
    time: str = Field(description="Meal time, e.g., '01:00 PM'")
    type: str = Field(description="breakfast, lunch, dinner, or snack")
    suggestion: str = Field(description="Restaurant or food recommendation")
    cuisine: str = Field(description="Type of cuisine, e.g., 'Rajasthani Thali'")
    cost_per_person: float = Field(description="Approximate cost per person in INR")


class DayPlan(BaseModel):
    """Plan for a single day."""
    day: int = Field(description="Day number (1, 2, 3, ...)")
    title: str = Field(description="Theme for the day, e.g., 'Heritage & History'")
    activities: list[Activity] = Field(description="List of activities for this day")
    meals: list[Meal] = Field(description="Meal recommendations for this day")
    transport_notes: str = Field(description="Transport tips for this day")


class Itinerary(BaseModel):
    """Complete travel itinerary."""
    title: str = Field(description="Catchy title for the trip, e.g., '3-Day Jaipur Heritage Trail'")
    days: list[DayPlan] = Field(description="Day-by-day plans")
    recommendations: list[str] = Field(description="3-5 general recommendations")
    packing_tips: list[str] = Field(description="3-5 packing tips for this trip")


# ============================================================
# Prompt Template
# ============================================================

ITINERARY_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an expert travel itinerary planner. Create a detailed, realistic 
day-by-day travel itinerary.

RULES:
1. Schedule 3-5 activities per day (not too packed, not too sparse).
2. Include breakfast, lunch, and dinner recommendations each day.
3. Respect attraction timings — don't schedule visits outside opening hours.
4. Group nearby attractions together to minimize travel time.
5. Include realistic travel time between activities.
6. Balance the days — don't put all the best attractions on day 1.
7. Keep total costs within the budget breakdown provided.
8. Prioritize activities matching the user's preferences.
9. Start days at 8:00-9:00 AM and end activities by 7:00-8:00 PM.
10. Include rest/downtime — don't schedule back-to-back without breaks."""
    ),
    (
        "human",
        """Create a {days}-day itinerary for {destination}.

TRIP DETAILS:
- Travelers: {travelers} people
- Budget: ₹{budget} total
- Preferences: {preferences}

AVAILABLE ATTRACTIONS:
{attractions}

BUDGET BREAKDOWN:
{budget_breakdown}

DESTINATION CONTEXT:
{context}

{revision_instructions}

Create a realistic, enjoyable itinerary that matches the preferences and budget."""
    ),
])


# ============================================================
# Agent Node Function
# ============================================================

def itinerary_agent_node(state: TravelState) -> dict:
    """
    LangGraph node function for the Itinerary Agent.
    
    Creates or revises a day-by-day travel itinerary using LLM reasoning.
    
    On first run: creates a fresh itinerary from attractions + budget data.
    On revision: includes the critique feedback to make targeted improvements.
    
    Reads from state:
      - destination, days, travelers, budget, preferences
      - retrieved_context, attractions, budget_breakdown
      - critique, revision_count (if revising)
    
    Writes to state:
      - itinerary
    """
    revision_count = state.get("revision_count", 0)
    is_revision = revision_count > 0

    if is_revision:
        logger.info(f"📝 Itinerary Agent: REVISION #{revision_count}")
    else:
        logger.info(f"📝 Itinerary Agent starting (fresh itinerary)")

    try:
        # Build revision instructions if this is a revision
        revision_instructions = ""
        if is_revision and state.get("critique"):
            critique = state["critique"]
            issues = critique.get("issues", [])
            suggestions = critique.get("suggestions", [])

            revision_instructions = f"""
IMPORTANT — THIS IS A REVISION (attempt #{revision_count}):
The previous itinerary was rejected by the quality reviewer.

ISSUES TO FIX:
{json.dumps(issues, indent=2)}

SUGGESTIONS:
{json.dumps(suggestions, indent=2)}

Please address ALL the issues above while keeping the parts that were good.
Do NOT just regenerate randomly — make targeted fixes based on the feedback."""

            logger.info(f"   Including critique with {len(issues)} issues to fix")

        # Prepare data for prompt
        attractions_text = json.dumps(state.get("attractions", []), indent=2)
        budget_text = json.dumps(state.get("budget_breakdown", {}), indent=2)
        context_text = "\n".join(state.get("retrieved_context", [])[:5])  # Top 5 chunks
        preferences_text = ", ".join(state.get("preferences", []))

        # Use slightly higher temperature for creative itinerary generation
        llm = get_llm(temperature=0.4)
        structured_llm = llm.with_structured_output(Itinerary)

        chain = ITINERARY_PROMPT | structured_llm

        result: Itinerary = chain.invoke({
            "destination": state["destination"],
            "days": state["days"],
            "travelers": state["travelers"],
            "budget": state["budget"],
            "preferences": preferences_text,
            "attractions": attractions_text,
            "budget_breakdown": budget_text,
            "context": context_text,
            "revision_instructions": revision_instructions,
        })

        itinerary_dict = result.model_dump()

        logger.info(
            f"✅ Itinerary Agent complete. "
            f"Generated {len(result.days)} day plan(s) "
            f"with title: '{result.title}'"
        )

        return {"itinerary": itinerary_dict}

    except Exception as e:
        logger.error(f"❌ Itinerary Agent failed: {e}", exc_info=True)
        return {
            "itinerary": {
                "title": f"Trip to {state.get('destination', 'Unknown')}",
                "days": [],
                "recommendations": [],
                "packing_tips": [],
            },
            "error": f"Itinerary Agent error: {str(e)}",
        }
