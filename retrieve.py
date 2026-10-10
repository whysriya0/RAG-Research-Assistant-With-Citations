# retrieve.py
import json
import ollama
from fastembed import SparseTextEmbedding
from qdrant_client import QdrantClient, models

COLLECTION, EMBED_MODEL, LLM = "papers", "bge-m3", "qwen2.5:7b"
client = QdrantClient(url="http://localhost:6333")
bm25 = SparseTextEmbedding("Qdrant/bm25")
_reranker = None

def _dense(q):
    return ollama.embed(model=EMBED_MODEL, input=[q])["embeddings"][0]

def _sparse(q):
    e = next(iter(bm25.query_embed(q)))
    return models.SparseVector(indices=e.indices.tolist(), values=e.values.tolist())

def _hybrid(q, pool):
    return client.query_points(
        COLLECTION,
        prefetch=[
            models.Prefetch(query=_dense(q), using="dense", limit=pool),
            models.Prefetch(query=_sparse(q), using="sparse", limit=pool),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=pool, with_payload=True,
    ).points

def _get_reranker():
    global _reranker
    if _reranker is None:
        from sentence_transformers import CrossEncoder
        _reranker = CrossEncoder("BAAI/bge-reranker-base")
    return _reranker

def _rewrite(q):
    """Split multi-part questions, make vague ones specific, add a hypothetical answer (HyDE)."""
    schema = {"type": "object", "properties": {
        "sub_queries": {"type": "array", "items": {"type": "string"}},
        "hypothetical_passage": {"type": "string"}},
        "required": ["sub_queries", "hypothetical_passage"]}
    prompt = (
        "You help search a collection of machine learning research papers.\n"
        "Given the user's question, return JSON with:\n"
        '- "sub_queries": 1-3 standalone search queries. If the question has several parts, '
        "write one query per part. If it is vague, rewrite it using precise technical terms "
        "a paper would use. Keep each under 20 words.\n"
        '- "hypothetical_passage": 2-3 sentences that could plausibly appear in a paper '
        "and answer the question.\n\nQuestion: " + q)
    r = ollama.chat(model=LLM, messages=[{"role": "user", "content": prompt}],
                    format=schema, options={"temperature": 0, "num_ctx": 4096})
    try:
        d = json.loads(r["message"]["content"])
        return d.get("sub_queries", [])[:3], d.get("hypothetical_passage", "")
    except Exception:
        return [], ""

def retrieve_rewrite(q, k=6, pool=30):
    subs, hyde = _rewrite(q)
    queries = [q] + subs + ([hyde] if hyde else [])
    # 1) search with every query, merge candidate lists with RRF
    fused, by_id = {}, {}
    for query in queries:
        for rank, h in enumerate(_hybrid(query, pool), 1):
            fused[h.id] = fused.get(h.id, 0) + 1 / (60 + rank)
            by_id[h.id] = h
    cands = [by_id[i] for i, _ in sorted(fused.items(), key=lambda x: -x[1])[:pool * 2]]
    # 2) rerank: score each chunk against the original AND each sub-query, keep its best score
    rr = _get_reranker()
    best = [float("-inf")] * len(cands)
    for query in [q] + subs:
        scores = rr.predict([(query, h.payload["text"]) for h in cands])
        best = [max(b, float(s)) for b, s in zip(best, scores)]
    for h, s in zip(cands, best):
        h.score = s
    return sorted(cands, key=lambda h: h.score, reverse=True)[:k]

def retrieve(q, k=6, mode="rerank", pool=50):
    if mode == "rewrite":
        return retrieve_rewrite(q, k)
    if mode == "dense":
        return client.query_points(COLLECTION, query=_dense(q), using="dense",
                                   limit=k, with_payload=True).points
    if mode == "sparse":
        return client.query_points(COLLECTION, query=_sparse(q), using="sparse",
                                   limit=k, with_payload=True).points
    hits = _hybrid(q, pool)
    if mode == "hybrid":
        return hits[:k]
    scores = _get_reranker().predict([(q, h.payload["text"]) for h in hits])
    for h, s in zip(hits, scores):
        h.score = float(s)
    return sorted(hits, key=lambda h: h.score, reverse=True)[:k]