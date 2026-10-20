import pytest
from hashlab.canonical import (
    canonicalize_json,
    canonicalize_raw_json,
    hash_canonical_json,
    parse_json,
)


def test_canonicalize_key_sorting():
    raw1 = '{"z": 1, "a": 2, "m": 3}'
    raw2 = '{"a": 2, "m": 3, "z": 1}'
    raw3 = '{\n  "m": 3,\n  "z": 1,\n  "a": 2\n}'

    c1_bytes, c1_str = canonicalize_raw_json(raw1)
    c2_bytes, c2_str = canonicalize_raw_json(raw2)
    c3_bytes, c3_str = canonicalize_raw_json(raw3)

    expected = '{"a":2,"m":3,"z":1}'
    assert c1_str == expected
    assert c2_str == expected
    assert c3_str == expected
    assert c1_bytes == c2_bytes == c3_bytes


def test_canonicalize_nested():
    data = {
        "user": {"name": "Alice", "id": 101},
        "tags": ["b", "a"],
        "active": True,
    }
    canon_bytes = canonicalize_json(data)
    # keys sorted, array order preserved
    expected = b'{"active":true,"tags":["b","a"],"user":{"id":101,"name":"Alice"}}'
    assert canon_bytes == expected


def test_canonicalize_utf8():
    data = {"greeting": "héllo", "emoji": "🚀"}
    canon_bytes = canonicalize_json(data)
    canon_str = canon_bytes.decode("utf-8")
    assert "héllo" in canon_str
    assert "🚀" in canon_str


def test_hash_canonical_json_identical_for_differing_whitespace_and_order():
    j1 = '{"b": 20, "a": 10}'
    j2 = '{\n  "a":   10,\n  "b": 20\n}'

    s1, len1, hex1, b64_1 = hash_canonical_json(j1)
    s2, len2, hex2, b64_2 = hash_canonical_json(j2)

    assert s1 == s2 == '{"a":10,"b":20}'
    assert len1 == len2
    assert hex1 == hex2
    assert b64_1 == b64_2


def test_canonicalize_invalid_json():
    with pytest.raises(ValueError, match="Invalid JSON"):
        canonicalize_raw_json("{invalid json}")

    with pytest.raises(ValueError, match="Invalid JSON"):
        parse_json('{"a": 1,}')
