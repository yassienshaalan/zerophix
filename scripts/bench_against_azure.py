#!/usr/bin/env python
import json, argparse
from zerophi.evaluators.bench_azure import run_benchmark

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--infile", required=True, help="Text file with one sample per line")
    ap.add_argument("--outfile", default="benchmark_results.json")
    args = ap.parse_args()
    texts = [line.strip() for line in open(args.infile, "r", encoding="utf-8").read().splitlines() if line.strip()]
    rows = run_benchmark(texts)
    with open(args.outfile, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"Wrote {args.outfile}")

if __name__ == "__main__":
    main()
