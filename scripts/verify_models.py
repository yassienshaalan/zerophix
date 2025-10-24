print('stub; lists local_models sizes')
import os, json
from pathlib import Path

def size_bytes(p: Path) -> int:
    total = 0
    for f in p.rglob("*"):
        if f.is_file():
            try:
                total += f.stat().st_size
            except Exception:
                pass
    return total

def main():
    root = Path("local_models")
    if not root.exists():
        print("local_models/ not found")
        return
    rows = []
    for d in sorted([p for p in root.iterdir() if p.is_dir()]):
        sz = size_bytes(d)
        rows.append({"dir": str(d), "size_gb": round(sz / 1e9, 3)})
    if not rows:
        print("No model directories found under local_models/")
    else:
        print(json.dumps(rows, indent=2))

if __name__ == "__main__":
    main()
