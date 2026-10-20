from __future__ import annotations

import argparse
import sys
from pathlib import Path

# force utf-8 on windows console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from hashlab import __version__
from hashlab.avalanche import compute_avalanche_bytes, compute_avalanche_file
from hashlab.canonical import hash_canonical_json
from hashlab.demo import (
    format_demo_result,
    run_all_demos,
    run_integer_vs_string_demo,
    run_key_order_demo,
    run_newline_demo,
    run_unicode_demo,
)
from hashlab.hasher import hash_bytes, hash_file, parse_hex


def handle_text(args: argparse.Namespace) -> int:
    text_val = args.text_arg if args.text_arg is not None else args.text_opt
    if text_val is None:
        if not sys.stdin.isatty():
            text_val = sys.stdin.read()
        else:
            sys.stderr.write("Error: Text input is required. Provide text as argument or via --text.\n")
            return 1

    data = text_val.encode("utf-8")
    byte_len, hex_digest, b64_digest = hash_bytes(data)
    sys.stdout.write(f"bytes: {byte_len}\n")
    sys.stdout.write(f"sha256: {hex_digest}\n")
    sys.stdout.write(f"base64: {b64_digest}\n")
    return 0


def handle_hex(args: argparse.Namespace) -> int:
    hex_val = args.hex_arg if args.hex_arg is not None else args.hex_opt
    if hex_val is None:
        if not sys.stdin.isatty():
            hex_val = sys.stdin.read().strip()
        else:
            sys.stderr.write("Error: Hexadecimal input is required. Provide hex as argument or via --hex.\n")
            return 1

    try:
        data = parse_hex(hex_val)
    except ValueError as e:
        sys.stderr.write(f"Error: {e}\n")
        return 1

    byte_len, hex_digest, b64_digest = hash_bytes(data)
    sys.stdout.write(f"bytes: {byte_len}\n")
    sys.stdout.write(f"sha256: {hex_digest}\n")
    sys.stdout.write(f"base64: {b64_digest}\n")
    return 0


def handle_file(args: argparse.Namespace) -> int:
    file_path = args.file_arg if args.file_arg is not None else args.file_opt
    if file_path is None:
        sys.stderr.write("Error: File path is required. Provide file as argument or via --file.\n")
        return 1

    try:
        byte_len, hex_digest, b64_digest = hash_file(file_path)
    except (FileNotFoundError, IsADirectoryError, OSError) as e:
        sys.stderr.write(f"Error: {e}\n")
        return 1

    sys.stdout.write(f"bytes: {byte_len}\n")
    sys.stdout.write(f"sha256: {hex_digest}\n")
    sys.stdout.write(f"base64: {b64_digest}\n")
    return 0


def handle_avalanche(args: argparse.Namespace) -> int:
    if args.bit is None:
        sys.stderr.write("Error: --bit <int> is required for avalanche analysis.\n")
        return 1

    if args.text is not None:
        data = args.text.encode("utf-8")
        try:
            orig_hex, mod_hex, changed = compute_avalanche_bytes(data, args.bit)
        except ValueError as e:
            sys.stderr.write(f"Error: {e}\n")
            return 1
    elif args.hex is not None:
        try:
            data = parse_hex(args.hex)
            orig_hex, mod_hex, changed = compute_avalanche_bytes(data, args.bit)
        except ValueError as e:
            sys.stderr.write(f"Error: {e}\n")
            return 1
    elif args.file is not None:
        try:
            orig_hex, mod_hex, changed = compute_avalanche_file(args.file, args.bit)
        except (ValueError, FileNotFoundError, IsADirectoryError, OSError) as e:
            sys.stderr.write(f"Error: {e}\n")
            return 1
    elif args.input_arg is not None:
        # positional fallback treated as text
        data = args.input_arg.encode("utf-8")
        try:
            orig_hex, mod_hex, changed = compute_avalanche_bytes(data, args.bit)
        except ValueError as e:
            sys.stderr.write(f"Error: {e}\n")
            return 1
    else:
        sys.stderr.write("Error: Must specify input using --text, --hex, or --file.\n")
        return 1

    sys.stdout.write(f"original_sha256: {orig_hex}\n")
    sys.stdout.write(f"modified_sha256: {mod_hex}\n")
    sys.stdout.write(f"changed_bits_in_digest: {changed}\n")
    return 0


