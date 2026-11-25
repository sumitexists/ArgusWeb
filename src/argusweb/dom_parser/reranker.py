
from argusweb.dom_parser.parser import snapshot_parser
from argusweb.dom_parser.bm25 import bm25_search
from argusweb.dom_parser.dense import search_dense

import time
async def reciprocal_rank_fusion(
    dense_ranking: list[int], 
    bm25_ranking: list[int], 
    top_k: int = 4, 
    k_rrf: int = 60
) -> list[int]:
    indices_score: dict[int, float] = {}

    for ranking in (dense_ranking, bm25_ranking):
        for rank, index in enumerate(ranking, start=1):
            indices_score[index] = indices_score.get(index, 0.0) + (1 / (k_rrf + rank))

    sorted_indices = [
        k for k, _ in sorted(indices_score.items(), key=lambda item: item[1], reverse=True)
    ]

    return sorted_indices[:top_k]

