# Assignment 1: Bytes, Hashes, and Reproducible Data (`hashlab`)

## Overview

In blockchain systems, consensus and immutability do not begin with tokens or coins—they begin with **bytes**, **encodings**, **canonical data representation**, and **cryptographic hash functions**.

`hashlab` is a command-line tool built in Python 3.11+ using the trusted standard-library implementation of SHA-256 (`hashlib.sha256`). It provides cryptographic diagnostics, demonstrates strict byte correctness and determinism, simulates the avalanche effect, enforces deterministic JSON canonicalization, and processes files of arbitrary size as streams without loading them into memory.

---

## Repository Structure

```text
assign01/
├── pyproject.toml         # Build configuration and CLI script entrypoint
├── requirements.txt       # Reproducible dependencies (pytest)
├── README.md              # Documentation and execution instructions
├── hashlab.py             # Root runner script (python hashlab.py ...)
├── .gitignore             # Separates build artifacts and virtualenvs from source
├── src/
│   └── hashlab/
│       ├── __init__.py    # Package initialization
│       ├── cli.py         # Command-line interface and argument parsing
│       ├── hasher.py      # Byte hashing, streaming file hasher, hex parser
│       ├── avalanche.py   # Bit flipping and Hamming distance analysis
│       ├── canonical.py   # Deterministic canonical JSON serialization & hashing
│       └── demo.py        # Visual difference demos (newlines, Unicode, types, keys)
└── tests/
    ├── test_hasher.py     # Tests for hex, empty/NIST vectors, trailing newlines
    ├── test_avalanche.py  # Tests for bit flipping, bounds, and Hamming distance
    ├── test_canonical.py  # Tests for canonical JSON ordering and rules
    ├── test_demo.py       # Tests for visual difference demonstration cases
    ├── test_streaming.py  # Tests for 100 MB file streaming and memory bounds
    └── test_cli.py        # End-to-end CLI command tests
```

---

## Setup & Installation

### Prerequisites
- Python 3.11 or higher
- `pip`

### Step 1: Create and Activate Virtual Environment

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
pip install -e .
```

After installation, the tool is available as the command `hashlab`.  
Alternatively, you can run the tool directly without installation via:
```bash
python hashlab.py <command> [options]
# or
python -m hashlab <command> [options]
```

---

## Commands & Usage

### 1. Text Mode (`hashlab text`)
Hashes an input string interpreted strictly as UTF-8 bytes.

```bash
hashlab text "Alice pays Bob 10"
```
**Output:**
```text
bytes: 17
sha256: 69ad18dfd1ac4b3d711b02ee62caa00a82f0f67cc11ebacdd0c0ede0d8b6eaed
base64: aa0Y39GsSz1xGwLuYsqgCoLw9nzBHrrN0MDt4Ni26u0=
```

---

### 2. Hex Mode (`hashlab hex`)
Decodes a hexadecimal string into raw bytes before hashing.
- Strips optional `0x` or `0X` prefix and whitespace.
- Rejects malformed hex (odd length, invalid characters) with a non-zero exit code.

```bash
hashlab hex 416c696365
```
**Output:**
```text
bytes: 5
sha256: 3bc51062973c458d5a6f2d8d64a023246354ad7e064b1e4e009ec8a0699a3043
base64: O8UQYpc8RY1aby2NZKAjJGNUrX4GSx5OAJ7IoGmaMEM=
```

**Malformed Hex Rejection Example:**
```bash
hashlab hex xyz
# Output: Error: Invalid hex string: odd length (3 digits). Hex strings must have an even number of characters.
```

---

### 3. File Mode (`hashlab file`)
Streams a file in chunks (default 64 KB) to compute byte length and SHA-256 digests. Memory usage remains constant ($O(1)$) regardless of whether the file is 10 KB or 100 GB.

```bash
hashlab file path/to/data.bin
```
**Output:**
```text
bytes: 104857600
sha256: <64-character hexadecimal digest>
base64: <44-character base64 digest>
```

---

### 4. Avalanche Command (`hashlab avalanche`)
Flips a single selected bit in the input and computes the **Hamming distance** (the number of differing bits) between the original and modified 256-bit digests.

- Bit indexing is 0-based in big-endian network byte order:
  - Byte index: `bit // 8`
  - Bit position within byte: `7 - (bit % 8)` (where bit 0 is MSB `0x80` and bit 7 is LSB `0x01`).

