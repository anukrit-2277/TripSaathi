"""
TripSaathi LangGraph Workflow
================================
Orchestrates the multi-agent travel planning workflow as a state machine.

WHAT IS LANGGRAPH?
------------------
LangGraph is a framework for building stateful, multi-agent applications
as directed graphs. Each node is a function (agent), edges define the flow,
and a typed state object flows through the entire graph.

LANGGRAPH vs LANGCHAIN:
-----------------------
LangChain: Building blocks. Chains, prompts, parsers, tools.
           Think of it as "individual Lego bricks."

LangGraph: Orchestration. Connects multiple chains/agents into a workflow
           with conditional routing and loops.
           Think of it as "the Lego instruction manual."

You can use LangChain WITHOUT LangGraph (simple sequential chains).
You can NOT use LangGraph without LangChain (LangGraph builds on LC components).

GRAPH STRUCTURE:
                ┌──────────────┐
                │    START     │
                └──────┬───────┘
                       │
                ┌──────▼───────┐
                │ Destination  │  ← RAG retrieval + extraction
                │ Agent        │
                └──────┬───────┘
                       │
                ┌──────▼───────┐
                │ Budget       │  ← Cost estimation (Python math)
                │ Agent        │
                └──────┬───────┘
                       │
                ┌──────▼───────┐
                │ Itinerary    │◄──┐  ← Day-by-day planning (LLM reasoning)
                │ Agent        │   │
                └──────┬───────┘   │
                       │           │
                ┌──────▼───────┐   │
                │ Critic       │   │  ← Quality review (hybrid validation)
                │ Agent        │───┘
                └──────┬───────┘
                       │
                  [Conditional]
                  ├── approved → END
                  └── rejected → Itinerary Agent (max 3 revisions)

KEY CONCEPTS:
- Node: A function that takes state and returns state updates
- Edge: Connection between nodes (defines execution order)
- Conditional Edge: Routes to different nodes based on state
- State: TypedDict shared across all nodes
- Compilation: graph.compile() creates an executable workflow

INTERVIEW QUESTIONS:
- Q: "What are nodes in LangGraph?"
  A: Functions that receive the full state, perform work (LLM calls,
     computation), and return a dict of state updates. LangGraph merges
     the updates into the state automatically.

- Q: "What are conditional edges?"
  A: Edges that route to different nodes based on a condition function.
     The function reads the state and returns a string key that maps to
     the next node. This enables loops and branching.

- Q: "How do you prevent infinite loops?"
  A: Use a counter in the state (revision_count). The conditional edge
     checks if revision_count >= MAX_REVISIONS and routes to END instead
     of looping back. This is a MUST for production systems.

- Q: "What is graph.compile()?"
  A: Converts the graph definition into an executable runnable. After
     compilation, you call graph.invoke(initial_state) to run the workflow.
     The compiled graph validates that all edges connect properly.

- Q: "Can LangGraph handle human-in-the-loop?"
  A: Yes! You can add a node that pauses execution and waits for human
     input. We don't implement this here, but it's a natural extension
     (e.g., "Does the user approve this itinerary before finalizing?").
"""

from langgraph.graph import StateGraph, END

from app.graph.state import TravelState
from app.agents.destination_agent import destination_agent_node
from app.agents.budget_agent import budget_agent_node
from app.agents.itinerary_agent import itinerary_agent_node
from app.agents.critic_agent import critic_agent_node
from app.core.logger import get_logger

logger = get_logger(__name__)


# ============================================================
# Conditional Edge Function
# ============================================================

def should_revise_or_finish(state: TravelState) -> str:
    """
    Conditional edge function: decides whether to revise or finish.
    
    This function is called AFTER the Critic Agent runs.
    It reads the state and returns a routing key:
      - "end"    → workflow is complete (approved or max revisions)
      - "revise" → route back to itinerary agent for revision
    
    The routing keys map to nodes (or END) in add_conditional_edges().
    
    Guard against infinite loops:
      - revision_count is incremented by the Critic Agent
      - If revision_count >= 3, we stop regardless of approval status
    """
    status = state.get("status", "approved")
    revision_count = state.get("revision_count", 0)

    if status in ("approved", "max_revisions_reached"):
        logger.info(f"🏁 Workflow routing → END (status: {status})")
        return "end"

    if revision_count >= 3:
        logger.warning(
            f"🏁 Workflow routing → END (max revisions reached: {revision_count})"
        )
        return "end"

    logger.info(
        f"🔄 Workflow routing → REVISE (revision #{revision_count}, status: {status})"
    )
    return "revise"


