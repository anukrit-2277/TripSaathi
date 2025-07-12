"""
TripSaathi RAG Retriever
==========================
Provides semantic search over the travel knowledge base.

WHAT IS A RETRIEVER?
--------------------
A Retriever is an interface that takes a text query and returns relevant
Document objects. It's the "R" in RAG — the Retrieval part.

How it works:
1. User query: "best historical places in Jaipur"
2. Query is embedded into a vector using the same embedding model
3. ChromaDB finds the K most similar document chunks (by cosine similarity)
4. Returns those chunks as Document objects with source attribution

SEMANTIC SEARCH vs KEYWORD SEARCH:
-----------------------------------
Keyword search (like SQL LIKE '%historical%'):
  - Misses synonyms: "heritage sites" won't match "historical places"
  - No understanding of meaning

Semantic search (what we use):
  - "historical places" matches "heritage sites", "ancient forts", "monuments"
  - Understands meaning, not just keywords
  - Works because embeddings capture semantic relationships

INTERVIEW QUESTIONS:
- Q: "What is a retriever in LangChain?"
  A: An abstraction that takes a query string and returns relevant Document
     objects. It wraps vector stores, search APIs, or any data source.

- Q: "What is cosine similarity?"
  A: Measures the angle between two vectors. 1.0 = identical direction
     (same meaning), 0.0 = perpendicular (unrelated), -1.0 = opposite.

- Q: "How do you improve RAG retrieval quality?"
  A: Better chunking strategy, metadata filtering, re-ranking retrieved results,
     hybrid search (combining semantic + keyword), or query expansion.
"""

from langchain_core.documents import Document
from app.rag.pipeline import get_vector_store
from app.core.logger import get_logger

logger = get_logger(__name__)


def retrieve_destination_info(
    query: str,
    destination: str | None = None,
    k: int = 5,
) -> list[Document]:
    """
    Retrieve relevant travel information using semantic search.
    
    This function:
    1. Takes a natural language query
    2. Optionally filters by destination (using ChromaDB metadata filtering)
    3. Returns the K most semantically similar document chunks
    
    Args:
        query: Natural language search query
               e.g., "historical monuments and forts", "budget food options"
        destination: Optional destination name to filter results
                    e.g., "jaipur" — only returns chunks from jaipur.md
        k: Number of results to return (default: 5)
    
    Returns:
        List of Document objects, each containing:
        - page_content: The relevant text chunk
        - metadata: {"source": "travel_data/jaipur.md", "destination": "jaipur"}
    
    Example:
        # Search across all destinations
        docs = retrieve_destination_info("best beaches for families")
        
        # Search only in Jaipur documents
        docs = retrieve_destination_info(
            "historical monuments and photography spots",
            destination="jaipur"
        )
    """
    vector_store = get_vector_store()

    # Build metadata filter for destination-specific search
    # ChromaDB supports metadata filtering: {"destination": "jaipur"}
    # This ensures we only search within the relevant destination's documents
    search_kwargs = {"k": k}
    if destination:
        destination_lower = destination.lower().strip()
        search_kwargs["filter"] = {"destination": destination_lower}
        logger.info(
            f"Retrieving info for destination='{destination_lower}', "
            f"query='{query[:80]}...', k={k}"
        )
    else:
        logger.info(f"Retrieving info (all destinations), query='{query[:80]}...', k={k}")

    # similarity_search performs:
    # 1. Embed the query using the same embedding model
    # 2. Find K nearest neighbors in the vector space
    # 3. Return the original text chunks with metadata
    results = vector_store.similarity_search(query, **search_kwargs)

    logger.info(
        f"Retrieved {len(results)} chunks. "
        f"Sources: {[r.metadata.get('destination', 'unknown') for r in results]}"
    )

    return results


def retrieve_with_scores(
    query: str,
    destination: str | None = None,
    k: int = 5,
) -> list[tuple[Document, float]]:
    """
    Retrieve documents with similarity scores.
    
    Same as retrieve_destination_info, but also returns the similarity score
    for each result. Useful for:
    - Debugging retrieval quality
    - Setting a minimum relevance threshold
    - Displaying confidence to the user
    
    Returns:
        List of (Document, score) tuples. Lower score = more similar (L2 distance).
    """
    vector_store = get_vector_store()

    search_kwargs = {"k": k}
    if destination:
        search_kwargs["filter"] = {"destination": destination.lower().strip()}

    results = vector_store.similarity_search_with_score(query, **search_kwargs)

    logger.info(
        f"Retrieved {len(results)} chunks with scores. "
        f"Score range: {min(s for _, s in results):.4f} - {max(s for _, s in results):.4f}"
        if results else "No results found"
    )

    return results


def multi_query_retrieve(
    queries: list[str],
    destination: str | None = None,
    k_per_query: int = 3,
) -> list[Document]:
    """
    Retrieve documents using multiple queries and deduplicate results.
    
    WHY MULTIPLE QUERIES?
    A single query might miss relevant info. For example, if a user likes
    "history and food," we search for both topics separately:
      - "historical monuments and heritage sites in Jaipur"
      - "food recommendations and restaurants in Jaipur"
    
    This gives us broader coverage than a single combined query.
    
    Deduplication ensures we don't return the same chunk twice.
    
    Args:
        queries: List of search queries to run
        destination: Optional destination filter
        k_per_query: Number of results per query
    
    Returns:
        Deduplicated list of Document objects from all queries.
    """
    all_results: list[Document] = []
    seen_contents: set[str] = set()

    for query in queries:
        results = retrieve_destination_info(
            query=query,
            destination=destination,
            k=k_per_query,
        )

        for doc in results:
            # Deduplicate by content (same chunk might appear in multiple queries)
            content_hash = doc.page_content[:200]  # Use first 200 chars as key
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                all_results.append(doc)

    logger.info(
        f"Multi-query retrieval: {len(queries)} queries → "
        f"{len(all_results)} unique chunks"
    )

    return all_results
