import ollama
from qdrant_client import QdrantClient, models

client = QdrantClient(url="http://localhost:6333")
def embed(texts):
    return ollama.embed(model="bge-m3", input=texts)["embeddings"]
docs = [
    "LoRA freezes the base weights and trains small low-rank update matrices.",
    "The Transformer uses self-attention instead of recurrence.",
    "Chinchilla showed models were undertrained for their size.",
]
vecs = embed(docs)
client.recreate_collection(
    collection_name="test",
    vectors_config=models.VectorParams(size=len(vecs[0]), distance=models.Distance.COSINE),
)
client.upsert("test", points=[
    models.PointStruct(id=i, vector=v, payload={"text": d, "source": "demo"})
    for i, (d, v) in enumerate(zip(docs, vecs))
])
q = embed(["how does fine-tuning with few parameters work?"])[0]
for h in client.query_points("test", query=q, limit=3).points:
    print(round(h.score, 3), h.payload["text"])