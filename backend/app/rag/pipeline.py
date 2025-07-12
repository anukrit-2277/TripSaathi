"""
TripSaathi RAG Pipeline
=========================
Handles the full RAG ingestion pipeline:
  Documents → Text Splitting → Embeddings → ChromaDB Vector Store

WHAT IS A RAG PIPELINE?
-----------------------
RAG = Retrieval-Augmented Generation

The problem: LLMs have training data cutoffs and can hallucinate facts.
The solution: Before asking the LLM a question, RETRIEVE relevant documents
from a knowledge base and include them in the prompt as context.

Pipeline steps:
1. LOAD:   Read documents from files (done in loader.py)
2. SPLIT:  Break large documents into smaller chunks
3. EMBED:  Convert text chunks into numerical vectors
4. STORE:  Save vectors in a vector database (ChromaDB)
5. RETRIEVE: At query time, find the most similar chunks

WHY TEXT SPLITTING?
-------------------
A Jaipur.md file is ~4000 words. If we embed the whole file as one vector,
the embedding captures the "average" meaning of the entire document —
losing specific details about individual attractions.

By splitting into chunks of ~1000 characters, each chunk captures a specific
topic (e.g., "Amber Fort details" or "Jaipur food recommendations"),
making semantic search more precise.

Chunk overlap (200 chars) ensures context isn't lost at split boundaries.
Without overlap, a sentence like "Amber Fort. Entry fee is ₹100." might get
split with "Amber Fort" in one chunk and "Entry fee is ₹100" in another.

WHY EMBEDDINGS?
---------------
Text is just characters — computers can't measure "similarity" between strings.
Embeddings convert text into numerical vectors (arrays of floats) in a
high-dimensional space where MEANING is captured:

  "historical monuments in Jaipur" → [0.12, -0.45, 0.78, ...]  (384 dimensions)
  "heritage sites and forts"       → [0.11, -0.43, 0.80, ...]  (very similar!)
  "best restaurants in Goa"        → [-0.32, 0.67, 0.15, ...]  (very different!)

Similar meanings → similar vectors → we can use vector distance to find relevant docs.

WHY CHROMADB?
-------------
ChromaDB is a vector database — it stores embeddings and supports efficient
similarity search (finding the K nearest vectors to a query vector).

vs Regular Database (PostgreSQL):
  - PostgreSQL: SELECT * WHERE destination = 'jaipur' (exact match)
  - ChromaDB: "find me documents similar to 'historical places'" (semantic match)

ChromaDB advantages for our project:
  - Simple API (3 lines to create a collection)
  - Persistent storage (survives restarts)
  - Metadata filtering (filter by destination)
  - No separate server needed

INTERVIEW QUESTIONS:
- Q: "What are embeddings?"
  A: Numerical vector representations of text where semantic similarity
     is captured as vector distance. Similar meanings → close vectors.

- Q: "Why chunk overlap?"
  A: Without overlap, context at chunk boundaries is lost. A 200-char
     overlap ensures sentences spanning two chunks appear in both.

- Q: "How does similarity search work?"
  A: The query is embedded into a vector. Then we find the K nearest vectors
     in the database using distance metrics (cosine similarity, L2 distance).

- Q: "ChromaDB vs FAISS vs Pinecone?"
  A: FAISS = Facebook's library, very fast, no persistence built-in.
     ChromaDB = easy API, persistence, metadata filtering. Good for prototyping.
     Pinecone = cloud-hosted, scalable, costs money. For production.
"""

import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from app.config import settings
from app.core.logger import get_logger
from app.rag.loader import load_travel_documents

logger = get_logger(__name__)

# Module-level variable to hold the initialized vector store
# This acts as a singleton — initialized once, reused across requests
_vector_store: Chroma | None = None
_embeddings: HuggingFaceEmbeddings | None = None


