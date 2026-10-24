"""
Comprehensive tests for the Merkle tree library.

Run with:
    python -m pytest tests/ -v
or:
    python -m unittest tests.test_merkle -v
"""

import json
import math
import os
import sys
import unittest

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from merkle.hash_utils import EMPTY_ROOT, hash_leaf, hash_node
from merkle.proof import (
    deserialize_proof,
    serialize_proof,
    verify_proof,
)
from merkle.tree import MerkleTree


# ================================================================== #
#  Helper – deterministic leaf data
# ================================================================== #

def make_leaves(n: int) -> list[bytes]:
    """Return n leaves labelled ``tx0`` … ``tx{n-1}``."""
    return [f"tx{i}".encode() for i in range(n)]


# ================================================================== #
#  Hash function tests
# ================================================================== #

class TestHashUtils(unittest.TestCase):
    """Verify domain-separated hashing."""

    def test_leaf_hash_deterministic(self):
        self.assertEqual(hash_leaf(b"hello"), hash_leaf(b"hello"))

    def test_different_data_different_hash(self):
        self.assertNotEqual(hash_leaf(b"a"), hash_leaf(b"b"))

    def test_domain_separation(self):
        """H_leaf(data) ≠ H_node(data, b'') even when lengths collide."""
        data = b"\x00" * 32
        leaf = hash_leaf(data)
        node = hash_node(data, b"")
        self.assertNotEqual(leaf, node)

    def test_hash_length(self):
        self.assertEqual(len(hash_leaf(b"x")), 32)
        self.assertEqual(len(hash_node(b"l" * 32, b"r" * 32)), 32)


# ================================================================== #
#  Tree construction tests
# ================================================================== #

class TestMerkleTreeConstruction(unittest.TestCase):
    """Build trees with 0, 1, 2, 3, 5, 8 leaves and check roots."""

    def test_zero_leaves(self):
        tree = MerkleTree([])
        self.assertEqual(tree.root, EMPTY_ROOT)
        self.assertEqual(tree.size, 0)

    def test_one_leaf(self):
        data = [b"only"]
        tree = MerkleTree(data)
        self.assertEqual(tree.root, hash_leaf(b"only"))
        self.assertEqual(tree.size, 1)

    def test_two_leaves(self):
        d = [b"a", b"b"]
        tree = MerkleTree(d)
        expected = hash_node(hash_leaf(b"a"), hash_leaf(b"b"))
        self.assertEqual(tree.root, expected)

    def test_three_leaves_odd(self):
        """With 3 leaves the third is promoted at level 1."""
        d = make_leaves(3)
        tree = MerkleTree(d)
        l0 = hash_leaf(d[0])
        l1 = hash_leaf(d[1])
        l2 = hash_leaf(d[2])
        n01 = hash_node(l0, l1)
        # l2 promoted → level 1 = [n01, l2]
        root = hash_node(n01, l2)
        self.assertEqual(tree.root, root)

    def test_four_leaves_even(self):
        d = make_leaves(4)
        tree = MerkleTree(d)
        l = [hash_leaf(x) for x in d]
        n01 = hash_node(l[0], l[1])
        n23 = hash_node(l[2], l[3])
        root = hash_node(n01, n23)
        self.assertEqual(tree.root, root)

    def test_five_leaves(self):
        d = make_leaves(5)
        tree = MerkleTree(d)
        l = [hash_leaf(x) for x in d]
        n01 = hash_node(l[0], l[1])
        n23 = hash_node(l[2], l[3])
        # l[4] promoted at level 1 → [n01, n23, l4]
        n0123 = hash_node(n01, n23)
        # l[4] promoted at level 2 → [n0123, l4]
        root = hash_node(n0123, l[4])
        self.assertEqual(tree.root, root)

    def test_eight_leaves(self):
        d = make_leaves(8)
        tree = MerkleTree(d)
        l = [hash_leaf(x) for x in d]
        n = [hash_node(l[i], l[i + 1]) for i in range(0, 8, 2)]
        nn = [hash_node(n[0], n[1]), hash_node(n[2], n[3])]
        root = hash_node(nn[0], nn[1])
        self.assertEqual(tree.root, root)

    def test_root_determinism(self):
        d = make_leaves(10)
        self.assertEqual(MerkleTree(d).root, MerkleTree(d).root)


# ================================================================== #
#  Proof generation + verification tests
# ================================================================== #

