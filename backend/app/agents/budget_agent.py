"""
TripSaathi Budget Agent
========================
Estimates trip costs using a combination of LLM extraction and Python arithmetic.

KEY DESIGN PRINCIPLE:
---------------------
LLMs are TERRIBLE at math. Ask GPT-4 to add 17 numbers and it'll often get
it wrong. So we use a hybrid approach:

  LLM handles: Understanding text → "Amber Fort entry is ₹100 for Indians"
  Python handles: 100 × 2 travelers = ₹200 total for Amber Fort

This is a critical pattern in production AI systems:
  - Use LLMs for REASONING (understanding context, extracting prices)
  - Use CODE for COMPUTATION (arithmetic, aggregation, validation)

INTERVIEW QUESTIONS:
- Q: "Why not let the LLM calculate the budget?"
  A: LLMs are probabilistic — they predict the next token, not compute math.
     "₹100 × 2 people × 3 days" might return ₹500 or ₹700 randomly.
     Python always returns ₹600.

- Q: "What's the design pattern here?"
  A: LLM-as-extractor + Code-as-calculator. The LLM is a smart parser
     that converts unstructured text to structured data. Then deterministic
     code does the math.

- Q: "How do you handle missing price information?"
  A: We use sensible defaults based on the budget category (budget/mid-range/
     luxury) inferred from the user's total budget.
"""

import json
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.core.llm import get_llm
from app.core.logger import get_logger
from app.graph.state import TravelState

logger = get_logger(__name__)


# ============================================================
# Pydantic Model for LLM Price Extraction
# ============================================================

class ExtractedPrices(BaseModel):
    """Prices extracted from RAG context by the LLM."""
    avg_budget_hotel_per_night: float = Field(
        description="Average budget hotel price per night in INR"
    )
    avg_midrange_hotel_per_night: float = Field(
        description="Average mid-range hotel price per night in INR"
    )
    avg_food_per_day_per_person: float = Field(
        description="Average food cost per day per person (3 meals) in INR"
    )
    avg_local_transport_per_day: float = Field(
        description="Average local transportation cost per day in INR"
    )
    budget_category: str = Field(
        description="Inferred budget category: 'budget', 'mid-range', or 'luxury'"
    )


PRICE_EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a travel cost analyst. Extract average price information 
from the provided context for the given destination.

Use ONLY the prices mentioned in the context. If a price isn't mentioned,
use reasonable estimates based on the destination's typical costs.

Budget categories (per person per day):
- budget: total < ₹2500/day
- mid-range: total ₹2500-6000/day
- luxury: total > ₹6000/day"""
    ),
    (
        "human",
        """Extract average prices for {destination}.

Total budget for entire trip: ₹{budget} for {travelers} travelers over {days} days.
That's approximately ₹{per_person_per_day} per person per day.

CONTEXT:
{context}

