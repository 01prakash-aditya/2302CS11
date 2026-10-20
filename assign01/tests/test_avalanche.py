import pytest
from hashlab.avalanche import (
    compute_avalanche_bytes,
    flip_bit,
    hamming_distance,
)


def test_flip_bit():
    # 'A' = 0x41 = 0b01000001
    data = b"A"
    assert flip_bit(data, 0) == b"\xc1"   # flip MSB
    assert flip_bit(data, 7) == b"@"      # flip LSB


def test_flip_bit_multi_byte():
    data = b"AB"
    flipped = flip_bit(data, 8)  # MSB of second byte
    assert flipped[0] == ord("A")
    assert flipped[1] == 0b11000010


def test_flip_bit_out_of_bounds():
    with pytest.raises(ValueError, match="empty input"):
        flip_bit(b"", 0)

    with pytest.raises(ValueError, match="out of bounds"):
        flip_bit(b"A", -1)

    with pytest.raises(ValueError, match="out of bounds"):
        flip_bit(b"A", 8)


def test_hamming_distance():
    d1 = bytes([0x00] * 32)
    d2 = bytes([0x00] * 32)
    assert hamming_distance(d1, d2) == 0

    d3 = bytes([0xFF] * 32)
    assert hamming_distance(d1, d3) == 256

    d4 = bytearray([0x00] * 32)
    d4[0] = 0x01
    assert hamming_distance(d1, bytes(d4)) == 1

    with pytest.raises(ValueError, match="same length"):
        hamming_distance(bytes(10), bytes(20))


def test_avalanche_effect():
    text = "Alice pays Bob 10"
    orig_hex, mod_hex, changed = compute_avalanche_bytes(text.encode("utf-8"), 7)
    assert orig_hex != mod_hex
    # expect ~128 bits to flip (50%), use wide bounds
    assert 70 <= changed <= 190
