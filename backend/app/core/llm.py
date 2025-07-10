"""
TripSaathi LLM Client Factory
===============================
Creates and configures the LLM (Large Language Model) client using LangChain.

WHAT IS THIS?
-------------
This module provides a single function `get_llm()` that returns a configured
LangChain ChatModel instance. All agents use this same function to get their
LLM — ensuring consistent configuration across the entire application.

WHY A FACTORY FUNCTION?
-----------------------
Instead of each agent creating its own LLM instance, we centralize it here:
1. Single place to change the LLM provider (swap Groq for OpenAI = 1 line)
2. Consistent settings (temperature, max_tokens) across all agents
3. Retry logic in one place
4. Easy to mock in tests

KEY CONCEPTS:
-------------
LANGCHAIN vs CALLING GROQ API DIRECTLY:
  Without LangChain:
    import groq
    client = groq.Client(api_key="...")
    response = client.chat.completions.create(model="...", messages=[...])
    text = response.choices[0].message.content
  
  With LangChain:
    from langchain_groq import ChatGroq
    llm = ChatGroq(model="...")
    response = llm.invoke("What are the best places in Jaipur?")
  
  LangChain advantages:
  - Swap providers without changing code (ChatGroq → ChatOpenAI → ChatAnthropic)
  - Built-in prompt templates, output parsers, and chaining
  - Integration with RAG, tools, and agents
  - Streaming, batching, and async support built-in

CHAT MODELS vs COMPLETION MODELS:
  - Completion: "Continue this text: The capital of France is..."
  - Chat: Multi-turn conversation with system/human/AI messages
  - Modern LLMs are all chat models. We use ChatGroq, not Groq.

TEMPERATURE:
  - 0.0 = Deterministic (same input → same output). Good for structured data.
  - 0.3 = Slightly creative. Our default — balanced for travel planning.
  - 1.0+ = Very creative/random. Good for brainstorming, bad for facts.

INTERVIEW QUESTIONS:
- Q: "What's the difference between a Chain and an Agent in LangChain?"
  A: A Chain has a FIXED sequence of steps (prompt → LLM → parser).
     An Agent can DECIDE which tools to call based on the input.
     Example: A Chain always calls the RAG retriever. An Agent might decide
     "I don't need RAG for this question, I'll answer directly."

- Q: "Why use LangChain instead of calling the API directly?"
  A: Abstraction (swap providers), composability (chain components together),
     ecosystem (vector stores, embeddings, tools), and standardized interfaces.

- Q: "What is structured output and why does it matter?"
  A: Instead of getting raw text from the LLM, we force it to return JSON
     matching a Pydantic model. This ensures downstream code can parse the
     response reliably. Without it, you'd need fragile string parsing.
"""

from langchain_groq import ChatGroq
from app.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


def get_llm(
    temperature: float | None = None,
    max_tokens: int | None = None,
    model: str | None = None,
) -> ChatGroq:
    """
    Create a configured LLM instance.
    
    This is a factory function — it creates a new instance each time.
    This allows different agents to use different temperatures if needed:
      - Budget Agent: temperature=0.1 (we want precise cost extraction)
      - Itinerary Agent: temperature=0.5 (we want creative suggestions)
      - Critic Agent: temperature=0.2 (we want consistent evaluation)
    
    Args:
        temperature: Override default temperature (0.0-2.0)
        max_tokens: Override default max tokens
        model: Override default model name
    
    Returns:
        Configured ChatGroq instance ready for use.
    
    Example:
        llm = get_llm()
        response = llm.invoke("What are the top attractions in Jaipur?")
        print(response.content)
    """
    _temperature = temperature if temperature is not None else settings.llm_temperature
    _max_tokens = max_tokens if max_tokens is not None else settings.llm_max_tokens
    _model = model or settings.llm_model_name

    logger.info(
        f"Creating LLM instance: model={_model}, "
        f"temperature={_temperature}, max_tokens={_max_tokens}"
    )

    # ChatGroq is LangChain's wrapper around the Groq API.
    # It implements the BaseChatModel interface, which means:
    # - .invoke(message) → single response
    # - .stream(message) → streaming response
    # - .batch([messages]) → parallel processing
    # - .with_structured_output(PydanticModel) → force JSON output
    llm = ChatGroq(
        api_key=settings.groq_api_key,
        model=_model,
        temperature=_temperature,
        max_tokens=_max_tokens,
        # max_retries: LangChain will automatically retry on transient errors
        # (rate limits, network timeouts). This is crucial for production.
        max_retries=3,
    )

    return llm
