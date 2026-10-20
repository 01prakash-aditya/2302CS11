import hashlib
import tracemalloc
from pathlib import Path
import pytest
from hashlab.avalanche import compute_avalanche_file
from hashlab.hasher import hash_file


def test_streaming_matches_hashlib(tmp_path: Path):
    test_file = tmp_path / "sample.txt"
    content = b"The quick brown fox jumps over the lazy dog\n" * 1000
    test_file.write_bytes(content)

    expected_hash = hashlib.sha256(content).hexdigest()
    total_bytes, hex_digest, b64_digest = hash_file(test_file, chunk_size=128)

    assert total_bytes == len(content)
    assert hex_digest == expected_hash


def test_100mb_streaming_memory_efficiency(tmp_path: Path):
    file_path = tmp_path / "large_100mb.bin"

    one_mb = b"A" * (1024 * 1024)
    expected_hasher = hashlib.sha256()
    with file_path.open("wb") as f:
        for _ in range(100):
            f.write(one_mb)
            expected_hasher.update(one_mb)

    expected_hex = expected_hasher.hexdigest()

    tracemalloc.start()
    tracemalloc.reset_peak()

    total_bytes, hex_digest, _ = hash_file(file_path, chunk_size=65536)

    _, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert total_bytes == 100 * 1024 * 1024
    assert hex_digest == expected_hex

    # should stay well under 5 MB, nowhere near 100 MB
    peak_mb = peak_memory / (1024 * 1024)
    assert peak_mb < 5.0, f"Peak memory grew excessively: {peak_mb:.2f} MB"


def test_streaming_file_avalanche(tmp_path: Path):
    test_file = tmp_path / "avalanche_sample.bin"
    data = b"Alice pays Bob 10"
    test_file.write_bytes(data)

    orig_hex, mod_hex, changed = compute_avalanche_file(test_file, bit_index=7)
    assert orig_hex != mod_hex
    assert 70 <= changed <= 190


def test_file_not_found(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        hash_file(tmp_path / "non_existent.bin")
