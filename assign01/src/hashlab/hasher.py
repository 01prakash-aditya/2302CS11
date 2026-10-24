from __future__ import annotations

import base64
import hashlib
from pathlib import Path

def hash_bytes(data: bytes) -> tuple[int, str, str]:
    digest = hashlib.sha256(data).digest()
    return len(data), digest.hex(), base64.b64encode(digest).decode("ascii")


def hash_file(filepath: str | Path, chunk_size: int = 65536) -> tuple[int, str, str]:
    # streams in chunks so memory stays bounded
    path = Path(filepath)
    if not path.is_file():
        if path.is_dir():
            raise IsADirectoryError(f"'{filepath}' is a directory, not a regular file.")
        raise FileNotFoundError(f"File not found: '{filepath}'")

    hasher = hashlib.sha256()
    total_bytes = 0

    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            total_bytes += len(chunk)
            hasher.update(chunk)

    digest = hasher.digest()
    return total_bytes, digest.hex(), base64.b64encode(digest).decode("ascii")

def parse_hex(hex_str: str) -> bytes:
    cleaned = hex_str.strip()
    if cleaned.startswith(("0x", "0X")):
        cleaned = cleaned[2:]
    cleaned = "".join(cleaned.split())

    if len(cleaned) % 2 != 0:
        raise ValueError(
            f"Invalid hex string: odd length ({len(cleaned)} digits). Hex strings must have an even number of characters."
        )

    try:
        return bytes.fromhex(cleaned)
    except ValueError as e:
        raise ValueError(f"Invalid hexadecimal input: {e}") from e