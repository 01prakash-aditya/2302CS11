"""
Merkle Tree construction.

Handles zero, one, odd, and even numbers of leaves.
When the number of nodes at a level is odd, the unpaired last node
is *promoted* to the next level without re-hashing (no duplication).
"""

from __future__ import annotations

import math
from typing import List, Optional

from merkle.hash_utils import hash_leaf, hash_node, EMPTY_ROOT


class MerkleTree:
    """
    A binary Merkle tree built from a list of raw leaf data.

    Attributes
    ----------
    leaves : list[bytes]
        Original leaf data supplied at construction time.
    leaf_hashes : list[bytes]
        Domain-separated SHA-256 hashes of each leaf.
    levels : list[list[bytes]]
        All tree levels, from leaves (index 0) up to the root.
    """

    def __init__(self, leaves: List[bytes]) -> None:
        """
        Build a Merkle tree from raw leaf data.

        Parameters
        ----------
        leaves : list[bytes]
            Each element is the raw data for one leaf (e.g., a transaction).
        """
        self.leaves: List[bytes] = list(leaves)
        self.leaf_hashes: List[bytes] = [hash_leaf(d) for d in self.leaves]
        self.levels: List[List[bytes]] = self._build()

    # ------------------------------------------------------------------ #
    #  Construction
    # ------------------------------------------------------------------ #

    def _build(self) -> List[List[bytes]]:
        """
        Build all tree levels bottom-up.

        Returns
        -------
        list[list[bytes]]
            ``levels[0]`` = leaf hashes, ``levels[-1]`` = [root].
            For an empty tree, returns ``[[]]``.
        """
        if not self.leaf_hashes:
            return [[]]

        levels: List[List[bytes]] = [self.leaf_hashes[:]]
        current = self.leaf_hashes[:]

        while len(current) > 1:
            next_level: List[bytes] = []
            i = 0
            while i + 1 < len(current):
                next_level.append(hash_node(current[i], current[i + 1]))
                i += 2
            # Odd node out → promote without re-hashing
            if len(current) % 2 == 1:
                next_level.append(current[-1])
            current = next_level
            levels.append(current)

        return levels

    # ------------------------------------------------------------------ #
    #  Properties
    # ------------------------------------------------------------------ #

    @property
    def root(self) -> bytes:
        """
        The Merkle root hash.

        Returns ``EMPTY_ROOT`` (= H_leaf(b'')) for an empty tree.
        """
        if not self.levels or not self.levels[-1]:
            return EMPTY_ROOT
        return self.levels[-1][0]

    @property
    def size(self) -> int:
        """Number of leaves in the tree."""
        return len(self.leaves)

    @property
    def height(self) -> int:
        """
        Number of levels (edges) from a leaf to the root.

        An empty or single-leaf tree has height 0.
        """
        if self.size <= 1:
            return 0
        return math.ceil(math.log2(self.size))

    # ------------------------------------------------------------------ #
    #  Proof generation
    # ------------------------------------------------------------------ #

    def prove(self, leaf_index: int) -> dict:
        """
        Generate an inclusion proof for the leaf at *leaf_index*.

        Parameters
        ----------
        leaf_index : int
            Zero-based index of the target leaf.

        Returns
        -------
        dict
            Proof dictionary with keys ``leaf_index``, ``tree_size``,
            and ``siblings`` (list of ``{side, hash}`` dicts).

        Raises
        ------
        ValueError
            If *leaf_index* is out of range or the tree is empty.
        """
        if self.size == 0:
            raise ValueError("Cannot generate a proof for an empty tree")
        if not (0 <= leaf_index < self.size):
            raise ValueError(
                f"leaf_index {leaf_index} out of range [0, {self.size})"
            )

        siblings: List[dict] = []
        idx = leaf_index

        for level_idx in range(len(self.levels) - 1):
            level = self.levels[level_idx]

            if idx % 2 == 0:
                # Current node is a left child
                if idx + 1 < len(level):
                    siblings.append(
                        {"side": "right", "hash": level[idx + 1].hex()}
                    )
                # else: promoted — no sibling at this level
            else:
                # Current node is a right child
                siblings.append(
                    {"side": "left", "hash": level[idx - 1].hex()}
                )

            idx //= 2

        return {
            "leaf_index": leaf_index,
            "tree_size": self.size,
            "siblings": siblings,
        }
