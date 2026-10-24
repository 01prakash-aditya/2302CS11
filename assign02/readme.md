# Assignment 2: Merkle Trees and Proofs of Inclusion

**Course:** BCT (Blockchain Technology) — 2302CS11  
**Author:** Aditya  
**Language:** Python 3.10+  
**Dependencies:** None (standard library only — `hashlib`, `json`, `argparse`, `math`)

---

## Project Structure

```
assign02/
├── README.md               ← You are here
├── requirements.txt         ← Dependency manifest (no external deps)
├── merkle/                  ← Library source code
│   ├── __init__.py          ← Package exports and specification
│   ├── __main__.py          ← python -m merkle entry point
│   ├── hash_utils.py        ← Domain-separated hash functions
│   ├── tree.py              ← MerkleTree construction and proof generation
│   ├── proof.py             ← Proof verification, serialization, validation
│   └── cli.py               ← CLI commands: root, prove, verify
├── tests/
│   ├── __init__.py
│   ├── test_merkle.py       ← 43 unit tests (construction, proofs, CLI, vectors)
│   └── test_vectors.json    ← Pinned deterministic test vectors
├── benchmark.py             ← Performance measurement script
└── benchmark_results.json   ← Generated benchmark results
```

---

## How to Execute

### Prerequisites

- **Python 3.10+** (uses `match` and type-hint syntax; no pip packages needed)

### Install Dependencies

```bash
pip install -r requirements.txt   # (empty — no external deps)
```

### CLI Commands

All commands are run from the `assign02/` directory:

```bash
# 1. Compute the Merkle root
python -m merkle root tx0 tx1 tx2 tx3 tx4

# 2. Generate an inclusion proof for leaf at index 2
python -m merkle prove --index 2 tx0 tx1 tx2 tx3 tx4

# 3. Save proof to a file
python -m merkle prove --index 2 --output proof.json tx0 tx1 tx2 tx3 tx4

# 4. Verify a proof from a file
python -m merkle verify --leaf tx2 --root <root_hex> --proof proof.json

# 5. Verify with inline JSON
python -m merkle verify --leaf tx2 --root <root_hex> --proof-inline '<proof_json>'

# 6. Read transactions from a file (one per line)
python -m merkle root --file transactions.txt
python -m merkle prove --index 3 --file transactions.txt
```

### Run Tests

```bash
python -m unittest tests.test_merkle -v
```

### Run Benchmarks

```bash
python benchmark.py
```

---

## Specification

### Domain-Separated Hashing

Two distinct hash domains prevent second-preimage attacks:

| Type | Formula | Purpose |
|------|---------|---------|
| Leaf | `H_leaf(data) = SHA-256(0x00 \|\| data)` | Hash raw transaction data |
| Node | `H_node(L, R) = SHA-256(0x01 \|\| left \|\| right)` | Hash two child hashes |

The single-byte prefix (`0x00` for leaves, `0x01` for internal nodes) ensures that
a leaf value can never collide with an internal node concatenation.

### Handling Odd Numbers of Leaves

When a tree level has an **odd number of nodes**, the last unpaired node is
**promoted** (carried up) to the next level **without re-hashing**. This avoids
the Bitcoin-style duplication that creates a subtle vulnerability.

### Edge Cases

| Leaves | Root |
|--------|------|
| 0 (empty) | `H_leaf(b"")` = `SHA-256(0x00)` = `6e340b9c...` |
| 1 | `H_leaf(data)` — the single leaf hash |
| 2 | `H_node(H_leaf(d0), H_leaf(d1))` |
| Odd ≥ 3 | Last node promoted at each odd level |

### Proof Format

```json
{
  "leaf_index": 2,
  "tree_size": 5,
  "siblings": [
    {"side": "right", "hash": "dd92b235..."},
    {"side": "left",  "hash": "e7f5de3c..."},
    {"side": "right", "hash": "590b66ca..."}
  ]
}
```