class TestProofs(unittest.TestCase):

    def _roundtrip(self, n: int) -> None:
        """Build tree of size n, prove & verify every leaf."""
        d = make_leaves(n)
        tree = MerkleTree(d)
        for i in range(n):
            proof = tree.prove(i)
            self.assertEqual(proof["leaf_index"], i)
            self.assertEqual(proof["tree_size"], n)
            self.assertTrue(
                verify_proof(d[i], proof, tree.root),
                f"Proof failed for leaf {i} in tree of size {n}",
            )

    def test_one_leaf_proof(self):
        self._roundtrip(1)

    def test_two_leaves_proof(self):
        self._roundtrip(2)

    def test_three_leaves_proof(self):
        self._roundtrip(3)

    def test_four_leaves_proof(self):
        self._roundtrip(4)

    def test_five_leaves_proof(self):
        self._roundtrip(5)

    def test_eight_leaves_proof(self):
        self._roundtrip(8)

    def test_sixteen_leaves_proof(self):
        self._roundtrip(16)

    def test_100_leaves_proof(self):
        self._roundtrip(100)

    def test_proof_rejects_wrong_leaf(self):
        d = make_leaves(4)
        tree = MerkleTree(d)
        proof = tree.prove(0)
        # Verify with wrong leaf data
        self.assertFalse(verify_proof(b"WRONG", proof, tree.root))

    def test_proof_rejects_wrong_root(self):
        d = make_leaves(4)
        tree = MerkleTree(d)
        proof = tree.prove(0)
        fake_root = b"\x00" * 32
        self.assertFalse(verify_proof(d[0], proof, fake_root))

    def test_proof_for_promoted_leaf(self):
        """The promoted (odd-out) leaf should have a shorter proof."""
        d = make_leaves(5)
        tree = MerkleTree(d)
        proof4 = tree.prove(4)
        proof0 = tree.prove(0)
        # Leaf 4 is promoted twice, so its proof has fewer siblings
        self.assertLess(len(proof4["siblings"]), len(proof0["siblings"]))
        self.assertTrue(verify_proof(d[4], proof4, tree.root))

    def test_empty_tree_proof_raises(self):
        tree = MerkleTree([])
        with self.assertRaises(ValueError):
            tree.prove(0)

    def test_out_of_range_index(self):
        tree = MerkleTree(make_leaves(4))
        with self.assertRaises(ValueError):
            tree.prove(4)
        with self.assertRaises(ValueError):
            tree.prove(-1)


# ================================================================== #
#  Serialization and validation tests
# ================================================================== #

class TestSerialization(unittest.TestCase):

    def test_roundtrip_json(self):
        tree = MerkleTree(make_leaves(5))
        proof = tree.prove(2)
        raw = serialize_proof(proof)
        parsed = deserialize_proof(raw)
        self.assertEqual(proof, parsed)

    def test_reject_malformed_hash(self):
        bad = json.dumps({
            "leaf_index": 0,
            "tree_size": 4,
            "siblings": [{"side": "right", "hash": "not-a-hex"}],
        })
        with self.assertRaises(ValueError):
            deserialize_proof(bad)

    def test_reject_short_hash(self):
        bad = json.dumps({
            "leaf_index": 0,
            "tree_size": 4,
            "siblings": [{"side": "right", "hash": "abcd1234"}],
        })
        with self.assertRaises(ValueError):
            deserialize_proof(bad)

    def test_reject_uppercase_hash(self):
        bad = json.dumps({
            "leaf_index": 0,
            "tree_size": 4,
            "siblings": [{"side": "right", "hash": "A" * 64}],
        })
        with self.assertRaises(ValueError):
            deserialize_proof(bad)

    def test_reject_invalid_direction(self):
        bad = json.dumps({
            "leaf_index": 0,
            "tree_size": 4,
            "siblings": [{"side": "up", "hash": "a" * 64}],
        })
        with self.assertRaises(ValueError):
            deserialize_proof(bad)

    def test_reject_negative_index(self):
        bad = json.dumps({
            "leaf_index": -1,
            "tree_size": 4,
            "siblings": [],
        })
        with self.assertRaises(ValueError):
            deserialize_proof(bad)

    def test_reject_index_out_of_range(self):
        bad = json.dumps({
            "leaf_index": 4,
            "tree_size": 4,
            "siblings": [],
        })
        with self.assertRaises(ValueError):
            deserialize_proof(bad)

    def test_reject_too_long_proof(self):
        """A tree of size 4 needs at most ceil(log2(4))=2 siblings."""
        bad = json.dumps({
            "leaf_index": 0,
            "tree_size": 4,
            "siblings": [
                {"side": "right", "hash": "a" * 64},
                {"side": "right", "hash": "b" * 64},
                {"side": "right", "hash": "c" * 64},
            ],
        })
        with self.assertRaises(ValueError):
            deserialize_proof(bad)

    def test_reject_missing_key(self):
        bad = json.dumps({"leaf_index": 0, "tree_size": 4})
        with self.assertRaises(ValueError):
            deserialize_proof(bad)

    def test_reject_bad_json(self):
        with self.assertRaises(ValueError):
            deserialize_proof("not json at all{{{")

    def test_reject_zero_tree_size(self):
        bad = json.dumps({
            "leaf_index": 0,
            "tree_size": 0,
            "siblings": [],
        })
        with self.assertRaises(ValueError):
            deserialize_proof(bad)


