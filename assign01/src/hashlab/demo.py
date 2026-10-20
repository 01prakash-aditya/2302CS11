from __future__ import annotations

import unicodedata
from typing import NamedTuple

from hashlab.canonical import canonicalize_json, hash_canonical_json
from hashlab.hasher import hash_bytes


class DemoResult(NamedTuple):
    case_name: str
    description: str
    items: list[dict[str, str | int]]
    conclusion: str


def run_newline_demo() -> DemoResult:
    text = "Alice pays Bob 10"
    v_none = text.encode("utf-8")
    v_lf = (text + "\n").encode("utf-8")
    v_crlf = (text + "\r\n").encode("utf-8")

    items = [
        {
            "variant": "No newline",
            "escaped_repr": repr(text),
            "byte_len": len(v_none),
            "hex_bytes": v_none.hex(),
            "sha256": hash_bytes(v_none)[1],
        },
        {
            "variant": "LF (\\n, Unix)",
            "escaped_repr": repr(text + "\n"),
            "byte_len": len(v_lf),
            "hex_bytes": v_lf.hex(),
            "sha256": hash_bytes(v_lf)[1],
        },
        {
            "variant": "CRLF (\\r\\n, Windows)",
            "escaped_repr": repr(text + "\r\n"),
            "byte_len": len(v_crlf),
            "hex_bytes": v_crlf.hex(),
            "sha256": hash_bytes(v_crlf)[1],
        },
    ]

    conclusion = (
        "Even though text editors often display them identically, invisible newline characters "
        "change the input byte length and completely alter the SHA-256 digest."
    )
    return DemoResult(
        case_name="1. Newline Differences",
        description="Comparing identical visible text with no newline, Unix LF (\\n), and Windows CRLF (\\r\\n).",
        items=items,
        conclusion=conclusion,
    )


def run_unicode_demo() -> DemoResult:
    word = "café"
    nfc = unicodedata.normalize("NFC", word)
    nfd = unicodedata.normalize("NFD", word)

    b_nfc = nfc.encode("utf-8")
    b_nfd = nfd.encode("utf-8")

    codepoints_nfc = " ".join(f"U+{ord(c):04X}" for c in nfc)
    codepoints_nfd = " ".join(f"U+{ord(c):04X}" for c in nfd)

    items = [
        {
            "variant": "NFC (Composed)",
            "visible": nfc,
            "codepoints": codepoints_nfc,
            "byte_len": len(b_nfc),
            "hex_bytes": b_nfc.hex(),
            "sha256": hash_bytes(b_nfc)[1],
        },
        {
            "variant": "NFD (Decomposed)",
            "visible": nfd,
            "codepoints": codepoints_nfd,
            "byte_len": len(b_nfd),
            "hex_bytes": b_nfd.hex(),
            "sha256": hash_bytes(b_nfd)[1],
        },
    ]

    conclusion = (
        "Both strings render identically on screen as 'café', but NFC stores 'é' as a single code "
        "point (U+00E9, 2 UTF-8 bytes) while NFD decomposes it into 'e' + combining accent (U+0065 U+0301, "
        "3 UTF-8 bytes). This produces totally different cryptographic digests."
    )
    return DemoResult(
        case_name="2. Unicode Normalization",
        description="Comparing pre-composed Unicode (NFC) with decomposed combining characters (NFD).",
        items=items,
        conclusion=conclusion,
    )


def run_integer_vs_string_demo() -> DemoResult:
    raw_int = '{"amount":100}'.encode("utf-8")
    raw_str = '{"amount":"100"}'.encode("utf-8")

    items = [
        {
            "variant": "Integer value 100",
            "json_payload": '{"amount": 100}',
            "raw_bytes_str": '{"amount":100}',
            "byte_len": len(raw_int),
            "hex_bytes": raw_int.hex(),
            "sha256": hash_bytes(raw_int)[1],
        },
        {
            "variant": "String value \"100\"",
            "json_payload": '{"amount": "100"}',
            "raw_bytes_str": '{"amount":"100"}',
            "byte_len": len(raw_str),
            "hex_bytes": raw_str.hex(),
            "sha256": hash_bytes(raw_str)[1],
        },
    ]

    conclusion = (
        "Although the number 100 looks identical to the human eye, the string representation "
        "adds quotes ('\"'), changing the byte count and generating a completely different hash. "
        "In blockchain protocols, type strictness is critical to avoid signature invalidation."
    )
    return DemoResult(
        case_name="3. Integer vs String Representation",
        description="Comparing JSON data where an amount is encoded as a numerical integer versus a string.",
        items=items,
        conclusion=conclusion,
    )


def run_key_order_demo() -> DemoResult:
    raw_json_1 = '{"sender":"Alice","amount":10}'
    raw_json_2 = '{"amount":10,"sender":"Alice"}'

    b1 = raw_json_1.encode("utf-8")
    b2 = raw_json_2.encode("utf-8")

    canon1_str, len1, hex1, _ = hash_canonical_json(raw_json_1)
    canon2_str, len2, hex2, _ = hash_canonical_json(raw_json_2)

    items = [
        {
            "variant": "Order 1 (sender, amount)",
            "raw_text": raw_json_1,
            "raw_sha256": hash_bytes(b1)[1],
            "canonical_text": canon1_str,
            "canonical_sha256": hex1,
        },
        {
            "variant": "Order 2 (amount, sender)",
            "raw_text": raw_json_2,
            "raw_sha256": hash_bytes(b2)[1],
            "canonical_text": canon2_str,
            "canonical_sha256": hex2,
        },
    ]

    conclusion = (
        "In raw text, JSON key permutation produces different byte sequences and different SHA-256 "
        "hashes. Canonical JSON sorts the keys deterministically, ensuring that both orders produce "
        "the exact same canonical bytes and identical SHA-256 digest."
    )
    return DemoResult(
        case_name="4. Key Order & Canonical JSON",
        description="Comparing different dictionary key orders in raw JSON versus canonical JSON.",
        items=items,
        conclusion=conclusion,
    )


def format_demo_result(res: DemoResult) -> str:
    lines = [
        f"=== {res.case_name} ===",
        res.description,
        "",
    ]
    for item in res.items:
        lines.append(f"  [{item['variant']}]")
        for k, v in item.items():
            if k != "variant":
                lines.append(f"    {k}: {v}")
        lines.append("")

    lines.append(f"  Conclusion: {res.conclusion}")
    lines.append("=" * 60)
    return "\n".join(lines)


def run_all_demos() -> list[DemoResult]:
    return [
        run_newline_demo(),
        run_unicode_demo(),
        run_integer_vs_string_demo(),
        run_key_order_demo(),
    ]
