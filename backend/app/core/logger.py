"""
TripSaathi Structured Logging
==============================
Sets up a consistent logging format across the entire application.

WHY STRUCTURED LOGGING?
-----------------------
1. Debugging: When something goes wrong with an LLM call or RAG retrieval,
   you need timestamps, module names, and log levels to trace the issue.

2. Production Readiness: print() doesn't have timestamps or levels.
   logging.info() does — and can be routed to files, monitoring tools, etc.

3. Multi-Agent Context: When 4 agents are running in sequence, you need
   to know WHICH agent logged a message. The logger name does this automatically.

HOW TO USE:
-----------
    from app.core.logger import get_logger
    
    logger = get_logger(__name__)  # __name__ = "app.agents.budget_agent"
    
    logger.info("Starting budget calculation")
    logger.warning("Budget exceeds limit by ₹2000")
    logger.error("LLM call failed", exc_info=True)

INTERVIEW QUESTIONS:
- Q: "Why use logging instead of print()?"
  A: print() has no levels, timestamps, or routing. logging gives you all three
     plus the ability to send logs to files, stdout, or monitoring services.

- Q: "What's the difference between logging.getLogger() and creating a new Logger?"
  A: getLogger() returns a singleton by name. Multiple calls with the same name
     return the SAME logger instance — this is the correct pattern.
"""

import logging
import sys
from app.config import settings


def get_logger(name: str) -> logging.Logger:
    """
    Create or retrieve a logger with consistent formatting.
    
    Args:
        name: Logger name, typically __name__ (e.g., "app.agents.budget_agent")
    
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if get_logger is called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Console handler — logs go to stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # Format: timestamp | level | module name | message
    # Example: 2024-01-15 10:30:45 | INFO | app.agents.budget_agent | Calculating costs...
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    # Prevent log messages from propagating to the root logger
    # (which would cause duplicate messages)
    logger.propagate = False

    return logger