Based on this budget level and the context, extract the average prices."""
    ),
])


# ============================================================
# Agent Node Function
# ============================================================

def budget_agent_node(state: TravelState) -> dict:
    """
    LangGraph node function for the Budget Agent.
    
    This agent:
    1. Uses LLM to extract price information from RAG context
    2. Uses PYTHON CODE (not LLM) for all arithmetic:
       - Activity costs = sum(entry_fee × travelers)
       - Hotel costs = per_night × nights × rooms
       - Food costs = per_day × travelers × days
       - Transport costs = per_day × days
    3. Compares total against budget
    4. Returns structured budget breakdown
    
    Reads from state:
      - destination, days, travelers, budget
      - retrieved_context, attractions
    
    Writes to state:
      - budget_breakdown
    """
    logger.info(f"💰 Budget Agent starting")
    logger.info(
        f"   Budget: ₹{state['budget']} for {state['travelers']} travelers, "
        f"{state['days']} days"
    )

    try:
        destination = state["destination"]
        days = state["days"]
        travelers = state["travelers"]
        budget = state["budget"]
        attractions = state["attractions"]
        context = state.get("retrieved_context", [])

        nights = days - 1  # 3-day trip = 2 nights
        if nights < 1:
            nights = 1

        # Calculate per-person-per-day budget for context
        per_person_per_day = budget / (travelers * days)

        # Step 1: Use LLM to extract price data from context
        llm = get_llm(temperature=0.1)  # Very low temperature for precise extraction
        structured_llm = llm.with_structured_output(ExtractedPrices)

        context_text = "\n\n".join(context[:10])  # Limit context to avoid token limits

        chain = PRICE_EXTRACTION_PROMPT | structured_llm
        prices: ExtractedPrices = chain.invoke({
            "destination": destination,
            "budget": budget,
            "travelers": travelers,
            "days": days,
            "per_person_per_day": round(per_person_per_day),
            "context": context_text,
        })

        logger.info(f"   Extracted prices — category: {prices.budget_category}")

        # Step 2: PYTHON ARITHMETIC (not LLM!)
        # This is deterministic and 100% accurate

        # --- Accommodation ---
        # Choose hotel tier based on extracted budget category
        if prices.budget_category == "luxury":
            hotel_per_night = prices.avg_midrange_hotel_per_night * 1.5
        elif prices.budget_category == "mid-range":
            hotel_per_night = prices.avg_midrange_hotel_per_night
        else:
            hotel_per_night = prices.avg_budget_hotel_per_night

        # Rooms needed: 1 room per 2 travelers (rounded up)
        rooms_needed = max(1, (travelers + 1) // 2)
        accommodation_total = hotel_per_night * nights * rooms_needed

        # --- Food ---
        food_per_day_per_person = prices.avg_food_per_day_per_person
        food_total = food_per_day_per_person * days * travelers

        # --- Transportation ---
        transport_per_day = prices.avg_local_transport_per_day
        transport_total = transport_per_day * days

        # --- Activities/Attractions ---
        activity_items = []
        activities_total = 0.0

        for attraction in attractions:
            entry_fee = attraction.get("entry_fee", 0)
            if entry_fee > 0:
                cost_for_group = entry_fee * travelers
                activity_items.append({
                    "name": attraction.get("name", "Unknown"),
                    "per_person": entry_fee,
                    "total": cost_for_group,
                })
                activities_total += cost_for_group

        # --- TOTAL CALCULATION (all Python, zero LLM) ---
        total_estimated = (
            accommodation_total
            + food_total
            + transport_total
            + activities_total
        )

        remaining = budget - total_estimated
        within_budget = total_estimated <= budget

        budget_breakdown = {
            "accommodation": {
                "per_night": round(hotel_per_night),
                "nights": nights,
                "rooms": rooms_needed,
                "total": round(accommodation_total),
            },
            "food": {
                "per_day_per_person": round(food_per_day_per_person),
                "days": days,
                "travelers": travelers,
                "total": round(food_total),
            },
            "transport": {
                "per_day": round(transport_per_day),
                "days": days,
                "total": round(transport_total),
            },
            "activities": {
                "items": activity_items,
                "total": round(activities_total),
            },
            "total_estimated": round(total_estimated),
            "budget_limit": budget,
            "remaining": round(remaining),
            "within_budget": within_budget,
            "budget_category": prices.budget_category,
        }

        if within_budget:
            logger.info(
                f"✅ Budget Agent complete. Total: ₹{round(total_estimated)} "
                f"(₹{round(remaining)} under budget)"
            )
        else:
            logger.warning(
                f"⚠️ Budget Agent: Over budget! Total: ₹{round(total_estimated)} "
                f"(₹{round(abs(remaining))} over budget)"
            )

        return {"budget_breakdown": budget_breakdown}

    except Exception as e:
        logger.error(f"❌ Budget Agent failed: {e}", exc_info=True)
        # Return a fallback budget breakdown so the workflow can continue
        return {
            "budget_breakdown": {
                "accommodation": {"per_night": 0, "nights": 0, "rooms": 0, "total": 0},
                "food": {"per_day_per_person": 0, "days": 0, "travelers": 0, "total": 0},
                "transport": {"per_day": 0, "days": 0, "total": 0},
                "activities": {"items": [], "total": 0},
                "total_estimated": 0,
                "budget_limit": state.get("budget", 0),
                "remaining": state.get("budget", 0),
                "within_budget": True,
                "budget_category": "budget",
            },
            "error": f"Budget Agent error: {str(e)}",
        }
