"""
TripSaathi — FastAPI Application Entry Point
=============================================
This is the main file that creates and configures the FastAPI application.

WHY FASTAPI?
------------
1. Async-First: LLM calls take 2-10 seconds. With Flask (synchronous), each
   request blocks a worker thread. FastAPI uses async/await, so one process
   can handle many concurrent requests while waiting for LLM responses.

2. Automatic Validation: Define a Pydantic model → FastAPI validates the
   request body automatically. No manual parsing or error checking.

3. Auto-Generated Docs: Visit /docs to see interactive Swagger UI. Great for
   testing APIs without Postman.

4. Type Hints Everywhere: The function signature IS the API contract.
   FastAPI reads the type hints to generate validation, docs, and serialization.

INTERVIEW QUESTIONS:
- Q: "FastAPI vs Flask vs Django — when would you use each?"
  A: FastAPI = async APIs with validation (our use case).
     Flask = simple synchronous apps, prototypes.
     Django = full-stack with ORM, admin panel, auth built-in.

- Q: "What is ASGI vs WSGI?"
  A: WSGI (Flask/Django) = synchronous. One request per thread.
     ASGI (FastAPI) = asynchronous. Can handle concurrent I/O-bound operations.
     
- Q: "What is CORS and why do we need it?"
  A: Browsers block requests from one origin (localhost:5173, our React app)
     to another origin (localhost:8000, our FastAPI backend). CORS middleware
     tells the browser "yes, this frontend is allowed to talk to me."

LIFESPAN EVENTS:
- on_startup: Initialize resources (DB connections, RAG pipeline)
- on_shutdown: Clean up resources (close DB connections)
Using the modern `lifespan` context manager pattern instead of deprecated
@app.on_event("startup") / @app.on_event("shutdown").
"""
# --- SQLite fix for Linux deployment (Railway/Render) ---
# ChromaDB requires SQLite >= 3.35. Railway's Linux has an older version.
# This swaps in pysqlite3-binary BEFORE chromadb gets imported.
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass  # On macOS/local, pysqlite3 isn't needed

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    
    This is the modern way to handle app lifecycle in FastAPI (v0.93+).
    Everything before `yield` runs on startup.
    Everything after `yield` runs on shutdown.
    
    We'll add RAG pipeline initialization and DB setup here in later phases.
    """
    logger.info("TripSaathi starting up...")

    # Initialize database first (fast)
    from app.db.database import init_db, close_db
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Database init skipped: {e}")

    # Initialize RAG in background thread (embedding download can be slow)
    import threading
    def _init_rag():
        from app.rag.pipeline import build_vector_store
        build_vector_store()
        logger.info("RAG pipeline initialized")
    threading.Thread(target=_init_rag, daemon=True).start()

    yield  # App is running — /health responds immediately

    logger.info("🛑 TripSaathi shutting down...")
    try:
        await close_db()
    except Exception:
        pass


# Create the FastAPI application
app = FastAPI(
    title="TripSaathi",
    description=(
        "Multi-Agent RAG Travel Planner — Generates realistic travel itineraries "
        "using specialized AI agents (Destination, Budget, Itinerary, Critic) "
        "powered by LangChain, LangGraph, and RAG."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# --- CORS Middleware ---
# In development, React runs on localhost:5173 (Vite's default port)
# and FastAPI runs on localhost:8000. Without CORS, the browser blocks
# the React app from making API calls to FastAPI.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # Allow all origins in development
    allow_credentials=False,       # No cookies/credentials needed for our API
    allow_methods=["*"],           # Allow all HTTP methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],           # Allow all headers
)


# --- Health Check Endpoint ---
# Every production API needs a health check. Load balancers, monitoring tools,
# and orchestrators (K8s, etc.) hit this endpoint to verify the service is alive.
@app.get(
    "/health",
    tags=["System"],
    summary="Health check",
    response_description="Returns OK if the service is running",
)
async def health_check():
    """
    Simple health check endpoint.
    Returns 200 OK if the server is running.
    """
    return {
        "status": "healthy",
        "service": "TripSaathi",
        "version": "1.0.0",
    }


# --- Root Endpoint ---
@app.get(
    "/",
    tags=["System"],
    summary="API root",
)
async def root():
    """Welcome endpoint with API information."""
    return {
        "message": "Welcome to TripSaathi — Multi-Agent RAG Travel Planner",
        "docs": "/docs",
        "health": "/health",
        "plan_trip": "/api/trip/plan",
    }


# --- Register API Routers ---
from app.api.routes.trips import router as trips_router
app.include_router(trips_router)