# ============================================================
# Build the LangGraph Workflow
# ============================================================

def build_travel_workflow():
    """
    Build and compile the multi-agent travel planning workflow.
    
    Returns a compiled LangGraph that can be invoked with:
        result = workflow.invoke(initial_state)
    
    The workflow is:
        START → Destination Agent → Budget Agent → Itinerary Agent 
              → Critic Agent → [approved? → END] or [rejected? → Itinerary Agent]
    """
    logger.info("Building LangGraph travel workflow...")

    # Step 1: Create the graph with our state type
    # StateGraph is the core LangGraph class. It's parameterized by the
    # state type (TravelState), which defines what data flows between nodes.
    workflow = StateGraph(TravelState)

    # Step 2: Add nodes
    # Each node is a function with signature: (state: TravelState) -> dict
    # The returned dict is merged into the state: state = {**state, **returned}
    workflow.add_node("destination_agent", destination_agent_node)
    workflow.add_node("budget_agent", budget_agent_node)
    workflow.add_node("itinerary_agent", itinerary_agent_node)
    workflow.add_node("critic_agent", critic_agent_node)

    # Step 3: Add edges (linear flow)
    # set_entry_point: which node runs first
    workflow.set_entry_point("destination_agent")

    # Regular edges: A → B (always goes to B after A)
    workflow.add_edge("destination_agent", "budget_agent")
    workflow.add_edge("budget_agent", "itinerary_agent")
    workflow.add_edge("itinerary_agent", "critic_agent")

    # Step 4: Conditional edge (the key feature!)
    # After critic_agent, route based on should_revise_or_finish():
    #   "end"    → END (workflow complete)
    #   "revise" → itinerary_agent (loop back for revision)
    workflow.add_conditional_edges(
        "critic_agent",             # Source node
        should_revise_or_finish,    # Condition function
        {
            "end": END,              # "end" → finish the workflow
            "revise": "itinerary_agent",  # "revise" → loop back
        },
    )

    # Step 5: Compile the graph
    # This validates the graph structure and creates an executable runnable.
    # After compilation, the graph is immutable.
    compiled = workflow.compile()

    logger.info("✅ LangGraph workflow compiled successfully")
    return compiled


# Create a module-level compiled workflow (singleton)
# This is compiled once and reused across all requests
travel_workflow = build_travel_workflow()


async def run_travel_workflow(
    destination: str,
    days: int,
    travelers: int,
    budget: float,
    preferences: list[str],
) -> TravelState:
    """
    Execute the travel planning workflow.
    
    This is the main entry point called by the API layer.
    
    Args:
        destination: Target destination (e.g., "Jaipur")
        days: Number of days
        travelers: Number of travelers
        budget: Total budget in INR
        preferences: List of user preferences
    
    Returns:
        Final TravelState with all fields populated by the agents.
    """
    logger.info(
        f"🚀 Starting travel workflow: {destination}, {days} days, "
        f"{travelers} travelers, ₹{budget}, preferences={preferences}"
    )

    # Build the initial state with user input
    initial_state: TravelState = {
        "destination": destination,
        "days": days,
        "travelers": travelers,
        "budget": budget,
        "preferences": preferences,

        # Initialize agent output fields as empty
        "retrieved_context": [],
        "attractions": [],
        "budget_breakdown": {},
        "itinerary": {},
        "critique": {},
        "revision_count": 0,
        "status": "",
        "error": "",
    }

    # Run the workflow
    # .invoke() runs the graph synchronously (each node in order)
    # The graph handles conditional routing automatically
    result = travel_workflow.invoke(initial_state)

    logger.info(
        f"🏁 Workflow complete. Status: {result.get('status')}, "
        f"Revisions: {result.get('revision_count', 0)}, "
        f"Score: {result.get('critique', {}).get('score', 'N/A')}"
    )

    return result
