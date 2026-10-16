#!/usr/bin/env python3
"""Streaming log parser for the incident log dump.

Reads the log file one line at a time (constant memory) and sorts every physical
line into exactly one of two buckets, so they close on the sum a reader checks:

    total = processed + malformed

  processed -- a usable record: valid JSON object carrying every required field
  malformed -- any line that is not a usable record

`malformed` is broken down underneath into the reasons a line was unusable
(invalid JSON, missing a required field, or a structural/blank line), but those
are detail; the headline numbers close on processed + malformed.

`errors` counts processed records whose level == "ERROR".

Judging vs repairing
--------------------
The dump is a single pretty-printed JSON array: it opens with `[`, closes with
`]`, and every element line ends with one separator comma. That single separator
comma is the known format, so a line is recognized as an element when it is a
JSON object optionally followed by exactly one trailing comma. Anything else is
*judged*, not repaired: a truncated object, a stack-trace line, a line with a
stray/doubled comma, or a non-object all fall through to malformed. We never
rewrite a line into something parseable and then call it clean.

Required fields are the ones a record is unusable without for summarization and
error counting; the four optional fields (host, request_id, trip_id,
duration_ms) are legitimately null/absent in the data. This list is mirrored in
the README's "Log format notes"; keep the two in sync.

Usage:
    python3 parse_logs.py <log_path>
"""
import json
import sys

REQUIRED_FIELDS = ("timestamp", "level", "service", "message")


def classify(line):
    """Classify one raw line. Returns (bucket, level_or_None).

    bucket is one of:
      "processed"  -- usable record (also returns its level)
      "structural" -- blank line or the array's `[` / `]` wrapper
      "invalid"    -- not valid JSON as an array element
      "missing"    -- valid JSON object missing a required field
    """
    s = line.strip()

    if not s or s in ("[", "]"):
        return "structural", None

    # Known format: a JSON object with at most ONE separator comma. More than
    # one trailing comma is a stray comma -> judged malformed, not repaired.
    if s.endswith(",") and not s.endswith(",,"):
        candidate = s[:-1]
    else:
        candidate = s

    try:
        record = json.loads(candidate)
    except json.JSONDecodeError:
        return "invalid", None

    if not isinstance(record, dict):
        return "invalid", None

    if any(field not in record for field in REQUIRED_FIELDS):
        return "missing", None

    return "processed", record.get("level")


def parse(path):
    c = {
        "total": 0,
        "processed": 0,
        "malformed": 0,
        "errors": 0,
        # breakdown of malformed (sums to malformed)
        "invalid": 0,
        "missing": 0,
        "structural": 0,
    }
    with open(path, encoding="utf-8") as f:
        for line in f:
            c["total"] += 1
            bucket, level = classify(line)
            if bucket == "processed":
                c["processed"] += 1
                if level == "ERROR":
                    c["errors"] += 1
            else:
                c["malformed"] += 1
                c[bucket] += 1
    return c


def main(argv):
    if len(argv) != 2:
        print("usage: python3 parse_logs.py <log_path>", file=sys.stderr)
        return 2

    try:
        c = parse(argv[1])
    except OSError as exc:
        print(f"error: cannot read {argv[1]}: {exc}", file=sys.stderr)
        return 1

    print(f"total:     {c['total']}")
    print(f"processed: {c['processed']}")
    print(f"malformed: {c['malformed']}")
    print(f"  - invalid JSON:            {c['invalid']}")
    print(f"  - missing required field:  {c['missing']}")
    print(f"  - structural (wrapper/blank): {c['structural']}")
    print(f"errors (of processed):     {c['errors']}")

    closes = c["processed"] + c["malformed"] == c["total"]
    print(
        f"check: processed + malformed = {c['processed']} + {c['malformed']} "
        f"= {c['processed'] + c['malformed']} == total {c['total']}  "
        f"[{'OK' if closes else 'MISMATCH'}]"
    )
    return 0 if closes else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
