import re, sys
from pathlib import Path

RE_ID = re.compile(r'bl_idname\s*=\s*["\']([\w\.]+)["\']')

def find_ops(repo_path: Path):
    ops = set()
    for py in repo_path.rglob("*.py"):
        try:
            text = py.read_text(encoding="utf-8")
        except Exception:
            continue
        ops.update(RE_ID.findall(text))
    return ops

if __name__ == "__main__":
    repo = Path(__file__).resolve().parents[1]  # repo root
    before_file = repo / "tools" / "ops_before.txt"
    after_file  = repo / "tools" / "ops_after.txt"

    if "--before" in sys.argv:
        ops = find_ops(repo)
        before_file.write_text("\n".join(sorted(ops)), encoding="utf-8")
        print(f"Saved BEFORE inventory to {before_file}")
        sys.exit(0)

    if "--after" in sys.argv:
        if not before_file.exists():
            print("Missing BEFORE snapshot. Run with --before first.")
            sys.exit(2)
        ops_before = set(before_file.read_text(encoding="utf-8").splitlines())
        ops_after  = find_ops(repo)
        after_file.write_text("\n".join(sorted(ops_after)), encoding="utf-8")

        removed = ops_before - ops_after
        added   = ops_after  - ops_before

        if removed or added:
            print("❌ Operator set changed!")
            if removed: print("Removed:", sorted(removed))
            if added:   print("Added:",   sorted(added))
            sys.exit(1)
        print("✅ Operator set unchanged.")
        sys.exit(0)

    print("Usage: python tools/ui_refactor_check.py --before | --after")
    sys.exit(64)
