"""
TripSaathi RAG Document Loader
================================
Loads travel knowledge base documents from the travel_data/ directory.

WHAT IS A DOCUMENT LOADER?
---------------------------
A Document Loader is the first step in a RAG pipeline. It reads raw files
(Markdown, PDF, HTML, etc.) and converts them into LangChain `Document` objects.

Each Document has:
  - page_content: The actual text content
  - metadata: Additional info (source file, destination name, etc.)

WHY METADATA MATTERS:
---------------------
When the Destination Agent searches for "best places in Jaipur," we want to
retrieve chunks ONLY from jaipur.md, not from goa.md. Metadata lets us
filter results by destination, making retrieval more precise.

INTERVIEW QUESTIONS:
- Q: "What document formats does LangChain support?"
  A: PDF, Markdown, HTML, CSV, JSON, Word docs, web pages, databases, etc.
     Each has a specialized loader.

- Q: "Why not just read files with open() and split by newlines?"
  A: LangChain's loaders handle edge cases (encoding, headers, tables),
     add metadata automatically, and integrate with the rest of the pipeline.
"""

import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.documents import Document
from app.core.logger import get_logger

logger = get_logger(__name__)


def load_travel_documents(data_dir: str = None) -> list[Document]:
    """
    Load all .md files from the travel_data/ directory.
    
    Each file represents one destination. We extract the destination name
    from the filename and add it as metadata, which enables filtering
    during retrieval (e.g., "only search Jaipur documents").
    
    Args:
        data_dir: Path to travel data directory. Defaults to travel_data/
                  relative to the backend directory.
    
    Returns:
        List of Document objects with page_content and metadata.
    
    Example:
        docs = load_travel_documents()
        # docs[0].page_content = "# Jaipur — The Pink City\n\n..."
        # docs[0].metadata = {"source": "travel_data/jaipur.md", "destination": "jaipur"}
    """
    if data_dir is None:
        # Default: travel_data/ relative to the backend/ directory
        data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "travel_data"
        )

    logger.info(f"Loading travel documents from: {data_dir}")

    if not os.path.exists(data_dir):
        raise FileNotFoundError(
            f"Travel data directory not found: {data_dir}. "
            "Make sure travel_data/ exists with .md files."
        )

    # DirectoryLoader reads all files matching a glob pattern from a directory.
    # We use TextLoader as the loader class because our .md files are plain text.
    #
    # Why TextLoader over UnstructuredMarkdownLoader?
    #   - TextLoader is simpler and lighter (no unstructured dependency)
    #   - Our .md files are structured enough that we don't need special parsing
    #   - UnstructuredMarkdownLoader would add unnecessary complexity
    loader = DirectoryLoader(
        data_dir,
        glob="**/*.md",           # Match all .md files recursively
        loader_cls=TextLoader,     # Use TextLoader for each file
        loader_kwargs={"encoding": "utf-8"},
        show_progress=True,
    )

    documents = loader.load()

    # Enrich each document with destination metadata
    # This allows us to filter retrieval by destination later
    for doc in documents:
        # Extract destination name from filename
        # "travel_data/jaipur.md" → "jaipur"
        filename = os.path.basename(doc.metadata.get("source", ""))
        destination = os.path.splitext(filename)[0].lower()
        doc.metadata["destination"] = destination

    logger.info(
        f"Loaded {len(documents)} documents: "
        f"{[d.metadata['destination'] for d in documents]}"
    )

    return documents
