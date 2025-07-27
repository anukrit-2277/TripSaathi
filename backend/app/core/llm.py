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

from typing import Type, TypeVar

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_groq import ChatGroq
from pydantic import BaseModel

from app.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


def _finish_reason(message) -> str | None:
    """
    Extract the provider's finish_reason from a LangChain AIMessage.

    "length" means the model hit the max_tokens ceiling and its output is
    truncated — which, for structured output, means the JSON is unparseable
    through no fault of the prompt. Worth surfacing loudly, since it is
    otherwise invisible without inspecting response_metadata by hand.
    """
    meta = getattr(message, "response_metadata", None) or {}
    return meta.get("finish_reason")


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
        # Per-call timeout so a hung/rate-limited request cannot block the
        # workflow for minutes. Combined with the outer workflow timeout,
        # this bounds total latency predictably.
        timeout=settings.llm_timeout_seconds,
        # 3 retries × exponential backoff can add 60s+ to a single call.
        # Drop to 1 retry so transient rate limits still recover, but we
        # fail fast instead of hanging the browser fetch.
        max_retries=1,
    )

    return llm


async def structured_invoke(
    prompt: ChatPromptTemplate,
    schema: Type[T],
    inputs: dict,
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> T:
    """
    Run a structured-output LLM call with a robust fallback path.

    Small Groq models (notably openai/gpt-oss-20b) frequently return partial
    tool arguments — e.g. only one field of a Pydantic schema — which Groq
    then rejects with HTTP 400 ``tool_use_failed``. That surfaces as a
    ``BadRequestError`` from the client library and kills the whole agent
    even though the model was clearly *willing* to answer.

    This helper wraps the call so that, if tool-calling fails validation,
    we retry the exact same schema using Groq's ``json_mode`` — which is
    less strict about tool metadata and much more forgiving on 20B models.
    JSON is then parsed back into the Pydantic model manually.

    If BOTH paths fail, the caller's exception handler still gets a real
    exception and can degrade gracefully.
    """
    llm = get_llm(temperature=temperature, max_tokens=max_tokens)

    # Primary path: tool calling — highest fidelity when it works.
    try:
        chain: Runnable = prompt | llm.with_structured_output(schema)
        return await chain.ainvoke(inputs)
    except Exception as first_err:
        msg = str(first_err).lower()
        # Only fall back for the specific failure modes JSON mode can fix:
        # tool-call schema violations and generic invalid-request errors.
        # Rate limits, timeouts, auth errors: re-raise so the caller sees
        # the real cause.
        if not any(k in msg for k in ("tool_use_failed", "tool call validation", "did not match schema")):
            raise
        # A truncated tool call and a malformed one both surface as
        # tool_use_failed, but only the first is fixed by more tokens.
        # Groq echoes the partial output in `failed_generation`, so an
        # unterminated JSON blob there is the truncation signature.
        if "failed to parse tool call arguments" in msg:
            logger.error(
                f"🚨 {schema.__name__} tool call was cut off mid-JSON — this is "
                f"almost always max_tokens being too low for a reasoning model "
                f"(reasoning tokens count against the same budget). "
                f"Consider raising LLM_MAX_TOKENS."
            )
        logger.warning(
            f"⚠️ Tool-calling structured output failed ({first_err}); "
            f"retrying with json_mode."
        )

    # Fallback path: JSON mode. We embed the schema into the prompt so the
    # model knows what to produce. Then parse the raw string back into the
    # Pydantic model. This is slightly more forgiving than tool-calling and
    # works reliably on smaller Groq models.
    import json

    # ChatPromptTemplate parses message strings as f-string templates, so
    # every literal { and } in the JSON schema would be read as a template
    # variable and blow up with "Invalid format specifier" BEFORE any LLM
    # call happens. Doubling the braces escapes them.
    #
    # This was a real bug: the fallback below never once executed, because
    # building the template raised on every single invocation. Any change
    # here must keep the escaping.
    schema_hint = json.dumps(schema.model_json_schema(), indent=2)
    escaped_schema_hint = schema_hint.replace("{", "{{").replace("}", "}}")
    fallback_prompt = ChatPromptTemplate.from_messages(
        prompt.messages
        + [
            (
                "system",
                (
                    "Return ONLY a single JSON object that conforms to this JSON "
                    "schema. Do not include any prose or markdown fences.\n\n"
                    f"SCHEMA:\n{escaped_schema_hint}"
                ),
            )
        ]
    )
    json_llm = get_llm(temperature=temperature, max_tokens=max_tokens).bind(
        response_format={"type": "json_object"}
    )
    raw = await (fallback_prompt | json_llm).ainvoke(inputs)

    if _finish_reason(raw) == "length":
        logger.error(
            f"🚨 {schema.__name__} json_mode output hit the max_tokens ceiling "
            f"(finish_reason=length). The JSON is truncated and will not parse. "
            f"Raise LLM_MAX_TOKENS."
        )

    text = raw.content if hasattr(raw, "content") else str(raw)
    try:
        return schema.model_validate_json(text)
    except Exception as parse_err:
        # Distinguish "model was cut off" from "model wrote bad JSON" — these
        # need completely different fixes and used to look identical in logs.
        if _finish_reason(raw) == "length":
            raise ValueError(
                f"{schema.__name__} output was truncated by the token limit "
                f"(finish_reason=length). Raise LLM_MAX_TOKENS — the current "
                f"budget cannot fit this response."
            ) from parse_err
        raise
