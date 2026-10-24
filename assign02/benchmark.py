#!/usr/bin/env python3
"""
Performance benchmark for Merkle tree construction and proof generation.

Measures:
  • Tree construction time
  • Proof generation time
  • Proof size (number of siblings and JSON byte length)

For 8 ; 1,024 ; and 131,072 (≥ 100,000) leaves.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from merkle.tree import MerkleTree
from merkle.proof import serialize_proof


def benchmark(n_leaves: int, trials: int = 5) -> dict:
    """
    Run construction and proof benchmarks for a tree of *n_leaves*.
    Returns a dict of results.
    """
    leaves = [f"transaction-{i:08d}".encode() for i in range(n_leaves)]

    # -- Construction time --
    build_times = []
    tree = None
    for _ in range(trials):
        t0 = time.perf_counter()
        tree = MerkleTree(leaves)
        t1 = time.perf_counter()
        build_times.append(t1 - t0)

    avg_build = sum(build_times) / len(build_times)
    min_build = min(build_times)

    # -- Proof generation time (for leaf at index n//2) --
    target_idx = n_leaves // 2
    prove_times = []
    proof = None
    for _ in range(trials):
        t0 = time.perf_counter()
        proof = tree.prove(target_idx)
        t1 = time.perf_counter()
        prove_times.append(t1 - t0)

    avg_prove = sum(prove_times) / len(prove_times)
    min_prove = min(prove_times)

    # -- Proof size --
    proof_json = serialize_proof(proof)
    proof_size_bytes = len(proof_json.encode())
    n_siblings = len(proof["siblings"])

    return {
        "n_leaves": n_leaves,
        "build_avg_s": avg_build,
        "build_min_s": min_build,
        "prove_avg_s": avg_prove,
        "prove_min_s": min_prove,
        "proof_siblings": n_siblings,
        "proof_json_bytes": proof_size_bytes,
        "root_hex": tree.root.hex(),
        "trials": trials,
    }


def main():
    sizes = [8, 1_024, 131_072]  # 131,072 = 2^17 ≥ 100,000
    print("=" * 76)
    print("  Merkle Tree Performance Benchmark")
    print("=" * 76)
    print()

    results = []
    for n in sizes:
        print(f"  Benchmarking n = {n:>10,d} leaves ...", end="", flush=True)
        r = benchmark(n)
        results.append(r)
        print(f"  done  (build: {r['build_avg_s']:.4f}s)")

    # -- Summary table --
    print()
    print("  +------------+--------------+--------------+-----------+-------------+")
    print("  |   Leaves   | Build (avg)  | Prove (avg)  | Siblings  | Proof bytes |")
    print("  +------------+--------------+--------------+-----------+-------------+")
    for r in results:
        print(
            f"  | {r['n_leaves']:>10,} "
            f"| {r['build_avg_s']:>10.6f} s "
            f"| {r['prove_avg_s']:>10.6f} s "
            f"| {r['proof_siblings']:>9} "
            f"| {r['proof_json_bytes']:>11,} |"
        )
    print("  +------------+--------------+--------------+-----------+-------------+")
    print()

    # -- Write JSON results --
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "benchmark_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"  Raw results saved to: {out_path}")
    print()


if __name__ == "__main__":
    main()
