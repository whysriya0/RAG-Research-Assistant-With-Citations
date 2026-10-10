# ingest.py
import json, re, sys, uuid, random
import hashlib, pickle
from pathlib import Path
import ollama
from qdrant_client import QdrantClient, models

RAW = Path("data/raw")
OUT = Path("data/chunks.jsonl")
COLLECTION = "papers"
EMBED_MODEL = "bge-m3"
MAX_TOK = 400       # chunk size cap (estimated tokens)
OVERLAP_TOK = 60    # overlap between consecutive chunks
MIN_TOK = 20        # drop tiny fragments
BATCH = 16

CACHE_F = Path(__file__).resolve().parent / "data" / "embed_cache.pkl"
_cache = pickle.load(CACHE_F.open("rb")) if CACHE_F.exists() else {}

def est_tokens(t: str) -> int:
    return len(t) // 4   # rough: ~4 chars per token

# ---------- 1. Load ----------
def load_pages(path: Path):
    """Return list of (page_number_or_None, markdown_text)."""
    if path.suffix.lower() == ".pdf":
        import pymupdf4llm
        pages = pymupdf4llm.to_markdown(str(path), page_chunks=True)
        return [(i + 1, p["text"]) for i, p in enumerate(pages)]
    return [(None, path.read_text(encoding="utf-8", errors="ignore"))]

# ---------- 2. Split by headings ----------
def sections(pages):
    """Return list of (heading_path, start_page, body_text)."""
    out, stack, body = [], [], []
    page0, in_code = None, False

    def flush():
        text = "\n".join(body).strip()
        if text:
            out.append((" > ".join(h for _, h in stack), page0, text))
        body.clear()

    for page, text in pages:
        for line in text.splitlines():
            if line.strip().startswith("```"):
                in_code = not in_code
            m = None if in_code else re.match(r"^(#{1,6})\s+(.+?)\s*#*$", line)
            if m:
                flush()
                level = len(m.group(1))
                while stack and stack[-1][0] >= level:
                    stack.pop()
                stack.append((level, m.group(2).strip()))
                page0 = page
            else:
                if not body:
                    page0 = page
                body.append(line)
    flush()
    return out

# ---------- 3. Pack paragraphs into chunks ----------
def to_units(body: str):
    """Paragraphs; oversized paragraphs are split into sentences."""
    units = []
    for p in re.split(r"\n\s*\n", body):
        p = p.strip()
        if not p:
            continue
        if est_tokens(p) <= MAX_TOK:
            units.append(p)
        else:
            units.extend(s for s in re.split(r"(?<=[.!?])\s+", p) if s.strip())
    return units

def pack(units):
    chunks, cur = [], []
    for u in units:
        if cur and est_tokens(" ".join(cur + [u])) > MAX_TOK:
            chunks.append("\n\n".join(cur))
            tail, t = [], 0
            for p in reversed(cur):          # carry overlap into next chunk
                t += est_tokens(p)
                if t > OVERLAP_TOK:
                    break
                tail.insert(0, p)
            cur = tail
        cur.append(u)
    if cur:
        chunks.append("\n\n".join(cur))
    return [c for c in chunks if est_tokens(c) >= MIN_TOK]

# ---------- 4. Build chunk records ----------
def build_chunks():
    records = []
    files = sorted(p for p in RAW.iterdir() if p.suffix.lower() in {".pdf", ".md", ".txt"})
    if not files:
        sys.exit(f"No .pdf/.md/.txt files in {RAW}")
    for f in files:
        n_before = len(records)
        for sec_path, page, body in sections(load_pages(f)):
            for text in pack(to_units(body)):
                idx = len(records)
                records.append({
                    "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{f.name}:{idx}")),
                    "doc": f.stem,
                    "section": sec_path,
                    "page": page,
                    "chunk_idx": idx,
                    "text": text,
                    # what we actually embed: text plus where it lives
                    "embed_text": f"{f.stem} | {sec_path}\n{text}",
                })
        print(f"{f.name}: {len(records) - n_before} chunks")
    return records

# ---------- 5. Embed + index ----------
def embed(texts):
    keys = [hashlib.sha1(f"{EMBED_MODEL}|{t}".encode()).hexdigest() for t in texts]
    missing = [(k, t) for k, t in zip(keys, texts) if k not in _cache]
    if missing:
        vecs = ollama.embed(model=EMBED_MODEL, input=[t for _, t in missing])["embeddings"]
        for (k, _), v in zip(missing, vecs):
            _cache[k] = v
        pickle.dump(_cache, CACHE_F.open("wb"))
    return [_cache[k] for k in keys]

def main():
    records = build_chunks()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    toks = sorted(est_tokens(r["text"]) for r in records)
    print(f"\nTotal chunks: {len(records)} | tokens min/median/max: "
          f"{toks[0]}/{toks[len(toks)//2]}/{toks[-1]}")

    client = QdrantClient(url="http://localhost:6333")
    dim = len(embed(["test"])[0])

    # Dev mode: rebuild from scratch each run so stale chunks never linger.
    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)
    client.create_collection(
        COLLECTION,
        vectors_config={"dense": models.VectorParams(size=dim, distance=models.Distance.COSINE)},
        # declared now so we can add sparse/BM25-style vectors later without re-creating
        sparse_vectors_config={"sparse": models.SparseVectorParams(modifier=models.Modifier.IDF)},
    )

    for i in range(0, len(records), BATCH):
        batch = records[i:i + BATCH]
        vecs = embed([r["embed_text"] for r in batch])
        client.upsert(COLLECTION, points=[
            models.PointStruct(
                id=r["id"],
                vector={"dense": v},
                payload={k: r[k] for k in ("doc", "section", "page", "chunk_idx", "text")},
            )
            for r, v in zip(batch, vecs)
        ])
        print(f"indexed {min(i + BATCH, len(records))}/{len(records)}", end="\r")
    print("\nDone.")

    print("\n--- 3 random chunks to eyeball ---")
    for r in random.sample(records, min(3, len(records))):
        print(f"\n[{r['doc']} | {r['section']} | p.{r['page']}]\n{r['text'][:500]}")

if __name__ == "__main__":
    main()