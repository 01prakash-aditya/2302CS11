from pathlib import Path
import pytest
from hashlab.cli import main


def test_cli_text_mode(capsys):
    ret = main(["text", "Alice pays Bob 10"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "bytes: 17" in captured.out
    assert "sha256: 69ad18dfd1ac4b3d711b02ee62caa00a82f0f67cc11ebacdd0c0ede0d8b6eaed" in captured.out
    assert "base64:" in captured.out


def test_cli_hex_mode_valid(capsys):
    ret = main(["hex", "416c696365"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "bytes: 5" in captured.out
    assert "sha256: 3bc51062973c458d5a6f2d8d64a023246354ad7e064b1e4e009ec8a0699a3043" in captured.out


def test_cli_hex_mode_malformed(capsys):
    ret = main(["hex", "xyz"])
    assert ret == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err


def test_cli_file_mode(tmp_path: Path, capsys):
    f = tmp_path / "test.txt"
    f.write_text("hello", encoding="utf-8")
    ret = main(["file", str(f)])
    assert ret == 0
    captured = capsys.readouterr()
    assert "bytes: 5" in captured.out
    assert "sha256: 2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824" in captured.out


def test_cli_avalanche_mode(capsys):
    ret = main(["avalanche", "--text", "Alice pays Bob 10", "--bit", "7"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "original_sha256:" in captured.out
    assert "modified_sha256:" in captured.out
    assert "changed_bits_in_digest:" in captured.out


def test_cli_canonical_json_mode(capsys):
    ret = main(["canonical-json", '{"b": 2, "a": 1}'])
    assert ret == 0
    captured = capsys.readouterr()
    assert 'canonical_json: {"a":1,"b":2}' in captured.out
    assert "bytes: 13" in captured.out
    assert "sha256: 43258cff783fe7036d8a43033f830adfc60ec037382473548ac742b888292777" in captured.out


def test_cli_demo_mode(capsys):
    ret = main(["demo", "--newlines"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Newline Differences" in captured.out
