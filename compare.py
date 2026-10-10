# compare.py
import sys
from retrieve import retrieve

q = " ".join(sys.argv[1:])
for mode in ["dense", "sparse", "hybrid", "rerank"]:
    print(f"\n===== {mode} =====")
    for i, h in enumerate(retrieve(q, k=5, mode=mode), 1):
        p = h.payload
        print(f"{i}. {h.score:.3f} {p['doc']} | {p['section']} | {p['text'][:90]!r}")