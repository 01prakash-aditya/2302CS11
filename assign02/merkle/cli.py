#!/usr/bin/env python3
"""
Merkle Tree CLI
===============

Commands
--------
root   – Compute the Merkle root of given transactions.
prove  – Generate an inclusion proof for a transaction.
verify – Verify an inclusion proof against a root.

Usage examples
--------------
    python -m merkle root tx0 tx1 tx2 tx3 tx4
    python -m merkle prove --index 2 tx0 tx1 tx2 tx3 tx4
    python -m merkle verify --leaf tx2 --root <hex> --proof proof.json
    python -m merkle verify --leaf tx2 --root <hex> --proof-inline '<json>'
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from merkle.hash_utils import EMPTY_ROOT
from merkle.proof import deserialize_proof, serialize_proof, verify_proof
from merkle.tree import MerkleTree


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="merkle",
        description="Merkle Tree CLI — build roots, generate proofs, verify inclusion.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ---- root ----
    p_root = sub.add_parser("root", help="Compute the Merkle root.")
    p_root.add_argument(
        "transactions",
        nargs="*",
        help="Transaction strings (leaves).  If none, reads stdin line-by-line.",
    )
    p_root.add_argument(
        "--file", "-f",
        type=str,
        default=None,
        help="Read transactions from a file (one per line).",
    )

    # ---- prove ----
    p_prove = sub.add_parser("prove", help="Generate an inclusion proof.")
    p_prove.add_argument(
        "--index", "-i",
        type=int,
        required=True,
        help="Zero-based leaf index.",
    )
    p_prove.add_argument(
        "transactions",
        nargs="*",
        help="Transaction strings.",
    )
    p_prove.add_argument(
        "--file", "-f",
        type=str,
        default=None,
        help="Read transactions from a file (one per line).",
    )
    p_prove.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Write proof JSON to this file instead of stdout.",
    )

    # ---- verify ----
    p_verify = sub.add_parser("verify", help="Verify an inclusion proof.")
    p_verify.add_argument(
        "--leaf", "-l",
        type=str,
        required=True,
        help="The leaf data (transaction string).",
    )
    p_verify.add_argument(
        "--root", "-r",
        type=str,
        required=True,
        help="Expected Merkle root (64-char hex).",
    )
    grp = p_verify.add_mutually_exclusive_group(required=True)
    grp.add_argument(
        "--proof",
        type=str,
        help="Path to a proof JSON file.",
    )
    grp.add_argument(
        "--proof-inline",
        type=str,
        help="Proof as an inline JSON string.",
    )

    return parser


def _read_transactions(args) -> list[bytes]:
    """Resolve the transaction list from CLI args, file, or stdin."""
    if getattr(args, "file", None):
        path = Path(args.file)
        if not path.exists():
            print(f"Error: file '{args.file}' not found.", file=sys.stderr)
            sys.exit(1)
        lines = path.read_text(encoding="utf-8").splitlines()
        return [line.encode() for line in lines if line.strip()]
    if args.transactions:
        return [tx.encode() for tx in args.transactions]
    # Read from stdin
    return [line.strip().encode() for line in sys.stdin if line.strip()]


# ------------------------------------------------------------------ #
#  Command handlers
# ------------------------------------------------------------------ #


def cmd_root(args) -> None:
    txs = _read_transactions(args)
    tree = MerkleTree(txs)
    print(tree.root.hex())


def cmd_prove(args) -> None:
    txs = _read_transactions(args)
    tree = MerkleTree(txs)
    try:
        proof = tree.prove(args.index)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    proof_json = serialize_proof(proof)

    if args.output:
        Path(args.output).write_text(proof_json + "\n", encoding="utf-8")
        print(f"Proof written to {args.output}")
        print(f"Root: {tree.root.hex()}")
    else:
        print(proof_json)
        print(f"\nRoot: {tree.root.hex()}", file=sys.stderr)


def cmd_verify(args) -> None:
    # Parse root
    root_hex = args.root.strip()
    try:
        expected_root = bytes.fromhex(root_hex)
    except ValueError:
        print(f"Error: invalid root hex '{root_hex}'", file=sys.stderr)
        sys.exit(1)
    if len(expected_root) != 32:
        print("Error: root must be a 64-char (32-byte) hex string.", file=sys.stderr)
        sys.exit(1)

    # Load proof
    if args.proof:
        path = Path(args.proof)
        if not path.exists():
            print(f"Error: file '{args.proof}' not found.", file=sys.stderr)
            sys.exit(1)
        raw = path.read_text(encoding="utf-8")
    else:
        raw = args.proof_inline

    # Verify
    leaf_data = args.leaf.encode()
    try:
        result = verify_proof(leaf_data, raw, expected_root)
    except ValueError as exc:
        print(f"Proof validation error: {exc}", file=sys.stderr)
        sys.exit(1)

    if result:
        print("[OK] Proof is VALID.")
    else:
        print("[FAIL] Proof is INVALID - computed root does not match.", file=sys.stderr)
        sys.exit(1)


# ------------------------------------------------------------------ #
#  Entry point
# ------------------------------------------------------------------ #


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    dispatch = {
        "root": cmd_root,
        "prove": cmd_prove,
        "verify": cmd_verify,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
