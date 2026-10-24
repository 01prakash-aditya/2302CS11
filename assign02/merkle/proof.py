"""
Proof serialization, deserialization, and verification.
"""

from __future__ import annotations

import json
import math
import re
from typing import Any, Dict, List, Union

from merkle.hash_utils import hash_leaf, hash_node

# Regex for a 64-character lowercase hex string (SHA-256 digest)
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


# ------------------------------------------------------------------ #
#  Serialization helpers
# ------------------------------------------------------------------ #


def serialize_proof(proof: dict) -> str:
    """
    Serialize a proof dict to a JSON string.

    Parameters
    ----------
    proof : dict
        Proof dictionary as returned by ``MerkleTree.prove()``.

    Returns
    -------
    str
        Pretty-printed JSON string.
    """
    return json.dumps(proof, indent=2)


def deserialize_proof(raw: str) -> dict:
    """
    Deserialize and *validate* a JSON proof string.

    Checks
    ------
    1. Required keys: ``leaf_index``, ``tree_size``, ``siblings``.
    2. ``leaf_index`` is a non-negative int < ``tree_size``.
    3. ``tree_size`` is a positive int.
    4. Every sibling has ``side`` ∈ {``"left"``, ``"right"``} and
       ``hash`` as a 64-char lowercase hex string.
    5. The number of siblings does not exceed
       ``ceil(log2(tree_size))`` (rejects unnecessarily long proofs).

    Parameters
    ----------
    raw : str
        JSON string.

    Returns
    -------
    dict
        Validated proof dictionary.

    Raises
    ------
    ValueError
        On any validation failure.
    """
    try:
        data: Dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc

    # --- required keys ---
    for key in ("leaf_index", "tree_size", "siblings"):
        if key not in data:
            raise ValueError(f"Missing required key: '{key}'")

    # --- tree_size ---
    tree_size = data["tree_size"]
    if not isinstance(tree_size, int) or tree_size < 1:
        raise ValueError(
            f"'tree_size' must be a positive integer, got {tree_size!r}"
        )

    # --- leaf_index ---
    leaf_index = data["leaf_index"]
    if not isinstance(leaf_index, int) or not (0 <= leaf_index < tree_size):
        raise ValueError(
            f"'leaf_index' must be in [0, {tree_size}), got {leaf_index!r}"
        )

    # --- siblings ---
    siblings = data["siblings"]
    if not isinstance(siblings, list):
        raise ValueError("'siblings' must be a list")

    # Max proof length = ceil(log2(tree_size)) for tree_size >= 2, 0 for size 1
    if tree_size == 1:
        max_len = 0
    else:
        max_len = math.ceil(math.log2(tree_size))

    if len(siblings) > max_len:
        raise ValueError(
            f"Proof too long: {len(siblings)} siblings but max is {max_len} "
            f"for tree_size={tree_size}"
        )

    for i, sib in enumerate(siblings):
        if not isinstance(sib, dict):
            raise ValueError(f"siblings[{i}] is not an object")

        # side
        side = sib.get("side")
        if side not in ("left", "right"):
            raise ValueError(
                f"siblings[{i}]['side'] must be 'left' or 'right', "
                f"got {side!r}"
            )

        # hash
        h = sib.get("hash")
        if not isinstance(h, str) or not _HEX64_RE.match(h):
            raise ValueError(
                f"siblings[{i}]['hash'] must be a 64-char lowercase hex "
                f"string, got {h!r}"
            )

    return data


# ------------------------------------------------------------------ #
#  Proof generation (standalone function)
# ------------------------------------------------------------------ #


def generate_proof(tree, leaf_index: int) -> dict:
    """
    Convenience wrapper around ``tree.prove(leaf_index)``.

    Parameters
    ----------
    tree : MerkleTree
    leaf_index : int

    Returns
    -------
    dict
    """
    return tree.prove(leaf_index)


# ------------------------------------------------------------------ #
#  Verification
# ------------------------------------------------------------------ #


def verify_proof(
    leaf_data: bytes,
    proof: Union[dict, str],
    expected_root: bytes,
) -> bool:
    """
    Verify a Merkle inclusion proof.

    Parameters
    ----------
    leaf_data : bytes
        Raw data of the leaf whose inclusion is being proven.
    proof : dict | str
        Proof dictionary or JSON string.  If a string, it is
        deserialized and validated first.
    expected_root : bytes
        The expected Merkle root (32 bytes).

    Returns
    -------
    bool
        ``True`` iff the computed root matches *expected_root*.

    Raises
    ------
    ValueError
        If the proof fails structural validation.
    """
    if isinstance(proof, str):
        proof = deserialize_proof(proof)
    else:
        # Validate dict form by round-tripping through JSON
        proof = deserialize_proof(json.dumps(proof))

    current = hash_leaf(leaf_data)

    for sibling in proof["siblings"]:
        sib_hash = bytes.fromhex(sibling["hash"])
        if sibling["side"] == "left":
            current = hash_node(sib_hash, current)
        else:  # "right"
            current = hash_node(current, sib_hash)

    return current == expected_root
