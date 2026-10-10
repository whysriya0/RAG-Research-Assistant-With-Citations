import json
from pathlib import Path
from fastembed import SparseTextEmbedding
from qdrant_client import QdrantClient, models

BASE = Path(__file__).resolve().parent
client = QdrantClient(url="http://localhost:6333")
bm25 = SparseTextEmbedding("Qdrant/bm25")

recs = [json.loads(l) for l in (BASE / "data" / "chunks.jsonl").open(encoding="utf-8")]
B = 64
for i in range(0, len(recs), B):
    batch = recs[i:i + B]
    embs = list(bm25.embed([r["embed_text"] for r in batch]))
    client.update_vectors("papers", points=[
        models.PointVectors(
            id=r["id"],
            vector={"sparse": models.SparseVector(indices=e.indices.tolist(), values=e.values.tolist())},
        ) for r, e in zip(batch, embs)
    ])
    print(f"{min(i + B, len(recs))}/{len(recs)}", end="\r")
print("\nDone.")