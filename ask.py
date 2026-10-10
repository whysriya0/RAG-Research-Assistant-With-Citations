# ask.py
import sys, json, re
from pathlib import Path
from datetime import datetime
import ollama
from retrieve import retrieve

LLM = "qwen2.5:7b"
K = 6
MODE = "rerank"          # dense | sparse | hybrid | rerank
TRACE = Path(__file__).resolve().parent / "traces.jsonl"

SYSTEM = """You answer questions using ONLY the numbered sources provided.
Return JSON. Break your answer into short claims. For each claim give:
- "claim": one sentence stating it, in your own words
- "source": the number of the source that supports it
- "quote": an EXACT, word-for-word excerpt (5-25 words) copied from that source
If the sources do not answer the question, set "answer_found" to false and "claims" to an empty list.
Never use outside knowledge. Never invent quotes."""

SCHEMA = {
    "type": "object",
    "properties": {
        "answer_found": {"type": "boolean"},
        "claims": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "claim": {"type": "string"},
                "source": {"type": "integer"},
                "quote": {"type": "string"},
            },
            "required": ["claim", "source", "quote"],
        }},
    },
    "required": ["answer_found", "claims"],
}

norm = lambda s: re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()

def check_quote(quote, text):
    """exact -> 'verified'; mostly there -> 'partial'; else 'NOT FOUND'."""
    nq, nt = norm(quote), norm(text)
    if not nq:
        return "NOT FOUND"
    if nq in nt:
        return "verified"
    words = nq.split()
    tset = set(nt.split())
    overlap = sum(w in tset for w in words) / len(words)
    return "partial" if overlap >= 0.85 else "NOT FOUND"

def ask(question):
    hits = retrieve(question, k=K, mode=MODE)
    context = "\n\n".join(
        f"[{i}] ({h.payload['doc']} | {h.payload['section']})\n{h.payload['text']}"
        for i, h in enumerate(hits, 1)
    )
    resp = ollama.chat(
        model=LLM,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"Sources:\n{context}\n\nQuestion: {question}"},
        ],
        format=SCHEMA,
        options={"num_ctx": 8192, "temperature": 0},
    )
    raw = resp["message"]["content"]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {"answer_found": False, "claims": []}
        print("!! model returned invalid JSON:", raw[:200])

    print(f"\n=== ANSWER ({MODE}) ===")
    if not data["answer_found"] or not data["claims"]:
        print("Not found in the sources.")
    results = []
    for c in data["claims"]:
        n = c["source"]
        if not 1 <= n <= len(hits):
            status = "BAD SOURCE ID"
        else:
            status = check_quote(c["quote"], hits[n - 1].payload["text"])
        results.append({**c, "status": status})
        icon = {"verified": "OK ", "partial": "~  "}.get(status, "XX ")
        print(f"{icon}{c['claim']} [{n}]")
        print(f"     quote ({status}): \"{c['quote']}\"")

    print("\n=== SOURCES ===")
    cited = {r["source"] for r in results}
    for i, h in enumerate(hits, 1):
        p = h.payload
        print(f"{'*' if i in cited else ' '}[{i}] {h.score:.3f} {p['doc']} | {p['section']} | p.{p['page']}")

    # trace: everything needed to debug this answer later
    with TRACE.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "time": datetime.now().isoformat(timespec="seconds"),
            "question": question, "mode": MODE, "model": LLM,
            "retrieved": [{"rank": i, "score": h.score, "id": h.id, **h.payload}
                          for i, h in enumerate(hits, 1)],
            "output": data, "verification": [r["status"] for r in results],
        }, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        ask(" ".join(sys.argv[1:]))
    else:
        while True:
            q = input("\nquestion> ").strip()
            if q in {"", "exit", "quit"}:
                break
            ask(q)