# tools/ui_v2_checker.py
import pandas as pd, os, re

CSV = "docs/ui-v2/operator_map.csv"
UI_PATHS = ["ui", "operators"]

def canonical(op):
    # strip trailing " (n)" if present
    return re.sub(r"\s*\(\d+\)\s*$", "", str(op).strip())

df = pd.read_csv(CSV)
rows = df[df["op_id"].notna()].copy()
rows["op_id_canon"] = rows["op_id"].apply(canonical)

# slurp sources
sources = {}
for root in UI_PATHS:
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if fn.endswith(".py"):
                path = os.path.join(dirpath, fn)
                try:
                    sources[path] = open(path, "r", encoding="utf-8").read()
                except Exception:
                    sources[path] = ""

# check presence
seen = {}
for _, r in rows.iterrows():
    op_raw = r["op_id"]
    op_id = r["op_id_canon"]
    found = [p for p, src in sources.items() if op_id in src]
    key = (op_raw, r.get("panel",""), r.get("section",""), r.get("instance",""))
    seen[key] = found

# print results
for (op_raw, panel, section, instance), files in seen.items():
    status = "✅" if files else "❌"
    print(f"{status} {op_raw} → {', '.join(files) if files else 'MISSING'}")
