import bm25s
import Stemmer
import asyncio

_stemmer = None


async def bm25_search(query : str, corpus : list[str], k : int = 10) -> list[int]:
    global _stemmer
    if _stemmer is None:
        _stemmer = Stemmer.Stemmer("english")

    corpus_token = bm25s.tokenize(corpus, stopwords="en", stemmer=_stemmer)

    retriever = bm25s.BM25()
    retriever.index(corpus_token)

    query_token = bm25s.tokenize(query, stemmer=_stemmer)

    safe_k = min(k, len(corpus))
    results, _ = await asyncio.to_thread(retriever.retrieve, query_token, k=safe_k)


    return results[0].tolist()
