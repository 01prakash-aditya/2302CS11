"""
Merkle Tree Library
===================
A pure-Python implementation of Merkle trees with domain-separated hashing,
inclusion proof generation, and verification.

Specification
-------------
- Hash function : SHA-256
- Leaf hash     : H_leaf(data) = SHA256(0x00 || data)
- Internal hash : H_node(l, r) = SHA256(0x01 || left || right)
- Odd leaves    : the unpaired node is promoted to the next level (no duplication)
- Empty tree    : root = SHA256(0x00)  (i.e., H_leaf of empty data)

Proof format (JSON)
-------------------
{
    "leaf_index": <int>,
    "tree_size":  <int>,
    "siblings": [
        {"side": "left"|"right", "hash": "<64-char hex>"},
        ...
    ]
}

"side" indicates the position of the *sibling* relative to the current
running hash.  If side == "right", the running hash is on the left.
"""

from merkle.tree import MerkleTree
from merkle.proof import generate_proof, verify_proof, serialize_proof, deserialize_proof
from merkle.hash_utils import hash_leaf, hash_node, EMPTY_ROOT

__all__ = [
    "MerkleTree",
    "generate_proof",
    "verify_proof",
    "serialize_proof",
    "deserialize_proof",
    "hash_leaf",
    "hash_node",
    "EMPTY_ROOT",
]
