"""
TripSaathi LangGraph State Definition
=======================================
Defines the shared state that flows through the entire multi-agent workflow.

WHAT IS LANGGRAPH STATE?
------------------------
In LangGraph, the "state" is a TypedDict that is passed to every node (agent)
in the graph. Each node can READ any field and WRITE to specific fields.

Think of it as a shared whiteboard:
  - Destination Agent writes attraction info on the whiteboard
  - Budget Agent reads that info and writes cost estimates
  - Itinerary Agent reads both and writes the schedule
  - Critic Agent reads everything and writes a review

WHY TYPEDDICT?
--------------
TypedDict gives us:
1. Type safety — IDE catches errors before runtime
2. Documentation — the state structure IS the documentation
3. Validation — LangGraph can verify state transitions
4. Clarity — easy to see which agent reads/writes what

INTERVIEW QUESTIONS:
- Q: "What is state management in LangGraph?"
  A: LangGraph uses a shared state (TypedDict or Pydantic model) that flows
     through all nodes. Each node receives the full state, modifies relevant
     fields, and returns the updated state.

- Q: "How does state differ from just passing function arguments?"
  A: State is persistent across the entire workflow. If the Critic rejects
     and routes back to the Itinerary Agent, the Itinerary Agent gets the
     FULL state including the critique — not just its original arguments.

- Q: "Can different nodes modify the same state field?"
  A: Yes, but it's bad practice. We design each field to be written by
     exactly ONE agent to avoid conflicts (see the state matrix below).

STATE FIELD OWNERSHIP:
  ┌──────────────────────┬────────────────┬────────────────────────┐
  │ Field                │ Written By     │ Read By                │
  ├──────────────────────┼────────────────┼────────────────────────┤
  │ destination          │ User Input     │ All agents             │
  │ days                 │ User Input     │ All agents             │
  │ travelers            │ User Input     │ Budget, Itinerary      │
  │ budget               │ User Input     │ Budget, Critic         │
  │ preferences          │ User Input     │ Destination, Itinerary │
  │ retrieved_context    │ Destination    │ Budget, Itinerary      │
  │ attractions          │ Destination    │ Budget, Itinerary      │
  │ budget_breakdown     │ Budget         │ Itinerary, Critic      │
  │ itinerary            │ Itinerary      │ Critic                 │
  │ critique             │ Critic         │ Itinerary (revision)   │
  │ revision_count       │ Critic         │ Conditional Edge       │
  │ status               │ Critic         │ Conditional Edge, API  │
  │ error                │ Any agent      │ API                    │
  └──────────────────────┴────────────────┴────────────────────────┘
"""

from typing import TypedDict


class TravelState(TypedDict):
    """
    Shared state for the multi-agent travel planning workflow.
    
    This is the single source of truth that flows through all nodes
    in the LangGraph workflow. Fields are grouped by who writes them.
    """

    # === USER INPUT (set at the beginning, never modified) ===
    destination: str           # e.g., "Jaipur"
    days: int                  # e.g., 3
    travelers: int             # e.g., 2
    budget: float              # e.g., 15000.0 (in ₹)
    preferences: list[str]     # e.g., ["history", "food", "photography"]

    # === DESTINATION AGENT OUTPUT ===
    retrieved_context: list[str]  # Raw text chunks from RAG retrieval
    attractions: list[dict]       # Structured attraction data extracted by LLM
    # Each attraction: {
    #   "name": "Amber Fort",
    #   "type": "monument",
    #   "entry_fee": 100,
    #   "duration_hours": 2.5,
    #   "timings": "8:00 AM - 5:30 PM",
    #   "description": "...",
    #   "photography_relevant": True,
    # }

    # === BUDGET AGENT OUTPUT ===
    budget_breakdown: dict
    # {
    #   "accommodation": {"per_night": 1500, "nights": 2, "total": 3000},
    #   "food": {"per_day_per_person": 500, "total": 3000},
    #   "transport": {"local": 2000, "total": 2000},
    #   "activities": {"items": [...], "total": 1500},
    #   "total_estimated": 9500,
    #   "budget_limit": 15000,
    #   "remaining": 5500,
    #   "within_budget": True,
    # }

    # === ITINERARY AGENT OUTPUT ===
    itinerary: dict
    # {
    #   "title": "3-Day Jaipur Heritage & Food Trail",
    #   "days": [
    #     {
    #       "day": 1,
    #       "title": "Forts & History",
    #       "activities": [...],
    #       "meals": [...],
    #       "transport_notes": "...",
    #     }
    #   ],
    #   "recommendations": [...],
    #   "packing_tips": [...],
    # }

    # === CRITIC AGENT OUTPUT ===
    critique: dict
    # {
    #   "status": "approved" | "rejected",
    #   "score": 8,  # out of 10
    #   "issues": [{"severity": "high"|"medium"|"low", "issue": "..."}],
    #   "suggestions": ["..."],
    #   "preference_coverage": {"history": True, "food": True, ...},
    # }

    revision_count: int   # Number of times the itinerary has been revised (max 3)
    status: str           # "approved" | "rejected" | "max_revisions_reached"

    # === ERROR HANDLING ===
    error: str            # Error message if any agent fails (empty string if no error)
