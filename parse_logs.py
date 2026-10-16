#!/usr/bin/env python3
"""Streaming log parser for the incident log dump.

Reads the log file one line at a time (constant memory), parses each line as a
JSON object, skips anything malformed, and prints processed / error / malformed
counts.

The dump is a pretty-printed JSON array (`.jsonl` extension notwithstanding):
it opens with `[`, closes with `]`, and every record line ends with a comma.
Those structural artifacts are stripped per line so real records parse; a line
that still fails to decode is counted as malformed and skipped.

Usage:
    python3 parse_logs.py <log_path>
"""
import json
import sys


def parse(path):
    processed = 0  # lines parsed into a valid JSON object
    errors = 0     # processed records whose level == "ERROR"
    malformed = 0  # non-empty lines that could not be parsed

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Skip blanks and the array's `[` / `]` wrapper lines.
            if not line or line in ("[", "]"):
                continue
            # Records in the dump are comma-separated array elements.
            if line.endswith(","):
                line = line[:-1]

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                malformed += 1
                continue

            if not isinstance(record, dict):
                malformed += 1
                continue

            processed += 1
            if record.get("level") == "ERROR":
                errors += 1

    return processed, errors, malformed


def main(argv):
    if len(argv) != 2:
        print("usage: python3 parse_logs.py <log_path>", file=sys.stderr)
        return 2

    try:
        processed, errors, malformed = parse(argv[1])
    except OSError as exc:
        print(f"error: cannot read {argv[1]}: {exc}", file=sys.stderr)
        return 1

    print(f"processed: {processed}")
    print(f"errors:    {errors}")
    print(f"malformed: {malformed}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
