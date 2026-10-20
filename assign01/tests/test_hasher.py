import base64
import hashlib
import pytest
from hashlab.hasher import hash_bytes, hash_file, parse_hex


def test_hash_bytes_empty():
    length, hex_digest, b64_digest = hash_bytes(b"")
    assert length == 0
    assert hex_digest == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert b64_digest == "47DEQpj8HBSa+/TImW+5JCeuQeRkm5NMpJWZG3hSuFU="


def test_hash_bytes_nist_abc():
    data = b"abc"
    length, hex_digest, b64_digest = hash_bytes(data)
    assert length == 3
    assert hex_digest == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    raw_digest = hashlib.sha256(data).digest()
    assert b64_digest == base64.b64encode(raw_digest).decode("ascii")


def test_trailing_newline_distinction():
    text1 = "Alice pays Bob 10"
    text2 = "Alice pays Bob 10\n"
    text3 = "Alice pays Bob 10\r\n"

    len1, hex1, _ = hash_bytes(text1.encode("utf-8"))
    len2, hex2, _ = hash_bytes(text2.encode("utf-8"))
    len3, hex3, _ = hash_bytes(text3.encode("utf-8"))

    assert len1 == 17
    assert len2 == 18
    assert len3 == 19
    assert hex1 != hex2
    assert hex2 != hex3
    assert hex1 != hex3


def test_parse_hex_valid():
    assert parse_hex("416c696365") == b"Alice"
    assert parse_hex("0x416c696365") == b"Alice"
    assert parse_hex("0X416C696365") == b"Alice"
    assert parse_hex("41 6c 69 63 65") == b"Alice"
    assert parse_hex("  0x416c696365  ") == b"Alice"


def test_parse_hex_malformed():
    with pytest.raises(ValueError, match="odd length"):
        parse_hex("abc")

    with pytest.raises(ValueError, match="Invalid hex"):
        parse_hex("xyz123")

    with pytest.raises(ValueError, match="Invalid hex"):
        parse_hex("0xGG12")
