# eval/run.py   usage: python eval\run.py [modes] [tag]
#   python eval\run.py                      -> all modes
#   python eval\run.py hybrid,rerank "chunk400"
import sys, json, re, csv, time
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
from retrieve import retrieve

MODES = sys.argv[1].split(",") if len(sys.argv) > 1 else ["dense", "sparse", "hybrid", "rerank"]
TAG = sys.argv[2] if len(sys.argv) > 2 else ""
TOPN = 10

norm = lambda s: re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()

chunks = [json.loads(l) for l in (BASE / "data" / "chunks.jsonl").open(encoding="utf-8")]
all_text = [norm(c["text"]) for c in chunks]

questions, skipped = [], []
for line in (BASE / "eval" / "questions.jsonl").open(encoding="utf-8"):
    if not line.strip():
        continue
    q = json.loads(line)
    if not q.get("answerable"):
        continue
    ev = q.get("evidence")
    if not ev or not any(norm(ev) in t for t in all_text):
        skipped.append(q["id"])
        continue
    questions.append(q)

print(f"Using {len(questions)} questions. Skipped (bad/missing evidence): {skipped or 'none'}\n")
if not questions:
    sys.exit("No usable questions. Fix evidence labels first (see check_labels.py).")

rows = []
for mode in MODES:
    ranks, lat, by_type = [], [], {}
    for q in questions:
        t0 = time.time()
        hits = retrieve(q["question"], k=TOPN, mode=mode)
        lat.append(time.time() - t0)
        ev = norm(q["evidence"])
        rank = next((i for i, h in enumerate(hits, 1) if ev in norm(h.payload["text"])), None)
        ranks.append(rank)
        by_type.setdefault(q.get("type", "?"), []).append(rank)

    n = len(ranks)
    rec = lambda k: sum(1 for r in ranks if r and r <= k) / n
    mrr = sum(1 / r for r in ranks if r) / n
    rows.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"), "tag": TAG, "mode": mode, "n": n,
        "recall@1": round(rec(1), 3), "recall@3": round(rec(3), 3),
        "recall@5": round(rec(5), 3), "mrr": round(mrr, 3),
        "avg_latency_s": round(sum(lat) / n, 2),
    })
    misses = [q["id"] for q, r in zip(questions, ranks) if not r or r > 5]
    print(f"[{mode}] misses@5: {misses or 'none'}")
    for t, rs in by_type.items():
        print(f"    {t:<12} recall@5 = {sum(1 for r in rs if r and r <= 5)}/{len(rs)}")

print(f"\n{'mode':<8} {'R@1':>6} {'R@3':>6} {'R@5':>6} {'MRR':>6} {'sec/q':>6}")
for r in rows:
    print(f"{r['mode']:<8} {r['recall@1']:>6} {r['recall@3']:>6} {r['recall@5']:>6} {r['mrr']:>6} {r['avg_latency_s']:>6}")

out = BASE / "results.csv"
new = not out.exists()
with out.open("a", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    if new:
        w.writeheader()
    w.writerows(rows)
print(f"\nAppended to {out}")