def handle_canonical_json(args: argparse.Namespace) -> int:
    input_str: str | None = None

    if args.file is not None:
        p = Path(args.file)
        if not p.is_file():
            sys.stderr.write(f"Error: File not found: '{args.file}'\n")
            return 1
        try:
            input_str = p.read_text(encoding="utf-8")
        except Exception as e:
            sys.stderr.write(f"Error reading file '{args.file}': {e}\n")
            return 1
    elif args.text is not None:
        input_str = args.text
    elif args.input_arg is not None:
        p = Path(args.input_arg)
        if p.is_file():
            try:
                input_str = p.read_text(encoding="utf-8")
            except Exception as e:
                sys.stderr.write(f"Error reading file '{args.input_arg}': {e}\n")
                return 1
        else:
            input_str = args.input_arg
    else:
        if not sys.stdin.isatty():
            input_str = sys.stdin.read()
        else:
            sys.stderr.write("Error: Provide JSON via argument, --text, --file, or stdin.\n")
            return 1

    try:
        canon_str, byte_len, hex_digest, b64_digest = hash_canonical_json(input_str)
    except ValueError as e:
        sys.stderr.write(f"Error: {e}\n")
        return 1

    sys.stdout.write(f"canonical_json: {canon_str}\n")
    sys.stdout.write(f"bytes: {byte_len}\n")
    sys.stdout.write(f"sha256: {hex_digest}\n")
    sys.stdout.write(f"base64: {b64_digest}\n")
    return 0


def handle_demo(args: argparse.Namespace) -> int:
    if args.newlines:
        sys.stdout.write(format_demo_result(run_newline_demo()) + "\n")
    elif args.unicode:
        sys.stdout.write(format_demo_result(run_unicode_demo()) + "\n")
    elif args.types:
        sys.stdout.write(format_demo_result(run_integer_vs_string_demo()) + "\n")
    elif args.keys:
        sys.stdout.write(format_demo_result(run_key_order_demo()) + "\n")
    else:
        for res in run_all_demos():
            sys.stdout.write(format_demo_result(res) + "\n\n")
    return 0


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hashlab",
        description="hashlab: diagnostic tool for bytes, hashes, avalanche analysis, and canonical json.",
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="subcommand", title="subcommands", required=True)

    p_text = subparsers.add_parser("text", help="Hash a UTF-8 text string.")
    p_text.add_argument("text_arg", nargs="?", default=None, help="Text to hash")
    p_text.add_argument("--text", "-t", dest="text_opt", default=None, help="Text to hash (via flag)")
    p_text.set_defaults(func=handle_text)

    p_hex = subparsers.add_parser("hex", help="Hash a hexadecimal byte string.")
    p_hex.add_argument("hex_arg", nargs="?", default=None, help="Hex string to hash")
    p_hex.add_argument("--hex", "-x", dest="hex_opt", default=None, help="Hex string to hash (via flag)")
    p_hex.set_defaults(func=handle_hex)

    p_file = subparsers.add_parser("file", help="Hash a file (streamed).")
    p_file.add_argument("file_arg", nargs="?", default=None, help="Path to file")
    p_file.add_argument("--file", "-f", dest="file_opt", default=None, help="Path to file (via flag)")
    p_file.set_defaults(func=handle_file)

    p_avalanche = subparsers.add_parser("avalanche", help="Flip one bit and report hamming distance.")
    p_avalanche.add_argument("input_arg", nargs="?", default=None, help="Text input")
    p_avalanche.add_argument("--text", default=None, help="Text input")
    p_avalanche.add_argument("--hex", default=None, help="Hex input")
    p_avalanche.add_argument("--file", default=None, help="File input")
    p_avalanche.add_argument("--bit", type=int, required=True, help="0-based bit index to flip")
    p_avalanche.set_defaults(func=handle_avalanche)

    p_canon = subparsers.add_parser("canonical-json", aliases=["canonical_json"], help="Canonicalize and hash JSON.")
    p_canon.add_argument("input_arg", nargs="?", default=None, help="JSON string or file path")
    p_canon.add_argument("--text", "-t", default=None, help="JSON string")
    p_canon.add_argument("--file", "-f", default=None, help="JSON file path")
    p_canon.set_defaults(func=handle_canonical_json)

    p_demo = subparsers.add_parser("demo", aliases=["demonstrate"], help="Show byte differences in visually similar inputs.")
    p_demo.add_argument("--newlines", action="store_true", help="Newline differences")
    p_demo.add_argument("--unicode", action="store_true", help="Unicode normalization")
    p_demo.add_argument("--types", action="store_true", help="Integer vs string")
    p_demo.add_argument("--keys", action="store_true", help="Key order in JSON")
    p_demo.set_defaults(func=handle_demo)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