def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Get or create the embedding model (singleton pattern).
    
    We use HuggingFace's all-MiniLM-L6-v2 model:
    - 384-dimensional vectors
    - Runs locally (no API calls, no cost)
    - Good balance of quality and speed
    - ~80MB model, downloaded once on first use
    
    Why not OpenAI embeddings?
    - Cost: OpenAI charges per token embedded
    - Privacy: Text never leaves your machine with local embeddings
    - Latency: No network round-trip
    - For our travel data size, local is more than sufficient
    """
    global _embeddings
    if _embeddings is None:
        logger.info("Loading HuggingFace embedding model: all-MiniLM-L6-v2")
        _embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},  # Use CPU (no GPU needed for this size)
            encode_kwargs={"normalize_embeddings": True},  # Normalize for cosine similarity
        )
        logger.info("Embedding model loaded successfully")
    return _embeddings


def build_vector_store(force_rebuild: bool = False) -> Chroma:
    """
    Build or load the ChromaDB vector store.
    
    This function:
    1. Checks if a persisted ChromaDB exists on disk
    2. If yes (and not force_rebuild), loads it (fast — no re-embedding needed)
    3. If no, runs the full pipeline: load → split → embed → store
    
    The pipeline runs ONCE, then ChromaDB persists to disk.
    Subsequent app restarts just load the existing store.
    
    Args:
        force_rebuild: If True, delete existing store and rebuild from scratch.
    
    Returns:
        Initialized Chroma vector store.
    """
    global _vector_store
    persist_dir = settings.chroma_persist_dir

    # If already loaded in memory, return it
    if _vector_store is not None and not force_rebuild:
        return _vector_store

    embeddings = get_embeddings()

    # Check if a persisted store exists
    if os.path.exists(persist_dir) and not force_rebuild:
        logger.info(f"Loading existing ChromaDB from: {persist_dir}")
        _vector_store = Chroma(
            persist_directory=persist_dir,
            embedding_function=embeddings,
            collection_name="travel_knowledge",
        )
        count = _vector_store._collection.count()
        logger.info(f"Loaded ChromaDB with {count} documents")
        return _vector_store

    # === FULL PIPELINE: Load → Split → Embed → Store ===

    # Step 1: Load documents
    logger.info("Building vector store from scratch...")
    documents = load_travel_documents()

    if not documents:
        raise ValueError("No documents found in travel_data/ directory")

    # Step 2: Split documents into chunks
    # RecursiveCharacterTextSplitter is the recommended splitter because:
    # - It tries to split on natural boundaries (paragraphs → sentences → words)
    # - It respects the hierarchy: \n\n → \n → " " → ""
    # - This keeps related content together better than a simple character split
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.rag_chunk_size,      # Max characters per chunk
        chunk_overlap=settings.rag_chunk_overlap,  # Overlap between chunks
        length_function=len,
        separators=[
            "\n## ",    # Split on markdown H2 headers first (section boundaries)
            "\n### ",   # Then H3 headers (subsection boundaries)
            "\n\n",     # Then paragraph breaks
            "\n",       # Then line breaks
            ". ",       # Then sentence boundaries
            " ",        # Then words
            "",         # Last resort: character by character
        ],
        is_separator_regex=False,
    )

    chunks = text_splitter.split_documents(documents)
    logger.info(
        f"Split {len(documents)} documents into {len(chunks)} chunks "
        f"(chunk_size={settings.rag_chunk_size}, overlap={settings.rag_chunk_overlap})"
    )

    # Step 3 & 4: Embed chunks and store in ChromaDB
    # Chroma.from_documents() does both embedding and storage in one call:
    # - Each chunk's page_content is converted to a vector using the embedding model
    # - The vector + original text + metadata are stored in ChromaDB
    # - ChromaDB persists to disk at persist_directory
    logger.info("Embedding chunks and storing in ChromaDB...")
    _vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_dir,
        collection_name="travel_knowledge",
    )

    count = _vector_store._collection.count()
    logger.info(f"Vector store built successfully with {count} chunks")

    return _vector_store


def get_vector_store() -> Chroma:
    """
    Get the initialized vector store.
    Call build_vector_store() first during app startup.
    """
    if _vector_store is None:
        return build_vector_store()
    return _vector_store
