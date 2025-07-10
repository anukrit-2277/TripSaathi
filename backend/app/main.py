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
    logger.info("🚀 TripSaathi starting up...")
    logger.info("📦 Initializing resources...")

    # Phase 3: Initialize RAG pipeline here
    # Phase 12: Initialize database connection here

    yield  # App is running and serving requests

    logger.info("🛑 TripSaathi shutting down...")
    # Cleanup resources here


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
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # Create React App (fallback)
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],      # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],      # Allow all headers
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
    }
