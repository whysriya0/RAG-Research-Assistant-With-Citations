# gen_eval.py
import json, io, contextlib
from pathlib import Path
from ask import ask

BASE = Path(__file__).resolve().parent
ans_ok = unans_ok = n_ans = n_unans = verified = total_claims = 0

for line in (BASE / "eval" / "questions.jsonl").open(encoding="utf-8"):
    if not line.strip():
        continue
    q = json.loads(line)
    with contextlib.redirect_stdout(io.StringIO()):
        out = ask(q["question"])
    data, results = out if out else ({"answer_found": False, "claims": []}, [])
    if q["answerable"]:
        n_ans += 1
        ans_ok += bool(data["answer_found"] and data["claims"])
        total_claims += len(results)
        verified += sum(r["status"] == "verified" for r in results)
    else:
        n_unans += 1
        unans_ok += not (data["answer_found"] and data["claims"])

print(f"answered answerable questions: {ans_ok}/{n_ans}")
print(f"correctly abstained on unanswerable: {unans_ok}/{n_unans}")
print(f"claims with verified quotes: {verified}/{total_claims}")