- **`side`**: The position of the sibling relative to the running hash.
  - `"right"` → running hash is on the left: `H_node(current, sibling)`
  - `"left"` → running hash is on the right: `H_node(sibling, current)`

### Proof Validation Rules

The deserializer rejects:

1. **Malformed hashes** — must be exactly 64 lowercase hex characters
2. **Invalid directions** — only `"left"` or `"right"` are accepted
3. **Wrong indexes** — `leaf_index` must be in `[0, tree_size)`
4. **Unnecessarily long proofs** — length must be ≤ `ceil(log2(tree_size))`
5. **Missing keys** — `leaf_index`, `tree_size`, and `siblings` are required

---

## Merkle Tree Diagram for 5 Transactions

The following diagram shows the exact tree structure and the **proof path for
leaf index 2** (`tx2`). Nodes on the proof path are marked with `[*]`, and
sibling hashes included in the proof are marked with `<<>>`.

```
                          Root [*]
                     410e561a...
                    /              \
               N2 [*]              <<L4>>
          f7ef01f2...          590b66ca...
          /          \
     <<N01>>         N23 [*]
   e7f5de3c...     fb92ff71...
    /      \        /      \
  L0       L1     L2[*]   <<L3>>
a91327..  b535c0.. 8f968b.. dd92b2..
  |        |        |        |
 tx0      tx1      tx2      tx3      tx4
```

### Proof path for `tx2` (leaf index 2):

```
Step  Current Hash              Sibling             Side     Result
----  -------------------------  ------------------  ------   ------
  0   H_leaf(tx2) = 8f968b..    L3 = dd92b2..       right    N23 = H_node(current, L3)
  1   N23 = fb92ff..             N01 = e7f5de..      left     N2  = H_node(N01, current)
  2   N2  = f7ef01..             L4 = 590b66..       right    Root = H_node(current, L4)
```

**Result:** computed root `410e561a...` matches expected root. Proof is **VALID**.

---

## Performance Report

Benchmarks run on the local machine with 5 trials per size.

| Leaves | Build Time (avg) | Prove Time (avg) | Proof Siblings | Proof Size (JSON) |
|-------:|:----------------:|:-----------------:|:--------------:|:-----------------:|
| 8 | ~0.0001 s | ~0.00002 s | 3 | 409 bytes |
| 1,024 | ~0.003 s | ~0.00001 s | 10 | 1,233 bytes |
| 131,072 | ~0.45 s | ~0.00001 s | 17 | 2,056 bytes |

### Observations

1. **Construction is O(n):** Building the tree scales linearly with the number of
   leaves since every node is hashed exactly once.

2. **Proof generation is O(log n):** Generating a proof only walks from the target
   leaf to the root, visiting one node per level. The ~13 microsecond time is
   essentially constant across all sizes.

3. **Proof size is O(log n):** The number of siblings equals the depth of the tree
   (`ceil(log2(n))` in the worst case). For 131,072 leaves, only 17 hashes
   (about 2 KB of JSON) suffice to prove inclusion — demonstrating the
   logarithmic efficiency that makes Merkle trees practical for blockchains.

4. **Promoted leaves get shorter proofs:** A leaf that is promoted (odd-one-out)
   skips one or more levels, resulting in fewer siblings. For 5 leaves, leaf 4's
   proof has only 1 sibling vs. 3 for the other leaves.

---

## Test Vectors

Deterministic test vectors are in [`tests/test_vectors.json`](tests/test_vectors.json).

Key pinned values:

| Input | Root Hash |
|-------|-----------|
| `["hello"]` | `8a2a5c9b768827de5a9552c38a044c66959c68f6d2f21b5260af54d2f87db827` |
| `["alice", "bob"]` | `3bc1199d175a1cfc2c3fe16b1920a93ca6397484cbda581a4b7c6b920f93ba83` |
| `["tx0".."tx4"]` | `410e561afb28190ea4a953dc541c5ee3965b9abc09724adfe1467fd55dfc1949` |
| `[]` (empty) | `6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d` |
