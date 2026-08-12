"""Two-stage retrieval: vector search followed by Cohere reranking."""
import os

import cohere
from dotenv import load_dotenv
from pinecone import Pinecone

from src.rag.index_chunks import EMBED_MODEL, INDEX_NAME, NAMESPACE

load_dotenv()

RERANK_MODEL = "rerank-v3.5"
CANDIDATES = 20
TOP_K = 5

_pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
_index = _pc.Index(INDEX_NAME)
_co = cohere.ClientV2(api_key=os.getenv("COHERE_API_KEY"))


def search(query: str, top_k: int = TOP_K, candidates: int = CANDIDATES) -> list[dict]:
    """Retrieve documentation chunks relevant to a query.

    Stage 1: dense vector search returns a broad candidate set.
    Stage 2: the reranker scores query-document pairs and keeps the best.
    """
    embedding = _co.embed(
        texts=[query],
        model=EMBED_MODEL,
        input_type="search_query",
        embedding_types=["float"],
    ).embeddings.float[0]

    matches = _index.query(
        vector=embedding,
        top_k=candidates,
        namespace=NAMESPACE,
        include_metadata=True,
    )["matches"]

    if not matches:
        return []

    documents = [m["metadata"]["text"] for m in matches]
    reranked = _co.rerank(
        query=query,
        documents=documents,
        model=RERANK_MODEL,
        top_n=top_k,
    )

    results = []
    for item in reranked.results:
        match = matches[item.index]
        results.append(
            {
                "text": match["metadata"]["text"],
                "title": match["metadata"]["title"],
                "url": match["metadata"]["url"],
                "vector_score": match["score"],
                "rerank_score": item.relevance_score,
            }
        )

    return results