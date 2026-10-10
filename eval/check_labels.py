# eval/check_labels.py
import json, re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
norm = lambda s: re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()

chunks = [json.loads(l) for l in (BASE / "data" / "chunks.jsonl").open(encoding="utf-8")]
for c in chunks:
    c["_n"] = norm(c["text"])

bad = 0
for line in (BASE / "eval" / "questions.jsonl").open(encoding="utf-8"):
    if not line.strip():
        continue
    q = json.loads(line)
    if not q.get("answerable"):
        continue
    ev = q.get("evidence")
    if not ev:
        print(f"{q['id']}: answerable but no evidence"); bad += 1; continue
    hits = [c for c in chunks if norm(ev) in c["_n"]]
    if not hits:
        print(f"{q['id']}: evidence NOT found in any chunk -> {ev[:60]!r}"); bad += 1
    elif q.get("doc") and not any(c["doc"] == q["doc"] for c in hits):
        print(f"{q['id']}: found, but not in doc {q['doc']!r} (in {hits[0]['doc']!r})"); bad += 1
    else:
        print(f"{q['id']}: ok ({len(hits)} chunk(s), e.g. {hits[0]['doc']} | {hits[0]['section']})")
print(f"\n{bad} problem(s)")