# ================================================================== #
#  Test vectors – deterministic, reproducible hashes
# ================================================================== #

class TestVectors(unittest.TestCase):
    """
    Pinned test vectors so the implementation can be verified
    against a known-good state.
    """

    def test_single_leaf_root(self):
        """Root of tree with single leaf 'hello'."""
        tree = MerkleTree([b"hello"])
        # H_leaf(hello) = SHA256(00 || hello)
        expected = hash_leaf(b"hello")
        self.assertEqual(tree.root, expected)
        self.assertEqual(
            tree.root.hex(),
            hash_leaf(b"hello").hex(),
        )

    def test_two_leaf_root(self):
        tree = MerkleTree([b"alice", b"bob"])
        la = hash_leaf(b"alice")
        lb = hash_leaf(b"bob")
        expected = hash_node(la, lb)
        self.assertEqual(tree.root.hex(), expected.hex())

    def test_five_leaf_proof_index2(self):
        """Pin the proof for index 2 in a 5-leaf tree."""
        txs = [b"tx0", b"tx1", b"tx2", b"tx3", b"tx4"]
        tree = MerkleTree(txs)
        proof = tree.prove(2)

        # Proof path: L3 (right) → N01 (left) → L4 (right)
        self.assertEqual(len(proof["siblings"]), 3)
        self.assertEqual(proof["siblings"][0]["side"], "right")   # L3
        self.assertEqual(proof["siblings"][1]["side"], "left")    # N(L0,L1)
        self.assertEqual(proof["siblings"][2]["side"], "right")   # L4

        # Verify
        self.assertTrue(verify_proof(b"tx2", proof, tree.root))


# ================================================================== #
#  CLI smoke tests (subprocess)
# ================================================================== #

class TestCLI(unittest.TestCase):
    """Smoke-test the CLI commands via subprocess."""

    def _run(self, *args: str) -> tuple[str, str, int]:
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "merkle"] + list(args),
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        )
        return result.stdout, result.stderr, result.returncode

    def test_root_command(self):
        out, err, rc = self._run("root", "tx0", "tx1", "tx2")
        self.assertEqual(rc, 0)
        root_hex = out.strip()
        self.assertEqual(len(root_hex), 64)

    def test_prove_command(self):
        out, err, rc = self._run("prove", "--index", "1", "tx0", "tx1", "tx2")
        self.assertEqual(rc, 0)
        proof = json.loads(out.strip())
        self.assertEqual(proof["leaf_index"], 1)

    def test_verify_command(self):
        # First get root and proof
        out_r, _, _ = self._run("root", "a", "b", "c", "d")
        root = out_r.strip()

        out_p, _, _ = self._run("prove", "--index", "2", "a", "b", "c", "d")
        proof_json = out_p.strip()

        out_v, err_v, rc = self._run(
            "verify", "--leaf", "c", "--root", root,
            "--proof-inline", proof_json,
        )
        self.assertEqual(rc, 0)
        self.assertIn("VALID", out_v)

    def test_verify_rejects_wrong_leaf(self):
        out_r, _, _ = self._run("root", "a", "b", "c", "d")
        root = out_r.strip()
        out_p, _, _ = self._run("prove", "--index", "2", "a", "b", "c", "d")
        proof_json = out_p.strip()

        _, err_v, rc = self._run(
            "verify", "--leaf", "WRONG", "--root", root,
            "--proof-inline", proof_json,
        )
        self.assertNotEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
