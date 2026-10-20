"""
canonicalization rules (rfc 8785 style):
1. keys sorted lexicographically by unicode code points
2. no whitespace outside strings; separators are ',' and ':'
3. utf-8 encoded, no BOM
4. integers without decimals/exponents; NaN/Infinity rejected
5. identical json structures always produce identical bytes
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hashlab.hasher import hash_bytes


def canonicalize_json(data: Any) -> bytes:
    try:
        serialized = json.dumps(
            data,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except ValueError as e:
        raise ValueError(f"Canonical JSON serialization failed: {e}") from e

    return serialized.encode("utf-8")


def parse_json(raw_input: str | bytes) -> Any:
    if isinstance(raw_input, bytes):
        try:
            raw_input = raw_input.decode("utf-8")
        except UnicodeDecodeError as e:
            raise ValueError(f"Input is not valid UTF-8 text: {e}") from e

    try:
        return json.loads(raw_input)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON syntax at line {e.lineno}, column {e.colno}: {e.msg}") from e


def canonicalize_raw_json(raw_input: str | bytes) -> tuple[bytes, str]:
    parsed = parse_json(raw_input)
    canonical_bytes = canonicalize_json(parsed)
    canonical_str = canonical_bytes.decode("utf-8")
    return canonical_bytes, canonical_str


def hash_canonical_json(raw_input: str | bytes) -> tuple[str, int, str, str]:
    canonical_bytes, canonical_str = canonicalize_raw_json(raw_input)
    byte_len, hex_digest, b64_digest = hash_bytes(canonical_bytes)
    return canonical_str, byte_len, hex_digest, b64_digest
