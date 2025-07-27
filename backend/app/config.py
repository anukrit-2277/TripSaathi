"""
TripSaathi Configuration
========================
Uses Pydantic Settings to load configuration from environment variables.

WHY PYDANTIC SETTINGS?
----------------------
1. Type Safety: Every config value is validated at startup. If GROQ_API_KEY
   is missing, the app crashes immediately with a clear error — not 30 minutes
   later when the first LLM call fails.

2. Single Source of Truth: All config lives in ONE place. No scattered
   os.getenv() calls throughout the codebase.

3. .env Support: Automatically loads from .env file (via python-dotenv).

4. Documentation: The class itself documents what config is needed.

INTERVIEW QUESTIONS:
- Q: "Why not just use os.getenv() everywhere?"
  A: No validation, no type safety, scattered across codebase, easy to miss.
  
- Q: "What happens if a required env var is missing?"
  A: Pydantic raises ValidationError at startup, not at runtime.

- Q: "How does this relate to the 12-Factor App methodology?"
  A: Factor #3 — "Store config in the environment." Pydantic Settings
     implements this cleanly.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.
    
    Pydantic Settings automatically:
    1. Reads from .env file (if it exists)
    2. Reads from actual environment variables (which override .env)
    3. Validates types (e.g., APP_PORT must be an int)
    4. Raises errors for missing required fields
    """

    # --- LLM Configuration ---
    groq_api_key: str = Field(
        ...,  # ... means REQUIRED — app won't start without it
        description="Groq API key for LLM access"
    )
    llm_model_name: str = Field(
        # llama-3.1-70b-versatile was decommissioned by Groq in early 2025.
        # llama-3.3-70b-versatile is the drop-in replacement.
        default="llama-3.3-70b-versatile",
        description="Groq model to use for LLM calls"
    )
    llm_temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="LLM temperature (0=deterministic, 2=creative)"
    )
    llm_max_tokens: int = Field(
        # NOTE: this budget must cover REASONING tokens, not just visible
        # output. The gpt-oss family are reasoning models — a single
        # itinerary call was measured spending ~550 tokens on reasoning
        # before emitting its first output token.
        #
        # The old value of 1536 was tuned for gpt-oss-20b's 8000 TPM free
        # tier, but it left only ~1000 usable tokens. A 3-day itinerary
        # (3 days x 3-5 activities + 3 meals + notes) does not fit, so the
        # response was cut off mid-JSON (finish_reason="length") and Groq
        # rejected the truncated tool call with 400 tool_use_failed.
        #
        # Measured on openai/gpt-oss-120b with a 3-day Jaipur itinerary:
        #   1536 -> fails    4096 -> works    8192 -> works
        # 6144 is 4096 plus headroom for longer (5-7 day) trips.
        #
        # TRADEOFF: Groq counts max_tokens against the TPM budget, so on a
        # free-tier key a workflow that burns revisions may see 429s. If
        # that happens, lower this rather than going back under ~4096.
        default=6144,
        ge=100,
        le=32768,
        description="Maximum tokens in LLM response"
    )
    llm_timeout_seconds: float = Field(
        default=45.0,
        ge=5.0,
        le=300.0,
        description="Per-request timeout for a single LLM call"
    )

    # --- Database ---
    database_url: str = Field(
        default="postgresql+asyncpg://localhost:5432/tripsaathi",
        description="PostgreSQL connection string"
    )

    # --- ChromaDB / RAG ---
    chroma_persist_dir: str = Field(
        default="./chroma_db",
        description="Directory for ChromaDB persistent storage"
    )
    rag_top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of document chunks to retrieve per RAG query"
    )
    rag_chunk_size: int = Field(
        default=1000,
        ge=100,
        le=5000,
        description="Character count per text chunk"
    )
    rag_chunk_overlap: int = Field(
        default=200,
        ge=0,
        le=1000,
        description="Overlap between text chunks"
    )

    # --- Server ---
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    app_debug: bool = Field(default=True)

    # --- Logging ---
    log_level: str = Field(default="INFO")

    model_config = {
        # Tell Pydantic Settings where to find the .env file
        "env_file": ".env",
        # If .env doesn't exist, don't crash (env vars might be set directly)
        "env_file_encoding": "utf-8",
        # Case-insensitive env var matching
        # So both GROQ_API_KEY and groq_api_key work
        "case_sensitive": False,
    }


# Singleton pattern: create ONE settings instance used throughout the app.
# This is loaded once at import time and reused everywhere.
#
# Usage in other files:
#   from app.config import settings
#   api_key = settings.groq_api_key
settings = Settings()
