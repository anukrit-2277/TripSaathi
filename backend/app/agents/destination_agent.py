"""
TripSaathi Destination Agent
==============================
The "Research Assistant" — retrieves and structures destination information
from the RAG knowledge base.

WHAT DOES THIS AGENT DO?
------------------------
1. Takes user input (destination + preferences)
2. Builds semantic search queries from preferences
3. Retrieves relevant chunks from ChromaDB via RAG
4. Uses LLM to extract STRUCTURED attraction data from raw text chunks
5. Returns structured data for downstream agents

WHY IS THIS AN "AGENT" AND NOT JUST A FUNCTION?
-----------------------------------------------
Good question! In this case, it's closer to a "chain" than a true "agent":
  - A FUNCTION: Deterministic. retrieve("Jaipur") → always same result.
  - A CHAIN: Fixed pipeline. RAG retrieval → LLM extraction → structured output.
  - An AGENT: Can DECIDE which tools to use. "Should I search RAG? Or use web?"

Our Destination Agent is technically a chain (fixed pipeline), but we call it
an "agent" because:
1. It uses LLM reasoning (not just pattern matching)
2. It's a node in our multi-agent LangGraph workflow
3. Future enhancement: could be upgraded to a true agent with tool calling

INTERVIEW QUESTIONS:
- Q: "Why use LLM for extraction instead of regex/parsing?"
  A: The knowledge base text is unstructured. Extracting "entry fee: ₹100
     for Indians" requires understanding natural language, not just patterns.

- Q: "What is structured output in LangChain?"
  A: Using .with_structured_output(PydanticModel) forces the LLM to return
     JSON matching the model. The LLM is instruction-tuned to follow schemas.
"""

import json
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.core.llm import get_llm
from app.core.logger import get_logger
from app.graph.state import TravelState
from app.rag.retriever import multi_query_retrieve

logger = get_logger(__name__)


# ============================================================
# Pydantic Models for Structured Output
# ============================================================
# These models define EXACTLY what the LLM must return.
# No ambiguity, no random prose — just structured data.

class Attraction(BaseModel):
    """A single tourist attraction with structured details."""
    name: str = Field(description="Name of the attraction")
    type: str = Field(description="Type: monument, temple, market, nature, museum, fort, lake, park, beach")
    entry_fee: float = Field(description="Entry fee in INR for Indians. 0 if free.")
    duration_hours: float = Field(description="Recommended visit duration in hours")
    timings: str = Field(description="Opening and closing times, e.g., '9:00 AM - 5:00 PM'")
    description: str = Field(description="Brief 1-2 sentence description")
    best_time: str = Field(description="Best time to visit, e.g., 'morning', 'sunset', 'anytime'")
    photography_relevant: bool = Field(description="Whether this is a good spot for photography")
    tips: str = Field(description="One practical tip for visitors")


class DestinationInfo(BaseModel):
    """Structured destination information extracted from RAG context."""
    attractions: list[Attraction] = Field(
        description="List of tourist attractions relevant to user preferences"
    )
    transport_overview: str = Field(
        description="Brief overview of local transportation options and costs"
    )
    best_time_to_visit: str = Field(
        description="Best season/months to visit this destination"
    )
    general_tips: list[str] = Field(
        description="3-5 general tips for visiting this destination"
    )


# ============================================================
# Prompt Template
# ============================================================

DESTINATION_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a travel research assistant. Your job is to extract structured 
destination information from the provided context.

IMPORTANT RULES:
1. Only use information from the PROVIDED CONTEXT. Do not make up facts.
2. If the context doesn't mention a specific detail (like entry fee), 
   use 0 for fees or "Not available" for text fields.
3. Prioritize attractions that match the user's preferences.
4. Include a mix of attraction types for a well-rounded trip.
5. Return at least 5 but no more than 12 attractions.
6. Be specific with prices — use the exact numbers from the context."""
    ),
    (
        "human",
        """Extract destination information from the following context.

DESTINATION: {destination}
USER PREFERENCES: {preferences}
NUMBER OF DAYS: {days}

CONTEXT FROM KNOWLEDGE BASE:
{context}

Extract structured information about attractions, transportation, best time to visit, 
and general tips. Prioritize attractions matching the user's preferences: {preferences}.
Make sure to include at least 5 relevant attractions with accurate details from the context."""
    ),
])


# ============================================================
# Agent Node Function
# ============================================================

def destination_agent_node(state: TravelState) -> dict:
    """
    LangGraph node function for the Destination Agent.
    
    This function is called by LangGraph as a node in the workflow.
    It receives the full state and returns a dict with the fields to UPDATE.
    
    LangGraph merges the returned dict into the existing state:
      state = {**state, **returned_dict}
    
    So we only need to return the fields WE write to:
      - retrieved_context
      - attractions
    
    Args:
        state: Current TravelState from LangGraph
    
    Returns:
        Dict with retrieved_context and attractions to merge into state.
    """
    logger.info(f"🔍 Destination Agent starting for: {state['destination']}")
    logger.info(f"   Preferences: {state['preferences']}")

    try:
        # Step 1: Build search queries from user preferences
        # Instead of one generic query, we create targeted queries for each preference
        # This gives us broader, more relevant retrieval
        destination = state["destination"]
        preferences = state["preferences"]

        queries = [
            f"attractions and places to visit in {destination}",
            f"entry fees, timings, and costs in {destination}",
            f"transportation and getting around in {destination}",
            f"food and restaurants in {destination}",
            f"accommodation and hotels in {destination}",
        ]

        # Add preference-specific queries
        for pref in preferences:
            queries.append(f"{pref} related attractions and activities in {destination}")

        # Step 2: Retrieve relevant chunks from RAG
        retrieved_docs = multi_query_retrieve(
            queries=queries,
            destination=destination,
            k_per_query=3,
        )

        # Extract text content from Document objects
        retrieved_context = [doc.page_content for doc in retrieved_docs]

        logger.info(f"   Retrieved {len(retrieved_context)} unique context chunks")

        if not retrieved_context:
            logger.warning(f"   No context found for {destination}. Proceeding with general knowledge.")
            return {
                "retrieved_context": [],
                "attractions": [],
                "error": f"No travel data found for {destination}. Please check if the destination is supported.",
            }

        # Step 3: Use LLM to extract structured information from raw text
        # .with_structured_output(DestinationInfo) forces the LLM to return
        # JSON matching our Pydantic model. This is CRITICAL — without it,
        # the LLM might return prose that downstream agents can't parse.
        llm = get_llm(temperature=0.2)  # Low temperature for factual extraction
        structured_llm = llm.with_structured_output(DestinationInfo)

        # Build the prompt with retrieved context
        context_text = "\n\n---\n\n".join(retrieved_context)
        preferences_text = ", ".join(preferences)

        chain = DESTINATION_PROMPT | structured_llm

        result: DestinationInfo = chain.invoke({
            "destination": destination,
            "preferences": preferences_text,
            "days": state["days"],
            "context": context_text,
        })

        # Convert Pydantic models to dicts for state storage
        attractions_list = [attr.model_dump() for attr in result.attractions]

        logger.info(
            f"✅ Destination Agent complete. "
            f"Found {len(attractions_list)} attractions."
        )

        return {
            "retrieved_context": retrieved_context,
            "attractions": attractions_list,
        }

    except Exception as e:
        logger.error(f"❌ Destination Agent failed: {e}", exc_info=True)
        return {
            "retrieved_context": [],
            "attractions": [],
            "error": f"Destination Agent error: {str(e)}",
        }
