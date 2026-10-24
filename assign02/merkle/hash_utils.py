"""
Domain-separated hash functions for the Merkle tree.

Specification
-------------
- H_leaf(data) = SHA-256(0x00 || data)
- H_node(left, right) = SHA-256(0x01 || left || right)

The single-byte domain-separation prefix prevents second-preimage attacks
that confuse leaf data with internal node concatenations.
"""

import hashlib

# Domain separation prefixes
LEAF_PREFIX = b"\x00"
NODE_PREFIX = b"\x01"


def hash_leaf(data: bytes) -> bytes:
    """
    Compute the leaf hash: SHA-256(0x00 || data).

    Parameters
    ----------
    data : bytes
        Raw transaction / leaf data.

    Returns
    -------
    bytes
        32-byte SHA-256 digest.
    """
    return hashlib.sha256(LEAF_PREFIX + data).digest()


def hash_node(left: bytes, right: bytes) -> bytes:
    """
    Compute the internal-node hash: SHA-256(0x01 || left || right).

    Parameters
    ----------
    left : bytes
        32-byte hash of the left child.
    right : bytes
        32-byte hash of the right child.

    Returns
    -------
    bytes
        32-byte SHA-256 digest.
    """
    return hashlib.sha256(NODE_PREFIX + left + right).digest()


# The root of an empty tree (zero leaves) is defined as H_leaf(b"").
EMPTY_ROOT = hash_leaf(b"")
