from hashlab.demo import (
    format_demo_result,
    run_all_demos,
    run_integer_vs_string_demo,
    run_key_order_demo,
    run_newline_demo,
    run_unicode_demo,
)


def test_newline_demo():
    res = run_newline_demo()
    assert res.case_name.startswith("1. Newline")
    assert len(res.items) == 3
    hashes = [item["sha256"] for item in res.items]
    assert len(set(hashes)) == 3
    assert "Conclusion:" in format_demo_result(res)


def test_unicode_demo():
    res = run_unicode_demo()
    assert res.case_name.startswith("2. Unicode")
    assert len(res.items) == 2
    hashes = [item["sha256"] for item in res.items]
    assert hashes[0] != hashes[1]
    byte_lens = [item["byte_len"] for item in res.items]
    assert byte_lens[0] == 5   # NFC
    assert byte_lens[1] == 6   # NFD


def test_integer_vs_string_demo():
    res = run_integer_vs_string_demo()
    assert res.case_name.startswith("3. Integer")
    assert len(res.items) == 2
    assert res.items[0]["sha256"] != res.items[1]["sha256"]


def test_key_order_demo():
    res = run_key_order_demo()
    assert res.case_name.startswith("4. Key Order")
    assert len(res.items) == 2
    assert res.items[0]["raw_sha256"] != res.items[1]["raw_sha256"]
    assert res.items[0]["canonical_sha256"] == res.items[1]["canonical_sha256"]


def test_run_all_demos():
    assert len(run_all_demos()) == 4
