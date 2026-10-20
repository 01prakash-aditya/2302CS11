from __future__ import annotations

import hashlib
from pathlib import Path

from hashlab.hasher import hash_bytes, hash_file


def flip_bit(data: bytes, bit_index: int) -> bytes:
    # bits indexed 0-based big-endian: bit 0 = MSB of byte 0
    total_bits = len(data) * 8
    if total_bits == 0:
        raise ValueError("Cannot flip bit in empty input (0 bytes).")
    if bit_index < 0 or bit_index >= total_bits:
        raise ValueError(
            f"Bit index {bit_index} is out of bounds for input of length "
            f"{len(data)} bytes ({total_bits} bits, valid indices: 0 to {total_bits - 1})."
        )

    byte_idx = bit_index // 8
    bit_in_byte = 7 - (bit_index % 8)
    mask = 1 << bit_in_byte

    buf = bytearray(data)
    buf[byte_idx] ^= mask
    return bytes(buf)


def hamming_distance(digest1: bytes, digest2: bytes) -> int:
    if len(digest1) != len(digest2):
        raise ValueError(
            f"Digests must have the same length: got {len(digest1)} and {len(digest2)} bytes."
        )
    diff = int.from_bytes(digest1, "big") ^ int.from_bytes(digest2, "big")
    return bin(diff).count("1")


def compute_avalanche_bytes(data: bytes, bit_index: int) -> tuple[str, str, int]:
    flipped = flip_bit(data, bit_index)
    digest1 = hashlib.sha256(data).digest()
    digest2 = hashlib.sha256(flipped).digest()
    return digest1.hex(), digest2.hex(), hamming_distance(digest1, digest2)


def compute_avalanche_file(
    filepath: str | Path, bit_index: int, chunk_size: int = 65536
) -> tuple[str, str, int]:
    # streams file, flips the target bit on-the-fly in the modified hasher
    path = Path(filepath)
    if not path.is_file():
        if path.is_dir():
            raise IsADirectoryError(f"'{filepath}' is a directory, not a regular file.")
        raise FileNotFoundError(f"File not found: '{filepath}'")

    file_size = path.stat().st_size
    total_bits = file_size * 8

    if total_bits == 0:
        raise ValueError("Cannot flip bit in empty file (0 bytes).")
    if bit_index < 0 or bit_index >= total_bits:
        raise ValueError(
            f"Bit index {bit_index} is out of bounds for file of length "
            f"{file_size} bytes ({total_bits} bits, valid indices: 0 to {total_bits - 1})."
        )

    target_byte_idx = bit_index // 8
    bit_in_byte = 7 - (bit_index % 8)
    mask = 1 << bit_in_byte

    hasher_orig = hashlib.sha256()
    hasher_mod = hashlib.sha256()

    current_offset = 0
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            chunk_len = len(chunk)
            hasher_orig.update(chunk)

            # flip the bit if target byte is in this chunk
            if current_offset <= target_byte_idx < current_offset + chunk_len:
                local_idx = target_byte_idx - current_offset
                mod_chunk = bytearray(chunk)
                mod_chunk[local_idx] ^= mask
                hasher_mod.update(mod_chunk)
            else:
                hasher_mod.update(chunk)

            current_offset += chunk_len

    digest_orig = hasher_orig.digest()
    digest_mod = hasher_mod.digest()

    return (
        digest_orig.hex(),
        digest_mod.hex(),
        hamming_distance(digest_orig, digest_mod),
    )
