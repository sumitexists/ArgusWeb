
import numpy as np
from langchain_ollama import OllamaEmbeddings

_embedder = None

async def get_embedder () -> OllamaEmbeddings:
    global _embedder
    if _embedder is None:
        _embedder = OllamaEmbeddings(
            model="qwen3-embedding:0.6b",
            dimensions=1024
        )
    return _embedder


async def embed(chunks : list[str] ) -> list[list[float]]:
    embedder = await get_embedder()
    chunk_embedding = await embedder.aembed_documents(chunks)

    return chunk_embedding


async def search_dense(query : str, chunks : list[str], top_k : int = 3) -> list[int]:
    query_embeddings = np.array(await embed([query]))
    chunks_embeddings = np.array(await embed(chunks))
    query_embeddings /= np.linalg.norm(query_embeddings, axis=1, keepdims=True)
    chunks_embeddings /= np.linalg.norm(chunks_embeddings, axis=1, keepdims=True)
    scores = chunks_embeddings @ query_embeddings.squeeze()
    safe_k = min(top_k, len(chunks))
    top_indexes = np.argsort(-scores)[:safe_k]

    return top_indexes.tolist()

    
