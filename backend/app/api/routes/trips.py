"""
TripSaathi Trip API Routes
============================
FastAPI routes for trip planning and retrieval.

ROUTE DESIGN:
- POST /api/trip/plan  → Run the multi-agent workflow and generate an itinerary
- GET  /api/trip/{id}  → Retrieve a previously generated trip (Phase 12: from DB)

WHY SEPARATE ROUTES FROM BUSINESS LOGIC?
-----------------------------------------
The route handler only:
1. Validates the request (via Pydantic)
2. Calls the workflow
3. Formats the response

The actual work (LLM calls, RAG retrieval, etc.) is done by the agents.
This separation means:
- Routes are easy to test (mock the workflow)
- Business logic is reusable (could be called from CLI, tests, etc.)
- Each layer has one responsibility
"""

import uuid
from fastapi import APIRouter, HTTPException

from app.api.schemas.trip import TripRequest, TripResponse, ErrorResponse
from app.graph.workflow import run_travel_workflow
from app.core.logger import get_logger

logger = get_logger(__name__)

# APIRouter groups related endpoints together.
# The prefix means all routes in this router start with /api/trip
router = APIRouter(prefix="/api/trip", tags=["Trip Planning"])

# In-memory trip storage (Phase 12 will replace with PostgreSQL)
_trip_store: dict[str, TripResponse] = {}


@router.post(
    "/plan",
    response_model=TripResponse,
    summary="Generate a travel itinerary",
    description=(
        "Runs the multi-agent workflow: Destination Agent → Budget Agent → "
        "Itinerary Agent → Critic Agent (with revision loop). "
        "Returns a complete trip plan with budget breakdown and quality review."
    ),
    responses={
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def plan_trip(request: TripRequest) -> TripResponse:
    """
    Generate a travel itinerary using the multi-agent RAG workflow.
    
    This endpoint:
    1. Validates the request (Pydantic does this automatically)
    2. Runs the LangGraph workflow (all 4 agents)
    3. Formats the result into a TripResponse
    4. Stores the trip in memory (later: PostgreSQL)
    
    The workflow may take 30-60 seconds depending on:
    - Number of revision loops
    - LLM response time
    - RAG retrieval time
    """
    logger.info(
        f"📥 Trip plan request: {request.destination}, {request.days} days, "
        f"{request.travelers} travelers, ₹{request.budget}"
    )

    try:
        # Run the multi-agent workflow
        result = await run_travel_workflow(
            destination=request.destination,
            days=request.days,
            travelers=request.travelers,
            budget=request.budget,
            preferences=request.preferences,
        )

        # Check for workflow errors
        if result.get("error") and not result.get("itinerary", {}).get("days"):
            raise HTTPException(
                status_code=500,
                detail=f"Workflow failed: {result['error']}",
            )

        # Generate trip ID
        trip_id = str(uuid.uuid4())[:8]

        # Extract sources from retrieved context
        sources = list(set(
            f"travel_data/{request.destination.lower()}.md"
            for _ in result.get("retrieved_context", [])
        ))

        # Build response
        itinerary = result.get("itinerary", {})
        budget_breakdown = result.get("budget_breakdown", {})

        response = TripResponse(
            trip_id=trip_id,
            destination=request.destination,
            days=request.days,
            travelers=request.travelers,
            total_estimated_cost=budget_breakdown.get("total_estimated", 0),
            within_budget=budget_breakdown.get("within_budget", False),
            itinerary=itinerary,
            budget_breakdown=budget_breakdown,
            critique=result.get("critique", {}),
            recommendations=itinerary.get("recommendations", []),
            sources=sources,
            status=result.get("status", "unknown"),
            revision_count=result.get("revision_count", 0),
        )

        # Store for later retrieval
        _trip_store[trip_id] = response

        logger.info(
            f"✅ Trip plan generated. ID: {trip_id}, "
            f"Status: {response.status}, Cost: ₹{response.total_estimated_cost}"
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Trip planning failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Trip planning failed: {str(e)}",
        )


@router.get(
    "/{trip_id}",
    response_model=TripResponse,
    summary="Get a previously generated trip",
    responses={
        404: {"model": ErrorResponse, "description": "Trip not found"},
    },
)
async def get_trip(trip_id: str) -> TripResponse:
    """
    Retrieve a previously generated trip by ID.
    
    Currently uses in-memory storage.
    Phase 12 will replace this with PostgreSQL persistence.
    """
    trip = _trip_store.get(trip_id)
    if trip is None:
        raise HTTPException(
            status_code=404,
            detail=f"Trip with ID '{trip_id}' not found",
        )
    return trip