```bash
hashlab avalanche --text "Alice pays Bob 10" --bit 7
```
**Output:**
```text
original_sha256: 69ad18dfd1ac4b3d711b02ee62caa00a82f0f67cc11ebacdd0c0ede0d8b6eaed
modified_sha256: effa3a722595f51264a12287702bfeb91e885a703d399a2c74c991a1fd57bcce
changed_bits_in_digest: 119
```
*Note:* In an ideal cryptographic hash function, changing 1 input bit causes each output bit to flip with probability $p = 0.5$. Out of 256 bits, an average of 128 bits flip. Here, flipping bit 7 resulted in 119 bits changing (~46.5%), confirming strong diffusion.

The `avalanche` command also accepts `--hex` and `--file` inputs. For files, the bit flip is performed on-the-fly during chunked streaming, maintaining constant memory.

---

### 5. Canonical JSON Mode (`hashlab canonical-json`)
Parses a JSON object, formats it deterministically using documented canonicalization rules, and hashes the resulting UTF-8 bytes.

```bash
hashlab canonical-json '{"b": 2, "a": 1}'
```
**Output:**
```text
canonical_json: {"a":1,"b":2}
bytes: 13
sha256: 43258cff783fe7036d8a43033f830adfc60ec037382473548ac742b888292777
base64: QyWM/3g/5wNtikMDP4MK38YOwDc4JHNUisdCuIgpJ3c=
```

#### Documented Canonicalization Rules (RFC 8785 Scheme):
1. **Key Sorting**: Dictionary/object keys are sorted recursively in lexicographical order by Unicode code points.
2. **Whitespace Suppression**: No whitespace is permitted outside of string literals (separators are strictly `','` between elements and `':'` between keys and values).
3. **Encoding**: Encoded strictly in UTF-8 without Byte Order Mark (BOM).
4. **Number Formatting**: Integers are rendered without decimals or exponent notation. Non-finite values (`NaN`, `Infinity`) are strictly rejected.
5. **Determinism**: Any two semantically identical JSON objects with differing whitespace, formatting, or initial key orders produce the exact same canonical bytes and identical SHA-256 hash.

---

### 6. Visual Differences Demonstration (`hashlab demo`)
Demonstrates that inputs which appear identical to humans produce distinct byte sequences and completely different hashes:

```bash
hashlab demo
```

Run specific demonstration categories:
- `hashlab demo --newlines`: Unix LF (`\n`) vs Windows CRLF (`\r\n`) vs no newline.
- `hashlab demo --unicode`: Unicode Normalization Form C (NFC, composed `é` = 2 bytes) vs Normalization Form D (NFD, decomposed `e` + accent = 3 bytes).
- `hashlab demo --types`: Numerical integer `100` (14 bytes payload) vs string `"100"` (16 bytes payload).
- `hashlab demo --keys`: Key permutations in raw JSON (different hashes) versus canonical JSON (converges to identical hash).

---

## Running the Automated Test Suite

Run all unit, integration, and streaming tests using `pytest`:

```bash
pytest -v
```

### Verification Against Acceptance Checks:
- **Instructor test vectors**: Verifies empty string, NIST `"abc"`, and custom payloads against standard SHA-256.
- **Reject malformed hex**: Confirms odd-length strings and non-hex characters raise errors and exit with code 1.
- **Distinguish trailing newline**: Proves `"Alice pays Bob 10"`, `"Alice pays Bob 10\n"`, and `"Alice pays Bob 10\r\n"` yield three unique digests.
- **100 MB streaming test**: Generates a 100 MB file, hashes it, and monitors memory using `tracemalloc`. Verifies peak memory growth during hashing is under 5 MB (far below 100 MB).
